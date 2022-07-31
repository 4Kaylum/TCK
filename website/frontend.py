from typing import Union

import aiohttp
from aiohttp.web import Request, Response, RouteTableDef, HTTPFound
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


def requires_permission(**kwargs):
    def inner(func):
        async def wrapper(request: Request):
            session = await aiohttp_session.get_session(request)
            user_info = session.get('user_info', {})
            permissions_int = user_info.get('permissions', 0)
            permissions = utils.WebsitePermissions(permissions_int)
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
async def videos(request: Request):
    videos = await get_videos(request)
    return {
        "videos": videos,
    }


async def get_videos(request: Request):
    """
    Get the last N videos of a given playlist ID
    (specified in config, as well as a Google Cloud
    API key).
    """

    # Get the playlist IDs
    api_key = request.app['config']['google']['api_key']
    playlist_ids = request.app['config']['google']['valid_playlists']

    # Get the videos from the channel
    videos = []
    url = "https://www.googleapis.com/youtube/v3/playlistItems"
    # https://developers.google.com/youtube/v3/docs/playlistItems/list
    headers = {
        "User-Agent": request.app['config']['user_agent'],
    }
    params = {
        "part": "snippet,contentDetails",
        "maxResults": 6,
        "playlistId": None,
        "key": api_key,
    }
    if playlist_ids:
        async with aiohttp.ClientSession(headers=headers) as session:
            for pid in playlist_ids:
                params["playlistId"] = pid
                site = await session.get(url, params=params)
                site.raise_for_status()
                data = await site.json()
                videos.extend(data['items'])

    # Format those into a more helpful object
    videos = [utils.Video(data=d) for d in videos]
    return videos


@routes.get("/contact")
@template("contact.htm.j2")
@add_standard_args()
async def contact(_: Request):
    return {}


@routes.get("/admin")
@routes.get("/admin/")
@template("admin/index.htm.j2")
@requires_permission(admin_panel=True)
@add_standard_args()
async def admin_index(_: Request):
    return {}
