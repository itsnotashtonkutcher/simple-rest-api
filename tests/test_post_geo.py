import socket
from unittest.mock import patch
from models import GeoLocation
from sqlalchemy import select
import asyncio


def test_post_geo_returns_ipstack_and_adds_data_for_ip(
    client, test_data, mock_locator, url_to_ip_and_ipstack_resp, test_session
):
    ip, ipstack_resp = [
        (ip, ipstack_resp)
        for _, (ip, ipstack_resp) in url_to_ip_and_ipstack_resp.items()
    ][0]
    result = asyncio.run(
        test_session.execute(select(GeoLocation).where(GeoLocation.ip == ip))
    )
    new_geo_location = result.scalars().first()
    assert new_geo_location is None

    response = client.post("/geo", json={"ip": ip})

    assert response.status_code == 201
    assert response.json() == ipstack_resp
    result = asyncio.run(
        test_session.execute(select(GeoLocation).where(GeoLocation.ip == ip))
    )
    new_geo_location = result.scalars().first()
    assert new_geo_location.ip == ip
    assert new_geo_location.ipstack_response == ipstack_resp


def test_post_geo_returns_ipstack_and_adds_data_for_url(
    client, test_data, mock_locator, url_to_ip_and_ipstack_resp, test_session
):
    url, ip, ipstack_resp = [
        (url, ip, ipstack_resp)
        for url, (ip, ipstack_resp) in url_to_ip_and_ipstack_resp.items()
    ][0]
    result = asyncio.run(
        test_session.execute(select(GeoLocation).where(GeoLocation.ip == ip))
    )
    new_geo_location = result.scalars().first()
    assert new_geo_location is None

    response = client.post("/geo", json={"url": url})

    assert response.status_code == 201
    assert response.json() == ipstack_resp
    result = asyncio.run(
        test_session.execute(select(GeoLocation).where(GeoLocation.ip == ip))
    )
    new_geo_location = result.scalars().first()
    assert new_geo_location.ip == ip
    assert new_geo_location.ipstack_response == ipstack_resp


def test_post_geo_returns_400_when_ip_and_url_are_specified(
    client, test_data, url_to_geo_locations
):
    ip = test_data[0].ip
    url, gloc_to_be_found = [
        (url, gloc) for url, gloc in url_to_geo_locations.items() if gloc.ip == ip
    ][0]
    response = client.post("/geo", json={"ip": ip, "url": url})

    assert response.status_code == 400
    assert response.json() == {"message": "Provide either ip or url (not both)"}


def test_post_geo_returns_404_when_accessing_not_existing_ip(
    client, test_data, mock_locator
):
    ip = "1.1.1.1"
    assert all([ip != gloc.ip for gloc in test_data])
    response = client.post("/geo", json={"ip": ip})

    assert response.status_code == 400
    assert response.json() == {"message": "Could not find data for given address"}


def test_post_geo_returns_400_when_accessing_not_existing_url(
    client, test_data, mock_locator, url_to_geo_locations
):
    url = "not.existing.url"
    assert url not in url_to_geo_locations
    response = client.post("/geo", json={"url": url})

    assert response.status_code == 400
    assert response.json() == {"message": "Could not resolve URL to IP"}


def test_post_geo_returns_400_when_socket_returns_error(
    client, test_data, url_to_geo_locations
):
    with patch("utils.locator.socket.gethostbyname", side_effect=socket.gaierror):
        ip = test_data[0].ip
        url = [url for url, gloc in url_to_geo_locations.items() if gloc.ip == ip][0]
        response = client.post("/geo", json={"url": url})

        assert response.status_code == 400
        assert response.json() == {"message": "Could not resolve URL to IP"}
