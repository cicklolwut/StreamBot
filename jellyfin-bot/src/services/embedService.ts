import { EmbedBuilder, TextChannel } from 'discord.js';
import { JellyfinItem } from '../types/jellyfin.js';
import { JellyfinClient } from '../utils/jellyfin.js';
import logger from '../utils/logger.js';

export class EmbedService {
    private jellyfinClient: JellyfinClient;

    constructor(jellyfinClient: JellyfinClient) {
        this.jellyfinClient = jellyfinClient;
    }

    async sendSearchResults(channel: TextChannel, results: JellyfinItem[], query: string, prefix: string): Promise<void> {
        if (results.length === 0) {
            await channel.send(`❌ No results found for "${query}"`);
            return;
        }

        // Send header
        const headerEmbed = new EmbedBuilder()
            .setColor(0x00AE86)
            .setTitle(`🔍 Search Results for "${query}"`)
            .setDescription(`Found ${results.length} items\n\n💡 Use \`${prefix}jfplay <item-id>\` to play an item`)
            .setTimestamp();

        await channel.send({ embeds: [headerEmbed] });

        // Send each result as individual embed
        for (let i = 0; i < Math.min(results.length, 10); i++) {
            const item = results[i];
            await this.sendItemEmbed(channel, item, i + 1);
            
            if (i < Math.min(results.length, 10) - 1) {
                await new Promise(resolve => setTimeout(resolve, 500));
            }
        }

        if (results.length > 10) {
            const remainingEmbed = new EmbedBuilder()
                .setColor(0x00AE86)
                .setTitle('📋 Additional Results')
                .setDescription(`...and ${results.length - 10} more items. Refine your search for more specific results.`);
            
            await channel.send({ embeds: [remainingEmbed] });
        }
    }

    async sendShowsResults(channel: TextChannel, shows: JellyfinItem[], query: string, prefix: string): Promise<void> {
        if (shows.length === 0) {
            await channel.send(`❌ No TV shows found for "${query}"`);
            return;
        }

        // Send header
        const headerEmbed = new EmbedBuilder()
            .setColor(0x00AE86)
            .setTitle(`📺 TV Shows for "${query}"`)
            .setDescription(`Found ${shows.length} shows\n\n💡 Use \`${prefix}jfseasons <series-id>\` to see seasons\n📖 Use \`${prefix}jfinfo <series-id>\` for show details`)
            .setTimestamp();

        await channel.send({ embeds: [headerEmbed] });

        // Send each show with rich embed
        for (let i = 0; i < Math.min(shows.length, 8); i++) {
            const show = shows[i];
            await this.sendSeriesEmbed(channel, show, i + 1);
            
            if (i < Math.min(shows.length, 8) - 1) {
                await new Promise(resolve => setTimeout(resolve, 700));
            }
        }

        if (shows.length > 8) {
            const remaining = shows.slice(8);
            const remainingText = remaining.map((show, index) => 
                `${index + 9}. **${show.Name}** ${show.ProductionYear ? `(${show.ProductionYear})` : ''} - ID: \`${show.Id}\``
            ).join('\n');

            const remainingEmbed = new EmbedBuilder()
                .setColor(0x00AE86)
                .setTitle('📋 Additional Shows')
                .setDescription(remainingText.substring(0, 2000));
            
            await channel.send({ embeds: [remainingEmbed] });
        }
    }

    async sendSeasons(channel: TextChannel, seasons: JellyfinItem[], seriesName: string, prefix: string): Promise<void> {
        if (seasons.length === 0) {
            await channel.send(`❌ No seasons found for this series`);
            return;
        }

        const seasonsText = seasons.map((season, index) => {
            let text = `${index + 1}. **${season.Name}**`;
            if (season.ChildCount) {
                text += ` (${season.ChildCount} episodes)`;
            }
            text += ` - ID: \`${season.Id}\``;
            return text;
        }).join('\n');

        const embed = new EmbedBuilder()
            .setColor(0x00AE86)
            .setTitle(`📅 Seasons for "${seriesName}"`)
            .setDescription(`${seasonsText}\n\n💡 Use \`${prefix}jfepisodes <season-id>\` to see episodes`)
            .setTimestamp();

        await channel.send({ embeds: [embed] });
    }

    async sendEpisodes(channel: TextChannel, episodes: JellyfinItem[], seasonName: string, prefix: string): Promise<void> {
        if (episodes.length === 0) {
            await channel.send(`❌ No episodes found for this season`);
            return;
        }

        // Send header
        const headerEmbed = new EmbedBuilder()
            .setColor(0x00AE86)
            .setTitle(`🎬 Episodes in "${seasonName}"`)
            .setDescription(`${episodes.length} episodes\n\n💡 Use \`${prefix}jfplay <episode-id>\` to play an episode`)
            .setTimestamp();

        await channel.send({ embeds: [headerEmbed] });

        // Send each episode with rich embed
        for (let i = 0; i < Math.min(episodes.length, 10); i++) {
            const episode = episodes[i];
            await this.sendEpisodeEmbed(channel, episode, i + 1);
            
            if (i < Math.min(episodes.length, 10) - 1) {
                await new Promise(resolve => setTimeout(resolve, 500));
            }
        }

        if (episodes.length > 10) {
            const remaining = episodes.slice(10);
            const remainingText = remaining.map((ep, index) => {
                let text = `${index + 11}. `;
                if (ep.IndexNumber) text += `E${ep.IndexNumber}: `;
                text += `**${ep.Name}**`;
                if (ep.RunTimeTicks) {
                    const minutes = Math.round(ep.RunTimeTicks / 10000 / 1000 / 60);
                    text += ` (${minutes}m)`;
                }
                text += ` - ID: \`${ep.Id}\``;
                return text;
            }).join('\n');

            const remainingEmbed = new EmbedBuilder()
                .setColor(0x00AE86)
                .setTitle('📋 Additional Episodes')
                .setDescription(remainingText.substring(0, 2000));
            
            await channel.send({ embeds: [remainingEmbed] });
        }
    }

    private async sendItemEmbed(channel: TextChannel, item: JellyfinItem, index: number): Promise<void> {
        const embed = new EmbedBuilder()
            .setColor(0x00AE86);

        let title = `${index}. ${item.Name}`;
        if (item.Type === 'Episode' && item.SeriesName) {
            title = `${index}. ${item.SeriesName} - S${item.ParentIndexNumber || '?'}E${item.IndexNumber || '?'}: ${item.Name}`;
        }
        if (item.ProductionYear) {
            title += ` (${item.ProductionYear})`;
        }

        embed.setTitle(title);

        if (item.Overview) {
            const truncated = item.Overview.length > 200 
                ? item.Overview.substring(0, 200) + '...' 
                : item.Overview;
            embed.setDescription(truncated);
        }

        if (item.RunTimeTicks) {
            const minutes = Math.round(item.RunTimeTicks / 10000 / 1000 / 60);
            embed.addFields({ name: 'Duration', value: `${minutes} minutes`, inline: true });
        }

        embed.addFields({ name: 'ID', value: `\`${item.Id}\``, inline: true });
        embed.addFields({ name: 'Type', value: item.Type, inline: true });

        const thumbnailUrl = this.jellyfinClient.getBestThumbnailUrl(item);
        if (thumbnailUrl) {
            embed.setThumbnail(thumbnailUrl);
        }

        try {
            await channel.send({ embeds: [embed] });
        } catch (error) {
            logger.error(`Failed to send item embed for ${item.Name}:`, error);
            // Fallback to text message
            await channel.send(`${index}. **${item.Name}** - ID: \`${item.Id}\``);
        }
    }

    private async sendSeriesEmbed(channel: TextChannel, series: JellyfinItem, index: number): Promise<void> {
        const embed = new EmbedBuilder()
            .setColor(0x00AE86)
            .setTitle(`${index}. ${series.Name}`)
            .setTimestamp();

        if (series.Overview) {
            const truncated = series.Overview.length > 300 
                ? series.Overview.substring(0, 300) + '...' 
                : series.Overview;
            embed.setDescription(truncated);
        }

        if (series.ProductionYear) {
            embed.addFields({ name: 'Year', value: series.ProductionYear.toString(), inline: true });
        }

        if (series.ChildCount) {
            embed.addFields({ name: 'Seasons', value: series.ChildCount.toString(), inline: true });
        }

        embed.addFields({ name: 'ID', value: `\`${series.Id}\``, inline: true });

        const thumbnailUrl = this.jellyfinClient.getBestThumbnailUrl(series, 'series');
        if (thumbnailUrl) {
            embed.setThumbnail(thumbnailUrl);
        }

        try {
            await channel.send({ embeds: [embed] });
        } catch (error) {
            logger.error(`Failed to send series embed for ${series.Name}:`, error);
            await channel.send(`${index}. **${series.Name}** - ID: \`${series.Id}\``);
        }
    }

    private async sendEpisodeEmbed(channel: TextChannel, episode: JellyfinItem, index: number): Promise<void> {
        const embed = new EmbedBuilder()
            .setColor(0x00AE86)
            .setTimestamp();

        let title = `${index}. `;
        if (episode.IndexNumber) {
            title += `E${episode.IndexNumber}: `;
        }
        title += episode.Name;

        embed.setTitle(title);

        if (episode.SeriesName) {
            embed.setAuthor({ name: episode.SeriesName });
        }

        if (episode.Overview) {
            const truncated = episode.Overview.length > 300 
                ? episode.Overview.substring(0, 300) + '...' 
                : episode.Overview;
            embed.setDescription(truncated);
        }

        if (episode.RunTimeTicks) {
            const minutes = Math.round(episode.RunTimeTicks / 10000 / 1000 / 60);
            embed.addFields({ name: 'Duration', value: `${minutes} minutes`, inline: true });
        }

        embed.addFields({ name: 'ID', value: `\`${episode.Id}\``, inline: true });

        const thumbnailUrl = this.jellyfinClient.getBestThumbnailUrl(episode, 'episode');
        if (thumbnailUrl) {
            embed.setImage(thumbnailUrl); // Full-size image for episodes
        }

        try {
            await channel.send({ embeds: [embed] });
        } catch (error) {
            logger.error(`Failed to send episode embed for ${episode.Name}:`, error);
            await channel.send(`${index}. **${episode.Name}** - ID: \`${episode.Id}\``);
        }
    }
}