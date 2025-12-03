import socket
from unittest.mock import patch


def test_get_geo_returns_ipstack_response_by_ip(client, test_data, mock_locator):
    ip = test_data[0].ip
    gloc_to_be_found = [gloc for gloc in test_data if gloc.ip == ip][0]
    response = client.get("/geo", params={"ip": ip})

    assert response.status_code == 200
    assert response.json() == gloc_to_be_found.ipstack_response


def test_get_geo_returns_ipstack_response_by_url(
    client, test_data, mock_locator, url_to_geo_locations
):
    ip = test_data[0].ip
    url, gloc_to_be_found = [
        (url, gloc) for url, gloc in url_to_geo_locations.items() if gloc.ip == ip
    ][0]
    response = client.get("/geo", params={"url": url})

    assert response.status_code == 200
    assert response.json() == gloc_to_be_found.ipstack_response


def test_get_geo_returns_400_when_ip_and_url_are_specified(
    client, test_data, url_to_geo_locations
):
    ip = test_data[0].ip
    url, gloc_to_be_found = [
        (url, gloc) for url, gloc in url_to_geo_locations.items() if gloc.ip == ip
    ][0]
    response = client.get("/geo", params={"ip": ip, "url": url})

    assert response.status_code == 400
    assert response.json() == {"message": "Provide either ip or url (not both)"}


def test_get_geo_returns_404_when_accessing_not_existing_ip(
    client, test_data, mock_locator
):
    ip = "1.1.1.1"
    assert all([ip != gloc.ip for gloc in test_data])
    response = client.get("/geo", params={"ip": ip})

    assert response.status_code == 404
    assert response.json() == {"message": "Location for given ip/url not found"}


def test_get_geo_returns_400_when_accessing_not_existing_url(
    client, test_data, mock_locator, url_to_geo_locations
):
    url = "not.existing.url"
    assert url not in url_to_geo_locations
    response = client.get("/geo", params={"url": url})

    assert response.status_code == 400
    assert response.json() == {"message": "Could not resolve URL to IP"}


def test_get_geo_returns_400_when_socket_returns_error(
    client, test_data, url_to_geo_locations
):
    with patch("utils.locator.socket.gethostbyname", side_effect=socket.gaierror):
        ip = "198.51.111.42"
        url = [url for url, gloc in url_to_geo_locations.items() if gloc.ip == ip][0]
        response = client.get("/geo", params={"url": url})

        assert response.status_code == 400
        assert response.json() == {"message": "Could not resolve URL to IP"}
