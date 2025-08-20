import axios, { AxiosInstance } from 'axios';
import { JellyfinConfig, JellyfinItem, JellyfinSearchResult, JellyfinStreamInfo, JellyfinItemType } from '../@types/jellyfin.js';
import logger from './logger.js';
import fs from 'fs';
import path from 'path';

export class JellyfinClient {
    private client: AxiosInstance;
    private config: JellyfinConfig;

    constructor(config: JellyfinConfig) {
        this.config = config;
        this.client = axios.create({
            baseURL: config.baseUrl,
            headers: {
                'Authorization': `MediaBrowser Token="${config.apiKey}"`,
                'X-MediaBrowser-Token': config.apiKey,
                'Content-Type': 'application/json'
            },
            timeout: 10000
        });

        // Add response interceptor for error handling
        this.client.interceptors.response.use(
            (response) => response,
            (error) => {
                logger.error(`Jellyfin API error: ${error.message}`, {
                    url: error.config?.url,
                    status: error.response?.status,
                    statusText: error.response?.statusText
                });
                throw error;
            }
        );
    }

    async testConnection(): Promise<boolean> {
        try {
            const response = await this.client.get('/System/Info');
            logger.info(`Connected to Jellyfin server: ${response.data.ServerName} v${response.data.Version}`);
            return true;
        } catch (error) {
            logger.error('Failed to connect to Jellyfin server:', error);
            return false;
        }
    }

    async searchItems(
        searchTerm: string,
        itemTypes: JellyfinItemType[] = ['Movie', 'Episode', 'Audio', 'Video'],
        limit: number = 20,
        parentId?: string
    ): Promise<JellyfinSearchResult> {
        try {
            const params: any = {
                searchTerm,
                includeItemTypes: itemTypes.join(','),
                limit,
                recursive: true,
                fields: 'Path,MediaSources,RunTimeTicks,Overview,ImageTags,BackdropImageTags,ParentId,SeriesId,SeasonId,ChildCount'
            };

            if (this.config.userId) {
                params.userId = this.config.userId;
            }

            if (parentId || this.config.libraryId) {
                params.parentId = parentId || this.config.libraryId;
            }

            const response = await this.client.get('/Items', { params });
            return response.data;
        } catch (error) {
            logger.error(`Failed to search items with term "${searchTerm}":`, error);
            throw error;
        }
    }

    async getItemById(itemId: string): Promise<JellyfinItem> {
        try {
            const params: any = {
                fields: 'Path,MediaSources,RunTimeTicks,Overview,ImageTags,BackdropImageTags,ParentId,SeriesId,SeasonId,ChildCount'
            };

            if (this.config.userId) {
                params.userId = this.config.userId;
            }

            const response = await this.client.get(`/Items/${itemId}`, { params });
            return response.data;
        } catch (error) {
            logger.error(`Failed to get item ${itemId}:`, error);
            throw error;
        }
    }

    async getRecentItems(
        itemTypes: JellyfinItemType[] = ['Movie', 'Episode', 'Audio', 'Video'],
        limit: number = 20,
        parentId?: string
    ): Promise<JellyfinSearchResult> {
        try {
            const params: any = {
                includeItemTypes: itemTypes.join(','),
                limit,
                recursive: true,
                sortBy: 'DateCreated',
                sortOrder: 'Descending',
                fields: 'Path,MediaSources,RunTimeTicks,Overview'
            };

            if (this.config.userId) {
                params.userId = this.config.userId;
            }

            if (parentId || this.config.libraryId) {
                params.parentId = parentId || this.config.libraryId;
            }

            const response = await this.client.get('/Items', { params });
            return response.data;
        } catch (error) {
            logger.error('Failed to get recent items:', error);
            throw error;
        }
    }

    async getLibraries(): Promise<JellyfinItem[]> {
        try {
            const params: any = {};
            if (this.config.userId) {
                params.userId = this.config.userId;
            }

            const response = await this.client.get('/Items', { 
                params: {
                    ...params,
                    includeItemTypes: 'CollectionFolder'
                }
            });
            return response.data.Items;
        } catch (error) {
            logger.error('Failed to get libraries:', error);
            throw error;
        }
    }

    async getStreamInfo(itemId: string): Promise<JellyfinStreamInfo> {
        try {
            // Get item details first
            const item = await this.getItemById(itemId);
            
            // Check if we can access the file locally
            const isLocal = await this.isItemLocallyAccessible(item);
            
            if (isLocal && item.Path) {
                logger.info(`Using local path for item ${itemId}: ${item.Path}`);
                return {
                    itemId,
                    streamUrl: item.Path,
                    isLocal: true,
                    localPath: item.Path
                };
            }

            // Generate streaming URL from Jellyfin
            const streamUrl = this.generateStreamUrl(itemId, item.Type);
            logger.info(`Using Jellyfin stream URL for item ${itemId}: ${streamUrl}`);
            
            return {
                itemId,
                streamUrl,
                isLocal: false
            };
        } catch (error) {
            logger.error(`Failed to get stream info for item ${itemId}:`, error);
            throw error;
        }
    }

    private async isItemLocallyAccessible(item: JellyfinItem): Promise<boolean> {
        if (!item.Path) {
            return false;
        }

        try {
            // Check if the path exists and is accessible
            const stats = await fs.promises.stat(item.Path);
            return stats.isFile();
        } catch (error) {
            // File doesn't exist or is not accessible locally
            return false;
        }
    }

    private generateStreamUrl(itemId: string, itemType: string): string {
        const baseUrl = this.config.baseUrl.replace(/\/$/, '');
        
        // Determine the appropriate streaming endpoint based on item type
        if (itemType === 'Audio') {
            return `${baseUrl}/Audio/${itemId}/stream?api_key=${this.config.apiKey}&static=false`;
        } else {
            // For Video, Movie, Episode, etc.
            return `${baseUrl}/Videos/${itemId}/stream?api_key=${this.config.apiKey}&static=false`;
        }
    }

    async getSeasons(seriesId: string): Promise<JellyfinSearchResult> {
        try {
            const params: any = {
                parentId: seriesId,
                includeItemTypes: 'Season',
                sortBy: 'IndexNumber',
                sortOrder: 'Ascending',
                fields: 'Overview,ImageTags,IndexNumber,ChildCount'
            };

            if (this.config.userId) {
                params.userId = this.config.userId;
            }

            const response = await this.client.get('/Items', { params });
            return response.data;
        } catch (error) {
            logger.error(`Failed to get seasons for series ${seriesId}:`, error);
            throw error;
        }
    }

    async getEpisodes(seasonId: string): Promise<JellyfinSearchResult> {
        try {
            const params: any = {
                parentId: seasonId,
                includeItemTypes: 'Episode',
                sortBy: 'IndexNumber',
                sortOrder: 'Ascending',
                fields: 'Path,MediaSources,RunTimeTicks,Overview,ImageTags,IndexNumber,ParentIndexNumber,SeriesName'
            };

            if (this.config.userId) {
                params.userId = this.config.userId;
            }

            const response = await this.client.get('/Items', { params });
            return response.data;
        } catch (error) {
            logger.error(`Failed to get episodes for season ${seasonId}:`, error);
            throw error;
        }
    }

    async searchShows(
        searchTerm: string,
        limit: number = 20,
        parentId?: string
    ): Promise<JellyfinSearchResult> {
        try {
            const params: any = {
                searchTerm,
                includeItemTypes: 'Series',
                limit,
                recursive: true,
                fields: 'Overview,ImageTags,BackdropImageTags,ProductionYear,ChildCount'
            };

            if (this.config.userId) {
                params.userId = this.config.userId;
            }

            if (parentId || this.config.libraryId) {
                params.parentId = parentId || this.config.libraryId;
            }

            const response = await this.client.get('/Items', { params });
            return response.data;
        } catch (error) {
            logger.error(`Failed to search shows with term "${searchTerm}":`, error);
            throw error;
        }
    }

    generateImageUrl(itemId: string, imageTag: string, imageType: string = 'Primary', maxWidth: number = 300, maxHeight: number = 450): string {
        const baseUrl = this.config.baseUrl.replace(/\/$/, '');
        return `${baseUrl}/Items/${itemId}/Images/${imageType}?maxWidth=${maxWidth}&maxHeight=${maxHeight}&tag=${imageTag}&api_key=${this.config.apiKey}`;
    }

    getBestThumbnailUrl(item: JellyfinItem, preferredType: 'episode' | 'series' | 'season' = 'episode'): string | null {
        if (!item.ImageTags) return null;

        // For episodes, prefer Primary (episode screenshot) or Thumb
        if (preferredType === 'episode') {
            if (item.ImageTags.Primary) {
                return this.generateImageUrl(item.Id, item.ImageTags.Primary, 'Primary', 400, 225); // 16:9 aspect ratio
            }
            if (item.ImageTags.Thumb) {
                return this.generateImageUrl(item.Id, item.ImageTags.Thumb, 'Thumb', 400, 225);
            }
        }

        // For series/seasons, prefer Primary poster
        if (preferredType === 'series' || preferredType === 'season') {
            if (item.ImageTags.Primary) {
                return this.generateImageUrl(item.Id, item.ImageTags.Primary, 'Primary', 300, 450); // Poster aspect ratio
            }
        }

        // Fallback to any available image
        if (item.ImageTags.Primary) {
            return this.generateImageUrl(item.Id, item.ImageTags.Primary, 'Primary', 300, 400);
        }
        if (item.ImageTags.Backdrop) {
            return this.generateImageUrl(item.Id, item.ImageTags.Backdrop, 'Backdrop', 500, 281);
        }
        if (item.ImageTags.Thumb) {
            return this.generateImageUrl(item.Id, item.ImageTags.Thumb, 'Thumb', 400, 225);
        }

        return null;
    }

    formatItemForDisplay(item: JellyfinItem, index?: number, showId: boolean = false): string {
        const prefix = index !== undefined ? `${index + 1}. ` : '';
        let displayName = `\`${item.Name}\``;

        // Add additional context for TV episodes
        if (item.Type === 'Episode' && item.SeriesName) {
            displayName = `\`${item.SeriesName}\` - S${item.ParentIndexNumber || '?'}E${item.IndexNumber || '?'}: \`${item.Name}\``;
        }

        // Add year for movies
        if (item.Type === 'Movie' && item.ProductionYear) {
            displayName += ` (${item.ProductionYear})`;
        }

        // Add runtime if available
        if (item.RunTimeTicks) {
            const minutes = Math.round(item.RunTimeTicks / 10000 / 1000 / 60);
            displayName += ` - ${minutes}m`;
        }

        // Add item ID if requested
        if (showId) {
            displayName += ` - ID: \`${item.Id}\``;
        }

        return `${prefix}${displayName}`;
    }

    formatItemDetails(item: JellyfinItem): string[] {
        const details: string[] = [];
        
        details.push(`📹 **${item.Name}**`);
        
        if (item.Type === 'Episode' && item.SeriesName) {
            details.push(`**Series**: ${item.SeriesName}`);
            if (item.ParentIndexNumber && item.IndexNumber) {
                details.push(`**Episode**: S${item.ParentIndexNumber}E${item.IndexNumber}`);
            }
        }

        if (item.ProductionYear) {
            details.push(`**Year**: ${item.ProductionYear}`);
        }

        if (item.RunTimeTicks) {
            const minutes = Math.round(item.RunTimeTicks / 10000 / 1000 / 60);
            details.push(`**Duration**: ${minutes} minutes`);
        }

        if (item.Overview) {
            const truncatedOverview = item.Overview.length > 200 
                ? item.Overview.substring(0, 200) + '...' 
                : item.Overview;
            details.push(`**Overview**: ${truncatedOverview}`);
        }

        details.push(`**Type**: ${item.Type}`);
        details.push(`**ID**: \`${item.Id}\``);

        return details;
    }

    formatSeriesForDisplay(item: JellyfinItem, index?: number): string {
        const prefix = index !== undefined ? `${index + 1}. ` : '';
        let displayName = `📺 \`${item.Name}\``;

        if (item.ProductionYear) {
            displayName += ` (${item.ProductionYear})`;
        }

        if (item.ChildCount) {
            displayName += ` - ${item.ChildCount} seasons`;
        }

        displayName += ` - ID: \`${item.Id}\``;
        return `${prefix}${displayName}`;
    }

    createSeriesEmbed(item: JellyfinItem, index?: number): { content: string, embed?: any } {
        const content = this.formatSeriesForDisplay(item, index);
        
        const thumbnailUrl = this.getBestThumbnailUrl(item, 'series');
        
        if (thumbnailUrl || item.Overview) {
            const embed: any = {
                color: 0x00AE86,
                title: item.Name
            };

            if (item.Overview) {
                const truncatedOverview = item.Overview.length > 300 
                    ? item.Overview.substring(0, 300) + '...' 
                    : item.Overview;
                embed.description = truncatedOverview;
            }

            if (thumbnailUrl) {
                embed.thumbnail = { url: thumbnailUrl }; // Use thumbnail for series posters (smaller)
            }

            if (item.ProductionYear) {
                embed.footer = { text: `Released: ${item.ProductionYear}` };
            }

            return { content, embed };
        }

        return { content };
    }

    formatSeasonForDisplay(item: JellyfinItem, index?: number): string {
        const prefix = index !== undefined ? `${index + 1}. ` : '';
        let displayName = `📅 ${item.Name}`;

        if (item.ChildCount) {
            displayName += ` (${item.ChildCount} episodes)`;
        }

        displayName += ` - ID: \`${item.Id}\``;
        return `${prefix}${displayName}`;
    }

    formatEpisodeForDisplay(item: JellyfinItem, index?: number, includeOverview: boolean = false): string {
        const prefix = index !== undefined ? `${index + 1}. ` : '';
        let displayName = `🎬 `;
        
        if (item.IndexNumber) {
            displayName += `E${item.IndexNumber}: `;
        }
        
        displayName += `\`${item.Name}\``;

        if (item.RunTimeTicks) {
            const minutes = Math.round(item.RunTimeTicks / 10000 / 1000 / 60);
            displayName += ` - ${minutes}m`;
        }

        displayName += ` - ID: \`${item.Id}\``;

        let result = `${prefix}${displayName}`;
        
        if (includeOverview && item.Overview) {
            const truncatedOverview = item.Overview.length > 150 
                ? item.Overview.substring(0, 150) + '...' 
                : item.Overview;
            result += `\n   _${truncatedOverview}_`;
        }

        // Thumbnail will be handled via Discord embeds, not inline text

        return result;
    }

    formatShowDetails(item: JellyfinItem): string[] {
        const details: string[] = [];
        
        details.push(`📺 **${item.Name}**`);
        
        if (item.ProductionYear) {
            details.push(`**Year**: ${item.ProductionYear}`);
        }

        if (item.ChildCount) {
            details.push(`**Seasons**: ${item.ChildCount}`);
        }

        if (item.Overview) {
            const truncatedOverview = item.Overview.length > 300 
                ? item.Overview.substring(0, 300) + '...' 
                : item.Overview;
            details.push(`**Overview**: ${truncatedOverview}`);
        }

        // Add series poster if available
        if (item.ImageTags?.Primary) {
            const posterUrl = this.generateImageUrl(item.Id, item.ImageTags.Primary);
            details.push(`🎭 [Show Poster](${posterUrl})`);
        }

        details.push(`**ID**: \`${item.Id}\``);

        return details;
    }

    createEpisodeEmbed(item: JellyfinItem, index?: number): { content: string, embed?: any } {
        const prefix = index !== undefined ? `${index + 1}. ` : '';
        let displayName = `🎬 `;
        
        if (item.IndexNumber) {
            displayName += `E${item.IndexNumber}: `;
        }
        
        displayName += `\`${item.Name}\``;

        if (item.RunTimeTicks) {
            const minutes = Math.round(item.RunTimeTicks / 10000 / 1000 / 60);
            displayName += ` - ${minutes}m`;
        }

        displayName += ` - ID: \`${item.Id}\``;

        const content = `${prefix}${displayName}`;
        
        // Create embed for thumbnail and overview
        const thumbnailUrl = this.getBestThumbnailUrl(item, 'episode');
        
        if (thumbnailUrl || item.Overview) {
            const embed: any = {
                color: 0x00AE86, // Jellyfin brand color
            };

            if (item.Overview) {
                const truncatedOverview = item.Overview.length > 200 
                    ? item.Overview.substring(0, 200) + '...' 
                    : item.Overview;
                embed.description = truncatedOverview;
            }

            if (thumbnailUrl) {
                embed.image = { url: thumbnailUrl };
            }

            // Add series context if available
            if (item.SeriesName) {
                embed.author = {
                    name: item.SeriesName,
                };
            }

            return { content, embed };
        }

        return { content };
    }
}