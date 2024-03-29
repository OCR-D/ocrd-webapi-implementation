from datetime import datetime
from os import environ

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from ocrd_webapi.authentication import (
    authenticate_user,
    register_user
)
from ocrd_webapi.constants import DB_URL, SERVER_URL
from ocrd_webapi.database import initiate_database
from ocrd_webapi.exceptions import ResponseException, AuthenticationError
from ocrd_webapi.routers import (
    discovery,
    user,
    workflow,
    workspace,
)

app = FastAPI(
    title="OCR-D Web API",
    description="HTTP API for offering OCR-D processing",
    contact={"email": "test@example.com"},
    license={
        "name": "Apache 2.0",
        "url": "http://www.apache.org/licenses/LICENSE-2.0.html",
    },
    version="0.11.0",
    servers=[
        {
            "url": SERVER_URL,
            "description": "The URL of your server offering the OCR-D API.",
        }
    ],
)
app.include_router(user.router)
app.include_router(discovery.router)
# app.include_router(processor.router)
app.include_router(workflow.router)
app.include_router(workspace.router)


@app.exception_handler(ResponseException)
async def exception_handler_empty404(request: Request, exc: ResponseException):
    """
    Exception-Handler needed to return Empty 404 JSON response
    """
    return JSONResponse(status_code=exc.status_code, content={} if not exc.body else exc.body)


@app.on_event("startup")
async def startup_event():
    """
    Executed once on startup
    """
    await initiate_database(DB_URL)

    default_admin_user = environ.get("OCRD_WEBAPI_USERNAME", "test")
    default_admin_pass = environ.get("OCRD_WEBAPI_PASSWORD", "test")

    # If the default admin user account is not available in the DB, create it
    try:
        await authenticate_user(default_admin_user, default_admin_pass)
    except AuthenticationError:
        # TODO: Note that this account is never removed from
        #  the DB automatically in the current implementation
        await register_user(
            default_admin_user,
            default_admin_pass,
            approved_user=True
        )


@app.get("/")
async def test():
    """
    to test if server is running on root-path
    """
    return datetime.now().strftime("%Y-%m-%d %H:%M")
