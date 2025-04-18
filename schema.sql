-- StreamBot Database Schema

-- Table for tracking Discord servers (guilds)
CREATE TABLE IF NOT EXISTS guilds (
    guild_id TEXT PRIMARY KEY,
    name TEXT,
    date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table for tracking command channels
CREATE TABLE IF NOT EXISTS command_channels (
    channel_id TEXT PRIMARY KEY,
    guild_id TEXT NOT NULL,
    name TEXT,
    date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (guild_id) REFERENCES guilds(guild_id)
);

-- Table for tracking voice channels to join
CREATE TABLE IF NOT EXISTS voice_channels (
    channel_id TEXT PRIMARY KEY,
    guild_id TEXT NOT NULL,
    name TEXT,
    date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (guild_id) REFERENCES guilds(guild_id)
);

-- Table for mapping command channels to voice channels
CREATE TABLE IF NOT EXISTS channel_mappings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    command_channel_id TEXT NOT NULL,
    voice_channel_id TEXT NOT NULL,
    date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (command_channel_id) REFERENCES command_channels(channel_id),
    FOREIGN KEY (voice_channel_id) REFERENCES voice_channels(channel_id)
);

-- Table for video categories
CREATE TABLE IF NOT EXISTS categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    folder_path TEXT NOT NULL,
    date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table for video metadata
CREATE TABLE IF NOT EXISTS videos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename TEXT NOT NULL,
    title TEXT,
    description TEXT,
    category_id INTEGER,
    series_name TEXT,
    season INTEGER,
    episode INTEGER,
    duration INTEGER, -- Duration in seconds
    width INTEGER,
    height INTEGER,
    codec TEXT,
    file_path TEXT NOT NULL,
    date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_played TIMESTAMP,
    FOREIGN KEY (category_id) REFERENCES categories(id)
);

-- Table for playlist history
CREATE TABLE IF NOT EXISTS playlists (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    created_by TEXT, -- Discord user ID who created the playlist
    date_created TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Junction table for playlist videos
CREATE TABLE IF NOT EXISTS playlist_videos (
    playlist_id INTEGER,
    video_id INTEGER,
    position INTEGER NOT NULL, -- Position in playlist
    date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (playlist_id, video_id),
    FOREIGN KEY (playlist_id) REFERENCES playlists(id),
    FOREIGN KEY (video_id) REFERENCES videos(id)
);

-- Table for hardware acceleration settings
CREATE TABLE IF NOT EXISTS hw_accel_settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    device_name TEXT,
    device_type TEXT, -- 'nvidia', 'amd', 'intel', etc.
    encoder TEXT, -- 'h264_nvenc', 'h264_qsv', 'h264_amf', etc.
    transcode_enabled BOOLEAN DEFAULT 0,
    preferred BOOLEAN DEFAULT 0,
    ffmpeg_options TEXT, -- Additional ffmpeg options as JSON
    date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
