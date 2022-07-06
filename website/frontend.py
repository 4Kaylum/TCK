from typing import Union

from aiohttp.web import Request, Response, RouteTableDef
import aiohttp_session
from aiohttp_jinja2 import template
from discord.ext import vbu

from cogs import utils


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
async def index(_: Request):
    return {}


@routes.get("/leaderboard")
@template("leaderboard.htm.j2")
@add_standard_args()
async def leaderboard(_: Request):
    return {}


@routes.get("/raffles")
@template("raffles.htm.j2")
@add_standard_args()
async def raffles(_: Request):
    async with vbu.Database() as db:
        rows = await db.call(
            """
            SELECT
                *
            FROM
                raffles
            WHERE
                end_time > TIMEZONE('UTC', NOW())
            """,
        )
    raffles = [
        utils.Raffle(data=i)
        for i in rows
    ]
    return {
        "raffles": [i for i in raffles if not i.is_giveaway],
        "giveaways": [i for i in raffles if i.is_giveaway],
    }


@routes.get("/videos")
@template("videos.htm.j2")
@add_standard_args()
async def videos(_: Request):
    return {}


@routes.get("/contact")
@template("contact.htm.j2")
@add_standard_args()
async def contact(_: Request):
    return {}
