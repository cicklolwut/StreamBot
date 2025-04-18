# Running StreamBot in Docker

This guide explains how to run StreamBot in a Docker container for easier deployment and isolation.

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) installed on your system
- [Docker Compose](https://docs.docker.com/compose/install/) (optional but recommended)
- Basic knowledge of Docker and containerization

## Setup Instructions

### 1. Prepare Your Environment

First, create a directory structure for your StreamBot Docker setup:

```bash
mkdir -p streambot/videos streambot/tmp/preview-cache
cd streambot
```

### 2. Copy the Required Files

Copy the following files to your `streambot` directory:

- `Dockerfile`
- `docker-compose.yml`
- All Python files (main_bot.py, db_utils.py, hw_accel.py, selfbot_embeds.py)
- `schema.sql`
- `requirements.txt`

### 3. Create Configuration File

Create a `config.json` file in your `streambot` directory. You can use the example below:

```json
{
  "token": "YOUR_DISCORD_TOKEN_HERE",
  "prefix": "$",
  "guild_id": "YOUR_GUILD_ID",
  "command_channel_id": "YOUR_COMMAND_CHANNEL_ID",
  "video_channel_id": "YOUR_VIDEO_CHANNEL_ID",
  "videos_dir": "/app/videos",
  "db_path": "/app/streambot.db",
  "ffmpeg_path": "ffmpeg",
  "preview_cache_dir": "/app/tmp/preview-cache",
  "stream_respect_video_params": false,
  "stream_width": 1280,
  "stream_height": 720,
  "stream_fps": 30,
  "stream_bitrate_kbps": 2000,
  "stream_max_bitrate_kbps": 2500,
  "stream_h26x_preset": "ultrafast",
  "hw_accel_enabled": true,
  "transcode_enabled": false
}
```

Note that the paths are set to `/app/` because that's the working directory inside the Docker container.

### 4. Hardware Acceleration (Optional)

If you want to use hardware acceleration, you'll need to configure it based on your GPU:

#### NVIDIA GPU

Uncomment the NVIDIA GPU configuration in `docker-compose.yml`:

```yaml
deploy:
  resources:
    reservations:
      devices:
        - driver: nvidia
          count: all
          capabilities: [gpu]
```

Make sure you have the [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html) installed.

#### Intel GPU

Uncomment the Intel QuickSync configuration in `docker-compose.yml`:

```yaml
devices:
  - /dev/dri:/dev/dri
```

#### AMD GPU

Uncomment the AMD GPU configuration in `docker-compose.yml`:

```yaml
devices:
  - /dev/kfd:/dev/kfd
  - /dev/dri:/dev/dri
```

### 5. Build and Start the Container

#### Using Docker Compose (Recommended)

```bash
docker-compose up -d
```

This will build the image and start the container in detached mode.

#### Using Docker CLI

If you're not using Docker Compose:

```bash
# Build the image
docker build -t streambot .

# Run the container
docker run -d \
  --name streambot \
  -v $(pwd)/config.json:/app/config.json \
  -v $(pwd)/streambot.db:/app/streambot.db \
  -v $(pwd)/videos:/app/videos \
  -v $(pwd)/tmp:/app/tmp \
  --restart unless-stopped \
  streambot
```

### 6. View Logs

To check the logs of your running container:

```bash
docker logs -f streambot
```

### 7. Add Videos

Place your videos in the `videos` directory on your host machine. They will be automatically available to the bot inside the container.

## Maintenance

### Stopping the Container

```bash
docker-compose down
```

or

```bash
docker stop streambot
```

### Updating the Bot

1. Pull the latest code changes
2. Rebuild the container:

```bash
docker-compose build
docker-compose up -d
```

or

```bash
docker build -t streambot .
docker stop streambot
docker rm streambot
docker run -d [same options as above] streambot
```

## Troubleshooting

### Permission Issues

If you encounter permission issues with volumes:

```bash
sudo chown -R 1000:1000 ./videos ./tmp
```

### FFmpeg Hardware Acceleration

If hardware acceleration isn't working, you may need to install additional drivers in the Dockerfile or map additional devices to the container.

### Database Issues

If the database isn't persisting between container restarts, ensure the volume mount for `streambot.db` is correct.
