from fastapi import FastAPI, APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi_utils.cbv import cbv
from typing import Optional
from pythreader import PyThread
from data_dispatcher.logs import Logged
from metacat.auth.server import install_exception_handlers
import uvicorn

data_router = APIRouter()


@cbv(data_router)
class DataHandler(object):

    request: Request

    def __init__(self):
        self.App = self.request.app.state.daemon_app

    @data_router.api_route("/data/add_project", methods=["GET", "POST"])
    def add_project(self, project_id: Optional[str] = None):
        self.App.add_project(int(project_id))
        self.App.debug("request to add project", project_id)
        return HTMLResponse("OK")


class App(Logged):
    def __init__(self, project_master):
        Logged.__init__(self, "DaemonWebServerApp")
        self.ProjectMaster = project_master

    def add_project(self, project_id):
        self.ProjectMaster.add_project(project_id)


def create_application(project_master):
    fastapi_app = FastAPI(
        title="Data Dispatcher Daemon", docs_url=None, redoc_url=None, openapi_url=None
    )
    fastapi_app.state.daemon_app = App(project_master)
    install_exception_handlers(fastapi_app)
    fastapi_app.include_router(data_router)
    return fastapi_app


class DaemonWebServer(PyThread):
    def __init__(self, config, project_master, **args):
        PyThread.__init__(self, name="DaemonWebServer")
        port = config["port"]
        app = create_application(project_master)
        self.Server = uvicorn.Server(
            uvicorn.Config(app, host="0.0.0.0", port=port, access_log=False, **args)
        )

    def run(self):
        self.Server.run()
