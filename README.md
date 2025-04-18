# StreamBot

A powerful Discord selfbot for streaming videos and live content to Discord voice channels with advanced features.

## This is certainly not anywhere near done

## Features

- **Stream videos** directly to Discord voice channels
- **Database integration** for tracking multiple channels across servers
- **Hardware acceleration support** for NVIDIA, Intel, and AMD GPUs 
- **Interactive embeds** for browsing and playing videos
- **Video categorization** using folder structure
- **TV show detection** with season/episode organization
- **Search functionality** to easily find your content
- **Playlist support** for playing multiple videos in sequence

## Installation

### Prerequisites

- Python 3.8 or higher
- FFmpeg installed and accessible in your PATH
- Discord user account token (selfbot)

### Setup

1. Clone the repository:
   ```
   git clone https://github.com/YourUsername/StreamBot.git
   cd StreamBot
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Run the setup script to create the config file and database:
   ```
   python setup.py
   ```

4. Edit the `config.json` file to add your Discord token and set other preferences.

## Configuration

Edit the `config.json` file with your settings:

```json
{
  "token": "",                           # Your Discord self-bot token
  "prefix": "$",                         # Command prefix
  "guild_id": "",                        # Default Discord server ID
  "command_channel_id": "",              # Default command channel ID
  "video_channel_id": "",                # Default voice/video channel ID
  "videos_dir": "./videos",              # Videos directory path
  "db_path": "./streambot.db",           # Database file path
  "ffmpeg_path": "ffmpeg",               # Path to FFmpeg executable
  "preview_cache_dir": "./tmp/preview-cache", # Cache directory for video thumbnails
  "stream_respect_video_params": false,  # Whether to respect video parameters
  "stream_width": 1280,                  # Stream width in pixels
  "stream_height": 720,                  # Stream height in pixels
  "stream_fps": 30,                      # Stream FPS
  "stream_bitrate_kbps": 2000,           # Stream bitrate in kbps
  "stream_max_bitrate_kbps": 2500,       # Maximum stream bitrate in kbps
  "stream_h26x_preset": "ultrafast",     # H26x preset for encoding
  "hw_accel_enabled": true,              # Enable hardware acceleration
  "transcode_enabled": false             # Enable video transcoding
}
```

## Video Organization

StreamBot now supports organizing videos in categories using folders:

```
videos/
├── Movies/
│   ├── Movie1.mp4
│   └── Movie2.mkv
├── TV Shows/
│   ├── Show 1/
│   │   ├── Show 1 - S01E01 - Pilot.mp4
│   │   └── Show 1 - S01E02 - Episode.mp4
│   └── Show 2/
│       ├── Show 2 S01E01 Pilot.mp4
│       └── Show 2 S01E02 Episode.mp4
└── Uncategorized/
    └── video.mp4
```

TV show episodes can be named in several formats:
- `Show Name - S01E02 - Episode Title.mp4`
- `Show Name S01E02 Episode Title.mp4`
- `Show.Name.1x02.Episode.Title.mp4`

## Usage

1. Start the bot:
   ```
   python main.py
   ```

2. Use commands in a Discord channel to control the bot:

### Commands

#### Video Playback
- `$play <file_path>` - Play a video
- `$stop` - Stop playback and leave voice channel
- `$pause` - Pause playback
- `$resume` - Resume playback

#### Video Management
- `$list` - Show interactive video browser with categories
- `$search <term>` - Search for videos
- `$scan` - Scan videos directory for new files

#### Playlist Management
- `$playlist <file1> <file2> ...` - Create and play a playlist
- `$playlist` - Show current playlist
- `$next` - Play next item in playlist
- `$prev` - Play previous item in playlist

#### Channel Management
- `$channel` - Show channel mappings
- `$channel <voice_channel_id>` - Set voice channel for this command channel
- `$add_channel <voice|command> <channel_id> [name]` - Add a channel
- `$map_channel <command_channel_id> <voice_channel_id>` - Map command channel to voice channel

#### System
- `$hwinfo` - Show hardware acceleration information
- `$help` - Show help message

## Interactive Embeds

The updated StreamBot features interactive embeds for browsing and playing videos:

1. **Categories View** - Shows all video categories with pagination
2. **Video List** - Shows videos within a category with pagination
3. **Series Episodes** - Shows episodes of a TV series organized by season
4. **Search Results** - Shows search results with options to play

Use reactions to navigate the embeds:
- ⬅️ / ➡️ - Navigate pages
- 📁 - Select a category
- 🎬 - View videos
- 📺 - Expand a TV series
- ▶️ - Play a video
- 📋 - Play all episodes in a series
- 🔙 - Go back to previous view
- ❌ - Close the embed

## Hardware Acceleration

The bot automatically detects available hardware acceleration devices:

- **NVIDIA GPUs** using NVENC encoder
- **Intel GPUs** using QuickSync (including Intel Arc)
- **AMD GPUs** using AMF encoder

Use the `$hwinfo` command to see detected hardware and current settings.

## Notes

- Selfbots violate Discord's Terms of Service. Use at your own risk.
- The bot requires a Discord user account token, not a bot token.
- For best performance, keep videos in the MP4 or MKV format with H.264 or H.265 codec.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
