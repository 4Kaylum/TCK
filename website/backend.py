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
    log = request.app['logger']

    # Check their code is valid and for us
    headers = {
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
        token_site = await session.post(url, headers=headers, data=params)
        if not token_site.ok:
            log.info("Failed to get token data: %s" % await token_site.text())
            return HTTPFound(location="/")
        auth_data = await token_site.json()
        log.info("Auth token data: %s" % auth_data)

        # Get the user's name and ID
        headers = {
            "Authorization": f"Bearer {auth_data['access_token']}",
            "User-Agent": request.app['config']['user_agent'],
        }
        url = "https://id.twitch.tv/oauth2/validate"
        validate_site = await session.get(url, headers=headers)
        if not validate_site.ok:
            log.info("Failed to validate token data: %s" % await validate_site.text())
            return HTTPFound(location="/")
        user_data = await validate_site.json()
        log.info("Validate token data: %s" % user_data)

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
    user_db_data = dict(db_data[0])
    user_db_data['id'] = str(user_db_data['id'])
    session['user_info'] = user_db_data
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


@routes.post("/api/submit_leaderboard_changes")
@utils.requires_permission(admin_panel=True)
async def submit_leaderboard_changes(request: Request):
    """
    Get submitted changes from the leaderboard admin page.
    """

    # Get the json data from the request
    data = await request.json()

    # Add that to the database
    new_data = []
    async with vbu.Database() as db:
        for row in data:
            new_row = await db.call(
                """
                INSERT INTO
                    leaderboards
                    (index, name, amount)
                VALUES
                    ($1, $2, $3)
                ON CONFLICT
                    (index)
                DO UPDATE
                SET
                    name = excluded.name,
                    amount = excluded.amount
                RETURNING
                    *
                """,
                int(row['index']), row['name'], int(row['amount']),
            )
            new_data.append(new_row)

    # And done
    return json_response({
        "message": "Leaderboards updated successfully! :3",
        "data": [
            dict(i)
            for i in new_data
        ],
    })
