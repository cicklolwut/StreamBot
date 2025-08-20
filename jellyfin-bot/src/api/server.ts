import express from 'express';
import cors from 'cors';
import { Client, TextChannel } from 'discord.js';
import { JellyfinClient } from '../utils/jellyfin.js';
import { EmbedService } from '../services/embedService.js';
import { APIRequest, APIResponse } from '../types/jellyfin.js';
import logger from '../utils/logger.js';

export class APIServer {
    private app: express.Application;
    private client: Client;
    private jellyfinClient: JellyfinClient;
    private embedService: EmbedService;
    private apiSecret: string;

    constructor(client: Client, jellyfinClient: JellyfinClient, apiSecret: string) {
        this.app = express();
        this.client = client;
        this.jellyfinClient = jellyfinClient;
        this.embedService = new EmbedService(jellyfinClient);
        this.apiSecret = apiSecret;

        this.setupMiddleware();
        this.setupRoutes();
    }

    private setupMiddleware(): void {
        this.app.use(cors());
        this.app.use(express.json());
        
        // Authentication middleware
        this.app.use((req, res, next) => {
            const apiKey = req.headers['x-api-key'];
            if (apiKey !== this.apiSecret) {
                return res.status(401).json({ success: false, message: 'Unauthorized' });
            }
            next();
        });
    }

    private setupRoutes(): void {
        // Health check
        this.app.get('/health', (req, res) => {
            res.json({ 
                success: true, 
                message: 'Jellyfin Discord Bot API is running',
                jellyfinConnected: true // Could add actual health check
            });
        });

        // Main API endpoint
        this.app.post('/jellyfin', async (req, res) => {
            try {
                const request: APIRequest = req.body;
                const response = await this.handleJellyfinRequest(request);
                res.json(response);
            } catch (error) {
                logger.error('API request failed:', error);
                res.status(500).json({ 
                    success: false, 
                    message: 'Internal server error' 
                });
            }
        });

        // Search endpoint
        this.app.post('/jellyfin/search', async (req, res) => {
            try {
                const { query, channelId, prefix = '$' } = req.body;
                
                if (!query || !channelId) {
                    return res.status(400).json({ 
                        success: false, 
                        message: 'Missing required fields: query, channelId' 
                    });
                }

                const channel = await this.getChannel(channelId);
                if (!channel) {
                    return res.status(404).json({ 
                        success: false, 
                        message: 'Channel not found' 
                    });
                }

                const results = await this.jellyfinClient.searchItems(query);
                await this.embedService.sendSearchResults(channel, results.Items, query, prefix);
                
                res.json({ 
                    success: true, 
                    message: `Sent ${results.Items.length} search results to channel`,
                    data: { count: results.Items.length }
                });
            } catch (error) {
                logger.error('Search request failed:', error);
                res.status(500).json({ 
                    success: false, 
                    message: error instanceof Error ? error.message : 'Search failed' 
                });
            }
        });

        // TV Shows search endpoint
        this.app.post('/jellyfin/shows', async (req, res) => {
            try {
                const { query, channelId, prefix = '$' } = req.body;
                
                if (!query || !channelId) {
                    return res.status(400).json({ 
                        success: false, 
                        message: 'Missing required fields: query, channelId' 
                    });
                }

                const channel = await this.getChannel(channelId);
                if (!channel) {
                    return res.status(404).json({ 
                        success: false, 
                        message: 'Channel not found' 
                    });
                }

                const results = await this.jellyfinClient.searchShows(query);
                await this.embedService.sendShowsResults(channel, results.Items, query, prefix);
                
                res.json({ 
                    success: true, 
                    message: `Sent ${results.Items.length} TV show results to channel`,
                    data: { count: results.Items.length }
                });
            } catch (error) {
                logger.error('Shows search failed:', error);
                res.status(500).json({ 
                    success: false, 
                    message: error instanceof Error ? error.message : 'Shows search failed' 
                });
            }
        });

        // Seasons endpoint
        this.app.post('/jellyfin/seasons', async (req, res) => {
            try {
                const { seriesId, channelId, prefix = '$' } = req.body;
                
                if (!seriesId || !channelId) {
                    return res.status(400).json({ 
                        success: false, 
                        message: 'Missing required fields: seriesId, channelId' 
                    });
                }

                const channel = await this.getChannel(channelId);
                if (!channel) {
                    return res.status(404).json({ 
                        success: false, 
                        message: 'Channel not found' 
                    });
                }

                const [seriesInfo, seasonsResult] = await Promise.all([
                    this.jellyfinClient.getItemById(seriesId),
                    this.jellyfinClient.getSeasons(seriesId)
                ]);
                
                await this.embedService.sendSeasons(channel, seasonsResult.Items, seriesInfo.Name, prefix);
                
                res.json({ 
                    success: true, 
                    message: `Sent ${seasonsResult.Items.length} seasons to channel`,
                    data: { count: seasonsResult.Items.length, seriesName: seriesInfo.Name }
                });
            } catch (error) {
                logger.error('Seasons request failed:', error);
                res.status(500).json({ 
                    success: false, 
                    message: error instanceof Error ? error.message : 'Failed to get seasons' 
                });
            }
        });

        // Episodes endpoint
        this.app.post('/jellyfin/episodes', async (req, res) => {
            try {
                const { seasonId, channelId, prefix = '$' } = req.body;
                
                if (!seasonId || !channelId) {
                    return res.status(400).json({ 
                        success: false, 
                        message: 'Missing required fields: seasonId, channelId' 
                    });
                }

                const channel = await this.getChannel(channelId);
                if (!channel) {
                    return res.status(404).json({ 
                        success: false, 
                        message: 'Channel not found' 
                    });
                }

                const [seasonInfo, episodesResult] = await Promise.all([
                    this.jellyfinClient.getItemById(seasonId),
                    this.jellyfinClient.getEpisodes(seasonId)
                ]);
                
                await this.embedService.sendEpisodes(channel, episodesResult.Items, seasonInfo.Name, prefix);
                
                res.json({ 
                    success: true, 
                    message: `Sent ${episodesResult.Items.length} episodes to channel`,
                    data: { count: episodesResult.Items.length, seasonName: seasonInfo.Name }
                });
            } catch (error) {
                logger.error('Episodes request failed:', error);
                res.status(500).json({ 
                    success: false, 
                    message: error instanceof Error ? error.message : 'Failed to get episodes' 
                });
            }
        });

        // Get item info endpoint (for playback)
        this.app.post('/jellyfin/item', async (req, res) => {
            try {
                const { itemId } = req.body;
                
                if (!itemId) {
                    return res.status(400).json({ 
                        success: false, 
                        message: 'Missing required field: itemId' 
                    });
                }

                const item = await this.jellyfinClient.getItemById(itemId);
                
                res.json({ 
                    success: true, 
                    message: 'Item retrieved successfully',
                    data: item
                });
            } catch (error) {
                logger.error('Get item failed:', error);
                res.status(500).json({ 
                    success: false, 
                    message: error instanceof Error ? error.message : 'Failed to get item' 
                });
            }
        });
    }

    private async handleJellyfinRequest(request: APIRequest): Promise<APIResponse> {
        const channel = await this.getChannel(request.channelId);
        if (!channel) {
            return { success: false, message: 'Channel not found' };
        }

        switch (request.action) {
            case 'search':
                const searchResults = await this.jellyfinClient.searchItems(request.data.query);
                await this.embedService.sendSearchResults(channel, searchResults.Items, request.data.query, request.data.prefix || '$');
                return { success: true, message: 'Search results sent', data: { count: searchResults.Items.length } };

            case 'searchShows':
                const showResults = await this.jellyfinClient.searchShows(request.data.query);
                await this.embedService.sendShowsResults(channel, showResults.Items, request.data.query, request.data.prefix || '$');
                return { success: true, message: 'TV show results sent', data: { count: showResults.Items.length } };

            // Add other cases as needed...

            default:
                return { success: false, message: 'Unknown action' };
        }
    }

    private async getChannel(channelId: string): Promise<TextChannel | null> {
        try {
            const channel = await this.client.channels.fetch(channelId);
            return channel as TextChannel;
        } catch (error) {
            logger.error(`Failed to fetch channel ${channelId}:`, error);
            return null;
        }
    }

    start(port: number): void {
        this.app.listen(port, () => {
            logger.info(`Jellyfin Discord Bot API server running on port ${port}`);
        });
    }
}