# StreamBot Project Notes

## Project Overview
- **Type**: Discord self-bot for streaming videos to Discord voice channels
- **Runtime**: Bun with TypeScript
- **Version**: 1.2.0
- **License**: MIT
- **Warning**: May violate Discord ToS - use at own risk

## Key Technologies & Dependencies
- **Discord**: discord.js-selfbot-v13 (v3.6.1)
- **Video Streaming**: @dank074/discord-video-stream (v5.0.1)
- **Video Processing**: fluent-ffmpeg (v2.1.3), FFmpeg (external dependency)
- **YouTube**: yt-dlp (auto-downloaded), play-dl (v1.9.7)
- **Twitch**: twitch-m3u8 (v1.1.5)
- **Web Server**: express (v5.1.0), bcrypt (v6.0.0)
- **Logging**: winston (v3.17.0)
- **Other**: axios, got, multer, dotenv

## File Structure & Key Locations
```
src/
├── index.ts           # Main bot application & command handling
├── server.ts          # Optional web interface for video management
├── config.ts          # Environment-based configuration
├── @types/index.ts    # TypeScript type definitions
└── utils/
    ├── ffmpeg.ts      # Video processing & screenshot generation
    ├── logger.ts      # Winston logging configuration
    ├── youtube.ts     # YouTube API wrapper using yt-dlp
    └── yt-dlp.ts      # yt-dlp binary management & wrapper
```

## Configuration (Environment Variables)
### Discord Self-bot
- `TOKEN`: Discord self-bot token
- `PREFIX`: Command prefix (default: "$")
- `GUILD_ID`: Discord server ID
- `COMMAND_CHANNEL_ID`: Command channel ID
- `VIDEO_CHANNEL_ID`: Voice/video channel ID

### Video Storage
- `VIDEOS_DIR`: Local video storage (default: "./videos")
- `PREVIEW_CACHE_DIR`: Thumbnail cache (default: "./tmp/preview-cache")

### Stream Settings
- `STREAM_RESPECT_VIDEO_PARAMS`: Respect original video params (true/false)
- `STREAM_WIDTH`: Video width (default: 1280)
- `STREAM_HEIGHT`: Video height (default: 720)
- `STREAM_FPS`: Frame rate (default: 30)
- `STREAM_BITRATE_KBPS`: Bitrate (default: 2000)
- `STREAM_MAX_BITRATE_KBPS`: Max bitrate (default: 2500)
- `STREAM_HARDWARE_ACCELERATION`: HW acceleration (true/false)
- `STREAM_VIDEO_CODEC`: Codec (H264/H265/VP8)
- `STREAM_H26X_PRESET`: Encoding preset (ultrafast to veryslow)

### Web Server (Optional)
- `SERVER_ENABLED`: Enable web interface (true/false)
- `SERVER_USERNAME`: Admin username (default: "admin")
- `SERVER_PASSWORD`: Admin password (default: "admin")
- `SERVER_PORT`: Server port (default: 8080)

### Jellyfin Integration (Optional)
- `JELLYFIN_ENABLED`: Enable Jellyfin integration (true/false)
- `JELLYFIN_BASE_URL`: Jellyfin server URL (default: "http://localhost:8096")
- `JELLYFIN_API_KEY`: Jellyfin API key (required if enabled)
- `JELLYFIN_USER_ID`: Specific user ID for user libraries (optional)
- `JELLYFIN_LIBRARY_ID`: Restrict to specific library (optional)

## Available Commands
| Command | Description |
|---------|-------------|
| `play <video>` | Stream local video file |
| `playlink <url>` | Stream from URL/YouTube/Twitch |
| `ytplay <query>` | Search and play YouTube video |
| `ytsearch <query>` | Search YouTube videos |
| `stop` | Stop current playback |
| `list` | Show local video library |
| `refresh` | Update video list |
| `status` | Show bot status |
| `preview <video>` | Generate video thumbnails |
| `help` | Show command help |
| `jfsearch <query>` | Search Jellyfin media library |
| `jfshows <query>` | Search TV shows specifically |
| `jfseasons <series-id>` | List seasons for a TV show |
| `jfepisodes <season-id>` | List episodes with synopses and thumbnails |
| `jfplay <item-id>` | Play media from Jellyfin |
| `jfrecent` | Show recently added items |
| `jflibs` | Show available libraries |
| `jfinfo <item-id>` | Show detailed item information |

## Core Functionality

### Video Sources Supported
1. **Local Files**: From configured videos directory
2. **YouTube**: Regular videos and live streams
3. **Twitch**: Live streams and VODs
4. **Direct URLs**: Any video file URL
5. **Jellyfin**: Media server integration with smart local/remote streaming

### Stream Processing
- Uses FFmpeg for video processing
- Supports multiple codecs: H264, H265, VP8
- Adaptive bitrate and resolution
- Hardware acceleration support
- Automatic parameter detection from source videos

### YouTube Integration
- yt-dlp automatically downloaded and updated
- Supports live stream detection and handling
- Video search and metadata extraction
- Format selection for optimal streaming

### Web Interface Features
- File upload and management
- Remote URL downloading
- Video preview with thumbnails
- Dark/light theme support
- Authentication with bcrypt

## Important Technical Details

### Stream Status Management
```typescript
streamStatus = {
    joined: boolean,
    joinsucc: boolean, 
    playing: boolean,
    manualStop: boolean,
    channelInfo: { guildId, channelId, cmdChannelId }
}
```

### yt-dlp Platform Support
- Windows: x64, x86
- macOS: Universal binary
- Linux: x64, ARM64, ARMv7

### FFmpeg Screenshot Generation
- Takes 5 screenshots at 10%, 30%, 50%, 70%, 90% timestamps
- Cached in preview directory
- 640x480 resolution for thumbnails

## Recent Development Activity
- v1.2.0: Latest version with dependency updates
- Enhanced YouTube handling via yt-dlp integration
- Improved error handling and logging
- Python 3 compatibility fixes
- Pterodactyl/Pelican deployment support
- Finishing messages for completed videos

## Security & Operational Notes
- Uses Discord self-bot (ToS violation risk)
- Requires Discord user token (sensitive)
- Web interface has basic authentication
- File upload capabilities (review for security)
- Automatic executable download (yt-dlp)
- Temp file cleanup implemented

## Docker Support
- Standard Docker Compose setup
- Cloudflare WARP integration option
- Volume mounts for videos and cache
- Environment variable configuration

## Potential Areas of Interest
1. **Discord Integration**: Self-bot implementation and streaming
2. **Video Processing**: FFmpeg integration and optimization
3. **YouTube/External Sources**: yt-dlp wrapper and content handling
4. **Web Interface**: File management and authentication
5. **Configuration**: Environment-based settings management
6. **Error Handling**: Comprehensive logging and cleanup

## Commands for Development
- `bun run start`: Start with Bun
- `bun run build`: TypeScript compilation
- `bun run start:node`: Start with Node.js
- `bun run server`: Web server only