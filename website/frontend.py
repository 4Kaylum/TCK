from aiohttp.web import HTTPFound, Request, Response, RouteTableDef
import aiohttp_session
from aiohttp_jinja2 import template
import discord
from discord.ext import vbu


routes = RouteTableDef()


@routes.get("/")
@template("index.htm.j2")
async def index(request: Request):
    return
