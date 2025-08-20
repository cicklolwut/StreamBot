<div align="center">

# StreamBot

[![Ceasefire Now](https://badge.techforpalestine.org/default)](https://techforpalestine.org/learn-more)

A powerful Discord selfbot for streaming videos and live content to Discord voice channels.

![GitHub release](https://img.shields.io/github/v/release/ysdragon/StreamBot)
[![CodeFactor](https://www.codefactor.io/repository/github/ysdragon/streambot/badge)](https://www.codefactor.io/repository/github/ysdragon/streambot)

</div>

## ✨ Features

- 📁 Stream videos from a local folder
- 🎬 Stream and search YouTube videos by title
- 🔗 Stream YouTube videos/live streams by link
- 🌐 Stream from arbitrary links (video files, live streams, Twitch, etc.)
- ⚡ Playback controls: play, stop
- 📋 Video library management

## 📋 Requirements
- [Bun](https://bun.sh/) `v1.1.39+`
- [FFmpeg](https://www.ffmpeg.org/) _(in PATH or working directory)_

## 🚀 Installation

This project is [hosted on GitHub](https://github.com/ysdragon/StreamBot).

1. Clone the repository:
```bash
git clone https://github.com/ysdragon/StreamBot
```

2. Install dependencies:
```bash
bun install
```

3. Configure environment:
   - Rename `.env.example` to `.env`
   - Update configuration values

## 🎮 Usage

Start with Bun:
```bash
bun run start
```

Start with Node.js:
```bash
bun run build
bun run start:node
```

## 🐳 Docker Setup

### Standard Setup
1. Create a directory and navigate to it:
```bash
mkdir streambot && cd streambot
```

2. Download the compose file:
```bash
wget https://raw.githubusercontent.com/ysdragon/StreamBot/main/docker-compose.yml
```

3. Configure environment variables in `docker-compose.yml`

4. Launch container:
```bash
docker compose up -d
```

### Cloudflare WARP Setup
1. Download WARP compose file:
```bash
wget https://raw.githubusercontent.com/ysdragon/StreamBot/main/docker-compose-warp.yml
```

2. Configure `docker-compose-warp.yml` and add your WARP license key

3. Launch with WARP:
```bash
docker compose -f docker-compose-warp.yml up -d
```
> [!NOTE]
> The basic video server will not work if you use WARP.


## 🎯 Commands

### Core Commands
| Command | Description |
|---------|-------------|
| `play <video>` | Play local video |
| `playlink <url>` | Stream from URL/YouTube/Twitch |
| `ytplay <query>` | Play YouTube video |
| `ytsearch <query>` | Search YouTube |
| `stop` | Stop playback |
| `list` | Show video library |
| `refresh` | Update video list |
| `status` | Show playback status |
| `preview <video>` | Generate thumbnails |
| `help` | Show help |

### Jellyfin Commands (Optional)
| Command | Description |
|---------|-------------|
| `jfsearch <query>` | Search Jellyfin media library |
| `jfshows <query>` | Search TV shows specifically |
| `jfseasons <series-id>` | List seasons for a TV show |
| `jfepisodes <season-id>` | List episodes with synopses and thumbnails |
| `jfplay <item-id>` | Play media from Jellyfin |
| `jfrecent` | Show recently added items |
| `jflibs` | Show available libraries |
| `jfinfo <item-id>` | Show detailed item information |

## Configuration

Configuration is done via `.env`:

```bash
# Selfbot options
TOKEN = "" # Your Discord self-bot token
PREFIX = "$" # The prefix used to trigger your self-bot commands
GUILD_ID = "" # The ID of the Discord server your self-bot will be running on
COMMAND_CHANNEL_ID = "" # The ID of the Discord channel where your self-bot will respond to commands
VIDEO_CHANNEL_ID = "" # The ID of the Discord voice/video channel where your self-bot will stream videos

# General options
VIDEOS_DIR = "./videos" # The local path where you store video files
PREVIEW_CACHE_DIR = "./tmp/preview-cache" # The local path where your self-bot will cache video preview thumbnails

# Stream options
STREAM_RESPECT_VIDEO_PARAMS = "false"  # This option is used to respect video parameters such as width, height, fps, bitrate, and max bitrate.
STREAM_WIDTH = "1280" # The width of the video stream in pixels
STREAM_HEIGHT = "720" # The height of the video stream in pixels
STREAM_FPS = "30" # The frames per second (FPS) of the video stream
STREAM_BITRATE_KBPS = "2000" # The bitrate of the video stream in kilobits per second (Kbps)
STREAM_MAX_BITRATE_KBPS = "2500" # The maximum bitrate of the video stream in kilobits per second (Kbps)
STREAM_HARDWARE_ACCELERATION = "false" # Whether to use hardware acceleration for video decoding, set to "true" to enable, "false" to disable
STREAM_VIDEO_CODEC = "H264" # The video codec to use for the stream, can be "H264" or "H265" or "VP8"

# STREAM_H26X_PRESET: Determines the encoding preset for H26x video streams. 
# If the STREAM_H26X_PRESET environment variable is set, it parses the value 
# using the parsePreset function. If not set, it defaults to 'ultrafast' for 
# optimal encoding speed. This preset is only applicable when the codec is 
# H26x; otherwise, it should be disabled or ignored.
# Available presets: "ultrafast", "superfast", "veryfast", "faster", 
# "fast", "medium", "slow", "slower", "veryslow".
STREAM_H26X_PRESET = "ultrafast"

# Videos server options
SERVER_ENABLED = "false" # Whether to enable the built-in video server
SERVER_USERNAME = "admin" # The username for the video server's admin interface
SERVER_PASSWORD = "admin" # The password for the video server's admin interface
SERVER_PORT = "8080" # The port number the video server will listen on

# Jellyfin integration options (optional)
JELLYFIN_ENABLED = "false" # Enable Jellyfin media library integration
JELLYFIN_BASE_URL = "http://localhost:8096" # Jellyfin server URL
JELLYFIN_API_KEY = "" # Jellyfin API key (generate in Dashboard > API Keys)
JELLYFIN_USER_ID = "" # Optional: specific user ID for user libraries
JELLYFIN_LIBRARY_ID = "" # Optional: restrict to specific library
```

## Get Token ?
Check the [Get token wiki](https://github.com/ysdragon/StreamBot/wiki/Get-Discord-user-token)

## Server

An optional basic HTTP server can be enabled to manage the video library:

- List videos
- Upload videos
- Delete videos
- Generate video preview thumbnails

## 🌟 Jellyfin Integration

StreamBot can integrate with your Jellyfin media server to browse and play your media library directly through Discord commands.

### Setup

1. **Enable Jellyfin Integration**:
   ```bash
   JELLYFIN_ENABLED="true"
   JELLYFIN_BASE_URL="http://your-jellyfin-server:8096"
   ```

2. **Generate API Key**:
   - Go to Jellyfin Dashboard → API Keys
   - Create a new API key for StreamBot
   - Add it to your configuration:
   ```bash
   JELLYFIN_API_KEY="your-api-key-here"
   ```

3. **Optional Configuration**:
   - **User ID**: Restrict to a specific user's libraries
   - **Library ID**: Restrict to a specific library (movies, TV shows, etc.)

### Features

- **🔍 Search**: Find media by title across your entire library
- **📺 TV Show Navigation**: Browse shows → seasons → episodes hierarchically
- **🖼️ Rich Media Display**: Episode thumbnails and detailed synopses
- **📅 Recent**: Browse recently added content
- **📚 Libraries**: View available media libraries
- **🎬 Smart Playback**: Automatically uses local files when available, streams when remote
- **ℹ️ Details**: View comprehensive media information

### TV Show Browsing Workflow

1. **Search for Shows**: `$jfshows breaking bad`
   
   Shows are displayed with **rich Discord embeds** featuring:
   - **Show posters** as thumbnails
   - **Complete series descriptions** from Jellyfin
   - **Production year** and season count
   
   ```
   1. 📺 `Breaking Bad` (2008) - 5 seasons - ID: `12345`
   [Discord Embed with show poster and description]
   ```

2. **Browse Seasons**: `$jfseasons 12345`
   ```
   📅 Seasons for "Breaking Bad"
   1. 📅 Season 1 (7 episodes) - ID: `54321`
   2. 📅 Season 2 (13 episodes) - ID: `54322`
   ```

3. **View Episodes**: `$jfepisodes 54321`
   
   Episodes are displayed with **rich Discord embeds** featuring:
   - **Episode screenshots** as full-size images
   - **Complete synopses** from Jellyfin metadata
   - **Series context** and episode information
   
   Each episode appears as a separate message with:
   ```
   1. 🎬 E1: `Pilot` - 58m - ID: `98765`
   [Discord Embed with episode screenshot and synopsis]
   
   2. 🎬 E2: `Cat's in the Bag...` - 48m - ID: `98766`
   [Discord Embed with episode screenshot and synopsis]
   ```

4. **Play Episode**: `$jfplay 98765`

### Local vs Remote Streaming

StreamBot intelligently handles media sources:

- **Local Access**: If the bot and Jellyfin are on the same machine/network and can access the media files directly, it will use the local file path for optimal performance
- **Remote Streaming**: If local access isn't available, it generates a streaming URL from Jellyfin for remote playback

This ensures the best possible streaming quality and performance regardless of your setup.

## Todo

- [x] Adding ytsearch and ytplay commands
- [x] Jellyfin media server integration
- [x] Smart local/remote streaming detection
- [x] Comprehensive media search and browsing

## 🤝 Contributing
Contributions are welcome! Feel free to:
- 🐛 Report bugs via [issues](https://github.com/ysdragon/StreamBot/issues/new)
- 🔧 Submit [pull requests](https://github.com/ysdragon/StreamBot/pulls)
- 💡 Suggest new features

## ⚠️ Legal

This bot may violate Discord's ToS. Use at your own risk.

## إبراء الذمة
أتبرأ من أي استخدام غير أخلاقي لهذا المشروع أمام الله.

## 📝 License

Licensed under MIT License. See [LICENSE](https://github.com/ysdragon/StreamBot/blob/main/LICENSE) for details.
