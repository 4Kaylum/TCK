from .flags import Flags, flag_value


__all__ = (
    'WebsitePermissions',
)


class WebsitePermissions(Flags):

    @flag_value
    def admin_panel(self):
        return 0b000_001
