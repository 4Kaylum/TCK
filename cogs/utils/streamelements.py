from dataclasses import dataclass
from typing import Dict, Optional
import logging

import aiohttp


__all__ = (
    'StreamElements',
    'UserPoints',
)


log = logging.getLogger("streamelements")
log.setLevel(logging.INFO)


@dataclass
class UserPoints:
    channel: str
    username: str
    points: int
    pointsAlltime: int
    watchtime: int
    rank: int


class StreamElements:
    """
    A representation of all the stream elements API endpoints.
    """

    BASE: str = "https://api.streamelements.com/kappa/v2{}"
    # BASE: str = "https://stoplight.io/mocks/streamelements/kappa/75539{}"
    channel_id_cache: Dict[str, str] = {}

    def __init__(self, token: str, channel_id_cache: Optional[Dict[str, str]] = None):
        self.token = token
        self.channel_id: Optional[str] = None
        if channel_id_cache:
            self.channel_id_cache = channel_id_cache

    async def _request(self, method: str, url: str, **kwargs):
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/json",
        }
        log.info("Performing %s %s with %s" % (method, url, kwargs))
        async with aiohttp.ClientSession() as session:
            async with session.request(
                    method,
                    self.BASE.format(url),
                    json=kwargs or None,
                    headers=headers) as r:
                r.raise_for_status()
                d = await r.json()
        log.info("Returned %s %s %s %s" % (method, url, r.status, d))
        return d

    async def get_channel_id(self) -> str:
        """
        Get the channel ID for the current token.
        """

        if self.channel_id:
            return self.channel_id
        data = await self._request("GET", "/channels/me")
        self.channel_id = data['_id']
        self.channel_id_cache[data['username']] = self.channel_id
        return self.channel_id

    async def get_user_points(
            self,
            *,
            channel: Optional[str] = None,
            user: str) -> UserPoints:
        """
        Get the number of points a user has for a given channel.

        Parameters
        ----------
        channel : Optional[str], optional
            The channel (ID) that you want to check the user against.
            If a channel is not provided, the channel associated with the
            given token is used.
        user : str
            The username of the user you want to check.

        Returns
        -------
        UserPoints
            An object containing the user's points information.
        """

        if channel is None:
            channel = await self.get_channel_id()
        data = await self._request("GET", f"/points/{channel}/{user}")
        return UserPoints(**data)

    async def modify_user_points(
            self,
            *,
            channel: Optional[str] = None,
            user: str,
            amount: int) -> None:
        """
        Modify the number of points that a user has.

        Parameters
        ----------
        channel : Optional[str], optional
            The channel (ID) that you want to check the user against.
            If a channel is not provided, the channel associated with the
            given token is used.
        user : str
            The username of the user you want to modify.
        amount : int
            The number of points you want to change them by.
        """

        if channel is None:
            channel = await self.get_channel_id()
        await self._request("PUT", f"/points/{channel}/{user}/{amount}")
