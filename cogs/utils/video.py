from datetime import datetime as dt


__all__ = (
    'Video',
)


class Video:
    """
    A container class for YouTube playlist items. Sort of.
    This entirely ignores that they're only partial items and instead
    pretends they're whole videos.
    """

    __slots__ = (
        'playlist_video_id',
        '_published_at',
        'title',
        'description',
        'channel_id',
        'channel',
        'id',
        'thumbnail',
    )

    def __init__(self, *, data: dict):
        self.playlist_video_id = data['id']
        self._published_at = data['contentDetails']['videoPublishedAt']
        self.title = data['snippet']['title']
        self.description = data['snippet']['description']
        self.channel_id = data['snippet']['channelId']
        self.channel = data['snippet']['channelTitle']
        self.id = data['contentDetails']['videoId']
        try:
            thumbnails = data['snippet']['thumbnails']
            if "maxres" in thumbnails:
                self.thumbnail = thumbnails['maxres']['url']
            # elif "standard" in thumbnails:
            #     self.thumbnail = thumbnails['standard']['url']
            # elif "high" in thumbnails:
            #     self.thumbnail = thumbnails['high']['url']
            elif "medium" in thumbnails:
                self.thumbnail = thumbnails['medium']['url']
            else:
                self.thumbnail = thumbnails['default']['url']
        except IndexError:
            self.thumbnail = ""
    
    @property
    def published_at(self) -> float:
        v = dt.strptime(self._published_at, "%Y-%m-%dT%H:%M:%SZ")  # 2011-11-22T15:29:40Z
        return v.timestamp()

    def to_json(self) -> dict:
        return {
            "playlist_video_id": self.playlist_video_id,
            "published_at": self.published_at,
            "title": self.title,
            "description": self.description,
            "channel_id": self.channel_id,
            "channel": self.channel,
            "id": self.id,
        }
    
