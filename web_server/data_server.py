from fastapi import FastAPI, APIRouter
from fastapi.responses import Response, HTMLResponse
from fastapi_utils.cbv import cbv
from a2wsgi import ASGIMiddleware
from typing import Optional
from data_dispatcher.db import DBProject, DBFileHandle, DBRSE, DBProximityMap
from data_dispatcher.logs import Logged, init_logger
from data_dispatcher import Version
from metacat.common import SignedToken, SignedTokenExpiredError, SignedTokenImmatureError, \
    SignedTokenUnacceptedAlgorithmError, SignedTokenSignatureVerificationError
from metacat.auth.server import BaseHandler, BaseApp, auth_router, install_exception_handlers
import json, urllib.parse, yaml, secrets, hashlib, logging
import requests
from datetime import datetime, timedelta
from data_dispatcher.query import ProjectQuery
import os

logger = logging.getLogger("data_dispatcher.data_server")

def to_bytes(x):
    if not isinstance(x, bytes):
        x = x.encode("utf-8")
    return x

def to_str(x):
    if isinstance(x, bytes):
        x = x.decode("utf-8")
    return x

def error_response(status, text):
    # same as webpie's (status, text) response: text/html
    return HTMLResponse(text, status_code=status)

def json_response(text):
    return Response(text, media_type="text/json")

data_router = APIRouter()

@cbv(data_router)
class Handler(BaseHandler):

    @data_router.api_route("/version", methods=["GET", "POST"])
    def version(self):
        return HTMLResponse(Version)

    @data_router.api_route("/probe", methods=["GET", "POST"])
    def probe(self):
        try:
            db = self.App.db()
        except:
            return error_response(500, "Database connection error")
        else:
            return HTMLResponse("OK")

    @data_router.api_route("/create_project", methods=["GET", "POST"])
    def create_project(self):
        #print("create_project()...")
        user, error = self.authenticated_user()
        #print("authenticated user:", user)
        if user is None:
            logger.info("create_project: returning 401: %s", error)
            return error_response(401, error)
        specs = json.loads(to_str(self.body))
        #print("specs:", specs)
        files = specs["files"]
        query = specs.get("query")
        worker_timeout = specs.get("worker_timeout")
        if worker_timeout is not None:
            worker_timeout = timedelta(seconds=worker_timeout)
        idle_timeout = specs.get("idle_timeout")
        if idle_timeout is not None:
            idle_timeout = timedelta(seconds=idle_timeout)
        attributes = specs.get("project_attributes", {})
        virtual = attributes.get("virtual", None)
        #print("opening DB...")
        db = self.App.db()
        #print("calling DBProject.create()...")
        project = DBProject.create(db, user.Username, attributes=attributes, query=query, worker_timeout=worker_timeout,
                        idle_timeout=idle_timeout, users=specs.get("users", []), roles=specs.get("roles", []))
        files_converted = []
        for f in files:
            if isinstance(f, str):
                try:
                    namespace, name = f.split(":")
                except:
                    return error_response(400, f"Invalid file specification: {f} - can not parse as namespace:name")
                files_converted.append({"namespace": namespace, "name":name})
            elif isinstance(f, dict):
                if "namespace" not in f or "name" not in f:
                    return error_response(400, f"Invalid file specification: {f} - namespace or name missing")
                attrs = f.get("attributes", {})
                if not isinstance(attrs, dict):
                    return error_response(400, f"Invalid file specification: {f} - invalid file attributes specification, expected a dictionary")
                files_converted.append({
                    "namespace":f["namespace"],
                    "name":f["name"],
                    "attributes":attrs
                })
            else:
                return error_response(400, f"Invalid file specification: {f} - unsupported type")
        project.add_files(files_converted)
        self.App.project_created(project.ID)
        return json_response(json.dumps(project.as_jsonable(with_handles=True)))

    @data_router.api_route("/delete_project", methods=["GET", "POST"])
    def delete_project(self, project_id: Optional[str] = None):
        if not project_id:
            return error_response(400, "Project id must be specified")
        user, error = self.authenticated_user()
        if user is None:
            return error_response(401, error)

        project_id = int(project_id)
        db = self.App.db()
        project = DBProject.get(db, project_id)
        if project is None:
            return error_response(404, "Project not found")
        if user.Username != project.Owner and not user.is_admin():
            return error_response(403, "Forbidden")
        project.delete()
        return json_response("null")

    @data_router.api_route("/activate_project", methods=["GET", "POST"])
    def activate_project(self, project_id: Optional[str] = None):
        if not project_id:
            return error_response(400, "Project id must be specified")
        user, error = self.authenticated_user()
        if user is None:
            return error_response(401, error)

        project_id = int(project_id)
        db = self.App.db()
        project = DBProject.get(db, project_id)
        if project is None:
            return error_response(404, "Project not found")
        if user.Username != project.Owner and not user.is_admin():
            return error_response(403, "Forbidden")
        project.activate()
        return json_response(json.dumps(project.as_jsonable(with_replicas=True)))

    @data_router.api_route("/restart_project", methods=["GET", "POST"])
    def restart_project(self, project_id: Optional[str] = None, force: str = "no", failed_only: str = "yes"):
        force = force == "yes"
        failed_only = failed_only == "yes"
        if not project_id:
            return error_response(400, "Project id must be specified")
        user, error = self.authenticated_user()
        if user is None:
            return error_response(401, error)

        project_id = int(project_id)
        db = self.App.db()
        project = DBProject.get(db, project_id)
        if project is None:
            return error_response(404, "Project not found")
        if user.Username != project.Owner and not user.is_admin():
            return error_response(403, "Forbidden")
        project.restart(force=force, failed_only=failed_only)
        return json_response(json.dumps(project.as_jsonable(with_replicas=True)))

    @data_router.api_route("/restart_handles", methods=["GET", "POST"])
    def restart_handles(self):
        params = json.loads(to_str(self.body))
        project_id = params.get("project_id")
        if not project_id:
            return error_response(400, "Project id must be specified")
        project_id = int(project_id)

        user, error = self.authenticated_user()
        if user is None:
            return error_response(401, error)

        db = self.App.db()
        project = DBProject.get(db, project_id)
        if project is None:
            return error_response(404, "Project not found")
        if user.Username != project.Owner and not user.is_admin():
            return error_response(403, "Forbidden")

        dids = params.get("handles")
        if dids is not None:
            project.restart_handles(dids=dids)
        else:
            states = [s for s in DBFileHandle.States if params.get(s)]
            project.restart_handles(states=states)

        return json_response(json.dumps(project.as_jsonable(with_replicas=True)))

    @data_router.api_route("/copy_project", methods=["GET", "POST"])
    def copy_project(self):
        user, error = self.authenticated_user()
        if user is None:
            return error_response(401, error)
        specs = json.loads(to_str(self.body))
        project_attributes = specs.get("project_attributes", {})
        file_attributes = specs.get("file_attributes", {})
        project_id = specs["project_id"]
        #print(specs.get("files"))
        db = self.App.db()
        original_project = DBProject.get(db, project_id)
        if original_project is None:
            return error_response(404, "Project not found")

        worker_timeout = specs.get("worker_timeout", original_project.WorkerTimeout)
        idle_timeout = specs.get("idle_timeout", original_project.IdleTimeout)
        if type(worker_timeout) == float:
            worker_timeout = worker_timeout
        elif worker_timeout == "no timeout":
            worker_timeout = None
        elif worker_timeout == "default" or worker_timeout == None:
            worker_timeout = original_project.WorkerTimeout
        if type(idle_timeout) == float:
            idle_timeout = idle_timeout
        elif idle_timeout == "no timeout":
            idle_timeout = None
        elif idle_timeout == "default" or idle_timeout == None:
            idle_timeout = original_project.IdleTimeout

        files_updated = []
        for h in original_project.handles():
            attrs = h.Attributes.copy()
            attrs.update(file_attributes)
            files_updated.append(dict(
                namespace=h.Namespace,
                name=h.Name,
                attributes=attrs
            ))
        project_attrs = original_project.Attributes.copy()
        project_attrs.update(project_attributes)
        project = DBProject.create(db, user.Username, attributes=project_attrs, query=original_project.Query, worker_timeout=worker_timeout, idle_timeout=idle_timeout)
        project.add_files(files_updated)
        project.add_log("event", event="copied", source=project_id, override=dict(
            project=project_attrs, file=file_attributes
        ))
        self.App.project_created(project.ID)
        return json_response(json.dumps(project.as_jsonable(with_handles=True)))

    @data_router.api_route("/cancel_project", methods=["GET", "POST"])
    def cancel_project(self, project_id: Optional[str] = None):
        if not project_id:
            return error_response(400, "Project id must be specified")
        user, error = self.authenticated_user()
        if user is None:
            return error_response(401, error)

        project_id = int(project_id)
        db = self.App.db()
        project = DBProject.get(db, project_id)
        if project is None:
            return error_response(404, "Project not found")
        if user.Username != project.Owner and not user.is_admin():
            return error_response(403, "Forbidden")
        project.cancel()
        return json_response(json.dumps(project.as_jsonable(with_replicas=True)))

    @data_router.api_route("/next_file", methods=["GET", "POST"])
    def next_file(self, project_id: Optional[str] = None, worker_id: Optional[str] = None, cpu_site: Optional[str] = None):
        #print("next_file...")
        user, error = self.authenticated_user()
        if user is None:
            return error_response(401, error)
        if worker_id is None or project_id is None:
            return error_response(400, "Project ID and Worker ID must be specified")
        db = self.App.db()
        project_id = int(project_id)
        project = DBProject.get(db, project_id)
        if not project:
            return error_response(404, "Project not found")
        if not (user.is_admin() or project.authorized_user(user.Username)):
            return error_response(403, "Not authorized")
        if project.State == "abandoned":
            project.activate()
        elif project.State != "active":
            return error_response(400, f"Inactive project. State={project.State}")
        handle, reason, retry = project.reserve_handle(worker_id, virtual=project.Attributes.get('virtual', False))
        if handle is None:
            out = {
                "handle": None,
                "reason": reason,
                "retry": retry
            }
        else:
            pmap = self.App.proximity_map()
            info = handle.as_jsonable(with_replicas=not project.Attributes.get('virtual',False))
            info["replicas"] = {
                    rse: r for rse, r in info.get("replicas", {}).items()
                    if r["available"] and r["rse_available"]
            }
            for rse, r in info.get("replicas", {}).items():
                try:
                    proximity = pmap.proximity(cpu_site, rse)
                except KeyError:
                    proximity = None
                r["preference"] = r["proximity"] = proximity
            info["project_attributes"] = project.Attributes or {}
            out = {
                "handle": info,
                "reason": "reserved",
                "retry": False
            }
        return json_response(json.dumps(out))

    @data_router.api_route("/release", methods=["GET", "POST"])
    def release(self, handle_id: Optional[str] = None, failed: str = "no", retry: str = "yes", worker_id: str = ""):
        if handle_id is None:
            return error_response(400, "File Handle ID (<project_id>:<namespace>:<name>) must be specified")
        user, error = self.authenticated_user()
        if user is None:
            return error_response(401, error)

        db = self.App.db()

        project_id, namespace, name = DBFileHandle.unpack_id(handle_id)

        project = DBProject.get(db, project_id)
        if project is None:
            return error_response(404, "Project not found")

        if not user.is_admin() and user.Username != project.Owner:
            return error_response(403, "Not authorized")

        handle = project.handle(namespace, name)
        if worker_id and handle.WorkerID != worker_id:
            return error_response(403, "Not authorized: wrong worker_id")

        failed = failed == "yes"
        retry = retry == "yes"

        handle = project.release_handle(namespace, name, failed, retry)
        if handle is None:
            return error_response(404, "Handle not found or was not reserved")
        if project.State == "abandoned":
            project.activate()
        return json_response(json.dumps(handle.as_jsonable()))

    def ______reset_file(self, handle_id=None, force="no"):
        # not fully implemented. need to be careful with the project status update - possible race condition
        if handle_id is None:
            return error_response(400, "File Handle ID (<project_id>:<namespace>:<name>) must be specified")
        user, error = self.authenticated_user()
        if user is None:
            return error_response(401, error)

        db = self.App.db()

        project_id, namespace, name = DBFileHandle.unpack_id(handle_id)

        project = DBProject.get(db, project_id)
        if project is None:
            return error_response(404, "Project not found")

        if not user.is_admin() and user.Username != project.Owner:
            return error_response(403, "Not authorized")

        force = force == "yes"

        handle = project.handle(namespace, name)
        if handle is None:
            return error_response(404, "Handle not found")
        if not force and handle.is_reserved():
            return error_response(400, "Handle is reserved")

        handle.reset()
        return json_response(json.dumps(handle.as_jsonable()))

    @data_router.api_route("/project_files", methods=["GET", "POST"])
    def project_files(self, project_id: Optional[str] = None, state: Optional[str] = None, ready_only: str = "no"):
        if project_id is None:
            return error_response(400, "Project ID must be specified")
        ready_only = ready_only == "yes"
        db = self.App.db()
        project_id = int(project_id)
        project = DBProject.get(db, project_id)
        if not project: return error_response(404, "Project not found")
        if project.Attributes.get("virtual", False):
             ready_only = "no"
        handles = project.files(state=state, ready_only=ready_only)
        return json_response(json.dumps([h.as_jsonable(with_replicas=ready_only) for h in handles]))

    @data_router.api_route("/project", methods=["GET", "POST"])
    def project(self, project_id: Optional[str] = None, with_files: str = "yes", with_replicas: str = "yes"):
        with_files = with_files == "yes"
        with_replicas = with_replicas == "yes"
        db = self.App.db()
        project_id = int(project_id)
        project = DBProject.get(db, project_id)
        if not project:
            return error_response(404, "Project not found")
        #print("project(): with handles/replicas: ", with_files, with_replicas)
        jsonable = project.as_jsonable(with_handles=with_files, with_replicas=with_replicas)
        return json_response(json.dumps(jsonable))

    @data_router.api_route("/project_handles_log", methods=["GET", "POST"])
    def project_handles_log(self, project_id: Optional[str] = None):
        project_id = int(project_id)
        db = self.App.db()
        project = DBProject.get(db, project_id)
        if not project:
            return error_response(404, "Project not found")
        project_log = [x.as_jsonable() for x in project.handles_log()]
        return json_response(json.dumps(project_log))

    @data_router.api_route("/projects", methods=["GET", "POST"])
    def projects(self, state: Optional[str] = None, not_state: Optional[str] = None, owner: Optional[str] = None, attributes: str = "",
                with_handles: str = "yes", with_replicas: str = "yes"):
        # default to only show projects owned by the current user
        user, error = self.authenticated_user()
        if user is None:
            return error_response(401, error)
        
        if owner is None:
            owner = user.Username
        elif owner == "all":
            owner = None
        else:
            owner = owner

        with_handles = with_handles == "yes"
        with_replicas = with_replicas == "yes"
        attributes = urllib.parse.unquote(attributes)
        attributes = json.loads(attributes) if attributes else None
        db = self.App.db()
        projects = DBProject.list(db, state=state, not_state=not_state, owner=owner, attributes=attributes)
        projects = sorted(projects, key=lambda p: p.ID)
        return json_response(json.dumps([p.as_jsonable(with_handles=with_handles, with_replicas=with_replicas) for p in projects]))

    @data_router.api_route("/search_projects", methods=["GET", "POST"])
    def search_projects(self):
        specs = json.loads(to_str(self.body))
        query_text = specs.get("query")
        owner = specs.get("owner")
        with_handles = specs.get("with_handles", False)
        with_replicas = specs.get("with_replicas", False)
        state = specs.get("state")
        query = ProjectQuery(query_text)
        sql = query.sql()
        db = self.App.db()
        projects = DBProject.from_sql(db, sql)
        projects = (project for project in projects
            if (not owner or project.Owner == owner)
                and (not state or project.State == state)
        )
        return json_response(json.dumps([p.as_jsonable(with_handles=with_handles, with_replicas=with_replicas) for p in projects]))

    @data_router.api_route("/file_handle", methods=["GET", "POST"])
    def file_handle(self, handle_id: Optional[str] = None, project_id: Optional[str] = None, file_id: Optional[str] = None, name: Optional[str] = None,
                namespace: Optional[str] = None):
        db = self.App.db()
        if handle_id:
            handle = DBFileHandle.get(db, int(handle_id))
        elif project_id is None:
            return error_response(400, "At least handle_id or project_id must be specified")
        elif file_id:
            handle = DBFileHandle.get_for_project(db, int(project_id), file_id=file_id)
        elif name:
            if not namespace:
                if not ':' in name:
                    return error_response(400, "File namespace unspecified")
                namespace, name = name.split(':', 1)
            handle = DBFileHandle.get_for_project(db, int(project_id), file_namespace=namespace, file_name=name)
        else:
            return error_response(400, "Either file_id, or file_name='namespace:name' or file_namespace and file_name must be specified")
        if not handle:
            return json_response("null")
        return json_response(json.dumps(handle.as_jsonable(with_replicas=True)))

    @data_router.api_route("/handles", methods=["GET", "POST"])
    def handles(self, project_id: Optional[str] = None, state: Optional[str] = None, not_state: Optional[str] = None, with_replicas: str = "no"):
        db = self.App.db()
        project_id = int(project_id)
        lst = DBFileHandle.list(db, project_id=project_id, not_state=not_state, state=state, with_replicas=with_replicas=="yes")
        return json_response(json.dumps([h.as_jsonable() for h in lst]))

    @data_router.api_route("/create_rse", methods=["GET", "POST"])
    def create_rse(self):
        user, error = self.authenticated_user()
        if user is None:
            return error_response(401, error)
        if not user.is_admin():
            return error_response(403, "Not authorized")

        db = self.App.db()

        specs = json.loads(to_str(self.body))
        name = specs.get("name")

        if DBRSE.get(db, name) is not None:
            return error_response(409, "Already exists")

        description = specs.get("description")
        is_enabled = specs.get("is_enabled")
        is_available = specs.get("is_available")
        is_tape = specs.get("is_tape")
        pin_url = specs.get("pin_url")
        poll_url = specs.get("poll_url")
        remove_prefix = specs.get("remove_prefix")
        add_prefix = specs.get("add_prefix")
        pin_prefix = specs.get("pin_prefix")

        preference = specs.get("preference")
        if preference != None:
            preference = int(preference)

        interface = specs.get("interface")
        if interface != "native" and interface != "wlcg":
            interface = None

        #return error_response(401, f"{specs}")

        rse = DBRSE.create(db, name, description, is_enabled, is_available, is_tape, pin_url, poll_url, remove_prefix, add_prefix, pin_prefix, preference, interface)
        return json_response(json.dumps(rse.as_jsonable()))

    @data_router.api_route("/update_rse", methods=["GET", "POST"])
    def update_rse(self, name: Optional[str] = None):
        user, error = self.authenticated_user()
        if user is None:
            return error_response(401, error)
        if not user.is_admin():
            return error_response(403, "Not authorized")

        updates = json.loads(to_str(self.body))
        name = updates.get("Name")
        rse = DBRSE.get(self.App.db(), name)
        if rse is None:
            return error_response(404, f"RSE {name} not found")

        updates.pop("Name")
        for k in list(updates):
            if updates[k] is None:
                del updates[k]

        for k,v in updates.items():
            if hasattr(rse, k):
                setattr(rse, k, v)
            else:
                return error_response(400, f"Bad key: {k}")

        rse.save()
        return json_response(json.dumps(rse.as_jsonable()))

    @data_router.api_route("/delete_rse", methods=["GET", "POST"])
    def delete_rse(self, name: Optional[str] = None):
        if not name:
            return error_response(400, "RSE name must be specified")
        user, error = self.authenticated_user()
        if user is None:
            return error_response(401, error)

        db = self.App.db()
        rse = DBRSE.get(db, name)

        if rse is None:
            return error_response(404, "RSE not found")
        if not user.is_admin():
            return error_response(403, "Not authorized")

        rse.delete()
        return json_response("null")

    @data_router.api_route("/rses", methods=["GET", "POST"])
    def rses(self):
        rses = DBRSE.list(self.App.db(), include_disabled=True)
        return json_response(json.dumps([r.as_jsonable() for r in rses]))

    @data_router.api_route("/get_rse", methods=["GET", "POST"])
    @data_router.api_route("/get_rse/{relpath:path}", methods=["GET", "POST"])
    def get_rse(self, relpath: str = "", name: Optional[str] = None):
        name = name or relpath
        rse = DBRSE.get(self.App.db(), name)
        if rse is None:
            return error_response(404, f"RSE {name} not found")
        return json_response(json.dumps(rse.as_jsonable()))

    @data_router.api_route("/set_rse_availability", methods=["GET", "POST"])
    @data_router.api_route("/set_rse_availability/{relpath:path}", methods=["GET", "POST"])
    def set_rse_availability(self, relpath: str = "", name: Optional[str] = None, available: Optional[str] = None):
        user, error = self.authenticated_user()
        if user is None:
            return error_response(401, error)
        if not user.is_admin():
            return error_response(403, "Not authorized")

        if available not in ("yes", "no"):
            return error_response(400, 'availability value must be specified as "yes" or "no"')

        name = name or relpath
        rse = DBRSE.get(self.App.db(), name)
        if rse is None:
            return error_response(404, f"RSE {name} not found")

        rse.Available = available == "yes"
        rse.save()

        return json_response(json.dumps(rse.as_jsonable()))


class App(BaseApp, Logged):

    def __init__(self, config, prefix):
        Logged.__init__(self, "DataServer")
        BaseApp.__init__(self, config, prefix=prefix)
        self.DaemonURL = config.get("daemon_server", {}).get("url")
        proximity_map_cfg = config.get("proximity_map", {})
        self.ProximityMapDefaults = proximity_map_cfg.get("defaults", {})
        self.ProximityMapOverrides = proximity_map_cfg.get("overrides", {})
        log_out = config.get("web_server",{}).get("log","-")
        init_logger(log_out, debug_enabled=True)
        self.init_auth_core(config)

    def proximity_map(self):
        db = self.db()
        return DBProximityMap(db, defaults=self.ProximityMapDefaults, overrides=self.ProximityMapOverrides)

    def project_created(self, project_id):
        if self.DaemonURL:
            url = f"{self.DaemonURL}/add_project?project_id={project_id}"
            response = requests.get(url)
            #self.debug(f"project_created({project_id}): response:", response)
        else:
            #self.debug("Daemon web servier URL is not configured")
            pass

def create_application(config=None):
    if config is None:
        config = os.environ.get("DATA_DISPATCHER_CFG")
        if not config:
            return None
    if isinstance(config, str):
        config = yaml.load(open(config, "r"), Loader=yaml.SafeLoader)

    prefix = (config.get("web_server", {}).get("data_prefix") or "").rstrip("/")
    app = App(config, prefix)

    fastapi_app = FastAPI(title="Data Dispatcher", version=Version, docs_url=None, redoc_url=None, openapi_url=None)
    fastapi_app.state.metacat_app = app         # used by metacat.auth.server.BaseHandler
    install_exception_handlers(fastapi_app)
    fastapi_app.include_router(data_router, prefix=prefix)
    fastapi_app.include_router(auth_router, prefix=prefix + "/auth")
    return fastapi_app


# FastAPI (ASGI) application, e.g. for uvicorn
app = create_application()

# WSGI application, e.g. for mod_wsgi or uWSGI
application = ASGIMiddleware(app) if app is not None else None

if __name__ == "__main__":
    import getopt, sys
    import uvicorn

    opts, args = getopt.getopt(sys.argv[1:], "c:")
    opts = dict(opts)
    config = yaml.load(open(opts["-c"], "r"), Loader=yaml.SafeLoader)
    server_config = config.get("web_server", {})
    port = server_config.get("data_port", 8088)
    print(f"Starting at port {port}...")
    uvicorn.run(create_application(config), host="0.0.0.0", port=port, access_log=False)
