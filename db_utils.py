import sqlite3
import os
import json
import logging
from datetime import datetime
from typing import List, Dict, Optional, Tuple, Any, Union

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self, db_path: str = "streambot.db"):
        """Initialize the database manager.
        
        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = db_path
        self.conn = None
        self.cursor = None
        self._connect()
        self._initialize_db()
    
    def _connect(self):
        """Connect to the SQLite database."""
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row  # This enables column access by name
            self.cursor = self.conn.cursor()
            logger.info(f"Connected to database at {self.db_path}")
        except sqlite3.Error as e:
            logger.error(f"Database connection error: {e}")
            raise
    
    def _initialize_db(self):
        """Initialize the database schema if it doesn't exist."""
        try:
            # Read the schema from a file
            schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")
            if os.path.exists(schema_path):
                with open(schema_path, 'r') as f:
                    schema = f.read()
                self.cursor.executescript(schema)
                self.conn.commit()
                logger.info("Database schema initialized")
            else:
                logger.warning("Schema file not found, database may not be properly initialized")
        except sqlite3.Error as e:
            logger.error(f"Database initialization error: {e}")
            raise
    
    def close(self):
        """Close the database connection."""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    # Guild and Channel Management
    
    def add_guild(self, guild_id: str, name: str) -> bool:
        """Add a new guild to the database.
        
        Args:
            guild_id: Discord guild ID
            name: Guild name
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.cursor.execute(
                "INSERT OR IGNORE INTO guilds (guild_id, name) VALUES (?, ?)",
                (guild_id, name)
            )
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            logger.error(f"Error adding guild: {e}")
            return False
    
    def add_command_channel(self, channel_id: str, guild_id: str, name: str) -> bool:
        """Add a new command channel to the database.
        
        Args:
            channel_id: Discord channel ID
            guild_id: Discord guild ID
            name: Channel name
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.cursor.execute(
                "INSERT OR IGNORE INTO command_channels (channel_id, guild_id, name) VALUES (?, ?, ?)",
                (channel_id, guild_id, name)
            )
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            logger.error(f"Error adding command channel: {e}")
            return False
    
    def add_voice_channel(self, channel_id: str, guild_id: str, name: str) -> bool:
        """Add a new voice channel to the database.
        
        Args:
            channel_id: Discord channel ID
            guild_id: Discord guild ID
            name: Channel name
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.cursor.execute(
                "INSERT OR IGNORE INTO voice_channels (channel_id, guild_id, name) VALUES (?, ?, ?)",
                (channel_id, guild_id, name)
            )
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            logger.error(f"Error adding voice channel: {e}")
            return False
    
    def map_channels(self, command_channel_id: str, voice_channel_id: str) -> bool:
        """Map a command channel to a voice channel.
        
        Args:
            command_channel_id: Discord command channel ID
            voice_channel_id: Discord voice channel ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.cursor.execute(
                """
                INSERT OR IGNORE INTO channel_mappings 
                (command_channel_id, voice_channel_id) 
                VALUES (?, ?)
                """,
                (command_channel_id, voice_channel_id)
            )
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            logger.error(f"Error mapping channels: {e}")
            return False
    
    def get_voice_channel_by_command_channel(self, command_channel_id: str) -> Optional[str]:
        """Get the voice channel associated with a command channel.
        
        Args:
            command_channel_id: Discord command channel ID
            
        Returns:
            Voice channel ID if found, None otherwise
        """
        try:
            self.cursor.execute(
                """
                SELECT voice_channel_id FROM channel_mappings 
                WHERE command_channel_id = ?
                """,
                (command_channel_id,)
            )
            result = self.cursor.fetchone()
            return result['voice_channel_id'] if result else None
        except sqlite3.Error as e:
            logger.error(f"Error getting voice channel: {e}")
            return None
    
    def get_all_channel_mappings(self) -> List[Dict[str, str]]:
        """Get all command channel to voice channel mappings.
        
        Returns:
            List of dictionaries with command_channel_id and voice_channel_id
        """
        try:
            self.cursor.execute(
                """
                SELECT cm.command_channel_id, cm.voice_channel_id, 
                       cc.name as command_channel_name, vc.name as voice_channel_name,
                       g.name as guild_name, g.guild_id
                FROM channel_mappings cm
                JOIN command_channels cc ON cm.command_channel_id = cc.channel_id
                JOIN voice_channels vc ON cm.voice_channel_id = vc.channel_id
                JOIN guilds g ON cc.guild_id = g.guild_id
                """
            )
            return [dict(row) for row in self.cursor.fetchall()]
        except sqlite3.Error as e:
            logger.error(f"Error getting channel mappings: {e}")
            return []
    
    # Video and Category Management
    
    def add_category(self, name: str, folder_path: str) -> Optional[int]:
        """Add a new video category.
        
        Args:
            name: Category name
            folder_path: Path to the category folder
            
        Returns:
            Category ID if successful, None otherwise
        """
        try:
            self.cursor.execute(
                "INSERT OR IGNORE INTO categories (name, folder_path) VALUES (?, ?)",
                (name, folder_path)
            )
            self.conn.commit()
            
            # Get the ID of the inserted category
            self.cursor.execute(
                "SELECT id FROM categories WHERE name = ?",
                (name,)
            )
            result = self.cursor.fetchone()
            return result['id'] if result else None
        except sqlite3.Error as e:
            logger.error(f"Error adding category: {e}")
            return None
    
    def get_all_categories(self) -> List[Dict[str, Any]]:
        """Get all video categories.
        
        Returns:
            List of category dictionaries
        """
        try:
            self.cursor.execute("SELECT * FROM categories ORDER BY name")
            return [dict(row) for row in self.cursor.fetchall()]
        except sqlite3.Error as e:
            logger.error(f"Error getting categories: {e}")
            return []
    
    def add_video(self, 
                 filename: str, 
                 file_path: str, 
                 title: Optional[str] = None, 
                 description: Optional[str] = None,
                 category_id: Optional[int] = None,
                 series_name: Optional[str] = None,
                 season: Optional[int] = None,
                 episode: Optional[int] = None,
                 duration: Optional[int] = None,
                 width: Optional[int] = None,
                 height: Optional[int] = None,
                 codec: Optional[str] = None) -> Optional[int]:
        """Add a video to the database.
        
        Args:
            filename: Video filename
            file_path: Full path to the video file
            title: Video title (defaults to filename if None)
            description: Video description
            category_id: Category ID
            series_name: Series name for TV shows
            season: Season number for TV shows
            episode: Episode number for TV shows
            duration: Video duration in seconds
            width: Video width in pixels
            height: Video height in pixels
            codec: Video codec
            
        Returns:
            Video ID if successful, None otherwise
        """
        try:
            # Default title to filename if not provided
            if title is None:
                title = os.path.splitext(filename)[0]
                
            self.cursor.execute(
                """
                INSERT OR IGNORE INTO videos 
                (filename, title, description, category_id, series_name, 
                 season, episode, duration, width, height, codec, file_path) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (filename, title, description, category_id, series_name, 
                 season, episode, duration, width, height, codec, file_path)
            )
            self.conn.commit()
            
            # Get the ID of the inserted video
            self.cursor.execute(
                "SELECT id FROM videos WHERE file_path = ?",
                (file_path,)
            )
            result = self.cursor.fetchone()
            return result['id'] if result else None
        except sqlite3.Error as e:
            logger.error(f"Error adding video: {e}")
            return None
    
    def update_video_metadata(self, video_id: int, metadata: Dict[str, Any]) -> bool:
        """Update video metadata.
        
        Args:
            video_id: Video ID
            metadata: Dictionary of metadata fields to update
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Build the SET part of the SQL query dynamically
            set_clause = ", ".join([f"{key} = ?" for key in metadata.keys()])
            values = list(metadata.values())
            values.append(video_id)  # For the WHERE clause
            
            self.cursor.execute(
                f"UPDATE videos SET {set_clause} WHERE id = ?",
                values
            )
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            logger.error(f"Error updating video metadata: {e}")
            return False
    
    def update_video_last_played(self, video_id: int) -> bool:
        """Update the last played timestamp for a video.
        
        Args:
            video_id: Video ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.cursor.execute(
                "UPDATE videos SET last_played = CURRENT_TIMESTAMP WHERE id = ?",
                (video_id,)
            )
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            logger.error(f"Error updating video last played: {e}")
            return False
    
    def get_videos_by_category(self, category_id: int) -> List[Dict[str, Any]]:
        """Get all videos in a category.
        
        Args:
            category_id: Category ID
            
        Returns:
            List of video dictionaries
        """
        try:
            self.cursor.execute(
                """
                SELECT v.*, c.name as category_name 
                FROM videos v
                LEFT JOIN categories c ON v.category_id = c.id
                WHERE v.category_id = ?
                ORDER BY v.series_name, v.season, v.episode, v.title
                """,
                (category_id,)
            )
            return [dict(row) for row in self.cursor.fetchall()]
        except sqlite3.Error as e:
            logger.error(f"Error getting videos by category: {e}")
            return []
    
    def get_all_videos(self) -> List[Dict[str, Any]]:
        """Get all videos.
        
        Returns:
            List of video dictionaries
        """
        try:
            self.cursor.execute(
                """
                SELECT v.*, c.name as category_name 
                FROM videos v
                LEFT JOIN categories c ON v.category_id = c.id
                ORDER BY v.series_name, v.season, v.episode, v.title
                """
            )
            return [dict(row) for row in self.cursor.fetchall()]
        except sqlite3.Error as e:
            logger.error(f"Error getting all videos: {e}")
            return []
    
    def search_videos(self, search_term: str) -> List[Dict[str, Any]]:
        """Search for videos by title, series name, or description.
        
        Args:
            search_term: Search term
            
        Returns:
            List of matching video dictionaries
        """
        try:
            # Create a search pattern for SQLite's LIKE operator
            pattern = f"%{search_term}%"
            
            self.cursor.execute(
                """
                SELECT v.*, c.name as category_name 
                FROM videos v
                LEFT JOIN categories c ON v.category_id = c.id
                WHERE v.title LIKE ? 
                   OR v.series_name LIKE ? 
                   OR v.description LIKE ?
                ORDER BY v.series_name, v.season, v.episode, v.title
                """,
                (pattern, pattern, pattern)
            )
            return [dict(row) for row in self.cursor.fetchall()]
        except sqlite3.Error as e:
            logger.error(f"Error searching videos: {e}")
            return []
    
    def get_episodes_by_series(self, series_name: str) -> List[Dict[str, Any]]:
        """Get all episodes in a TV series.
        
        Args:
            series_name: Series name
            
        Returns:
            List of episode dictionaries
        """
        try:
            self.cursor.execute(
                """
                SELECT v.*, c.name as category_name 
                FROM videos v
                LEFT JOIN categories c ON v.category_id = c.id
                WHERE v.series_name = ?
                ORDER BY v.season, v.episode
                """,
                (series_name,)
            )
            return [dict(row) for row in self.cursor.fetchall()]
        except sqlite3.Error as e:
            logger.error(f"Error getting episodes by series: {e}")
            return []
    
    # Playlist Management
    
    def create_playlist(self, name: str, created_by: str) -> Optional[int]:
        """Create a new playlist.
        
        Args:
            name: Playlist name
            created_by: Discord user ID who created the playlist
            
        Returns:
            Playlist ID if successful, None otherwise
        """
        try:
            self.cursor.execute(
                "INSERT INTO playlists (name, created_by) VALUES (?, ?)",
                (name, created_by)
            )
            self.conn.commit()
            
            # Get the ID of the inserted playlist
            self.cursor.execute(
                "SELECT id FROM playlists WHERE name = ? AND created_by = ? ORDER BY date_created DESC LIMIT 1",
                (name, created_by)
            )
            result = self.cursor.fetchone()
            return result['id'] if result else None
        except sqlite3.Error as e:
            logger.error(f"Error creating playlist: {e}")
            return None
    
    def add_video_to_playlist(self, playlist_id: int, video_id: int, position: int) -> bool:
        """Add a video to a playlist.
        
        Args:
            playlist_id: Playlist ID
            video_id: Video ID
            position: Position in the playlist
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.cursor.execute(
                """
                INSERT OR REPLACE INTO playlist_videos 
                (playlist_id, video_id, position) 
                VALUES (?, ?, ?)
                """,
                (playlist_id, video_id, position)
            )
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            logger.error(f"Error adding video to playlist: {e}")
            return False
    
    def get_playlist_videos(self, playlist_id: int) -> List[Dict[str, Any]]:
        """Get all videos in a playlist.
        
        Args:
            playlist_id: Playlist ID
            
        Returns:
            List of video dictionaries
        """
        try:
            self.cursor.execute(
                """
                SELECT v.*, pv.position 
                FROM playlist_videos pv
                JOIN videos v ON pv.video_id = v.id
                WHERE pv.playlist_id = ?
                ORDER BY pv.position
                """,
                (playlist_id,)
            )
            return [dict(row) for row in self.cursor.fetchall()]
        except sqlite3.Error as e:
            logger.error(f"Error getting playlist videos: {e}")
            return []
    
    # Hardware Acceleration Settings
    
    def add_hw_accel_device(self, 
                           device_name: str, 
                           device_type: str, 
                           encoder: str,
                           transcode_enabled: bool = False,
                           preferred: bool = False,
                           ffmpeg_options: Optional[Dict[str, Any]] = None) -> Optional[int]:
        """Add a hardware acceleration device.
        
        Args:
            device_name: Device name
            device_type: Device type ('nvidia', 'amd', 'intel', etc.)
            encoder: Encoder name ('h264_nvenc', 'h264_qsv', 'h264_amf', etc.)
            transcode_enabled: Whether transcoding is enabled
            preferred: Whether this is the preferred device
            ffmpeg_options: Additional ffmpeg options as dictionary
            
        Returns:
            Device ID if successful, None otherwise
        """
        try:
            # If this is set as preferred, unset any other preferred devices
            if preferred:
                self.cursor.execute(
                    "UPDATE hw_accel_settings SET preferred = 0"
                )
            
            # Convert ffmpeg_options dictionary to JSON string
            options_json = json.dumps(ffmpeg_options) if ffmpeg_options else None
            
            self.cursor.execute(
                """
                INSERT INTO hw_accel_settings 
                (device_name, device_type, encoder, transcode_enabled, preferred, ffmpeg_options) 
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (device_name, device_type, encoder, int(transcode_enabled), int(preferred), options_json)
            )
            self.conn.commit()
            
            # Get the ID of the inserted device
            self.cursor.execute(
                "SELECT id FROM hw_accel_settings WHERE device_name = ? ORDER BY date_added DESC LIMIT 1",
                (device_name,)
            )
            result = self.cursor.fetchone()
            return result['id'] if result else None
        except sqlite3.Error as e:
            logger.error(f"Error adding hardware acceleration device: {e}")
            return None
    
    def get_preferred_hw_accel_device(self) -> Optional[Dict[str, Any]]:
        """Get the preferred hardware acceleration device.
        
        Returns:
            Device dictionary if found, None otherwise
        """
        try:
            self.cursor.execute(
                "SELECT * FROM hw_accel_settings WHERE preferred = 1 LIMIT 1"
            )
            result = self.cursor.fetchone()
            
            if result:
                result_dict = dict(result)
                # Parse the ffmpeg_options JSON string back to a dictionary
                if result_dict['ffmpeg_options']:
                    result_dict['ffmpeg_options'] = json.loads(result_dict['ffmpeg_options'])
                return result_dict
            return None
        except sqlite3.Error as e:
            logger.error(f"Error getting preferred hardware acceleration device: {e}")
            return None
    
    def get_all_hw_accel_devices(self) -> List[Dict[str, Any]]:
        """Get all hardware acceleration devices.
        
        Returns:
            List of device dictionaries
        """
        try:
            self.cursor.execute("SELECT * FROM hw_accel_settings")
            results = [dict(row) for row in self.cursor.fetchall()]
            
            # Parse the ffmpeg_options JSON string back to a dictionary for each device
            for result in results:
                if result['ffmpeg_options']:
                    result['ffmpeg_options'] = json.loads(result['ffmpeg_options'])
            
            return results
        except sqlite3.Error as e:
            logger.error(f"Error getting hardware acceleration devices: {e}")
            return []


# Initialize the database
def init_db(db_path: str = "streambot.db"):
    """Initialize the database.
    
    Args:
        db_path: Path to the SQLite database file
        
    Returns:
        DatabaseManager instance
    """
    return DatabaseManager(db_path)
