import socket
from unittest.mock import patch
from models import GeoLocation
from sqlalchemy import select
import asyncio


def test_delete_geo_deletes_data_by_ip(
    client, test_data, mock_locator, url_to_ip_and_ipstack_resp, test_session
):
    geo_loc_to_delete = test_data[0]
    ip = geo_loc_to_delete.ip

    response = client.delete("/geo", params={"ip": ip})

    assert response.status_code == 204
    result = asyncio.run(
        test_session.execute(select(GeoLocation).where(GeoLocation.ip == ip))
    )
    deleted_geo_location = result.scalars().first()
    assert deleted_geo_location is None


def test_delete_geo_deletes_data_by_url(
    client, test_data, mock_locator, url_to_geo_locations, test_session
):
    url, geo_loc_to_delete = [
        (url, gloc) for url, gloc in url_to_geo_locations.items()
    ][0]
    ip = geo_loc_to_delete.ip

    response = client.delete("/geo", params={"url": url})

    assert response.status_code == 204
    result = asyncio.run(
        test_session.execute(select(GeoLocation).where(GeoLocation.ip == ip))
    )
    deleted_geo_location = result.scalars().first()
    assert deleted_geo_location is None


def test_delete_geo_returns_400_when_ip_and_url_are_specified(
    client, test_data, url_to_geo_locations
):
    ip = test_data[0].ip
    url, gloc_to_be_found = [
        (url, gloc) for url, gloc in url_to_geo_locations.items() if gloc.ip == ip
    ][0]
    response = client.delete("/geo", params={"ip": ip, "url": url})

    assert response.status_code == 400
    assert response.json() == {"message": "Provide either ip or url (not both)"}


def test_delete_geo_returns_400_when_removing_not_existing_ip(
    client, test_data, mock_locator
):
    ip = "1.1.1.1"
    assert all([ip != gloc.ip for gloc in test_data])
    response = client.delete("/geo", params={"ip": ip})

    assert response.status_code == 404
    assert response.json() == {"message": "Location for given ip/url not found"}


def test_delete_geo_returns_400_when_accessing_not_existing_url(
    client, test_data, mock_locator, url_to_geo_locations
):
    url = "not.existing.url"
    assert url not in url_to_geo_locations
    response = client.delete("/geo", params={"url": url})

    assert response.status_code == 400
    assert response.json() == {"message": "Could not resolve URL to IP"}


def test_delete_geo_returns_400_when_socket_returns_error(
    client, test_data, url_to_geo_locations
):
    with patch("utils.locator.socket.gethostbyname", side_effect=socket.gaierror):
        ip = test_data[0].ip
        url = [url for url, gloc in url_to_geo_locations.items() if gloc.ip == ip][0]
        response = client.delete("/geo", params={"url": url})

        assert response.status_code == 400
        assert response.json() == {"message": "Could not resolve URL to IP"}
