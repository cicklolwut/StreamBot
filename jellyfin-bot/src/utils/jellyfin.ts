import axios, { AxiosInstance } from 'axios';
import { JellyfinConfig, JellyfinItem, JellyfinSearchResult, JellyfinItemType } from '../types/jellyfin.js';
import logger from './logger.js';

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

        this.client.interceptors.response.use(
            (response) => response,
            (error) => {
                logger.error(`Jellyfin API error: ${error.message}`, {
                    url: error.config?.url,
                    status: error.response?.status
                });
                throw error;
            }
        );
    }

    async testConnection(): Promise<boolean> {
        try {
            const response = await this.client.get('/System/Info');
            logger.info(`Connected to Jellyfin: ${response.data.ServerName} v${response.data.Version}`);
            return true;
        } catch (error) {
            logger.error('Failed to connect to Jellyfin server:', error);
            return false;
        }
    }

    async searchItems(
        searchTerm: string,
        itemTypes: JellyfinItemType[] = ['Movie', 'Episode', 'Audio', 'Video'],
        limit: number = 20
    ): Promise<JellyfinSearchResult> {
        const params: any = {
            searchTerm,
            includeItemTypes: itemTypes.join(','),
            limit,
            recursive: true,
            fields: 'Path,MediaSources,RunTimeTicks,Overview,ImageTags,BackdropImageTags,ParentId,SeriesId,SeasonId,ChildCount'
        };

        if (this.config.userId) params.userId = this.config.userId;
        if (this.config.libraryId) params.parentId = this.config.libraryId;

        const response = await this.client.get('/Items', { params });
        return response.data;
    }

    async searchShows(searchTerm: string, limit: number = 20): Promise<JellyfinSearchResult> {
        const params: any = {
            searchTerm,
            includeItemTypes: 'Series',
            limit,
            recursive: true,
            fields: 'Overview,ImageTags,BackdropImageTags,ProductionYear,ChildCount'
        };

        if (this.config.userId) params.userId = this.config.userId;
        if (this.config.libraryId) params.parentId = this.config.libraryId;

        const response = await this.client.get('/Items', { params });
        return response.data;
    }

    async getSeasons(seriesId: string): Promise<JellyfinSearchResult> {
        const params: any = {
            parentId: seriesId,
            includeItemTypes: 'Season',
            sortBy: 'IndexNumber',
            sortOrder: 'Ascending',
            fields: 'Overview,ImageTags,IndexNumber,ChildCount'
        };

        if (this.config.userId) params.userId = this.config.userId;

        const response = await this.client.get('/Items', { params });
        return response.data;
    }

    async getEpisodes(seasonId: string): Promise<JellyfinSearchResult> {
        const params: any = {
            parentId: seasonId,
            includeItemTypes: 'Episode',
            sortBy: 'IndexNumber',
            sortOrder: 'Ascending',
            fields: 'Path,MediaSources,RunTimeTicks,Overview,ImageTags,IndexNumber,ParentIndexNumber,SeriesName'
        };

        if (this.config.userId) params.userId = this.config.userId;

        const response = await this.client.get('/Items', { params });
        return response.data;
    }

    async getItemById(itemId: string): Promise<JellyfinItem> {
        const params: any = {
            fields: 'Path,MediaSources,RunTimeTicks,Overview,ImageTags,BackdropImageTags,ParentId,SeriesId,SeasonId,ChildCount'
        };

        if (this.config.userId) params.userId = this.config.userId;

        const response = await this.client.get(`/Items/${itemId}`, { params });
        return response.data;
    }

    async getRecentItems(
        itemTypes: JellyfinItemType[] = ['Movie', 'Episode', 'Audio', 'Video'],
        limit: number = 20
    ): Promise<JellyfinSearchResult> {
        const params: any = {
            includeItemTypes: itemTypes.join(','),
            limit,
            recursive: true,
            sortBy: 'DateCreated',
            sortOrder: 'Descending',
            fields: 'Path,MediaSources,RunTimeTicks,Overview,ImageTags,BackdropImageTags'
        };

        if (this.config.userId) params.userId = this.config.userId;
        if (this.config.libraryId) params.parentId = this.config.libraryId;

        const response = await this.client.get('/Items', { params });
        return response.data;
    }

    generateImageUrl(itemId: string, imageTag: string, imageType: string = 'Primary', maxWidth: number = 400, maxHeight: number = 300): string {
        const baseUrl = this.config.baseUrl.replace(/\/$/, '');
        return `${baseUrl}/Items/${itemId}/Images/${imageType}?maxWidth=${maxWidth}&maxHeight=${maxHeight}&tag=${imageTag}&api_key=${this.config.apiKey}`;
    }

    getBestThumbnailUrl(item: JellyfinItem, preferredType: 'episode' | 'series' | 'season' = 'episode'): string | null {
        if (!item.ImageTags) return null;

        if (preferredType === 'episode') {
            if (item.ImageTags.Primary) {
                return this.generateImageUrl(item.Id, item.ImageTags.Primary, 'Primary', 600, 338);
            }
            if (item.ImageTags.Thumb) {
                return this.generateImageUrl(item.Id, item.ImageTags.Thumb, 'Thumb', 600, 338);
            }
        }

        if (preferredType === 'series' || preferredType === 'season') {
            if (item.ImageTags.Primary) {
                return this.generateImageUrl(item.Id, item.ImageTags.Primary, 'Primary', 400, 600);
            }
        }

        // Fallback
        if (item.ImageTags.Primary) {
            return this.generateImageUrl(item.Id, item.ImageTags.Primary, 'Primary', 400, 400);
        }
        if (item.ImageTags.Backdrop) {
            return this.generateImageUrl(item.Id, item.ImageTags.Backdrop, 'Backdrop', 600, 338);
        }

        return null;
    }
}