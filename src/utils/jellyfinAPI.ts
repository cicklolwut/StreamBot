import axios, { AxiosInstance } from 'axios';
import logger from './logger.js';
import { JellyfinItem } from '../@types/jellyfin.js';

export interface JellyfinAPIConfig {
    apiUrl: string;
    apiSecret: string;
    enabled: boolean;
}

export class JellyfinAPIClient {
    private client: AxiosInstance;
    private config: JellyfinAPIConfig;

    constructor(config: JellyfinAPIConfig) {
        this.config = config;
        this.client = axios.create({
            baseURL: config.apiUrl,
            headers: {
                'X-API-Key': config.apiSecret,
                'Content-Type': 'application/json'
            },
            timeout: 10000
        });

        this.client.interceptors.response.use(
            (response) => response,
            (error) => {
                logger.error(`Jellyfin API client error: ${error.message}`, {
                    url: error.config?.url,
                    status: error.response?.status
                });
                throw error;
            }
        );
    }

    async isAvailable(): Promise<boolean> {
        if (!this.config.enabled) return false;
        
        try {
            const response = await this.client.get('/health');
            return response.data.success === true;
        } catch (error) {
            logger.warn('Jellyfin bot API not available:', error instanceof Error ? error.message : String(error));
            return false;
        }
    }

    async searchItems(query: string, channelId: string, prefix: string = '$'): Promise<boolean> {
        if (!this.config.enabled) return false;

        try {
            const response = await this.client.post('/jellyfin/search', {
                query,
                channelId,
                prefix
            });
            
            if (response.data.success) {
                logger.info(`Jellyfin search sent: ${response.data.data.count} results for "${query}"`);
                return true;
            }
            
            logger.warn('Jellyfin search failed:', response.data.message);
            return false;
        } catch (error) {
            logger.error('Failed to send Jellyfin search request:', error);
            return false;
        }
    }

    async searchShows(query: string, channelId: string, prefix: string = '$'): Promise<boolean> {
        if (!this.config.enabled) return false;

        try {
            const response = await this.client.post('/jellyfin/shows', {
                query,
                channelId,
                prefix
            });
            
            if (response.data.success) {
                logger.info(`Jellyfin shows search sent: ${response.data.data.count} results for "${query}"`);
                return true;
            }
            
            logger.warn('Jellyfin shows search failed:', response.data.message);
            return false;
        } catch (error) {
            logger.error('Failed to send Jellyfin shows search request:', error);
            return false;
        }
    }

    async getSeasons(seriesId: string, channelId: string, prefix: string = '$'): Promise<boolean> {
        if (!this.config.enabled) return false;

        try {
            const response = await this.client.post('/jellyfin/seasons', {
                seriesId,
                channelId,
                prefix
            });
            
            if (response.data.success) {
                logger.info(`Jellyfin seasons sent: ${response.data.data.count} seasons for series ${seriesId}`);
                return true;
            }
            
            logger.warn('Jellyfin seasons request failed:', response.data.message);
            return false;
        } catch (error) {
            logger.error('Failed to send Jellyfin seasons request:', error);
            return false;
        }
    }

    async getEpisodes(seasonId: string, channelId: string, prefix: string = '$'): Promise<boolean> {
        if (!this.config.enabled) return false;

        try {
            const response = await this.client.post('/jellyfin/episodes', {
                seasonId,
                channelId,
                prefix
            });
            
            if (response.data.success) {
                logger.info(`Jellyfin episodes sent: ${response.data.data.count} episodes for season ${seasonId}`);
                return true;
            }
            
            logger.warn('Jellyfin episodes request failed:', response.data.message);
            return false;
        } catch (error) {
            logger.error('Failed to send Jellyfin episodes request:', error);
            return false;
        }
    }

    async getItem(itemId: string): Promise<JellyfinItem | null> {
        if (!this.config.enabled) return null;

        try {
            const response = await this.client.post('/jellyfin/item', {
                itemId
            });
            
            if (response.data.success) {
                return response.data.data;
            }
            
            logger.warn('Jellyfin get item failed:', response.data.message);
            return null;
        } catch (error) {
            logger.error('Failed to get Jellyfin item:', error);
            return null;
        }
    }

    async getStreamInfo(itemId: string): Promise<{ streamUrl: string; isLocal: boolean; localPath?: string } | null> {
        const item = await this.getItem(itemId);
        if (!item) return null;

        // Check if we can access the file locally
        if (item.Path) {
            try {
                // In a real implementation, you'd check file system access
                // For now, assume local access based on path structure
                const isLocal = !item.Path.startsWith('http') && item.Path.includes('/');
                
                if (isLocal) {
                    logger.info(`Using local path for item ${itemId}: ${item.Path}`);
                    return {
                        streamUrl: item.Path,
                        isLocal: true,
                        localPath: item.Path
                    };
                }
            } catch (error) {
                logger.warn(`Failed to check local access for ${itemId}:`, error);
            }
        }

        // Generate streaming URL from Jellyfin
        // This would need the Jellyfin configuration from the bot API
        logger.info(`Using Jellyfin stream URL for item ${itemId}`);
        return {
            streamUrl: `jellyfin://stream/${itemId}`, // Placeholder - would need actual Jellyfin streaming URL
            isLocal: false
        };
    }

    getDisplayName(item: JellyfinItem): string {
        let displayName = item.Name;

        if (item.Type === 'Episode' && item.SeriesName) {
            displayName = `${item.SeriesName} - S${item.ParentIndexNumber || '?'}E${item.IndexNumber || '?'}: ${item.Name}`;
        }

        if (item.ProductionYear) {
            displayName += ` (${item.ProductionYear})`;
        }

        return displayName;
    }
}