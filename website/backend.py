from datetime import datetime as dt
from typing import Optional, Union, overload
from urllib.parse import urlencode
import json

import aiohttp
from aiohttp.web import HTTPFound, Request, Response, RouteTableDef, json_response
import aiohttp_session
import asyncpg
from discord.ext import vbu

from cogs import utils


routes = RouteTableDef()


def streamelements(r: Request):
    token = r.app['config']['streamelements']['token']
    return utils.StreamElements(token)


def try_parse_time(input_time: str, parse) -> Optional[dt]:
    try:
        return dt.strptime(input_time, parse)
    except:
        return None


def parse_time(input_time: str) -> dt:
    formats = [
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M",
        "%Y-%m-%d %H:%M",
    ]
    for f in formats:
        t = try_parse_time(input_time, f)
        if t:
            return t
    raise TypeError()


@overload
def json_encode(item: dict) -> dict: ...
@overload
def json_encode(item: list) -> list: ...

def json_encode(item: Union[dict, list]) -> Union[dict, list]:
    return json.loads(json.dumps(item, cls=utils.HTTPEncoder))


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


@routes.put("/api/leaderboard")
@utils.requires_permission(admin_panel=True)
async def put_leaderboard(request: Request):
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
                    (
                        index,
                        name,
                        amount
                    )
                VALUES
                    (
                        $1,
                        $2,
                        $3
                    )
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
            new_data.append(new_row[0])

    # And done
    return json_response({
        "message": "Leaderboards updated successfully! :3",
        "data": [
            json_encode(dict(i))
            for i in new_data
        ],
    })


@routes.put("/api/raffle")
@utils.requires_permission(admin_panel=True)
async def put_raffle(request: Request):
    """
    Get submitted changes from the raffle admin page.
    """

    # Get the json data from the request
    raffle_data = await request.json()

    # See if this raffle has an ID; if not then it's new
    raffle_is_new = not bool(raffle_data.get('id'))

    # Add that to the database
    async with vbu.Database() as db:
        if raffle_is_new:
            new_rows = await db.call(
                """
                INSERT INTO
                    raffles
                    (
                        id,
                        name,
                        start_time,
                        end_time,
                        description,
                        image,
                        entry_price,
                        max_entries,
                        deleted
                    )
                VALUES
                    (
                        uuid_generate_v4(),
                        $1,
                        TIMEZONE('UTC', NOW()),
                        $2,
                        $3,
                        $4,
                        $5,
                        $6,
                        FALSE
                    )
                RETURNING
                    *
                """,
                raffle_data['name'], parse_time(raffle_data['end_time']),
                raffle_data['description'], raffle_data['image'],
                raffle_data['entry_price'], raffle_data['max_entries'],
            )
        else:
            new_rows = await db.call(
                """
                UPDATE
                    raffles
                SET
                    name = $2,
                    end_time = $3,
                    description = $4,
                    image = $5
                WHERE
                    id = $1
                RETURNING
                    *
                """,
                raffle_data['id'], raffle_data['name'],
                parse_time(raffle_data['end_time']),
                raffle_data['description'], raffle_data['image'],
            )

    # And done
    if raffle_is_new:
        message = "Raffle created successfully! :3"
    else:
        message = "Raffle updated successfully! :3"
    return json_response({
        "message": message,
        "data": [
            json_encode(dict(new_rows[0])),
        ],
    })


@routes.delete("/api/raffle/{id}")
@utils.requires_permission(admin_panel=True)
async def delete_raffle(request: Request):
    """
    Set a raffle to deleted
    """

    # Get the json data from the request
    raffle_id = request.match_info['id']

    # Add that to the database
    async with vbu.Database() as db:
        await db.call(
            """
            UPDATE
                raffles
            SET
                deleted = TRUE
            WHERE
                id = $1
            """,
            raffle_id,
        )

    return json_response({
        "message": "Raffle deleted :3",
        "data": [],
    })


@routes.post("/api/join_raffle")
async def post_join_raffle(request: Request):
    """
    Allow a logged in user to join a raffle.
    """

    # Get the json data from the request
    try:
        data = await request.json()
    except:
        data = {}
    session = await aiohttp_session.get_session(request)
    if not session.get("user_info", {}).get("id"):
        return json_response(
            {
                "message": "Not logged in.",
                "data": [],
            },
            status=401,
        )
    if data.get("id") is None:
        return json_response(
            {
                "message": "Missing ID from payload.",
                "data": [],
            },
            status=400,
        )

    # Add that to the database
    async with vbu.Database() as db:

        # Check the ID refers to a giveaway
        giveaway_rows = await db.call(
            """
            SELECT
                *
            FROM
                raffles
            WHERE
                id = $1
            AND
                deleted IS FALSE
            AND
                end_time > TIMEZONE('UTC', NOW())
            """,
            data['id'],
        )
        if not giveaway_rows:
            return json_response(
                {
                    "message": "Giveaway does not exist.",
                    "data": [],
                },
                status=403,
            )
        raffle = utils.Raffle(data=giveaway_rows[0])

        # Check their current entries
        entered_rows = await db.call(
            """
            SELECT
                *
            FROM
                raffle_entries
            WHERE
                user_id = $1
            AND
                raffle_id = $2
            """,
            session['user_info']['id'], data['id'],
        )
        if len(entered_rows) >= raffle.max_entries:
            return json_response(
                {
                    "message": "Entered max amount of times already.",
                    "data": [],
                },
                status=403,
            )

        # See if any points are required to enter
        if raffle.entry_price > 0:

            # Check they have the required points to enter the raffle
            se = streamelements(request)
            twitch_username = session['user_info']['twitch_username']
            points = await se.get_user_points(user=twitch_username)
            if points.points < (raffle.entry_price or 0):
                return json_response(
                    {
                        "message": "Not enough points to spend.",
                        "data": [],
                    },
                    status=403,
                )

            # Remove number of points from their user
            await se.modify_user_points(
                user=twitch_username,
                amount=-raffle.entry_price,
            )

        # Add their entry
        entry_rows = await db.call(
            """
            INSERT INTO
                raffle_entries
                (
                    raffle_id,
                    user_id
                )
            VALUES
                (
                    $1,
                    $2
                )
            RETURNING
                *
            """,
            giveaway_rows[0]['id'], session['user_info']['id']
        )

    # And done
    return json_response({
        "message": "Added entry",
        "data": [
            json_encode(dict(entry_rows[0])),
        ],
    })


@routes.get("/api/raffle_entries")
async def get_raffle_entries(request: Request):
    """
    Get the raffle entries for the logged in user.
    """

    # Get the json data from the request
    data = request.query or {}

    # Get the logged in user
    session = await aiohttp_session.get_session(request)
    if not session.get("user_info", {}).get("id"):
        return json_response({})

    # Open DB to check entries
    async with vbu.Database() as db:
        entered_rows = await db.call(
            """
            SELECT
                raffle_id, COUNT(id)
            FROM
                raffle_entries
            WHERE
                user_id = $1
            AND
                raffle_id = $2
            GROUP BY
                raffle_id
            """,
            session['user_info']['id'], data.get("id", "")
        )

    # And done
    if not entered_rows:
        return json_response({})
    return json_response(
        dict(entered_rows[0]),
        dumps=utils.HTTPEncoder().encode,
    )
