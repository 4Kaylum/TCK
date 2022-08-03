from typing import Union

from aiohttp.web import HTTPFound, Request, Response
import aiohttp_session

from .website_permissions import WebsitePermissions


__all__ = (
    'add_standard_args',
    'requires_permission',
)


def add_standard_args():
    def inner(func):
        async def wrapper(request: Request):
            d: Union[None, Response, dict] = await func(request)
            if d is None:
                d = {}
            elif isinstance(d, Response):
                return d
            d['session'] = await aiohttp_session.get_session(request)
            d['request'] = request
            return d
        return wrapper
    return inner


def requires_permission(**kwargs):
    def inner(func):
        async def wrapper(request: Request):
            session = await aiohttp_session.get_session(request)
            user_info = session.get('user_info', {})
            permissions_int = user_info.get('permissions', 0)
            permissions = WebsitePermissions(permissions_int)
            for i, o in kwargs.items():
                if getattr(permissions, i) == o:
                    pass
                else:
                    if user_info:
                        return HTTPFound("/")
                    return HTTPFound("/login")
            return await func(request)
        return wrapper
    return inner
