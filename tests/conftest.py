import pytest
import asyncio
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app import app
from database import Base
from utils import get_db
from models import GeoLocation
from unittest.mock import patch, Mock

DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(DATABASE_URL, echo=False)
TestingSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


@pytest.fixture(scope="function")
def test_session():
    async def setup():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        return TestingSessionLocal()

    async def teardown():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)

    loop = asyncio.new_event_loop()
    conn = loop.run_until_complete(setup())
    yield conn
    loop.run_until_complete(teardown())


@pytest.fixture
def client(test_session):
    async def mock_of_get_db():
        async with TestingSessionLocal() as session:
            yield session

    app.dependency_overrides[get_db] = mock_of_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def test_data(test_session, url_to_geo_locations):
    geo_locations = [gloc for _, gloc in url_to_geo_locations.items()]

    async def add_data():
        async with TestingSessionLocal() as db_session:
            db_session.add_all(geo_locations)
            await db_session.commit()
            for geo_location in geo_locations:
                await db_session.refresh(geo_location)
            return geo_locations

    loop = asyncio.new_event_loop()
    return loop.run_until_complete(add_data())


@pytest.fixture()
def mock_locator(url_to_geo_locations, url_to_ip_and_ipstack_resp):
    url_to_ip = {url: gloc.ip for url, gloc in url_to_geo_locations.items()}
    ip_to_ipstack_resp = {
        gloc.ip: gloc.ipstack_response for _, gloc in url_to_geo_locations.items()
    }
    # add mocked data to be recognizable by locator-called functions
    for url, (ip, ipstack_resp) in url_to_ip_and_ipstack_resp.items():
        url_to_ip[url] = ip
        ip_to_ipstack_resp[ip] = ipstack_resp

    def mock_ipstack_get_location(ip: str):
        return ip_to_ipstack_resp.get(ip, None)

    def mock_socket_gethostbyname(url: str):
        return url_to_ip.get(url, None)

    ipstack_lookup_mock = Mock()
    ipstack_lookup_mock.get_location = mock_ipstack_get_location
    with patch(
        "utils.locator.socket.gethostbyname", new=mock_socket_gethostbyname
    ) as socket_mock, patch(
        "utils.locator.GeoLookup", return_value=ipstack_lookup_mock
    ) as lookup_mock:

        yield socket_mock, lookup_mock


@pytest.fixture()
def url_to_ip_and_ipstack_resp():
    # data that can be returned by locator function
    # used to mock ipstack and socket behaviour of uncreated data
    return {
        "github.com": (
            "162.159.140.229",
            {
                "ip": "162.159.140.229",
                "type": "ipv4",
                "continent_code": "NA",
                "continent_name": "North America",
                "country_code": "US",
                "country_name": "United States",
                "region_code": "CA",
                "region_name": "California",
                "city": "San Francisco",
                "zip": "94117",
                "latitude": 37.775001525878906,
                "longitude": -122.41832733154297,
                "msa": "41860",
                "dma": "807",
                "radius": "0",
                "ip_routing_type": "fixed",
                "connection_type": "tx",
                "location": {
                    "geoname_id": 5391959,
                    "capital": "Washington D.C.",
                    "languages": [
                        {"code": "en", "name": "English", "native": "English"}
                    ],
                    "country_flag": "https://assets.ipstack.com/flags/us.svg",
                    "country_flag_emoji": "🇺🇸",
                    "country_flag_emoji_unicode": "U+1F1FA U+1F1F8",
                    "calling_code": "1",
                    "is_eu": False,
                },
            },
        )
    }


@pytest.fixture()
def url_to_geo_locations() -> dict[str, GeoLocation]:
    return {
        "unknown.address.com": GeoLocation(
            ip="198.51.111.42",
            ipstack_response={
                "ip": "198.51.111.42",
                "type": "ipv4",
                "continent_code": None,
                "continent_name": None,
                "country_code": None,
                "country_name": None,
                "region_code": None,
                "region_name": None,
                "city": None,
                "zip": None,
                "latitude": 0.0,
                "longitude": 0.0,
                "msa": None,
                "dma": None,
                "radius": None,
                "ip_routing_type": None,
                "connection_type": None,
                "location": {
                    "geoname_id": None,
                    "capital": None,
                    "languages": None,
                    "country_flag": None,
                    "country_flag_emoji": None,
                    "country_flag_emoji_unicode": None,
                    "calling_code": None,
                    "is_eu": None,
                },
            },
        ),
        "google.com": GeoLocation(
            ip="142.251.98.139",
            ipstack_response={
                "ip": "142.251.98.139",
                "type": "ipv4",
                "continent_code": "NA",
                "continent_name": "North America",
                "country_code": "US",
                "country_name": "United States",
                "region_code": "CA",
                "region_name": "California",
                "city": "Mountain View",
                "zip": "94041",
                "latitude": 37.38801956176758,
                "longitude": -122.07431030273438,
                "msa": "41940",
                "dma": "807",
                "radius": "0",
                "ip_routing_type": "fixed",
                "connection_type": "tx",
                "location": {
                    "geoname_id": 7173909,
                    "capital": "Washington D.C.",
                    "languages": [
                        {"code": "en", "name": "English", "native": "English"}
                    ],
                    "country_flag": "https://assets.ipstack.com/flags/us.svg",
                    "country_flag_emoji": "🇺🇸",
                    "country_flag_emoji_unicode": "U+1F1FA U+1F1F8",
                    "calling_code": "1",
                    "is_eu": False,
                },
            },
        ),
    }
