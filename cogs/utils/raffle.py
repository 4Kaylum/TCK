from typing import Optional
from uuid import UUID
from datetime import datetime as dt


__all__ = (
    'Raffle',
)


class Raffle:
    """
    A raffle or giveaway item.

    Attributes
    -----------
    id: UUID
        The ID of the raffle.
    name: str
        The name of the item being given away.
    start_time: dt
        The start time of the raffle, ie when it was created.
    end_time: dt
        The end time of the raffle.
    description: Optional[str]
        A description of the item being given away.
    image: Optional[str]
        An image to be shown with the item.
    entry_price: Optional[int]
        An entry price for the raffle. If it's ``0``, then max_entries will
        automatically be set to ``1``.
    max_entries: Optional[int]
        The maximum number of times that a user can enter the giveaway.
    is_giveaway: bool
        Whether or not this raffle is a giveaway or not. Shorthand for
        ``.entry_price in [None, 0]``.
    """

    __slots__ = (
        'id',
        'name',
        'start_time',
        'end_time',
        'description',
        'image',
        'entry_price',
        '_max_entries',
    )

    def __init__(self, *, data: dict):
        self.id: UUID = data['id']
        self.name: str = data['name']
        self.start_time: dt = data['start_time']
        self.end_time: dt = data['end_time']
        self.description: Optional[str] = data['description']
        self.image: Optional[str] = data['image']
        self.entry_price: Optional[int] = data['entry_price']
        self._max_entries: Optional[int] = data['max_entries']

    @property
    def max_entries(self) -> Optional[int]:
        if self.entry_price is None or self.entry_price <= 0:
            return 1
        return self._max_entries

    @property
    def is_giveaway(self) -> bool:
        return self.entry_price in [None, 0]

