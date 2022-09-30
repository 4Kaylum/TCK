import aiohttp
from aiohttp.web import Request, RouteTableDef
from aiohttp_jinja2 import template
from discord.ext import vbu

from cogs import utils


routes = RouteTableDef()



@routes.get("/")
@routes.get("/index")
@template("index.htm.j2")
@utils.add_standard_args()
async def index(_: Request):
    return {}


@routes.get("/leaderboard")
@template("leaderboard.htm.j2")
@utils.add_standard_args()
async def leaderboard(_: Request):
    """
    Show all of the users that are to appear on the leaderboard page.
    """

    async with vbu.Database() as db:
        rows = await db.call(
            """
            SELECT
                *
            FROM
                leaderboards
            ORDER BY
                index DESC
            """
        )
    leaderboard_items = [None] * 10
    for i in rows:
        leaderboard_items[i['index'] - 1] = dict(i)
    return {
        "leaderboard_items": leaderboard_items,
    }


@routes.get("/giveaways")
@template("giveaways.htm.j2")
@utils.add_standard_args()
async def giveaways(_: Request):
    """
    Grab all of the data for the raffles page, allowing users to
    enter each raffle or giveaway.
    """

    async with vbu.Database() as db:
        rows = await db.call(
            """
            SELECT
                *
            FROM
                raffles
            WHERE
                deleted IS FALSE
            AND
                end_time > TIMEZONE('UTC', NOW())
            AND
                start_time <= TIMEZONE('UTC', NOW())
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
@utils.add_standard_args()
async def videos(request: Request):
    """
    Get all the videos and show em uwu.
    """

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
@utils.add_standard_args()
async def contact(_: Request):
    return {}


@routes.get("/admin")
@routes.get("/admin/")
@template("admin/index.htm.j2")
@utils.requires_permission(admin_panel=True)
@utils.add_standard_args()
async def admin_index(_: Request):
    return {}


@routes.get("/admin/leaderboard")
@template("admin/leaderboard.htm.j2")
@utils.requires_permission(admin_panel=True)
@utils.add_standard_args()
async def admin_leaderboard(_: Request):
    async with vbu.Database() as db:
        rows = await db.call(
            """
            SELECT
                *
            FROM
                leaderboards
            ORDER BY
                index DESC
            """
        )
    leaderboard_items = [None] * 10
    for i in rows:
        leaderboard_items[i['index'] - 1] = dict(i)
    return {
        "leaderboard_items": leaderboard_items,
    }


@routes.get("/admin/giveaways")
@template("admin/giveaways.htm.j2")
@utils.requires_permission(admin_panel=True)
@utils.add_standard_args()
async def admin_giveaways(_: Request):
    async with vbu.Database() as db:
        rows = await db.call(
            """
            SELECT
                *
            FROM
                raffles
            WHERE
                deleted = FALSE
            ORDER BY
                start_time
                DESC
            """,
        )
    raffles = [
        utils.Raffle(data=i)
        for i in rows
    ]
    return {
        "raffles": raffles,
    }
