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

    def __init__(self, data: dict):
        self.playlist_video_id = data['id']
        self._published_at = data['snippet']['contentDetails']['videoId']
        self.title = data['snippet']['title']
        self.description = data['snippet']['description']
        self.channel_id = data['snippet']['channelId']
        self.channel = data['snippet']['channelTitle']
        self.id = data['snippet']['contentDetails']['videoId']
        try:
            self.thumbnail = data['snippet']['thumbnails'][-1]['url']
        except IndexError:
            self.thumbnail = ""
    
    @property
    def published_at(self) -> int:
        v = dt.strptime(self._published_at, "%Y-%m-%dT%H:%M:%SZ")  # 2011-11-22T15:29:40Z
        return v.timestamp()

    def to_json(self):
        return {
            "playlist_video_id": self.playlist_video_id,
            "published_at": self.published_at,
            "title": self.title,
            "description": self.description,
            "channel_id": self.channel_id,
            "channel": self.channel,
            "id": self.id,
        }
    
