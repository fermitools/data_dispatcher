from fastapi import FastAPI, APIRouter
from fastapi.responses import Response, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi_utils.cbv import cbv
from a2wsgi import ASGIMiddleware
from typing import Optional
from data_dispatcher.db import DBProject, DBFileHandle, DBRSE, DBProximityMap       # , DBUser
from data_dispatcher import Version
from metacat.auth.server import BaseHandler, BaseApp, auth_router, gui_auth_router, install_exception_handlers, \
    sanitize
import urllib, os, yaml, time, json, pprint, logging
from urllib.parse import quote, unquote, unquote_plus
from wsdbtools import ConnectionPool
from datetime import timezone, datetime
from data_dispatcher.query import ProjectQuery
import os

logger = logging.getLogger("data_dispatcher.gui_server")

def json_response(text, media_type="text/json"):
    return Response(text, media_type=media_type)

def page_index(page, npages, page_size, url_prefix):
    last_page = npages - 1
    next_page = page + 1
    prev_page = page - 1
    if "?" not in url_prefix:
        url_prefix = url_prefix + "?"
    else:
        url_prefix = url_prefix + "&"
    first_page_link = f"{url_prefix}page=0&page_size={page_size}"
    prev_page_link = f"{url_prefix}page={prev_page}&page_size={page_size}"
    next_page_link = f"{url_prefix}page={next_page}&page_size={page_size}"
    last_page_link = f"{url_prefix}page={last_page}&page_size={page_size}"

    index_page_links = None
    if npages > 1:
        index_page_links = []
        if page > 1:
            index_page_links.append((1, first_page_link))
        if page > 2:
            index_page_links.append(("...", None))
        if prev_page >= 0:
            index_page_links.append((prev_page+1, prev_page_link))
        index_page_links.append((page+1, None))
        if page < last_page:
            index_page_links.append((next_page+1, next_page_link))
        if next_page < last_page - 1:
            index_page_links.append(("...", None))
        if next_page < last_page:
            index_page_links.append((last_page+1, last_page_link))
    #print(f"page_index({page}, {npages}) -> ", index_page_links)
    return index_page_links

projects_router = APIRouter()

@cbv(projects_router)
class ProjectsHandler(BaseHandler):
    
    HandleStateOrder = {
        state:i for i, state in enumerate([
            "available", 
            "reserved",
            "not found",
            "found",
            "done",
            "failed"
        ])
    }
    
    def parse_datetime(self, dt):
        dt = (dt or "").strip()
        if not dt:  return None
        utc = dt.endswith("UTC")
        if utc:
            dt = dt[:-3].strip()
        date, time = None, None
        if " " in dt:
            dt = datetime.strptime(dt, "%Y-%m-%d %H:%M:%S")
        else:
            dt = datetime.strptime(dt, "%Y-%m-%d")
        dt = dt.replace(tzinfo=timezone.utc)
        return dt

    @projects_router.api_route("/P/projects", methods=["GET", "POST"])
    @sanitize()
    def projects(self, message: str = "", page: str = "0", page_size: str = "1000"):
        db = self.App.db()
        page = int(page)
        page_size = int(page_size)
        istart = page*page_size
        form_dict = self.form
        user, _ = self.authenticated_user()
        
        search_user = None
        search_active_only = True
        search_created_after = search_created_before = None
        
        form_posted = self.request.method == "POST"
        if form_posted:
            search_user = form_dict.get("search_user", "").strip() or None
            search_active_only = form_dict.get("search_active_only", "off") == "on"
            search_created_after = self.parse_datetime(form_dict.get("search_created_after"))
            search_created_before = self.parse_datetime(form_dict.get("search_created_before"))
        
        state = "active" if search_active_only else None

        do_search = form_dict.get("action") == "Search"
        query_text = ""
        if do_search:
            query_text = form_dict.get("query")
            if query_text:
                query = ProjectQuery(query_text)
                sql = query.sql()
                projects = list(DBProject.from_sql(db, sql))
                projects = [p for p in projects 
                    if (not search_user or p.Owner == search_user)
                        and (not search_active_only or p.State == "active")
                ]
            else:
                projects = DBProject.list(db, with_handle_counts=False, state=state, owner=search_user)
            projects = [p for p in projects 
                            if
                                (search_created_after is None or p.CreatedTimestamp >= search_created_after) and
                                (search_created_before is None or p.CreatedTimestamp <= search_created_before)
                            ]
        else:
            projects = list(DBProject.list(db, with_handle_counts=False, state='active'))
            
        projects = sorted(projects, key=lambda p: p.ID)
            
        nprojects = len(projects)
        logger.debug("projects found: %s", nprojects)
        npages = (nprojects + page_size - 1)//page_size
        projects = projects[istart:istart + page_size]
        for project in projects:
            if project.HandleCounts:
                ntotal = sum(project.HandleCounts.values())
                project._HandleShares = {state:float(count)/ntotal for state, count in project.HandleCounts.items()}
        if message:   message = urllib.parse.unquote_plus(message)

        last_page = npages - 1
        next_page = page + 1
        prev_page = page - 1
        next_page_link = f"projects?page={next_page}&page_size={page_size}"
        prev_page_link = f"projects?page={prev_page}&page_size={page_size}"
        first_page_link = f"projecst?page=0&page_size={page_size}"
        last_page_link = f"projects?page={last_page}&page_size={page_size}"

        index_page_links = None
        if npages > 1:
            index_page_links = {}
            if page != first_page_link: index_page_links[0] = first_page_link
            if prev_page >= 0: index_page_links[prev_page] = prev_page_link
            if next_page < npages: index_page_links[next_page] = next_page_link
            if page != last_page: index_page_links[last_page] = last_page_link
            index_page_links[page] = None
            index_page_links = sorted(index_page_links.items())

        logger.debug("page_index: %s", index_page_links)

        return self.render_to_response("projects.html", projects=projects, handle_states = DBFileHandle.States, message=message,
            page = page, page_index = index_page_links
        )

    @projects_router.api_route("/P/handle_logs", methods=["GET", "POST"])
    @sanitize()
    def handle_logs(self, project_id: Optional[str] = None):
        db = self.App.db()
        project_id = int(project_id)
        project = DBProject.get(db, project_id)
        if project is None:
            return HTMLResponse("Project not found", status_code=404)
        log_records = sorted([entry for entry in project.handles_log() if entry.Type == "state"], key = lambda e:e.T)
        return json_response(json.dumps([e.as_jsonable() for e in log_records]))

    @projects_router.api_route("/P/handle_state_counts", methods=["GET", "POST"])
    @sanitize()
    def handle_state_counts(self, project_id: Optional[str] = None):
        db = self.App.db()
        project_id = int(project_id)
        project = DBProject.get(db, project_id)
        if project is None:
            return HTMLResponse("Project not found", status_code=404)
        counts = {state:0 for state in DBFileHandle.States}
        for did, state in project.handle_states().items():
            counts[state] = counts.get(state, 0) + 1
        return json_response(json.dumps(counts))

    @projects_router.api_route("/P/handle_counts_history", methods=["GET", "POST"])
    @sanitize()
    def handle_counts_history(self, project_id: Optional[str] = None):
        db = self.App.db()
        project_id = int(project_id)
        project = DBProject.get(db, project_id)
        if project is None:
            return HTMLResponse("Project not found", status_code=404)
        log_records = sorted([entry for entry in project.handles_log() if entry.Type == "state"], key = lambda e:e.T)
        if not log_records:
            return json_response("[]")
        tmin = log_records[0].T.timestamp()
        tmax = log_records[1].T.timestamp()
        interval = tmax - tmin
        bin = 1.0
        if interval >= 3600:
            bin = 10.0
        if interval >= 3600*12:
            bin = 60.0
        if interval >= 3600*24:
            bin = 300.0
        history = []        # [{counts,t}, ...]
        n_ready = n_reserved = n_failed = n_done = 0
        last_t = None
        counts = {"initial":0, "reserved":0, "done":0, "failed":0}
        entry = None
        for entry in log_records:
            t = int((entry.T.timestamp()-tmin)/bin)
            if last_t is None:
                last_t = t
            if t != last_t:
                data = counts.copy()
                data["t"] = last_t
                data["t_display"] = entry.T.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
                history.append(data)
                last_t = t
            state = entry["state"]
            old_state = entry.get("old_state")
            if not old_state and entry.get("event") == "worker_timeout":
                old_state = "reserved"
            assert state in counts and (old_state is None or old_state in counts)
            counts[state] += 1
            if old_state:
                counts[old_state] -= 1
        if not history or history[-1]["t"] != last_t:
            data = counts.copy()
            data["t"] = last_t
            data["t_display"] = entry.T.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S") if entry is not None else ""
            history.append(data)
        return json_response(json.dumps(history))

    @projects_router.api_route("/P/project", methods=["GET", "POST"])
    @sanitize()
    def project(self, project_id: Optional[str] = None, page: str = "0", page_size: str = "1000"):
        page = int(page)
        page_size = int(page_size)

        db = self.App.db()
        project_id = int(project_id)
        project = DBProject.get(db, project_id)
        
        if project is None:
            message = urllib.parse.quote_plus(f"Project {project_id} not found")
            self.redirect(f"./projects?message={message}")

        all_handles = sorted(project.handles(with_replicas=True, reload=True), 
                key=lambda h: (self.HandleStateOrder.get(h.state(), 100), h.Attempts, h.Namespace, h.Name))

        nhandles = len(all_handles)
        istart = page*page_size
        t0 = time.time()
        handles = all_handles[istart:istart+page_size]
        #handles = list(project.get_handles([h.did() for h in all_handles[istart:istart+page_size]]))
        npages = (nhandles + page_size - 1)//page_size
            
        available_handles = 0
        handle_counts_by_state = {state:0 for state in DBFileHandle.States}     # {state -> count}
        state_index = {}        # {state -> page number}
        for i, h in enumerate(all_handles):
            replicas = h.replicas()
            h.n_replicas = len(replicas)
            h.n_available_replicas = len([r for r in replicas.values() if r.is_available()]) 
            state = h.state()
            #print("handle State:", h.State, "  state():", state)
            handle_counts_by_state[state] = handle_counts_by_state.get(state, 0) + 1

            if not state in state_index:
                state_index[state] = i//page_size

        state_page_links = {s: f"project?project_id={project_id}&page={p}&page_size={page_size}#state:{s}" for s, p in state_index.items()}

            
        #handles_log = {}            # {did -> [log record, ...]}
        #files_log = {}              # {did -> [log record, ...]}
        #combined_log = {}
        project_log = project.get_log()
        
        #for log_record in project.handles_log():
        #    #print("gui.project(): handle log_record:", log_record)
        #    did = log_record.Namespace + ":" + log_record.Name
        #    handles_log.setdefault(did, []).append(log_record)
        #    combined_log.setdefault(did, []).append(log_record)

        if False:
            for log_record in project.files_log():
                did = log_record.Namespace + ":" + log_record.Name
                files_log.setdefault(did, []).append(log_record)
                combined_log.setdefault(did, []).append(log_record)

            for did in list(combined_log.keys()):
                combined_log[did] = sorted(combined_log[did], key=lambda r: r.T)
        #print("gui.project(): handles_log:", handles_log)
    
        return self.render_to_response("project.html", project=project,
            handles=handles,
            available_handles=available_handles,
            handle_counts_by_state=handle_counts_by_state, states=DBFileHandle.States,
            project_log = project.get_log(),
            page = page, 
            page_index = page_index(page, npages, page_size, f"project?project_id={project_id}"), 
            state_index = state_page_links
        )

    @projects_router.api_route("/P/project_handles_log", methods=["GET", "POST"])
    @sanitize()
    def project_handles_log(self, project_id: Optional[str] = None, page: str = "0", page_size: str = "1000"):
        page = int(page)
        page_size = int(page_size)

        db = self.App.db()
        project_id = int(project_id)
        project = DBProject.get(db, project_id)
        
        if project is None:
            message = urllib.parse.quote_plus(f"Project {project_id} not found")
            self.redirect(f"./projects?message={message}")

        all_records = [record for record in project.handles_log() if record.Data.get("event") != "create"]
        all_records = sorted(all_records, key=lambda r:r.T)
        nrecords = len(all_records)
        npages = (nrecords + page_size - 1)//page_size
        istart = page*page_size
        records = all_records[istart:istart+page_size]

        for record in records:
            data = record.Data.copy()
            data.pop("old_state", None)
            data.pop("state", None)
            data.pop("event", None)
            data.pop("worker", None)
            record._RestOfData = data

        t0 = time.time()

        return self.render_to_response("project_handles_log.html", project=project,
            records=records,
            page = page, page_index = page_index(page, npages, page_size,f"project_handles_log?project_id={project_id}")
        )

    @projects_router.api_route("/P/handle", methods=["GET", "POST"])
    @sanitize()
    def handle(self, project_id: Optional[str] = None, namespace: Optional[str] = None, name: Optional[str] = None):
        db = self.App.db()
        handle = DBFileHandle.get(db, int(project_id), namespace, name)
        if handle is None:
            self.redirect(f"./project?project_id={project_id}&error=Handle+not+found")
        handle_log = list(handle.get_log(reversed=True))
        for entry in handle_log:
            data = entry.Data.copy()
            data.pop("old_state", None)
            data.pop("state", None)
            data.pop("event", None)
            data.pop("worker", None)
            entry._RestOfData = data
        return self.render_to_response("handle.html", project_id=project_id, handle=handle, handle_log = handle_log)

    def cvt_time_delta(self, delta):
        if delta[-1] in "smhd":
            unit = delta[-1]
            unit = {
                's':    1,
                'm':    60,
                'h':    3600,
                'd':    24*3600
            }[unit]
            return unit * float(delta[:-1])
        else:
            return float(delta)
        
    @projects_router.api_route("/P/handle_event_counts", methods=["GET", "POST"])
    @sanitize()
    def handle_event_counts(self, t0: Optional[str] = None, window: Optional[str] = None, bin: Optional[str] = None):
        db = self.App.db()
        if t0 is None:
            t0 = time.time() - self.cvt_time_delta(window)
        else:
            t0 = float(t0)
        bin = self.cvt_time_delta(bin)
        t0 = int(t0/bin)*bin
        t0, t1, events, counts = DBFileHandle.event_counts(db, t0, bin)
        return json_response(json.dumps({
            "t0": t0,
            "t1": t1,
            "events": events,
            "counts": counts,
            "bin": bin
        }), media_type="application/json")
        
    @projects_router.api_route("/P/stats", methods=["GET", "POST"])
    def stats(self):
        return self.render_to_response("stats.html")

rse_router = APIRouter()

@cbv(rse_router)
class RSEHandler(BaseHandler):
    
    @rse_router.api_route("/R/proximity_map", methods=["GET", "POST"])
    @sanitize()
    def proximity_map(self, message: str = ""):
        enabled_rses = set(r.Name for r in DBRSE.list(self.App.db(), include_disabled=False))
        pmap = self.App.proximity_map(rses=enabled_rses)
        overrides = pmap.Overrides
        overrides_cpus = sorted(overrides.keys(), key=lambda x: "-" if x.upper() == "DEFAULT" else x)
        overrides_rses = set()
        for m in overrides.values():
            overrides_rses |= set(m.keys())
        overrides_rses = sorted(overrides_rses, key=lambda x: "-" if x.upper() == "DEFAULT" else x)
        return self.render_to_response("proximity_map.html", proximity_map = pmap, default_proximity=pmap.Default,
            overrides = overrides, overrides_cpus=overrides_cpus, overrides_rses=overrides_rses
        )

    @rse_router.api_route("/R/rses", methods=["GET", "POST"])
    @rse_router.api_route("/R/index", methods=["GET", "POST"])
    @sanitize()
    def rses(self):
        user, auth_error = self.authenticated_user()
        is_admin = user is not None and user.is_admin()
        rses = list(DBRSE.list(self.App.db(), include_disabled=True))
        rses = sorted(rses, key=lambda r: (0 if r.Enabled else 1, r.Name))
        return self.render_to_response("rses.html", rses=rses, is_admin=is_admin)

    @rse_router.api_route("/R", methods=["GET", "POST"])
    @rse_router.api_route("/R/", methods=["GET", "POST"])
    def default(self):
        self.redirect(self.appRootPath() + "/R/index")
    
    @rse_router.api_route("/R/rse", methods=["GET", "POST"])
    @rse_router.api_route("/R/rse/{relpath:path}", methods=["GET", "POST"])
    @sanitize()
    def rse(self, relpath: str = "", name: Optional[str] = None):
        name = name or relpath
        rse = DBRSE.get(self.App.db(), name)
        if rse is None:
            self.redirect("./rses")
        user, auth_error = self.authenticated_user()
        is_admin = user is not None and user.is_admin()
        mode = "edit" if is_admin else "view"
        return self.render_to_response("rse.html", rse=rse, mode=mode)

    @rse_router.api_route("/R/create", methods=["GET", "POST"])
    @sanitize()
    def create(self):
        user, auth_error = self.authenticated_user()
        is_admin = user is not None and user.is_admin()
        if not is_admin:
            self.redirect("./rses")
        return self.render_to_response("rse.html", is_admin=is_admin, mode="create")

    def parse_proximity_map(self, text):
        pmap = []
        for line in text.split("\n"):
            line = line.strip()
            if line:
                site, proximity = line.split(":", 1)
                site = site.strip()
                proximity = int(proximity.strip())
                pmap.append([site, proximity])

    @rse_router.api_route("/R/do_create", methods=["GET", "POST"])
    @sanitize()
    def do_create(self):
        user, auth_error = self.authenticated_user()
        is_admin = user is not None and user.is_admin()
        if not is_admin:
            self.redirect("./rses")
        
        name = self.form["name"]
        rse = DBRSE.create(self.App.db(), name)
        self._do_update(rse, self.form)
        self.redirect(f"./rses")
        
    @rse_router.api_route("/R/do_update", methods=["GET", "POST"])
    @sanitize()
    def do_update(self):
        user, auth_error = self.authenticated_user()
        is_admin = user is not None and user.is_admin()
        if not is_admin:
            self.redirect("./rses")
        
        name = self.form["name"]
        rse = DBRSE.get(self.App.db(), name)
        if rse is None:
            self.redirect("./rses")
        self._do_update(rse, self.form)
        self.redirect(f"./rses")
        
    def _do_update(self, rse, form):
        rse.Type = form.get("type", "")
        rse.Tape = form.get("is_tape", "no") != "no"
        rse.Available = form.get("is_available", "no") != "no"
        rse.RemovePrefix = form.get("remove_pefix", "")
        rse.AddPrefix = form.get("add_pefix", "")
        rse.PollURL = form.get("poll_url") or None
        rse.PinURL = form.get("pin_url") or None
        rse.PinPrefix = form.get("pin_prefix") or None
        rse.Description = form.get("description", "")
        rse.Preference = int(form.get("preference", 0))
        rse.Enabled = form.get("is_enabled", "no") != "no"
        rse.save()


top_router = APIRouter()

@cbv(top_router)
class TopHandler(BaseHandler):

    @top_router.api_route("/", methods=["GET", "POST"])
    @top_router.api_route("/index", methods=["GET", "POST"])
    def index(self):
        self.redirect(self.appRootPath() + "/P/projects")


def pretty_time_delta(t):
    if t == None:   return ""
    sign = ''
    if t < 0:   
        sign = '-'
        t = -t
    seconds = t
    if seconds < 60:
        out = '%.1fs' % (seconds,)
    elif seconds < 3600:
        seconds = int(seconds)
        minutes = seconds // 60
        seconds = seconds % 60
        out = '%dm%ds' % (minutes, seconds)
    elif seconds < 3600*24:
        seconds = int(seconds)
        minutes = seconds // 60
        hours = minutes // 60
        minutes = minutes % 60
        out = '%dh%02dm' % (hours, minutes)
    else:
        seconds = int(seconds)
        minutes = seconds // 60
        hours = minutes // 60
        minutes = minutes % 60
        days = hours // 24
        hours = hours % 24
        out = "%dd%02dh%02dm" % (days, hours, minutes)
        
    return sign + out

def as_dt_utc(t):
    from datetime import datetime
    if t is None:   return ""
    if isinstance(t, datetime):
        t = t.timestamp()
    if isinstance(t, (int, float)):
        t = datetime.fromtimestamp(t, timezone.utc)
    return t.strftime("%D&nbsp;%H:%M:%S")
    
def pprint_data(data):
    import pprint
    return pprint.pformat(data, indent=2)
    
def format_log_data(data):
    import pprint
    parts = []
    need_break = False
    first_line = True
    for k, v in sorted(data.items()):
        formatted = '%s=<span style="white-space:pre">%s</span>&nbsp; ' % (k, pprint.pformat(v))
        if not first_line and (isinstance(v, (dict, list)) or need_break):
            parts.append("<br/>")
        parts.append(formatted)
        need_break = isinstance(v, (dict, list))
        first_line = False
    return "".join(parts)
    
def none_as_blank(x):
    if x is None:   return ''
    else: return str(x)

class App(BaseApp):
    
    def __init__(self, config, prefix):
        BaseApp.__init__(self, config, prefix=prefix)
        self.Config = config
        proximity_cfg = config.get("proximity_map", {})
        self.DefaultProximity = proximity_cfg.get("default_proximity", -1)
        self.PMDefaults = proximity_cfg.get("defaults", {})
        self.PMOverrides = proximity_cfg.get("overrides", {})
        self.SiteTitle = config.get("web_server", {}).get("site_title", "DEMO Data Dispatcher")
        self.MetaCatURL = config.get("metacat_url")
        self.init_auth_core(config)

    def proximity_map(self, rses=None):
        return DBProximityMap(self.db(), default=self.DefaultProximity, rses=rses, defaults=self.PMDefaults, overrides=self.PMOverrides)

    def init(self):
        #print("App.init... prefix:", self.Prefix)
        templdir = ScriptHome
        self.initJinjaEnvironment(
            tempdirs=[templdir, "."],
            globals={
                "GLOBAL_Version": Version, 
                "GLOBAL_SiteTitle": self.SiteTitle,
                "GLOBAL_MetaCatURL": self.MetaCatURL
            },
            filters = {
                "pretty_time_delta": pretty_time_delta,
                "format_log_data": format_log_data,
                "as_dt_utc": as_dt_utc,
                "none_as_blank": none_as_blank
            }
        )

# templates and static files are next to this module
ScriptHome = os.path.dirname(os.path.abspath(__file__))

def create_application(config=None):
    if config is None:
        config = os.environ.get("DATA_DISPATCHER_CFG")
        if not config:
            return None
    if isinstance(config, str):
        config = yaml.load(open(config, "r"), Loader=yaml.SafeLoader)
    prefix = (config.get("gui_prefix") or "").rstrip("/")
    app = App(config, prefix)
    app.init()

    fastapi_app = FastAPI(title="Data Dispatcher GUI", version=Version, docs_url=None, redoc_url=None, openapi_url=None)
    fastapi_app.state.metacat_app = app         # used by metacat.auth.server.BaseHandler
    install_exception_handlers(fastapi_app)
    fastapi_app.include_router(top_router, prefix=prefix)
    fastapi_app.include_router(projects_router, prefix=prefix)
    fastapi_app.include_router(rse_router, prefix=prefix)
    # metacat auth routers use paths relative to where they are included
    fastapi_app.include_router(gui_auth_router, prefix=prefix + "/A")
    fastapi_app.include_router(auth_router, prefix=prefix + "/A")
    fastapi_app.mount(prefix + "/static", StaticFiles(directory=ScriptHome + "/static"), name="static")
    return fastapi_app

# FastAPI (ASGI) application, e.g. for uvicorn
app = create_application()

# WSGI application, e.g. for mod_wsgi or uWSGI
application = ASGIMiddleware(app) if app is not None else None

if __name__ == "__main__":
    import getopt, sys
    import uvicorn

    opts, args = getopt.getopt(sys.argv[1:], "c:l")
    opts = dict(opts)
    config = yaml.load(open(opts["-c"], "r"), Loader=yaml.SafeLoader)
    server_config = config.get("web_server", {})
    port = server_config.get("gui_port", 8080)
    print("Starting on port:", port)
    access_log = "-l" in opts or bool(server_config.get("gui_logging"))
    uvicorn.run(create_application(config), host="0.0.0.0", port=port, access_log=access_log)
