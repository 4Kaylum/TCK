from typing import Union

from aiohttp.web import HTTPFound, Request, Response, RouteTableDef
import aiohttp_session
from aiohttp_jinja2 import template
import discord
from discord.ext import vbu


routes = RouteTableDef()


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


@routes.get("/")
@routes.get("/index")
@template("index.htm.j2")
@add_standard_args()
async def index(request: Request):
    return {}


@routes.get("/leaderboard")
@template("leaderboard.htm.j2")
@add_standard_args()
async def leaderboard(request: Request):
    return {}


@routes.get("/raffles")
@template("raffles.htm.j2")
@add_standard_args()
async def raffles(request: Request):
    return {}


@routes.get("/videos")
@template("videos.htm.j2")
@add_standard_args()
async def videos(request: Request):
    return {}
