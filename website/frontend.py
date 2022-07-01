from aiohttp.web import HTTPFound, Request, Response, RouteTableDef
import aiohttp_session
from aiohttp_jinja2 import template
import discord
from discord.ext import vbu


routes = RouteTableDef()


@routes.get("/")
@routes.get("/index")
@template("index.htm.j2")
async def index(request: Request):
    return {}


@routes.get("/leaderboard")
@template("leaderboard.htm.j2")
async def leaderboard(request: Request):
    return {}
