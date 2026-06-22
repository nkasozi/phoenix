"""Health check for the application."""

from fastapi import APIRouter, Response, status

from phiphi import config

router = APIRouter()


@router.get(
    "/oauth2/insecure_auth",
    tags=["oauth"],
    status_code=status.HTTP_202_ACCEPTED,
)
async def insecure_auth(response: Response) -> None:
    """This route will be used for a local cluster to be run without oauth2 implement."""
    response.headers["Gap-Auth"] = config.settings.FIRST_ADMIN_USER_EMAIL
    response.headers["X-Auth-Request-Email"] = config.settings.FIRST_ADMIN_USER_EMAIL
    response.headers["X-Auth-Request-User"] = "1"
