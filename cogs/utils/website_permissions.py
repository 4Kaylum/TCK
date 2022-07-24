class WebsitePermissions:

    VALID_FLAGS = {
        "admin_panel": 0b000_000_000_001,
    }

    def __init__(self, value: int = 0, **kwargs):
        self.value = value
        for i, o in kwargs.items():
            setattr(self, i, o)

    @classmethod
    def all(cls):
        return cls(0b111_111_111_111)

    @property
    def admin_panel(self) -> bool:
        return bool(self.value & self.VALID_FLAGS['admin_panel'])

    @admin_panel.setter
    def admin_panel(self, v: bool):
        if v:
            self.value |= self.VALID_FLAGS['admin_panel']
        else:
            self.value &= ~self.VALID_FLAGS['admin_panel']
