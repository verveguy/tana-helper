from logging import getLogger

from fastapi import APIRouter

from service import settings
from service.settings import Settings, set_settings

router = APIRouter()

logger = getLogger()


# expose our configuration Webapp on /configure
@router.get("/configure", tags=["Configuration"])
def configure():
    return settings.settings


@router.post("/configure", tags=["Configuration"])
def set_configuration(new_settings: Settings):
    logger.info("Received new configuration settings")
    updated_settings = set_settings(new_settings)
    logger.info("Configuration updated successfully")
    return updated_settings
