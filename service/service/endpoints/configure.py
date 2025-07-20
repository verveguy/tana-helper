from logging import getLogger

from fastapi import APIRouter

from service.settings import Settings, set_settings, settings

router = APIRouter()

logger = getLogger()


# expose our configuration Webapp on /configure
@router.get("/configuration", tags=["Configuration"])
def configure():
    global settings
    return settings


@router.post("/configuration", tags=["Configuration"])
def set_configuration(new_settings: Settings):
    global settings
    settings = set_settings(new_settings)
    return settings
