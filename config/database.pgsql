CREATE EXTENSION IF NOT EXISTS "uuid-ossp";


CREATE TABLE IF NOT EXISTS guild_settings(
    guild_id BIGINT PRIMARY KEY,
    prefix TEXT
);
-- A default guild settings table.
-- This is required for VBU and should not be deleted.
-- You can add more columns to this table should you want to add more guild-specific
-- settings.


CREATE TABLE IF NOT EXISTS user_settings(
    user_id BIGINT PRIMARY KEY
);
-- A default guild settings table.
-- This is required for VBU and should not be deleted.
-- You can add more columns to this table should you want to add more user-specific
-- settings.
-- This table is not suitable for member-specific settings as there's no
-- guild ID specified.


CREATE TABLE IF NOT EXISTS users(
    id UUID PRIMARY KEY,
    permissions BIGINT NOT NULL DEFAULT 0,
    twitch_id TEXT NOT NULL UNIQUE,
    twitch_username TEXT NOT NULL,
    discord_id TEXT UNIQUE,
    discord_username TEXT
);
