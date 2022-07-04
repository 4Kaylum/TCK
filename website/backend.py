from aiohttp.web import HTTPFound, Request, Response, RouteTableDef, json_response
import aiohttp_session
from discord.ext import vbu

from cogs import utils


routes = RouteTableDef()


@routes.get("/login_processor")
async def login_processor(request: Request):
    """
    Page the discord login redirects the user to when successfully logged in with Discord.
    """

    # Process their login code
    v = await vbu.web.process_discord_login(request)

    # It failed - we want to redirect back to the index
    if isinstance(v, Response):
        return HTTPFound(location="/")

    # It succeeded - let's redirect them to where we specified to go if we
    # used a decorator, OR back to the index page
    session = await aiohttp_session.get_session(request)
    return HTTPFound(location=session.pop("redirect_on_login", "/"))


@routes.get("/logout")
async def logout(request: Request):
    """
    Destroy the user's login session.
    """

    session = await aiohttp_session.get_session(request)
    session.invalidate()
    return HTTPFound(location="/")


@routes.get("/login")
async def login(request: Request):
    """
    Redirect the user to the bot's Oauth login page.
    """

    return HTTPFound(location=vbu.web.get_discord_login_url(request, "/login_processor"))


@routes.get("/api/get_videos")
async def get_videos(request: Request):
    """
    Get the last N videos of a given playlist ID
    (specified in config, as well as a Google Cloud
    API key). 
    """

    # Get the playlist IDs
    api_key = request.app['config']['google']['api_key']
    playlist_ids = request.app['config']['google']['valid_playists']

    # Get the videos from the channel
    videos = []
    url = "https://www.googleapis.com/youtube/v3/playlistItems"  # https://developers.google.com/youtube/v3/docs/playlistItems/list
    headers = {
        "User-Agent": request.app['config']['user_agent'],
    }
    params = {
        "part": "snippet,contentDetails",
        "maxResults": 6,
        "playlistId": None,
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
    videos = [utils.Video(d).to_json() for d in videos]

    # And done
    return json_response(videos)
