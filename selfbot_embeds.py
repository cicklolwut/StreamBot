import discord
import asyncio
import logging
import os
import json
from typing import List, Dict, Optional, Tuple, Any, Union, Callable
from datetime import datetime

logger = logging.getLogger(__name__)

class EmbedBuilder:
    """Class to build and manage Discord selfbot embeds."""
    
    def __init__(self, client):
        """Initialize the embed builder.
        
        Args:
            client: Discord client instance
        """
        self.client = client
        self.default_color = 0x3498db  # Blueish color
    
    def create_basic_embed(self, 
                          title: str, 
                          description: Optional[str] = None, 
                          color: Optional[int] = None) -> dict:
        """Create a basic embed dictionary.
        
        Args:
            title: Embed title
            description: Embed description
            color: Embed color (hex integer)
            
        Returns:
            Embed dictionary
        """
        embed = {
            "title": title,
            "type": "rich",
            "color": color or self.default_color
        }
        
        if description:
            embed["description"] = description
        
        # Add timestamp
        embed["timestamp"] = datetime.utcnow().isoformat()
        
        return embed
    
    def add_field(self, 
                 embed: dict, 
                 name: str, 
                 value: str, 
                 inline: bool = False) -> dict:
        """Add a field to an embed.
        
        Args:
            embed: Embed dictionary
            name: Field name
            value: Field value
            inline: Whether the field should be inline
            
        Returns:
            Updated embed dictionary
        """
        if "fields" not in embed:
            embed["fields"] = []
        
        embed["fields"].append({
            "name": name,
            "value": value,
            "inline": inline
        })
        
        return embed
    
    def add_footer(self, 
                  embed: dict, 
                  text: str, 
                  icon_url: Optional[str] = None) -> dict:
        """Add a footer to an embed.
        
        Args:
            embed: Embed dictionary
            text: Footer text
            icon_url: URL to footer icon
            
        Returns:
            Updated embed dictionary
        """
        embed["footer"] = {
            "text": text
        }
        
        if icon_url:
            embed["footer"]["icon_url"] = icon_url
        
        return embed
    
    def add_thumbnail(self, embed: dict, url: str) -> dict:
        """Add a thumbnail to an embed.
        
        Args:
            embed: Embed dictionary
            url: URL to thumbnail image
            
        Returns:
            Updated embed dictionary
        """
        embed["thumbnail"] = {
            "url": url
        }
        
        return embed
    
    def add_image(self, embed: dict, url: str) -> dict:
        """Add a main image to an embed.
        
        Args:
            embed: Embed dictionary
            url: URL to image
            
        Returns:
            Updated embed dictionary
        """
        embed["image"] = {
            "url": url
        }
        
        return embed
    
    def add_author(self, 
                  embed: dict, 
                  name: str, 
                  url: Optional[str] = None, 
                  icon_url: Optional[str] = None) -> dict:
        """Add an author to an embed.
        
        Args:
            embed: Embed dictionary
            name: Author name
            url: URL to author
            icon_url: URL to author icon
            
        Returns:
            Updated embed dictionary
        """
        embed["author"] = {
            "name": name
        }
        
        if url:
            embed["author"]["url"] = url
        
        if icon_url:
            embed["author"]["icon_url"] = icon_url
        
        return embed
    
    async def send_embed(self, 
                        channel_id: int, 
                        embed: dict, 
                        content: Optional[str] = None) -> discord.Message:
        """Send an embed to a channel.
        
        Args:
            channel_id: Discord channel ID
            embed: Embed dictionary
            content: Optional message content
            
        Returns:
            Sent message object
        """
        try:
            channel = self.client.get_channel(channel_id)
            if not channel:
                channel = await self.client.fetch_channel(channel_id)
            
            # For user accounts, we need to send the embed as a JSON string
            embed_json = json.dumps(embed)
            
            message = await channel.send(
                content=content,
                embed=discord.Embed.from_dict(json.loads(embed_json))
            )
            
            return message
        except Exception as e:
            logger.error(f"Error sending embed: {e}")
            raise
    
    async def edit_embed(self, 
                        message: discord.Message, 
                        embed: dict, 
                        content: Optional[str] = None) -> discord.Message:
        """Edit an embed message.
        
        Args:
            message: Discord message to edit
            embed: New embed dictionary
            content: New message content
            
        Returns:
            Edited message object
        """
        try:
            # Update the message with the new embed
            embed_json = json.dumps(embed)
            
            edited_message = await message.edit(
                content=content or message.content,
                embed=discord.Embed.from_dict(json.loads(embed_json))
            )
            
            return edited_message
        except Exception as e:
            logger.error(f"Error editing embed: {e}")
            raise


class InteractiveEmbed:
    """Class to create interactive embeds with buttons and pagination."""
    
    def __init__(self, client, embed_builder: EmbedBuilder, db_manager=None):
        """Initialize the interactive embed.
        
        Args:
            client: Discord client instance
            embed_builder: Embed builder instance
            db_manager: Database manager instance
        """
        self.client = client
        self.embed_builder = embed_builder
        self.db_manager = db_manager
        
        # Store active interactive embeds
        self.active_embeds = {}
        
        # Register message handlers with the client
        self._register_handlers()
    
    def _register_handlers(self):
        """Register message handlers with the client."""
        # This is called in __init__ to register the reaction_add event handler
        @self.client.event
        async def on_raw_reaction_add(payload):
            await self._handle_reaction(payload)
    
    async def _handle_reaction(self, payload):
        """Handle reaction add events for interactive embeds.
        
        Args:
            payload: Reaction payload
        """
        # Skip reactions from the bot itself
        if payload.user_id == self.client.user.id:
            return
        
        # Check if this is an active interactive embed
        if payload.message_id in self.active_embeds:
            # Get the handler for this embed
            handler = self.active_embeds[payload.message_id]
            
            # Call the handler with the reaction info
            await handler(payload)
    
    async def create_paginated_embed(self, 
                                    channel_id: int, 
                                    title: str, 
                                    items: List[Dict[str, Any]], 
                                    items_per_page: int = 10,
                                    description: Optional[str] = None,
                                    thumbnail_url: Optional[str] = None,
                                    footer_text: Optional[str] = None) -> discord.Message:
        """Create a paginated embed.
        
        Args:
            channel_id: Discord channel ID
            title: Embed title
            items: List of items to paginate
            items_per_page: Number of items per page
            description: Embed description
            thumbnail_url: URL to thumbnail image
            footer_text: Footer text
            
        Returns:
            Sent message object
        """
        # Store pagination state
        state = {
            "current_page": 0,
            "total_pages": max(1, (len(items) + items_per_page - 1) // items_per_page),
            "items": items,
            "items_per_page": items_per_page,
            "title": title,
            "description": description,
            "thumbnail_url": thumbnail_url,
            "footer_text": footer_text
        }
        
        # Create the initial embed
        embed = self._create_page_embed(state)
        
        # Send the embed
        message = await self.embed_builder.send_embed(channel_id, embed)
        
        # Add reactions for navigation if there's more than one page
        if state["total_pages"] > 1:
            await message.add_reaction("⬅️")  # Left arrow
            await message.add_reaction("➡️")  # Right arrow
        
        # Add close reaction
        await message.add_reaction("❌")  # X to close
        
        # Store the pagination state and handler
        self.active_embeds[message.id] = lambda payload: self._handle_pagination(payload, message, state)
        
        return message
    
    def _create_page_embed(self, state: Dict[str, Any]) -> dict:
        """Create an embed for a specific page of items.
        
        Args:
            state: Pagination state
            
        Returns:
            Embed dictionary
        """
        # Extract pagination state
        current_page = state["current_page"]
        items = state["items"]
        items_per_page = state["items_per_page"]
        title = state["title"]
        description = state["description"]
        thumbnail_url = state["thumbnail_url"]
        footer_text = state["footer_text"] or f"Page {current_page+1} of {state['total_pages']}"
        
        # Calculate slice indices for the current page
        start_idx = current_page * items_per_page
        end_idx = min(start_idx + items_per_page, len(items))
        
        # Create the base embed
        embed = self.embed_builder.create_basic_embed(title, description)
        
        # Add each item as a field
        for i, item in enumerate(items[start_idx:end_idx], 1):
            # Format based on item type
            name = item.get("name", f"Item {start_idx+i}")
            value = item.get("value", str(item))
            inline = item.get("inline", False)
            
            self.embed_builder.add_field(embed, name, value, inline)
        
        # Add thumbnail if provided
        if thumbnail_url:
            self.embed_builder.add_thumbnail(embed, thumbnail_url)
        
        # Add footer with page info
        self.embed_builder.add_footer(embed, footer_text)
        
        return embed
    
    async def _handle_pagination(self, payload, message, state):
        """Handle pagination reactions.
        
        Args:
            payload: Reaction payload
            message: Paginated embed message
            state: Pagination state
        """
        # Get the emoji
        emoji = str(payload.emoji)
        
        # Handle navigation
        if emoji == "⬅️" and state["current_page"] > 0:
            # Go to previous page
            state["current_page"] -= 1
            embed = self._create_page_embed(state)
            await self.embed_builder.edit_embed(message, embed)
        
        elif emoji == "➡️" and state["current_page"] < state["total_pages"] - 1:
            # Go to next page
            state["current_page"] += 1
            embed = self._create_page_embed(state)
            await self.embed_builder.edit_embed(message, embed)
        
        elif emoji == "❌":
            # Close the embed
            await message.delete()
            if message.id in self.active_embeds:
                del self.active_embeds[message.id]
        
        # Remove the user's reaction
        try:
            user = await self.client.fetch_user(payload.user_id)
            await message.remove_reaction(payload.emoji, user)
        except:
            pass  # Ignore errors removing reactions
    
    async def create_category_embed(self, channel_id: int) -> discord.Message:
        """Create an embed showing video categories.
        
        Args:
            channel_id: Discord channel ID
            
        Returns:
            Sent message object
        """
        if not self.db_manager:
            raise ValueError("Database manager is required for category embeds")
        
        # Get categories from the database
        categories = self.db_manager.get_all_categories()
        
        # Format categories for the embed
        category_items = []
        for category in categories:
            # Get the number of videos in this category
            videos = self.db_manager.get_videos_by_category(category["id"])
            
            category_items.append({
                "name": f"📁 {category['name']}",
                "value": f"**{len(videos)}** videos\nSelect with 📁",
                "inline": True,
                "id": category["id"]
            })
        
        # Create the paginated embed
        message = await self.create_paginated_embed(
            channel_id=channel_id,
            title="Video Categories",
            items=category_items,
            items_per_page=8,
            description="Select a category to view videos",
            footer_text="React with 📁 to select a category"
        )
        
        # Add select reaction
        await message.add_reaction("📁")  # Folder icon to select
        
        # Override the handler for this specific embed
        self.active_embeds[message.id] = lambda payload: self._handle_category_selection(
            payload, message, category_items
        )
        
        return message
    
    async def _handle_category_selection(self, payload, message, categories):
        """Handle category selection reactions.
        
        Args:
            payload: Reaction payload
            message: Category embed message
            categories: List of category items
        """
        # Get the emoji
        emoji = str(payload.emoji)
        
        # Handle navigation and close normally
        if emoji in ["⬅️", "➡️", "❌"]:
            # Get pagination state
            state = {
                "current_page": 0,
                "total_pages": max(1, (len(categories) + 8 - 1) // 8),
                "items": categories,
                "items_per_page": 8,
                "title": "Video Categories",
                "description": "Select a category to view videos",
                "thumbnail_url": None,
                "footer_text": "React with 📁 to select a category"
            }
            
            await self._handle_pagination(payload, message, state)
            return
        
        # Handle category selection
        if emoji == "📁":
            # Get selected category index based on current page
            try:
                # Get the current page from the footer
                embed = message.embeds[0].to_dict()
                footer_text = embed.get("footer", {}).get("text", "")
                current_page = 0
                if "Page" in footer_text:
                    current_page = int(footer_text.split()[1]) - 1
                
                # Prompt for index selection
                prompt_embed = self.embed_builder.create_basic_embed(
                    "Select Category Number",
                    "Reply with the number of the category to view (e.g. '1', '2', etc.)"
                )
                
                # Add the categories as fields for reference
                for i, category in enumerate(categories[current_page*8:current_page*8+8], 1):
                    self.embed_builder.add_field(
                        prompt_embed,
                        f"{i}. {category['name'].lstrip('📁 ')}",
                        "",
                        inline=True
                    )
                
                prompt_message = await self.embed_builder.send_embed(message.channel.id, prompt_embed)
                
                # Wait for a response
                def check(m):
                    return (m.author.id == payload.user_id and 
                            m.channel.id == message.channel.id and 
                            m.content.isdigit() and 
                            1 <= int(m.content) <= min(8, len(categories) - current_page*8))
                
                try:
                    response = await self.client.wait_for('message', check=check, timeout=30.0)
                    
                    # Get the selected category
                    selection = int(response.content) - 1
                    category_idx = current_page * 8 + selection
                    selected_category = categories[category_idx]
                    
                    # Delete the prompt message and response
                    await prompt_message.delete()
                    await response.delete()
                    
                    # Show videos in the selected category
                    await self.create_video_list_embed(
                        channel_id=message.channel.id,
                        category_id=selected_category["id"],
                        category_name=selected_category["name"].lstrip('📁 ')
                    )
                    
                except asyncio.TimeoutError:
                    # Delete the prompt message if the user didn't respond
                    await prompt_message.delete()
                
            except Exception as e:
                logger.error(f"Error handling category selection: {e}")
        
        # Remove the user's reaction
        try:
            user = await self.client.fetch_user(payload.user_id)
            await message.remove_reaction(payload.emoji, user)
        except:
            pass  # Ignore errors removing reactions
    
    async def create_video_list_embed(self, 
                                     channel_id: int, 
                                     category_id: Optional[int] = None,
                                     category_name: Optional[str] = None) -> discord.Message:
        """Create an embed showing videos in a category.
        
        Args:
            channel_id: Discord channel ID
            category_id: Category ID or None for all videos
            category_name: Category name for display
            
        Returns:
            Sent message object
        """
        if not self.db_manager:
            raise ValueError("Database manager is required for video list embeds")
        
        # Get videos from the database
        if category_id is not None:
            videos = self.db_manager.get_videos_by_category(category_id)
            title = f"Videos in {category_name}"
        else:
            videos = self.db_manager.get_all_videos()
            title = "All Videos"
        
        # Group videos by series if applicable
        series_dict = {}
        individual_videos = []
        
        for video in videos:
            if video["series_name"]:
                if video["series_name"] not in series_dict:
                    series_dict[video["series_name"]] = []
                series_dict[video["series_name"]].append(video)
            else:
                individual_videos.append(video)
        
        # Format videos for the embed
        video_items = []
        
        # Add series first
        for series_name, series_videos in series_dict.items():
            video_items.append({
                "name": f"📺 {series_name}",
                "value": f"**{len(series_videos)}** episodes\nReact with 📺 to expand",
                "inline": True,
                "type": "series",
                "series_name": series_name,
                "videos": series_videos
            })
        
        # Add individual videos
        for video in individual_videos:
            duration_str = ""
            if video["duration"]:
                minutes = video["duration"] // 60
                seconds = video["duration"] % 60
                duration_str = f" ({minutes}:{seconds:02d})"
            
            video_items.append({
                "name": f"🎬 {video['title']}",
                "value": f"Type: {video.get('codec', 'Unknown')}{duration_str}\nReact with ▶️ to play",
                "inline": True,
                "type": "video",
                "video_id": video["id"],
                "file_path": video["file_path"]
            })
        
        # Create the paginated embed
        message = await self.create_paginated_embed(
            channel_id=channel_id,
            title=title,
            items=video_items,
            items_per_page=8,
            description="Select a video or series to play",
            footer_text="React with ▶️ to play a video, 📺 to expand a series, or 🔙 to go back"
        )
        
        # Add navigation reactions
        await message.add_reaction("▶️")  # Play button
        if any(item["type"] == "series" for item in video_items):
            await message.add_reaction("📺")  # TV icon for series
        await message.add_reaction("🔙")  # Back button
        
        # Override the handler for this specific embed
        self.active_embeds[message.id] = lambda payload: self._handle_video_selection(
            payload, message, video_items, category_id, category_name
        )
        
        return message
    
    async def _handle_video_selection(self, payload, message, video_items, category_id, category_name):
        """Handle video selection reactions.
        
        Args:
            payload: Reaction payload
            message: Video list embed message
            video_items: List of video items
            category_id: Category ID
            category_name: Category name
        """
        # Get the emoji
        emoji = str(payload.emoji)
        
        # Handle navigation and close normally
        if emoji in ["⬅️", "➡️", "❌"]:
            # Get pagination state
            state = {
                "current_page": 0,
                "total_pages": max(1, (len(video_items) + 8 - 1) // 8),
                "items": video_items,
                "items_per_page": 8,
                "title": f"Videos in {category_name}" if category_name else "All Videos",
                "description": "Select a video or series to play",
                "thumbnail_url": None,
                "footer_text": "React with ▶️ to play a video, 📺 to expand a series, or 🔙 to go back"
            }
            
            await self._handle_pagination(payload, message, state)
            return
        
        # Handle back button
        if emoji == "🔙":
            # Go back to category list
            await self.create_category_embed(message.channel.id)
            await message.delete()
            if message.id in self.active_embeds:
                del self.active_embeds[message.id]
            return
        
        # Handle video play or series expansion
        if emoji in ["▶️", "📺"]:
            # Prompt for index selection
            try:
                # Get the current page from the footer
                embed = message.embeds[0].to_dict()
                footer_text = embed.get("footer", {}).get("text", "")
                current_page = 0
                if "Page" in footer_text:
                    current_page = int(footer_text.split()[1]) - 1
                
                # Filter items based on reaction type
                filtered_items = []
                if emoji == "▶️":
                    filtered_items = [item for item in video_items[current_page*8:current_page*8+8] 
                                     if item["type"] == "video"]
                elif emoji == "📺":
                    filtered_items = [item for item in video_items[current_page*8:current_page*8+8] 
                                     if item["type"] == "series"]
                
                if not filtered_items:
                    return
                
                # Prompt for selection
                prompt_title = "Select Video to Play" if emoji == "▶️" else "Select Series to Expand"
                prompt_embed = self.embed_builder.create_basic_embed(
                    prompt_title,
                    f"Reply with the number of the {'video' if emoji == '▶️' else 'series'} (e.g. '1', '2', etc.)"
                )
                
                # Add the items as fields for reference
                for i, item in enumerate(filtered_items, 1):
                    name = item["name"].lstrip("🎬 ").lstrip("📺 ")
                    self.embed_builder.add_field(
                        prompt_embed,
                        f"{i}. {name}",
                        "",
                        inline=True
                    )
                
                prompt_message = await self.embed_builder.send_embed(message.channel.id, prompt_embed)
                
                # Wait for a response
                def check(m):
                    return (m.author.id == payload.user_id and 
                            m.channel.id == message.channel.id and 
                            m.content.isdigit() and 
                            1 <= int(m.content) <= len(filtered_items))
                
                try:
                    response = await self.client.wait_for('message', check=check, timeout=30.0)
                    
                    # Get the selected item
                    selection = int(response.content) - 1
                    selected_item = filtered_items[selection]
                    
                    # Delete the prompt message and response
                    await prompt_message.delete()
                    await response.delete()
                    
                    if emoji == "▶️" and selected_item["type"] == "video":
                        # Play the selected video
                        play_command = f"{self.client.command_prefix}play {selected_item['file_path']}"
                        # Simulate the user sending the play command
                        fake_message = discord.Object(id=0)
                        fake_message.content = play_command
                        fake_message.author = await self.client.fetch_user(payload.user_id)
                        fake_message.channel = message.channel
                        
                        # Update last played in the database
                        if self.db_manager:
                            self.db_manager.update_video_last_played(selected_item["video_id"])
                        
                        # Send the play command
                        await message.channel.send(play_command)
                        
                    elif emoji == "📺" and selected_item["type"] == "series":
                        # Show episodes in the selected series
                        await self.create_series_episodes_embed(
                            channel_id=message.channel.id,
                            series_name=selected_item["series_name"],
                            episodes=selected_item["videos"],
                            category_id=category_id,
                            category_name=category_name
                        )
                        
                        # Delete the video list message
                        await message.delete()
                        if message.id in self.active_embeds:
                            del self.active_embeds[message.id]
                    
                except asyncio.TimeoutError:
                    # Delete the prompt message if the user didn't respond
                    await prompt_message.delete()
                
            except Exception as e:
                logger.error(f"Error handling video selection: {e}")
        
        # Remove the user's reaction
        try:
            user = await self.client.fetch_user(payload.user_id)
            await message.remove_reaction(payload.emoji, user)
        except:
            pass  # Ignore errors removing reactions
    
    async def create_series_episodes_embed(self, 
                                         channel_id: int, 
                                         series_name: str,
                                         episodes: List[Dict[str, Any]],
                                         category_id: Optional[int] = None,
                                         category_name: Optional[str] = None) -> discord.Message:
        """Create an embed showing episodes in a series.
        
        Args:
            channel_id: Discord channel ID
            series_name: Series name
            episodes: List of episode dictionaries
            category_id: Original category ID
            category_name: Original category name
            
        Returns:
            Sent message object
        """
        # Sort episodes by season and episode number
        sorted_episodes = sorted(episodes, key=lambda x: (x.get("season", 0), x.get("episode", 0)))
        
        # Group episodes by season
        seasons = {}
        for episode in sorted_episodes:
            season_num = episode.get("season", 0)
            if season_num not in seasons:
                seasons[season_num] = []
            seasons[season_num].append(episode)
        
        # Format episodes for the embed
        episode_items = []
        
        # Add season headers if there are multiple seasons
        if len(seasons) > 1:
            for season_num, season_episodes in seasons.items():
                season_display = f"Season {season_num}" if season_num > 0 else "Specials"
                episode_items.append({
                    "name": f"📂 {season_display}",
                    "value": f"**{len(season_episodes)}** episodes",
                    "inline": False,
                    "type": "header"
                })
                
                # Add episodes in this season
                for episode in season_episodes:
                    ep_num = episode.get("episode", 0)
                    ep_display = f"E{ep_num}" if ep_num > 0 else "Special"
                    
                    duration_str = ""
                    if episode.get("duration"):
                        minutes = episode["duration"] // 60
                        seconds = episode["duration"] % 60
                        duration_str = f" ({minutes}:{seconds:02d})"
                    
                    episode_items.append({
                        "name": f"🎬 {season_display} {ep_display}: {episode['title']}",
                        "value": f"Type: {episode.get('codec', 'Unknown')}{duration_str}\nReact with ▶️ to play",
                        "inline": True,
                        "type": "video",
                        "video_id": episode["id"],
                        "file_path": episode["file_path"]
                    })
        else:
            # Just list all episodes if there's only one season
            for episode in sorted_episodes:
                ep_num = episode.get("episode", 0)
                ep_display = f"Episode {ep_num}" if ep_num > 0 else "Special"
                
                duration_str = ""
                if episode.get("duration"):
                    minutes = episode["duration"] // 60
                    seconds = episode["duration"] % 60
                    duration_str = f" ({minutes}:{seconds:02d})"
                
                episode_items.append({
                    "name": f"🎬 {ep_display}: {episode['title']}",
                    "value": f"Type: {episode.get('codec', 'Unknown')}{duration_str}\nReact with ▶️ to play",
                    "inline": True,
                    "type": "video",
                    "video_id": episode["id"],
                    "file_path": episode["file_path"]
                })
        
        # Create the paginated embed
        message = await self.create_paginated_embed(
            channel_id=channel_id,
            title=f"Episodes in {series_name}",
            items=episode_items,
            items_per_page=8,
            description="Select an episode to play",
            footer_text="React with ▶️ to play an episode, 📋 to play all, or 🔙 to go back"
        )
        
        # Add navigation reactions
        await message.add_reaction("▶️")  # Play button for individual episodes
        await message.add_reaction("📋")  # Play all episodes
        await message.add_reaction("🔙")  # Back button
        
        # Override the handler for this specific embed
        self.active_embeds[message.id] = lambda payload: self._handle_episode_selection(
            payload, message, episode_items, series_name, category_id, category_name
        )
        
        return message
    
    async def _handle_episode_selection(self, payload, message, episode_items, series_name, category_id, category_name):
        """Handle episode selection reactions.
        
        Args:
            payload: Reaction payload
            message: Episode list embed message
            episode_items: List of episode items
            series_name: Series name
            category_id: Original category ID
            category_name: Original category name
        """
        # Get the emoji
        emoji = str(payload.emoji)
        
        # Handle navigation and close normally
        if emoji in ["⬅️", "➡️", "❌"]:
            # Get pagination state
            state = {
                "current_page": 0,
                "total_pages": max(1, (len(episode_items) + 8 - 1) // 8),
                "items": episode_items,
                "items_per_page": 8,
                "title": f"Episodes in {series_name}",
                "description": "Select an episode to play",
                "thumbnail_url": None,
                "footer_text": "React with ▶️ to play an episode, 📋 to play all, or 🔙 to go back"
            }
            
            await self._handle_pagination(payload, message, state)
            return
        
        # Handle back button
        if emoji == "🔙":
            # Go back to video list
            await self.create_video_list_embed(
                channel_id=message.channel.id,
                category_id=category_id,
                category_name=category_name
            )
            await message.delete()
            if message.id in self.active_embeds:
                del self.active_embeds[message.id]
            return
        
        # Handle play all episodes
        if emoji == "📋":
            # Get all playable episodes (filter out headers)
            playable_episodes = [item for item in episode_items if item["type"] == "video"]
            
            if playable_episodes:
                # Create a playlist with all episodes
                playlist_name = f"{series_name} Playlist"
                playlist_message = await message.channel.send(f"Creating playlist: {playlist_name}...")
                
                # Create playlist command
                playlist_paths = " ".join([f'"{ep["file_path"]}"' for ep in playable_episodes])
                play_command = f"{self.client.command_prefix}playlist {playlist_paths}"
                
                # Send the play command
                await message.channel.send(play_command)
                
                # Update last played in the database
                if self.db_manager:
                    for episode in playable_episodes:
                        self.db_manager.update_video_last_played(episode["video_id"])
                
                # Edit playlist message
                await playlist_message.edit(content=f"Playing playlist: {playlist_name} ({len(playable_episodes)} episodes)")
            
            return
        
        # Handle episode play
        if emoji == "▶️":
            # Prompt for index selection
            try:
                # Get the current page from the footer
                embed = message.embeds[0].to_dict()
                footer_text = embed.get("footer", {}).get("text", "")
                current_page = 0
                if "Page" in footer_text:
                    current_page = int(footer_text.split()[1]) - 1
                
                # Filter items based on type
                filtered_items = [item for item in episode_items[current_page*8:current_page*8+8] 
                                 if item["type"] == "video"]
                
                if not filtered_items:
                    return
                
                # Prompt for selection
                prompt_embed = self.embed_builder.create_basic_embed(
                    "Select Episode to Play",
                    "Reply with the number of the episode (e.g. '1', '2', etc.)"
                )
                
                # Add the episodes as fields for reference
                for i, item in enumerate(filtered_items, 1):
                    name = item["name"].lstrip("🎬 ")
                    self.embed_builder.add_field(
                        prompt_embed,
                        f"{i}. {name}",
                        "",
                        inline=True
                    )
                
                prompt_message = await self.embed_builder.send_embed(message.channel.id, prompt_embed)
                
                # Wait for a response
                def check(m):
                    return (m.author.id == payload.user_id and 
                            m.channel.id == message.channel.id and 
                            m.content.isdigit() and 
                            1 <= int(m.content) <= len(filtered_items))
                
                try:
                    response = await self.client.wait_for('message', check=check, timeout=30.0)
                    
                    # Get the selected episode
                    selection = int(response.content) - 1
                    selected_episode = filtered_items[selection]
                    
                    # Delete the prompt message and response
                    await prompt_message.delete()
                    await response.delete()
                    
                    # Play the selected episode
                    play_command = f"{self.client.command_prefix}play {selected_episode['file_path']}"
                    
                    # Update last played in the database
                    if self.db_manager:
                        self.db_manager.update_video_last_played(selected_episode["video_id"])
                    
                    # Send the play command
                    await message.channel.send(play_command)
                    
                except asyncio.TimeoutError:
                    # Delete the prompt message if the user didn't respond
                    await prompt_message.delete()
                
            except Exception as e:
                logger.error(f"Error handling episode selection: {e}")
        
        # Remove the user's reaction
        try:
            user = await self.client.fetch_user(payload.user_id)
            await message.remove_reaction(payload.emoji, user)
        except:
            pass  # Ignore errors removing reactions
    
    async def create_search_embed(self, channel_id: int, search_term: str) -> discord.Message:
        """Create an embed showing search results.
        
        Args:
            channel_id: Discord channel ID
            search_term: Search term
            
        Returns:
            Sent message object
        """
        if not self.db_manager:
            raise ValueError("Database manager is required for search embeds")
        
        # Get search results from the database
        results = self.db_manager.search_videos(search_term)
        
        # Format results for the embed
        result_items = []
        
        for video in results:
            duration_str = ""
            if video["duration"]:
                minutes = video["duration"] // 60
                seconds = video["duration"] % 60
                duration_str = f" ({minutes}:{seconds:02d})"
            
            category_name = video.get("category_name", "Uncategorized")
            series_info = f"From: {video['series_name']}" if video["series_name"] else ""
            
            result_items.append({
                "name": f"🎬 {video['title']}",
                "value": f"{series_info}\nCategory: {category_name}\nType: {video.get('codec', 'Unknown')}{duration_str}\nReact with ▶️ to play",
                "inline": True,
                "type": "video",
                "video_id": video["id"],
                "file_path": video["file_path"]
            })
        
        # Create the paginated embed
        message = await self.create_paginated_embed(
            channel_id=channel_id,
            title=f"Search Results for \"{search_term}\"",
            items=result_items,
            items_per_page=6,  # Fewer per page due to more details
            description=f"Found {len(result_items)} results" if result_items else "No results found",
            footer_text="React with ▶️ to play a video or 🔙 to go back"
        )
        
        # Add navigation reactions
        if result_items:
            await message.add_reaction("▶️")  # Play button
        await message.add_reaction("🔙")  # Back button
        
        # Override the handler for this specific embed
        self.active_embeds[message.id] = lambda payload: self._handle_search_selection(
            payload, message, result_items
        )
        
        return message
    
    async def _handle_search_selection(self, payload, message, result_items):
        """Handle search result selection reactions.
        
        Args:
            payload: Reaction payload
            message: Search result embed message
            result_items: List of search result items
        """
        # Get the emoji
        emoji = str(payload.emoji)
        
        # Handle navigation and close normally
        if emoji in ["⬅️", "➡️", "❌"]:
            # Get pagination state
            title = message.embeds[0].title
            state = {
                "current_page": 0,
                "total_pages": max(1, (len(result_items) + 6 - 1) // 6),
                "items": result_items,
                "items_per_page": 6,
                "title": title,
                "description": f"Found {len(result_items)} results" if result_items else "No results found",
                "thumbnail_url": None,
                "footer_text": "React with ▶️ to play a video or 🔙 to go back"
            }
            
            await self._handle_pagination(payload, message, state)
            return
        
        # Handle back button
        if emoji == "🔙":
            # Go back to category list
            await self.create_category_embed(message.channel.id)
            await message.delete()
            if message.id in self.active_embeds:
                del self.active_embeds[message.id]
            return
        
        # Handle video play
        if emoji == "▶️":
            # Prompt for index selection
            try:
                # Get the current page from the footer
                embed = message.embeds[0].to_dict()
                footer_text = embed.get("footer", {}).get("text", "")
                current_page = 0
                if "Page" in footer_text:
                    current_page = int(footer_text.split()[1]) - 1
                
                # Get videos on the current page
                filtered_items = result_items[current_page*6:current_page*6+6]
                
                if not filtered_items:
                    return
                
                # Prompt for selection
                prompt_embed = self.embed_builder.create_basic_embed(
                    "Select Video to Play",
                    "Reply with the number of the video (e.g. '1', '2', etc.)"
                )
                
                # Add the videos as fields for reference
                for i, item in enumerate(filtered_items, 1):
                    name = item["name"].lstrip("🎬 ")
                    self.embed_builder.add_field(
                        prompt_embed,
                        f"{i}. {name}",
                        "",
                        inline=True
                    )
                
                prompt_message = await self.embed_builder.send_embed(message.channel.id, prompt_embed)
                
                # Wait for a response
                def check(m):
                    return (m.author.id == payload.user_id and 
                            m.channel.id == message.channel.id and 
                            m.content.isdigit() and 
                            1 <= int(m.content) <= len(filtered_items))
                
                try:
                    response = await self.client.wait_for('message', check=check, timeout=30.0)
                    
                    # Get the selected video
                    selection = int(response.content) - 1
                    selected_video = filtered_items[selection]
                    
                    # Delete the prompt message and response
                    await prompt_message.delete()
                    await response.delete()
                    
                    # Play the selected video
                    play_command = f"{self.client.command_prefix}play {selected_video['file_path']}"
                    
                    # Update last played in the database
                    if self.db_manager:
                        self.db_manager.update_video_last_played(selected_video["video_id"])
                    
                    # Send the play command
                    await message.channel.send(play_command)
                    
                except asyncio.TimeoutError:
                    # Delete the prompt message if the user didn't respond
                    await prompt_message.delete()
                
            except Exception as e:
                logger.error(f"Error handling search selection: {e}")
        
        # Remove the user's reaction
        try:
            user = await self.client.fetch_user(payload.user_id)
            await message.remove_reaction(payload.emoji, user)
        except:
            pass  # Ignore errors removing reactions


# Initialize interactive embeds
def init_embeds(client, db_manager=None):
    """Initialize interactive embeds.
    
    Args:
        client: Discord client instance
        db_manager: Database manager instance
        
    Returns:
        InteractiveEmbed instance
    """
    embed_builder = EmbedBuilder(client)
    return InteractiveEmbed(client, embed_builder, db_manager)
