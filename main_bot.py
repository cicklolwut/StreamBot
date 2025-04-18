import discord
import asyncio
import os
import sys
import logging
import subprocess
import re
import json
import argparse
from typing import List, Dict, Optional, Tuple, Any, Union
from datetime import datetime
import traceback

# Import our modules
from db_utils import init_db, DatabaseManager
from hw_accel import init_hw_accel, HardwareAcceleration
from selfbot_embeds import init_embeds, InteractiveEmbed

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("streambot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Constants
DEFAULT_CONFIG_PATH = "./config.json"
DEFAULT_SCHEMA_PATH = "./schema.sql"

class StreamBot(discord.Client):
    """Discord selfbot for streaming videos to Discord voice channels."""
    
    def __init__(self, config_path: str = DEFAULT_CONFIG_PATH):
        """Initialize the bot.
        
        Args:
            config_path: Path to the configuration file
        """
        # Initialize with discord.py-self specific options
        super().__init__(
            self_bot=True,  # Important for selfbots
            chunk_guilds_at_startup=False,
            heartbeat_timeout=120.0
        )
        
        # Load configuration
        self.config = self._load_config(config_path)
        
        # Set command prefix
        self.command_prefix = self.config.get("prefix", "$")
        
        # Initialize database
        self.db_manager = None
        self._init_database()
        
        # Initialize hardware acceleration
        self.hw_accel = None
        self._init_hw_acceleration()
        
        # Initialize interactive embeds
        self.interactive_embeds = None
        
        # State variables
        self.current_voice_channel = None
        self.current_stream_process = None
        self.current_playlist = []
        self.current_playlist_index = 0
        
        # Command handlers
        self.commands = {
            "play": self._cmd_play,
            "stop": self._cmd_stop,
            "pause": self._cmd_pause,
            "resume": self._cmd_resume,
            "list": self._cmd_list,
            "search": self._cmd_search,
            "playlist": self._cmd_playlist,
            "next": self._cmd_next,
            "prev": self._cmd_prev,
            "channel": self._cmd_channel,
            "add_channel": self._cmd_add_channel,
            "map_channel": self._cmd_map_channel,
            "scan": self._cmd_scan_videos,
            "hwinfo": self._cmd_hw_info,
            "help": self._cmd_help
        }
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from file.
        
        Args:
            config_path: Path to the configuration file
            
        Returns:
            Configuration dictionary
        """
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    config = json.load(f)
                    logger.info(f"Loaded configuration from {config_path}")
                    return config
            else:
                logger.warning(f"Config file {config_path} not found, using default values")
                return self._create_default_config(config_path)
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            return self._create_default_config(config_path)
    
    def _create_default_config(self, config_path: str) -> Dict[str, Any]:
        """Create a default configuration file.
        
        Args:
            config_path: Path to save the configuration file
            
        Returns:
            Default configuration dictionary
        """
        default_config = {
            "token": "",
            "prefix": "$",
            "guild_id": "",
            "command_channel_id": "",
            "video_channel_id": "",
            "videos_dir": "./videos",
            "db_path": "./streambot.db",
            "ffmpeg_path": "ffmpeg",
            "preview_cache_dir": "./tmp/preview-cache",
            "stream_respect_video_params": False,
            "stream_width": 1280,
            "stream_height": 720,
            "stream_fps": 30,
            "stream_bitrate_kbps": 2000,
            "stream_max_bitrate_kbps": 2500,
            "stream_h26x_preset": "ultrafast",
            "hw_accel_enabled": True,
            "transcode_enabled": False,
            "server_enabled": False,
            "server_username": "admin",
            "server_password": "admin",
            "server_port": 8080
        }
        
        try:
            with open(config_path, 'w') as f:
                json.dump(default_config, f, indent=4)
                logger.info(f"Created default configuration at {config_path}")
        except Exception as e:
            logger.error(f"Error creating default configuration: {e}")
        
        return default_config
    
    def _init_database(self):
        """Initialize the database."""
        try:
            db_path = self.config.get("db_path", "./streambot.db")
            
            # Ensure the schema.sql file exists
            if not os.path.exists(DEFAULT_SCHEMA_PATH):
                with open(DEFAULT_SCHEMA_PATH, 'w') as f:
                    # Copy the schema from our schema artifact
                    from pathlib import Path
                    script_dir = Path(__file__).parent
                    schema_path = script_dir / "db_schema.sql"
                    
                    if os.path.exists(schema_path):
                        with open(schema_path, 'r') as schema_file:
                            f.write(schema_file.read())
                    else:
                        logger.error(f"Schema file not found at {schema_path}")
                        return
            
            # Initialize the database
            self.db_manager = init_db(db_path)
            logger.info(f"Initialized database at {db_path}")
            
            # Add default guild and channels from config
            guild_id = self.config.get("guild_id")
            cmd_channel_id = self.config.get("command_channel_id")
            video_channel_id = self.config.get("video_channel_id")
            
            if guild_id and cmd_channel_id and video_channel_id:
                self.db_manager.add_guild(guild_id, "Default Guild")
                self.db_manager.add_command_channel(cmd_channel_id, guild_id, "Default Command Channel")
                self.db_manager.add_voice_channel(video_channel_id, guild_id, "Default Voice Channel")
                self.db_manager.map_channels(cmd_channel_id, video_channel_id)
                logger.info(f"Added default channels from config")
            
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            logger.error(traceback.format_exc())
    
    def _init_hw_acceleration(self):
        """Initialize hardware acceleration."""
        try:
            ffmpeg_path = self.config.get("ffmpeg_path", "ffmpeg")
            
            # Initialize hardware acceleration
            self.hw_accel = init_hw_accel(self.db_manager, ffmpeg_path)
            logger.info(f"Initialized hardware acceleration")
            
            # Log detected devices
            devices = self.hw_accel.detected_devices
            logger.info(f"Detected {len(devices)} hardware acceleration devices")
            for device in devices:
                logger.info(f"- {device['device_name']} ({device['device_type']}): {device['encoder']}")
            
        except Exception as e:
            logger.error(f"Error initializing hardware acceleration: {e}")
            logger.error(traceback.format_exc())
    
    async def on_ready(self):
        """Called when the bot is ready."""
        logger.info(f'Logged in as {self.user.name} ({self.user.id})')
        
        # Initialize interactive embeds
        self.interactive_embeds = init_embeds(self, self.db_manager)
        logger.info(f"Initialized interactive embeds")
        
        # Scan videos directory
        await self._scan_videos_directory()
        
        logger.info(f'Bot is ready!')
    
    async def on_message(self, message):
        """Called when a message is received.
        
        Args:
            message: Discord message
        """
        # Ignore messages from self
        if message.author.id != self.user.id:
            return
        
        # Check if message starts with command prefix
        if not message.content.startswith(self.command_prefix):
            return
        
        # Extract command and arguments
        command_parts = message.content[len(self.command_prefix):].split(maxsplit=1)
        command = command_parts[0].lower() if command_parts else ""
        args = command_parts[1] if len(command_parts) > 1 else ""
        
        # Handle command
        if command in self.commands:
            # Check if command should be executed in this channel
            if not await self._is_valid_command_channel(message.channel.id):
                return
            
            try:
                # Log command
                logger.info(f"Executing command: {command} {args}")
                
                # Execute command
                await self.commands[command](message, args)
            except Exception as e:
                logger.error(f"Error executing command {command}: {e}")
                logger.error(traceback.format_exc())
                await message.channel.send(f"Error executing command: {e}")
    
    async def _is_valid_command_channel(self, channel_id: int) -> bool:
        """Check if a channel is a valid command channel.
        
        Args:
            channel_id: Discord channel ID
            
        Returns:
            True if valid, False otherwise
        """
        if not self.db_manager:
            # If no database, use the channel from config
            return str(channel_id) == self.config.get("command_channel_id")
        
        # Get all command channels from the database
        cmd_channels = self.db_manager.cursor.execute(
            "SELECT channel_id FROM command_channels"
        ).fetchall()
        
        # Check if the channel is in the list
        return any(str(channel_id) == row['channel_id'] for row in cmd_channels)
    
    async def _get_voice_channel_for_command(self, command_channel_id: int) -> Optional[int]:
        """Get the voice channel associated with a command channel.
        
        Args:
            command_channel_id: Discord command channel ID
            
        Returns:
            Voice channel ID if found, None otherwise
        """
        if not self.db_manager:
            # If no database, use the channel from config
            return int(self.config.get("video_channel_id"))
        
        # Get the voice channel from the database
        voice_channel_id = self.db_manager.get_voice_channel_by_command_channel(str(command_channel_id))
        
        if voice_channel_id:
            return int(voice_channel_id)
        
        # Fall back to the config
        return int(self.config.get("video_channel_id"))
    
    async def _scan_videos_directory(self):
        """Scan the videos directory and add videos to the database."""
        if not self.db_manager:
            return
        
        videos_dir = self.config.get("videos_dir", "./videos")
        
        if not os.path.exists(videos_dir):
            os.makedirs(videos_dir)
            logger.info(f"Created videos directory at {videos_dir}")
        
        logger.info(f"Scanning videos directory: {videos_dir}")
        
        # Check for subdirectories (categories)
        try:
            for root, dirs, files in os.walk(videos_dir):
                # Skip the preview cache directory
                if self.config.get("preview_cache_dir", "") in root:
                    continue
                
                # Get the relative path from the videos directory
                rel_path = os.path.relpath(root, videos_dir)
                
                # If this is a subdirectory, add it as a category
                if rel_path != "." and not rel_path.startswith(".."):
                    category_name = os.path.basename(root)
                    category_id = self.db_manager.add_category(category_name, root)
                    logger.info(f"Added category: {category_name} ({root})")
                else:
                    category_id = None
                    category_name = "Uncategorized"
                
                # Process video files
                video_extensions = ['.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm']
                video_files = [f for f in files if os.path.splitext(f)[1].lower() in video_extensions]
                
                for filename in video_files:
                    # Get the full path to the video
                    file_path = os.path.join(root, filename)
                    
                    # Extract metadata from the filename
                    title, series_name, season, episode = self._parse_filename(filename)
                    
                    # Get video duration and codec using ffprobe
                    duration, width, height, codec = await self._get_video_metadata(file_path)
                    
                    # Add the video to the database
                    self.db_manager.add_video(
                        filename=filename,
                        file_path=file_path,
                        title=title,
                        description=None,
                        category_id=category_id,
                        series_name=series_name,
                        season=season,
                        episode=episode,
                        duration=duration,
                        width=width,
                        height=height,
                        codec=codec
                    )
                    
                    logger.info(f"Added video: {filename} ({file_path})")
            
            logger.info(f"Finished scanning videos directory")
            
        except Exception as e:
            logger.error(f"Error scanning videos directory: {e}")
            logger.error(traceback.format_exc())
    
    def _parse_filename(self, filename: str) -> Tuple[str, Optional[str], Optional[int], Optional[int]]:
        """Parse a filename to extract metadata.
        
        Args:
            filename: Video filename
            
        Returns:
            Tuple of (title, series_name, season, episode)
        """
        # Remove extension
        name = os.path.splitext(filename)[0]
        
        # Try to match TV show patterns
        # Pattern like "Show Name - S01E02 - Episode Title"
        match = re.match(r'(.+?)\s*-\s*S(\d+)E(\d+)(?:\s*-\s*(.+))?', name)
        if match:
            series_name = match.group(1).strip()
            season = int(match.group(2))
            episode = int(match.group(3))
            title = match.group(4).strip() if match.group(4) else f"Episode {episode}"
            return (title, series_name, season, episode)
        
        # Pattern like "Show Name S01E02 Episode Title"
        match = re.match(r'(.+?)\s*S(\d+)E(\d+)(?:\s+(.+))?', name)
        if match:
            series_name = match.group(1).strip()
            season = int(match.group(2))
            episode = int(match.group(3))
            title = match.group(4).strip() if match.group(4) else f"Episode {episode}"
            return (title, series_name, season, episode)
        
        # Pattern like "Show.Name.1x02.Episode.Title"
        match = re.match(r'(.+?)\.(\d+)x(\d+)(?:\.(.+))?', name.replace(' ', '.'))
        if match:
            series_name = match.group(1).replace('.', ' ').strip()
            season = int(match.group(2))
            episode = int(match.group(3))
            title = match.group(4).replace('.', ' ').strip() if match.group(4) else f"Episode {episode}"
            return (title, series_name, season, episode)
        
        # If no pattern matches, assume it's a movie
        return (name, None, None, None)
    
    async def _get_video_metadata(self, file_path: str) -> Tuple[Optional[int], Optional[int], Optional[int], Optional[str]]:
        """Get video metadata using ffprobe.
        
        Args:
            file_path: Path to the video file
            
        Returns:
            Tuple of (duration, width, height, codec)
        """
        try:
            # Use ffprobe to get video metadata
            ffprobe_cmd = [
                self.config.get("ffmpeg_path", "ffmpeg").replace("ffmpeg", "ffprobe"),
                "-v", "error",
                "-select_streams", "v:0",
                "-show_entries", "stream=codec_name,width,height,duration",
                "-of", "json",
                file_path
            ]
            
            # Run ffprobe
            result = await asyncio.create_subprocess_exec(
                *ffprobe_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await result.communicate()
            
            if result.returncode != 0:
                logger.error(f"Error getting video metadata: {stderr.decode()}")
                return (None, None, None, None)
            
            # Parse the JSON output
            metadata = json.loads(stdout.decode())
            
            # Extract relevant information
            if 'streams' in metadata and metadata['streams']:
                stream = metadata['streams'][0]
                duration = int(float(stream.get('duration', 0)))
                width = stream.get('width')
                height = stream.get('height')
                codec = stream.get('codec_name')
                
                return (duration, width, height, codec)
            
            return (None, None, None, None)
            
        except Exception as e:
            logger.error(f"Error getting video metadata: {e}")
            return (None, None, None, None)
    
    async def _join_voice_channel(self, channel_id: int) -> bool:
        """Join a voice channel.
        
        Args:
            channel_id: Discord voice channel ID
            
        Returns:
            True if joined successfully, False otherwise
        """
        try:
            # Get the channel
            channel = self.get_channel(channel_id)
            if not channel:
                channel = await self.fetch_channel(channel_id)
            
            # Check if it's a voice channel
            if not isinstance(channel, discord.VoiceChannel):
                logger.error(f"Channel {channel_id} is not a voice channel")
                return False
            
            # Connect to the channel
            self.current_voice_channel = await channel.connect()
            logger.info(f"Joined voice channel: {channel.name} ({channel.id})")
            
            return True
            
        except Exception as e:
            logger.error(f"Error joining voice channel: {e}")
            return False
    
    async def _leave_voice_channel(self):
        """Leave the current voice channel."""
        if self.current_voice_channel:
            await self.current_voice_channel.disconnect()
            self.current_voice_channel = None
            logger.info("Left voice channel")
    
    async def _stream_video(self, file_path: str, transcode: bool = False) -> bool:
        """Stream a video to the current voice channel.
        
        Args:
            file_path: Path to the video file
            transcode: Whether to transcode the video
            
        Returns:
            True if streaming started successfully, False otherwise
        """
        if not self.current_voice_channel:
            logger.error("Not connected to a voice channel")
            return False
        
        # Stop any current stream
        await self._stop_stream()
        
        try:
            # Get hardware acceleration settings
            hw_device = None
            if self.hw_accel and self.config.get("hw_accel_enabled", True):
                hw_device = self.hw_accel.get_preferred_device()
            
            # Build the ffmpeg command
            ffmpeg_cmd = [self.config.get("ffmpeg_path", "ffmpeg")]
            
            # Input file
            ffmpeg_cmd.extend(["-i", file_path])
            
            # Hardware acceleration or transcoding options
            if transcode or self.config.get("transcode_enabled", False):
                # Use hardware acceleration if available
                if hw_device:
                    # Add hardware acceleration arguments
                    hw_args = self.hw_accel.generate_ffmpeg_hw_accel_args(hw_device)
                    ffmpeg_cmd.extend(hw_args)
                else:
                    # Software encoding settings
                    ffmpeg_cmd.extend([
                        "-c:v", "libx264",
                        "-preset", self.config.get("stream_h26x_preset", "ultrafast"),
                        "-tune", "zerolatency",
                        "-crf", "23"
                    ])
                
                # Respect video parameters if enabled
                if self.config.get("stream_respect_video_params", False):
                    ffmpeg_cmd.extend([
                        "-s", f"{self.config.get('stream_width', 1280)}x{self.config.get('stream_height', 720)}",
                        "-r", str(self.config.get("stream_fps", 30)),
                        "-b:v", f"{self.config.get('stream_bitrate_kbps', 2000)}k",
                        "-maxrate", f"{self.config.get('stream_max_bitrate_kbps', 2500)}k",
                        "-bufsize", f"{self.config.get('stream_bitrate_kbps', 2000) * 2}k"
                    ])
            else:
                # Copy video codec (no transcoding)
                ffmpeg_cmd.extend(["-c:v", "copy"])
            
            # Audio settings (always copy audio)
            ffmpeg_cmd.extend(["-c:a", "copy"])
            
            # Output format
            ffmpeg_cmd.extend([
                "-f", "matroska",
                "-"  # Output to stdout
            ])
            
            # Log the command
            logger.info(f"Starting stream with command: {' '.join(ffmpeg_cmd)}")
            
            # Start the ffmpeg process
            self.current_stream_process = await asyncio.create_subprocess_exec(
                *ffmpeg_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            # Start streaming
            self.current_voice_channel.play(
                discord.FFmpegPCMAudio(
                    source=self.current_stream_process.stdout,
                    pipe=True
                )
            )
            
            # Log that streaming started
            logger.info(f"Started streaming: {file_path}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error streaming video: {e}")
            logger.error(traceback.format_exc())
            return False
    
    async def _stop_stream(self):
        """Stop the current stream."""
        # Stop voice client
        if self.current_voice_channel and self.current_voice_channel.is_playing():
            self.current_voice_channel.stop()
            logger.info("Stopped voice client")
        
        # Stop ffmpeg process
        if self.current_stream_process:
            try:
                self.current_stream_process.terminate()
                await self.current_stream_process.wait()
            except:
                pass
            self.current_stream_process = None
            logger.info("Stopped ffmpeg process")
    
    async def _pause_stream(self):
        """Pause the current stream."""
        if self.current_voice_channel and self.current_voice_channel.is_playing():
            self.current_voice_channel.pause()
            logger.info("Paused stream")
            return True
        return False
    
    async def _resume_stream(self):
        """Resume the current stream."""
        if self.current_voice_channel and self.current_voice_channel.is_paused():
            self.current_voice_channel.resume()
            logger.info("Resumed stream")
            return True
        return False
    
    async def _play_playlist(self):
        """Play the current playlist."""
        if not self.current_playlist:
            logger.warning("Playlist is empty")
            return False
        
        # Check if we're at the end of the playlist
        if self.current_playlist_index >= len(self.current_playlist):
            self.current_playlist_index = 0
        
        # Get the current video
        current_video = self.current_playlist[self.current_playlist_index]
        
        # Check if the file exists
        if not os.path.exists(current_video):
            logger.warning(f"Video file not found: {current_video}")
            # Skip to the next video
            self.current_playlist_index += 1
            return await self._play_playlist()
        
        # Join voice channel if not already connected
        if not self.current_voice_channel:
            voice_channel_id = await self._get_voice_channel_for_command(int(self.config.get("command_channel_id")))
            if not await self._join_voice_channel(voice_channel_id):
                logger.error("Failed to join voice channel")
                return False
        
        # Stream the video
        if await self._stream_video(current_video):
            logger.info(f"Playing playlist item {self.current_playlist_index + 1}/{len(self.current_playlist)}: {current_video}")
            return True
        
        return False
    
    # Command handlers
    
    async def _cmd_play(self, message, args):
        """Handle the play command.
        
        Args:
            message: Discord message
            args: Command arguments
        """
        if not args:
            await message.channel.send("Please specify a video file path")
            return
        
        # Check if the file exists
        if not os.path.exists(args):
            # Try to find the file in the videos directory
            videos_dir = self.config.get("videos_dir", "./videos")
            potential_path = os.path.join(videos_dir, args)
            
            if os.path.exists(potential_path):
                file_path = potential_path
            else:
                await message.channel.send(f"Video file not found: {args}")
                return
        else:
            file_path = args
        
        # Get the voice channel for this command channel
        voice_channel_id = await self._get_voice_channel_for_command(message.channel.id)
        
        # Join the voice channel if not already connected
        if not self.current_voice_channel:
            if not await self._join_voice_channel(voice_channel_id):
                await message.channel.send("Failed to join voice channel")
                return
        
        # Stream the video
        transcode = self.config.get("transcode_enabled", False)
        if await self._stream_video(file_path, transcode):
            await message.channel.send(f"Now playing: {os.path.basename(file_path)}")
            
            # Clear the playlist and add this video as the only item
            self.current_playlist = [file_path]
            self.current_playlist_index = 0
        else:
            await message.channel.send("Failed to start streaming")
    
    async def _cmd_stop(self, message, args):
        """Handle the stop command.
        
        Args:
            message: Discord message
            args: Command arguments
        """
        await self._stop_stream()
        await self._leave_voice_channel()
        await message.channel.send("Stopped streaming and left voice channel")
    
    async def _cmd_pause(self, message, args):
        """Handle the pause command.
        
        Args:
            message: Discord message
            args: Command arguments
        """
        if await self._pause_stream():
            await message.channel.send("Paused streaming")
        else:
            await message.channel.send("No active stream to pause")
    
    async def _cmd_resume(self, message, args):
        """Handle the resume command.
        
        Args:
            message: Discord message
            args: Command arguments
        """
        if await self._resume_stream():
            await message.channel.send("Resumed streaming")
        else:
            await message.channel.send("No paused stream to resume")
    
    async def _cmd_list(self, message, args):
        """Handle the list command.
        
        Args:
            message: Discord message
            args: Command arguments
        """
        if self.interactive_embeds:
            # Show interactive video categories
            await self.interactive_embeds.create_category_embed(message.channel.id)
        else:
            # Fallback to basic listing
            videos_dir = self.config.get("videos_dir", "./videos")
            
            if not os.path.exists(videos_dir):
                await message.channel.send(f"Videos directory not found: {videos_dir}")
                return
            
            # Get video files
            video_extensions = ['.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm']
            video_files = []
            
            for root, _, files in os.walk(videos_dir):
                for file in files:
                    if os.path.splitext(file)[1].lower() in video_extensions:
                        rel_path = os.path.relpath(os.path.join(root, file), videos_dir)
                        video_files.append(rel_path)
            
            if not video_files:
                await message.channel.send("No video files found")
                return
            
            # Create a list of files
            video_files.sort()
            video_list = "\n".join(video_files)
            
            # Send the list in chunks to avoid Discord's message limit
            chunk_size = 1900  # Discord's limit is 2000 characters
            for i in range(0, len(video_list), chunk_size):
                chunk = video_list[i:i+chunk_size]
                await message.channel.send(f"```\n{chunk}\n```")
    
    async def _cmd_search(self, message, args):
        """Handle the search command.
        
        Args:
            message: Discord message
            args: Command arguments
        """
        if not args:
            await message.channel.send("Please specify a search term")
            return
        
        if self.interactive_embeds and self.db_manager:
            # Show interactive search results
            await self.interactive_embeds.create_search_embed(message.channel.id, args)
        else:
            # Fallback to basic search
            videos_dir = self.config.get("videos_dir", "./videos")
            
            if not os.path.exists(videos_dir):
                await message.channel.send(f"Videos directory not found: {videos_dir}")
                return
            
            # Get video files that match the search term
            video_extensions = ['.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm']
            video_files = []
            
            for root, _, files in os.walk(videos_dir):
                for file in files:
                    if os.path.splitext(file)[1].lower() in video_extensions and args.lower() in file.lower():
                        rel_path = os.path.relpath(os.path.join(root, file), videos_dir)
                        video_files.append(rel_path)
            
            if not video_files:
                await message.channel.send(f"No video files found matching: {args}")
                return
            
            # Create a list of files
            video_files.sort()
            video_list = "\n".join(video_files)
            
            # Send the list in chunks to avoid Discord's message limit
            chunk_size = 1900  # Discord's limit is 2000 characters
            await message.channel.send(f"Found {len(video_files)} videos matching: {args}")
            for i in range(0, len(video_list), chunk_size):
                chunk = video_list[i:i+chunk_size]
                await message.channel.send(f"```\n{chunk}\n```")
    
    async def _cmd_playlist(self, message, args):
        """Handle the playlist command.
        
        Args:
            message: Discord message
            args: Command arguments
        """
        if not args:
            # If no arguments, show the current playlist
            if not self.current_playlist:
                await message.channel.send("Playlist is empty")
                return
            
            playlist_items = []
            for i, item in enumerate(self.current_playlist, 1):
                marker = "▶️ " if i-1 == self.current_playlist_index else ""
                playlist_items.append(f"{marker}{i}. {os.path.basename(item)}")
            
            playlist_text = "\n".join(playlist_items)
            await message.channel.send(f"Current playlist ({len(self.current_playlist)} items):\n```\n{playlist_text}\n```")
            return
        
        # Parse the playlist items
        items = []
        
        # Check if we have quoted paths
        if '"' in args:
            # Split by quotes
            parts = args.split('"')
            for i in range(1, len(parts), 2):
                if parts[i].strip():
                    items.append(parts[i])
        else:
            # Split by spaces
            items = args.split()
        
        if not items:
            await message.channel.send("Please specify video file paths")
            return
        
        # Verify all files exist
        videos_dir = self.config.get("videos_dir", "./videos")
        valid_items = []
        
        for item in items:
            if os.path.exists(item):
                valid_items.append(item)
            else:
                # Try to find the file in the videos directory
                potential_path = os.path.join(videos_dir, item)
                if os.path.exists(potential_path):
                    valid_items.append(potential_path)
                else:
                    await message.channel.send(f"Video file not found: {item}")
        
        if not valid_items:
            await message.channel.send("No valid video files specified")
            return
        
        # Set the playlist
        self.current_playlist = valid_items
        self.current_playlist_index = 0
        
        # Get the voice channel for this command channel
        voice_channel_id = await self._get_voice_channel_for_command(message.channel.id)
        
        # Join the voice channel if not already connected
        if not self.current_voice_channel:
            if not await self._join_voice_channel(voice_channel_id):
                await message.channel.send("Failed to join voice channel")
                return
        
        # Start playing the playlist
        if await self._play_playlist():
            await message.channel.send(f"Started playlist with {len(valid_items)} items")
        else:
            await message.channel.send("Failed to start playlist")
    
    async def _cmd_next(self, message, args):
        """Handle the next command.
        
        Args:
            message: Discord message
            args: Command arguments
        """
        if not self.current_playlist:
            await message.channel.send("Playlist is empty")
            return
        
        # Move to the next item
        self.current_playlist_index += 1
        
        # Check if we're at the end of the playlist
        if self.current_playlist_index >= len(self.current_playlist):
            self.current_playlist_index = 0
            await message.channel.send("Reached the end of the playlist, restarting from the beginning")
        
        # Play the next item
        if await self._play_playlist():
            current_file = os.path.basename(self.current_playlist[self.current_playlist_index])
            await message.channel.send(f"Playing next item ({self.current_playlist_index + 1}/{len(self.current_playlist)}): {current_file}")
        else:
            await message.channel.send("Failed to play next item")
    
    async def _cmd_prev(self, message, args):
        """Handle the prev command.
        
        Args:
            message: Discord message
            args: Command arguments
        """
        if not self.current_playlist:
            await message.channel.send("Playlist is empty")
            return
        
        # Move to the previous item
        self.current_playlist_index -= 1
        
        # Check if we're at the beginning of the playlist
        if self.current_playlist_index < 0:
            self.current_playlist_index = len(self.current_playlist) - 1
            await message.channel.send("Reached the beginning of the playlist, moving to the end")
        
        # Play the previous item
        if await self._play_playlist():
            current_file = os.path.basename(self.current_playlist[self.current_playlist_index])
            await message.channel.send(f"Playing previous item ({self.current_playlist_index + 1}/{len(self.current_playlist)}): {current_file}")
        else:
            await message.channel.send("Failed to play previous item")
    
    async def _cmd_channel(self, message, args):
        """Handle the channel command.
        
        Args:
            message: Discord message
            args: Command arguments
        """
        if not args:
            # Show the current voice channel mappings
            if not self.db_manager:
                await message.channel.send(f"Using default voice channel: {self.config.get('video_channel_id')}")
                return
            
            # Get all channel mappings
            mappings = self.db_manager.get_all_channel_mappings()
            
            if not mappings:
                await message.channel.send("No channel mappings found")
                return
            
            # Format the mappings
            mapping_lines = []
            for mapping in mappings:
                cmd_channel = mapping['command_channel_name'] or mapping['command_channel_id']
                voice_channel = mapping['voice_channel_name'] or mapping['voice_channel_id']
                guild = mapping['guild_name'] or mapping['guild_id']
                mapping_lines.append(f"Guild: {guild}, Command: {cmd_channel} -> Voice: {voice_channel}")
            
            mapping_text = "\n".join(mapping_lines)
            await message.channel.send(f"Channel mappings:\n```\n{mapping_text}\n```")
            return
        
        # Parse the voice channel ID
        try:
            voice_channel_id = int(args)
        except ValueError:
            await message.channel.send("Please specify a valid voice channel ID")
            return
        
        # Update the configuration
        self.config["video_channel_id"] = str(voice_channel_id)
        
        # Update the mapping in the database
        if self.db_manager:
            # Add the voice channel
            guild_id = self.config.get("guild_id")
            self.db_manager.add_voice_channel(str(voice_channel_id), guild_id, "Voice Channel")
            
            # Map the command channel to the voice channel
            cmd_channel_id = str(message.channel.id)
            self.db_manager.map_channels(cmd_channel_id, str(voice_channel_id))
        
        # Save the configuration
        with open(DEFAULT_CONFIG_PATH, 'w') as f:
            json.dump(self.config, f, indent=4)
        
        await message.channel.send(f"Set voice channel to {voice_channel_id}")
    
    async def _cmd_add_channel(self, message, args):
        """Handle the add_channel command.
        
        Args:
            message: Discord message
            args: Command arguments
        """
        if not self.db_manager:
            await message.channel.send("Database is not initialized")
            return
        
        # Parse command arguments (channel_type, channel_id, name)
        parts = args.split(maxsplit=2)
        
        if len(parts) < 2:
            await message.channel.send("Usage: add_channel <voice|command> <channel_id> [name]")
            return
        
        channel_type = parts[0].lower()
        
        try:
            channel_id = int(parts[1])
        except ValueError:
            await message.channel.send("Please specify a valid channel ID")
            return
        
        name = parts[2] if len(parts) > 2 else f"{channel_type.capitalize()} Channel"
        guild_id = self.config.get("guild_id")
        
        # Add the channel to the database
        if channel_type == "voice":
            self.db_manager.add_voice_channel(str(channel_id), guild_id, name)
            await message.channel.send(f"Added voice channel: {name} ({channel_id})")
        elif channel_type == "command":
            self.db_manager.add_command_channel(str(channel_id), guild_id, name)
            await message.channel.send(f"Added command channel: {name} ({channel_id})")
        else:
            await message.channel.send("Channel type must be 'voice' or 'command'")
    
    async def _cmd_map_channel(self, message, args):
        """Handle the map_channel command.
        
        Args:
            message: Discord message
            args: Command arguments
        """
        if not self.db_manager:
            await message.channel.send("Database is not initialized")
            return
        
        # Parse command arguments (command_channel_id, voice_channel_id)
        parts = args.split()
        
        if len(parts) != 2:
            await message.channel.send("Usage: map_channel <command_channel_id> <voice_channel_id>")
            return
        
        try:
            cmd_channel_id = int(parts[0])
            voice_channel_id = int(parts[1])
        except ValueError:
            await message.channel.send("Please specify valid channel IDs")
            return
        
        # Map the channels
        self.db_manager.map_channels(str(cmd_channel_id), str(voice_channel_id))
        await message.channel.send(f"Mapped command channel {cmd_channel_id} to voice channel {voice_channel_id}")
    
    async def _cmd_scan_videos(self, message, args):
        """Handle the scan command.
        
        Args:
            message: Discord message
            args: Command arguments
        """
        await message.channel.send("Scanning videos directory, this may take a while...")
        await self._scan_videos_directory()
        await message.channel.send("Finished scanning videos directory")
    
    async def _cmd_hw_info(self, message, args):
        """Handle the hwinfo command.
        
        Args:
            message: Discord message
            args: Command arguments
        """
        if not self.hw_accel:
            await message.channel.send("Hardware acceleration is not initialized")
            return
        
        # Get hardware acceleration info
        devices = self.hw_accel.detected_devices
        
        if not devices:
            await message.channel.send("No hardware acceleration devices detected")
            return
        
        # Format the device information
        device_lines = []
        for i, device in enumerate(devices, 1):
            device_lines.append(f"{i}. {device['device_name']} ({device['device_type']})")
            device_lines.append(f"   Encoder: {device['encoder']}")
            
            # Add ffmpeg options
            options = device.get('ffmpeg_options', {})
            if options:
                options_str = ", ".join(f"{k}={v}" for k, v in options.items())
                device_lines.append(f"   Options: {options_str}")
            
            # Add device details
            details = device.get('details', {})
            if details:
                details_str = ", ".join(f"{k}={v}" for k, v in details.items())
                device_lines.append(f"   Details: {details_str}")
        
        # Get the preferred device
        preferred = self.hw_accel.get_preferred_device()
        if preferred:
            device_lines.append(f"\nPreferred device: {preferred['device_name']} ({preferred['device_type']})")
        
        # Add hardware transcoding status
        hw_enabled = self.config.get("hw_accel_enabled", True)
        transcode_enabled = self.config.get("transcode_enabled", False)
        device_lines.append(f"\nHardware acceleration: {'Enabled' if hw_enabled else 'Disabled'}")
        device_lines.append(f"Transcoding: {'Enabled' if transcode_enabled else 'Disabled'}")
        
        # Send the device information
        device_text = "\n".join(device_lines)
        await message.channel.send(f"Hardware acceleration devices:\n```\n{device_text}\n```")
    
    async def _cmd_help(self, message, args):
        """Handle the help command.
        
        Args:
            message: Discord message
            args: Command arguments
        """
        # Create help text
        help_lines = [
            f"StreamBot Commands (prefix: {self.command_prefix}):",
            "",
            "Video Playback:",
            f"  {self.command_prefix}play <file_path> - Play a video",
            f"  {self.command_prefix}stop - Stop playback and leave voice channel",
            f"  {self.command_prefix}pause - Pause playback",
            f"  {self.command_prefix}resume - Resume playback",
            "",
            "Video Management:",
            f"  {self.command_prefix}list - Show video categories and files",
            f"  {self.command_prefix}search <term> - Search for videos",
            f"  {self.command_prefix}scan - Scan videos directory for new files",
            "",
            "Playlist Management:",
            f"  {self.command_prefix}playlist <file1> <file2> ... - Create and play a playlist",
            f"  {self.command_prefix}playlist - Show current playlist",
            f"  {self.command_prefix}next - Play next item in playlist",
            f"  {self.command_prefix}prev - Play previous item in playlist",
            "",
            "Channel Management:",
            f"  {self.command_prefix}channel - Show channel mappings",
            f"  {self.command_prefix}channel <voice_channel_id> - Set voice channel for this command channel",
            f"  {self.command_prefix}add_channel <voice|command> <channel_id> [name] - Add a channel",
            f"  {self.command_prefix}map_channel <command_channel_id> <voice_channel_id> - Map command channel to voice channel",
            "",
            "System:",
            f"  {self.command_prefix}hwinfo - Show hardware acceleration information",
            f"  {self.command_prefix}help - Show this help message"
        ]
        
        help_text = "\n".join(help_lines)
        await message.channel.send(f"```\n{help_text}\n```")


def main():
    """Main entry point."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="StreamBot - Discord selfbot for streaming videos")
    parser.add_argument("--config", "-c", type=str, default=DEFAULT_CONFIG_PATH,
                      help=f"Path to configuration file (default: {DEFAULT_CONFIG_PATH})")
    args = parser.parse_args()
    
    # Create the bot
    bot = StreamBot(args.config)
    
    # Run the bot
    bot.run(bot.config.get("token"))


if __name__ == "__main__":
    main()
