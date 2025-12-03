from ipstack import GeoLookup
from settings import settings
from ipaddress import IPv4Address, IPv6Address
import socket
from typing import Union
from fastapi.concurrency import run_in_threadpool

IPAddress = Union[IPv4Address, IPv6Address]


class Locator:
    def __init__(self):
        self.ipstack_lookup = GeoLookup(settings.ipstack_key)

    async def get_location_for(self, ip: str):
        # probably not the bottleneck, but used for async demonstration
        return await run_in_threadpool(self.ipstack_lookup.get_location, ip)

    @staticmethod
    async def resolve_to_ip(ip_or_url: IPAddress | str) -> str | None:
        match ip_or_url:
            case IPv4Address() | IPv6Address():
                return str(ip_or_url)
            case str() as url:
                try:
                    return await run_in_threadpool(socket.gethostbyname, url)
                except socket.gaierror:
                    return None
