from urllib.parse import urlencode

import aiohttp
from aiohttp.web import HTTPFound, Request, Response, RouteTableDef, json_response
import aiohttp_session
import asyncpg
from discord.ext import vbu

from cogs import utils


routes = RouteTableDef()


@routes.get("/login_processor/discord")
async def discord_login_processor(request: Request):
    """
    Page the discord login redirects the user to when successfully
    logged in with Discord.
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


@routes.get("/login_processor/twitch")
async def twitch_login_processor(request: Request):
    """
    Page the discord login redirects the user to when successfully
    logged in with Twitch.
    """

    # See if they pressed cancel
    if request.query.get("error"):
        return HTTPFound(location="/")

    # Check their code is valid and for us
    headers = {
        "Content-Type": "xxx-www-form-encoded",
        "User-Agent": request.app['config']['user_agent'],
    }
    params = {
        "client_id": request.app['config']['twitch']['client_id'],
        "client_secret": request.app['config']['twitch']['client_secret'],
        "code": request.query.get("code", ""),
        "grant_type": "authorization_code",
        "redirect_uri": request.app['config']['website_base_url'] + "/login_processor/twitch"
    }
    async with aiohttp.ClientSession() as session:
        url = "https://id.twitch.tv/oauth2/token"
        site = await session.post(url, headers=headers, data=params)
        if not site.ok:
            return HTTPFound(location="/")
        auth_data = await site.json()

        # Get the user's name and ID
        headers = {
            "Authorization": f"Bearer OAuth {auth_data['access_token']}",
            "User-Agent": request.app['config']['user_agent'],
        }
        url = "https://id.twitch.tv/oauth2/validate"
        site = await session.post(url, headers=headers)
        if not site.ok:
            return HTTPFound(location="/")
        user_data = await site.json()

    # Store their data in the database if necessary
    async with vbu.Database() as db:
        try:
            db_data = await db.call(
                """
                INSERT INTO
                    users
                    (
                        id,
                        twitch_id,
                        twitch_username
                    )
                VALUES
                    (
                        uuid_generate_v4(),  -- uuid
                        $1,  -- twitch id
                        $2  -- twitch username
                    )
                RETURNING
                    *
                """,
                user_data['user_id'], user_data['login'],
            )
        except asyncpg.UniqueViolationError:
            db_data = await db.call(
                """
                SELECT
                    *
                FROM
                    users
                WHERE
                    twitch_id = $1
                """,
                user_data['user_id'],
            )

    # It succeeded - sick
    # Let's store that and direct them as necessary
    session = await aiohttp_session.get_session(request)
    session['user'] = dict(db_data[0])
    return HTTPFound(location="/")


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

    params = urlencode({
        "client_id": request.app['config']['twitch']['client_id'],
        "redirect_uri": request.app['config']['website_base_url'] + "/login_processor/twitch",
        "response_type": "code",
        "scope": "user:read:email",
    })
    return HTTPFound(location=f"https://id.twitch.tv/oauth2/authorize?{params}")


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
