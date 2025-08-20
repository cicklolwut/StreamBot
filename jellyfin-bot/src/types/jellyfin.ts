export interface JellyfinConfig {
    baseUrl: string;
    apiKey: string;
    userId?: string;
    libraryId?: string;
}

export interface JellyfinItem {
    Id: string;
    Name: string;
    Type: string;
    MediaType?: string;
    Path?: string;
    RunTimeTicks?: number;
    ProductionYear?: number;
    Overview?: string;
    SeriesName?: string;
    SeasonName?: string;
    IndexNumber?: number;
    ParentIndexNumber?: number;
    SeriesId?: string;
    SeasonId?: string;
    ParentId?: string;
    ChildCount?: number;
    ImageTags?: {
        Primary?: string;
        Backdrop?: string;
        Logo?: string;
        Thumb?: string;
    };
    BackdropImageTags?: string[];
    MediaSources?: JellyfinMediaSource[];
}

export interface JellyfinMediaSource {
    Id: string;
    Path: string;
    Protocol: string;
    Container: string;
    Size: number;
    Name: string;
    IsRemote: boolean;
    HasMixedProtocols: boolean;
}

export interface JellyfinSearchResult {
    Items: JellyfinItem[];
    TotalRecordCount: number;
    StartIndex: number;
}

export type JellyfinItemType = 
    | 'Movie' 
    | 'Series' 
    | 'Season' 
    | 'Episode' 
    | 'Audio' 
    | 'MusicAlbum' 
    | 'MusicArtist' 
    | 'Video' 
    | 'AudioBook';

export interface APIRequest {
    action: 'search' | 'searchShows' | 'getSeasons' | 'getEpisodes' | 'getItem' | 'getRecent';
    channelId: string;
    data: any;
}

export interface APIResponse {
    success: boolean;
    message?: string;
    data?: any;
}