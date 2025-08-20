import { Client, GatewayIntentBits } from 'discord.js';
import dotenv from 'dotenv';
import { JellyfinClient } from './utils/jellyfin.js';
import { APIServer } from './api/server.js';
import logger from './utils/logger.js';

dotenv.config();

// Configuration
const config = {
    discordToken: process.env.DISCORD_TOKEN || '',
    guildId: process.env.GUILD_ID || '',
    channelId: process.env.CHANNEL_ID || '',
    apiPort: parseInt(process.env.API_PORT || '3001'),
    apiSecret: process.env.API_SECRET || 'your-secret-key',
    jellyfin: {
        baseUrl: process.env.JELLYFIN_BASE_URL || 'http://localhost:8096',
        apiKey: process.env.JELLYFIN_API_KEY || '',
        userId: process.env.JELLYFIN_USER_ID || undefined,
        libraryId: process.env.JELLYFIN_LIBRARY_ID || undefined
    }
};

// Validate configuration
if (!config.discordToken) {
    logger.error('DISCORD_TOKEN is required');
    process.exit(1);
}

if (!config.jellyfin.apiKey) {
    logger.error('JELLYFIN_API_KEY is required');
    process.exit(1);
}

// Create Discord client
const client = new Client({
    intents: [
        GatewayIntentBits.Guilds,
        GatewayIntentBits.GuildMessages,
        GatewayIntentBits.MessageContent
    ]
});

// Create Jellyfin client
const jellyfinClient = new JellyfinClient(config.jellyfin);

// Create API server
const apiServer = new APIServer(client, jellyfinClient, config.apiSecret);

// Discord client events
client.once('ready', async () => {
    logger.info(`✅ Discord bot logged in as ${client.user?.tag}`);
    
    // Test Jellyfin connection
    const jellyfinConnected = await jellyfinClient.testConnection();
    if (!jellyfinConnected) {
        logger.error('❌ Failed to connect to Jellyfin server');
        process.exit(1);
    }

    // Start API server
    apiServer.start(config.apiPort);
    
    logger.info('🚀 Jellyfin Discord Bot is ready!');
});

client.on('error', (error) => {
    logger.error('Discord client error:', error);
});

client.on('shardError', (error) => {
    logger.error('Discord shard error:', error);
});

// Handle process termination
process.on('SIGINT', () => {
    logger.info('🛑 Shutting down Jellyfin Discord Bot...');
    client.destroy();
    process.exit(0);
});

process.on('SIGTERM', () => {
    logger.info('🛑 Shutting down Jellyfin Discord Bot...');
    client.destroy();
    process.exit(0);
});

// Start the bot
client.login(config.discordToken).catch((error) => {
    logger.error('Failed to login to Discord:', error);
    process.exit(1);
});