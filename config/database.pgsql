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
-- ID is an identifier for the account. Technically we could use the
-- Twitch ID as a primary key, but this is cleaner if someone wants to
-- change the Twitch account associated with their data, for example.
-- Twitch and Discord usernames are just for display purposes, and
-- won't auto-update. Maybe just every sign in - I have the access
-- token anyway so I might as well.


CREATE TABLE IF NOT EXISTS raffles(
    id UUID PRIMARY KEY,
    name TEXT NOT NULL,
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP NOT NULL,
    description TEXT,
    image TEXT,
    entry_price INTEGER DEFAULT 0,
    max_entries INTEGER DEFAULT 1,
    deleted BOOLEAN NOT NULL DEFAULT FALSE
);
-- id UUID the ID of the raffle.
-- name TEXT the name of the item being raffled.
-- start_time TIMESTAMP the start time of the raffle.
-- end_time TIMESTAMP the end time of the raffle.
-- description TEXT? the tagline of the item being raffled.
-- image TEXT? a link (to go straight into an img src) to an image for
-- the raffle item.
-- entry_price INTEGER? the entry price for the raffle; if set to null
-- then the raffle will be registered as a giveaway and max_entries will
-- always be overriden to be 1.
-- max_entries INTEGER? the maximum number of times that a user can enter
-- a given raffle.


CREATE TABLE IF NOT EXISTS leaderboards(
    index INTEGER PRIMARY KEY,
    name TEXT,
    amount INTEGER
);
