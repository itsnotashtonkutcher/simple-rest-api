from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from settings import settings
from utils import Locator, IPAddress, get_db, get_locator, setup_logger
from models import GeoLocation
from pydantic import BaseModel
from sqlalchemy.exc import SQLAlchemyError
import logging

setup_logger()
logger = logging.getLogger(settings.logger_name)
app = FastAPI(title="Geo Location API")


class PostLocation(BaseModel):
    ip: IPAddress | None = None
    url: str | None = None


@app.exception_handler(SQLAlchemyError)
def handle_database_errors(_: Request, __: SQLAlchemyError):
    logger.error("Database connection error", exc_info=True)
    # same error message to not expose details to user
    return JSONResponse({"message": "Unexpected error occurred, try again later."}, 500)


@app.exception_handler(HTTPException)
def handle_general_errors(_: Request, exc: HTTPException):
    # every response should be in JSON format
    return JSONResponse({"message": exc.detail}, exc.status_code)


@app.exception_handler(Exception)
def handle_general_errors(_: Request, __: Exception):
    logger.error("Unexpected error", exc_info=True)
    return JSONResponse({"message": "Unexpected error occurred, try again later."}, 500)


@app.get("/geo")
async def get_geo(
    ip: IPAddress | None = None,
    url: str = None,
    db: AsyncSession = Depends(get_db),
    locator: Locator = Depends(get_locator),
):
    _raise_if_ip_and_url_not_exclusive(ip, url)

    ip = await locator.resolve_to_ip(ip or url)
    if ip is None:
        raise HTTPException(400, "Could not resolve URL to IP")
    geo_location = await pull_geo_location_by(ip, db)
    if not geo_location:
        raise HTTPException(404, "Location for given ip/url not found")
    return geo_location.ipstack_response


@app.post("/geo", status_code=201)
async def post_geo(
    location: PostLocation,
    db: AsyncSession = Depends(get_db),
    locator: Locator = Depends(get_locator),
):
    _raise_if_ip_and_url_not_exclusive(location.ip, location.url)

    ip = await locator.resolve_to_ip(location.ip or location.url)
    if ip is None:
        raise HTTPException(400, "Could not resolve URL to IP")

    geo_location = await pull_geo_location_by(ip, db)
    if geo_location:
        raise HTTPException(409, "Geo location already exist")

    ipstack_response = await locator.get_location_for(ip)
    if not ipstack_response:
        raise HTTPException(400, "Could not find data for given address")

    geo_location = GeoLocation(ip=ip, ipstack_response=ipstack_response)
    db.add(geo_location)
    await db.commit()
    await db.refresh(geo_location)

    return geo_location.ipstack_response


@app.delete("/geo", status_code=204)
async def delete_geo(
    ip: IPAddress | None = None,
    url: str = None,
    db: AsyncSession = Depends(get_db),
    locator: Locator = Depends(get_locator),
):
    _raise_if_ip_and_url_not_exclusive(ip, url)
    ip = await locator.resolve_to_ip(ip or url)
    if ip is None:
        raise HTTPException(400, "Could not resolve URL to IP")
    geo_location = await pull_geo_location_by(ip, db)
    if not geo_location:
        raise HTTPException(404, "Location for given ip/url not found")

    await db.delete(geo_location)
    await db.commit()
    return


async def pull_geo_location_by(ip: IPAddress | str, db: AsyncSession) -> GeoLocation:
    query = select(GeoLocation).where(GeoLocation.ip == ip)
    result = await db.execute(query)
    return result.scalars().first()


def _raise_if_ip_and_url_not_exclusive(ip: IPAddress | None = None, url: str = None):
    if ip and url:
        raise HTTPException(400, "Provide either ip or url (not both)")
    elif not ip and not url:
        raise HTTPException(400, "Ip or url has to be provided")
