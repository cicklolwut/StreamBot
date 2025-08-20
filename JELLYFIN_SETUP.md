# 🌟 Jellyfin Integration Setup Guide

## Overview

The Jellyfin integration has been redesigned to use a **two-bot architecture** to overcome Discord self-bot limitations:

1. **Main StreamBot** (Self-bot) - Handles video streaming and command processing
2. **Jellyfin Discord Bot** (Regular bot) - Handles rich embeds, thumbnails, and Jellyfin API interactions

## Why Two Bots?

Discord self-bots have significant limitations:
- ❌ **No embed support** - Cannot send rich embeds with thumbnails
- ❌ **Limited message formatting** - Cannot create the rich media browsing experience
- ⚠️ **ToS violations** - Using self-bots risks account suspension

**Solution**: Regular Discord bot handles visual presentation while self-bot handles streaming.

## Architecture

```
User Command → StreamBot (Self-bot) → API Call → Jellyfin Bot (Regular) → Rich Embeds in Discord
                    ↓
              Video Streaming (if play command)
```

## Setup Instructions

### Prerequisites

1. **Discord Bot Token** (regular bot, not user token)
   - Go to [Discord Developer Portal](https://discord.com/developers/applications)
   - Create a new application
   - Go to "Bot" section
   - Create bot and copy token
   - **Important**: Invite bot to your server with appropriate permissions

2. **Jellyfin Server** with API access
   - Running Jellyfin instance
   - API key generated in Jellyfin Dashboard

### Step 1: Configure Main StreamBot

Update your `.env` file:

```bash
# Existing StreamBot configuration
TOKEN="your-discord-user-token"
PREFIX="$"
GUILD_ID="your-server-id"
COMMAND_CHANNEL_ID="your-command-channel-id"
VIDEO_CHANNEL_ID="your-video-channel-id"

# Jellyfin Integration (NEW)
JELLYFIN_ENABLED="true"
JELLYFIN_BASE_URL="http://localhost:8096"
JELLYFIN_API_KEY="your-jellyfin-api-key"

# Jellyfin Discord Bot API (NEW)
JELLYFIN_BOT_API_URL="http://localhost:3001"
JELLYFIN_BOT_API_SECRET="your-shared-secret-key"
```

### Step 2: Setup Jellyfin Discord Bot

1. **Navigate to Jellyfin bot directory**:
   ```bash
   cd jellyfin-bot
   ```

2. **Install dependencies**:
   ```bash
   npm install
   # or
   bun install
   ```

3. **Configure Jellyfin bot** (`.env`):
   ```bash
   # Discord Bot Configuration
   DISCORD_TOKEN="your-discord-bot-token"
   GUILD_ID="your-server-id"  # Same as main bot
   CHANNEL_ID="your-command-channel-id"  # Same as main bot
   
   # API Server Configuration
   API_PORT="3001"
   API_SECRET="your-shared-secret-key"  # Must match main bot
   
   # Jellyfin Configuration
   JELLYFIN_BASE_URL="http://localhost:8096"
   JELLYFIN_API_KEY="your-jellyfin-api-key"  # Same as main bot
   JELLYFIN_USER_ID=""  # Optional
   JELLYFIN_LIBRARY_ID=""  # Optional
   ```

4. **Start Jellyfin Discord Bot**:
   ```bash
   bun run start
   # or
   npm start
   ```

### Step 3: Start Main StreamBot

```bash
cd ../  # Back to main directory
bun run start
```

## Bot Permissions

### Jellyfin Discord Bot Permissions Required:
- ✅ **Send Messages**
- ✅ **Embed Links** 
- ✅ **Attach Files**
- ✅ **Read Message History**
- ✅ **Use Slash Commands** (optional)

### Self-bot (Main StreamBot):
- Inherits user permissions in the server

## Commands Available

| Command | Description | Handled By |
|---------|-------------|------------|
| `$jfsearch <query>` | Search Jellyfin media | Jellyfin Bot (rich embeds) |
| `$jfshows <query>` | Search TV shows | Jellyfin Bot (with posters) |
| `$jfseasons <series-id>` | List seasons | Jellyfin Bot |
| `$jfepisodes <season-id>` | List episodes with thumbnails | Jellyfin Bot |
| `$jfplay <item-id>` | Play media | StreamBot (streaming) |
| `$jfinfo <item-id>` | Show item details | Jellyfin Bot |

## User Experience

### Enhanced Visual Browsing

**TV Show Search**: `$jfshows breaking bad`
```
📺 TV Shows for "breaking bad"

[Rich Discord Embed with show poster]
1. Breaking Bad (2008) - 5 seasons - ID: abc123
Complete series description with poster thumbnail
Released: 2008
```

**Episode Browsing**: `$jfepisodes season-id`
```
🎬 Episodes in "Season 1"

[Individual embeds for each episode with screenshots]
1. E1: Pilot - 58m - ID: xyz789
Complete episode synopsis below screenshot
Breaking Bad [Series name]
[Full-size episode screenshot]

2. E2: Cat's in the Bag... - 48m - ID: xyz790
Episode synopsis below screenshot
[Full-size episode screenshot]
```

## Troubleshooting

### Common Issues

1. **"Jellyfin Discord bot is not available"**
   - Ensure Jellyfin bot is running (`bun run start` in jellyfin-bot/)
   - Check API_PORT matches between both bots
   - Verify API_SECRET matches between both bots

2. **"No embeds showing"**
   - Verify Discord bot token (not user token) in Jellyfin bot
   - Check bot permissions in Discord server
   - Ensure bot is invited to correct server/channel

3. **"Failed to connect to Jellyfin"**
   - Verify Jellyfin server is running
   - Check JELLYFIN_API_KEY is correct
   - Test Jellyfin API manually: `curl -H "X-MediaBrowser-Token: YOUR_API_KEY" http://localhost:8096/System/Info`

### Health Check

Test if everything is working:

```bash
# Test Jellyfin bot API
curl -H "X-API-Key: your-secret-key" http://localhost:3001/health

# Expected response:
{
  "success": true,
  "message": "Jellyfin Discord Bot API is running",
  "jellyfinConnected": true
}
```

## Development

### Running in Development

**Terminal 1 - Jellyfin Bot**:
```bash
cd jellyfin-bot
bun run dev
```

**Terminal 2 - Main StreamBot**:
```bash
bun run start
```

### Logs

Both bots provide detailed logging:
- **Jellyfin Bot**: `[JELLYFIN-BOT]` prefix
- **Main Bot**: Standard StreamBot logs
- **API Communication**: Logged in both bots

## Benefits of New Architecture

✅ **Rich Visual Experience**: Full Discord embeds with thumbnails and descriptions  
✅ **Better UX**: Professional media browsing like Netflix/Plex  
✅ **Reliable**: Separates concerns between streaming and presentation  
✅ **Scalable**: Can add more visual features without self-bot limitations  
✅ **Maintainable**: Clear separation of responsibilities  

## Migration from Old Version

If upgrading from the previous single-bot Jellyfin integration:

1. **Remove old Jellyfin utilities** (if any)
2. **Add new environment variables** as shown above
3. **Set up Jellyfin Discord bot** following steps above
4. **Test commands** to ensure both bots communicate properly

The command syntax remains the same - users won't notice the difference except for much better visual presentation!