#!/bin/bash

# StreamBot Docker setup script
echo "=== StreamBot Docker Setup ==="
echo

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "Error: Docker is not installed. Please install Docker first."
    echo "Visit https://docs.docker.com/get-docker/ for installation instructions."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "Warning: Docker Compose is not installed."
    echo "It's recommended to install Docker Compose for easier management."
    echo "Visit https://docs.docker.com/compose/install/ for installation instructions."
    echo
    USE_COMPOSE=false
else
    USE_COMPOSE=true
fi

# Create necessary directories
echo "Creating directories..."
mkdir -p videos tmp/preview-cache
echo "Done."
echo

# Check if config.json exists
if [ ! -f config.json ]; then
    echo "Configuration file not found. Creating a template..."
    cat > config.json << EOL
{
  "token": "",
  "prefix": "$",
  "guild_id": "",
  "command_channel_id": "",
  "video_channel_id": "",
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
EOL
    echo "Created config.json template."
    echo "Please edit config.json and add your Discord token and other settings."
    echo
fi

# Detect hardware acceleration
echo "Detecting hardware acceleration options..."
HW_ACCEL_OPTION=""

# Check for NVIDIA GPUs
if command -v nvidia-smi &> /dev/null; then
    echo "NVIDIA GPU detected."
    
    # Check for NVIDIA Container Toolkit
    if docker info | grep -q "Runtimes:.*nvidia"; then
        echo "NVIDIA Container Toolkit is installed."
        HW_ACCEL_OPTION="nvidia"
    else
        echo "NVIDIA Container Toolkit is not installed."
        echo "Visit https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html"
        echo "to install it for hardware acceleration."
    fi
fi

# Check for Intel GPU
if [ -d "/dev/dri" ]; then
    if lspci | grep -i 'vga.*intel' &> /dev/null; then
        echo "Intel GPU detected."
        if [ -z "$HW_ACCEL_OPTION" ]; then
            HW_ACCEL_OPTION="intel"
        fi
    fi
fi

# Check for AMD GPU
if [ -d "/dev/dri" ]; then
    if lspci | grep -i 'vga.*amd' &> /dev/null; then
        echo "AMD GPU detected."
        if [ -z "$HW_ACCEL_OPTION" ]; then
            HW_ACCEL_OPTION="amd"
        fi
    fi
fi

# Update docker-compose.yml with hardware acceleration options
if [ -n "$HW_ACCEL_OPTION" ]; then
    echo "Enabling $HW_ACCEL_OPTION hardware acceleration in docker-compose.yml..."
    
    # Make a backup of the original file
    cp docker-compose.yml docker-compose.yml.bak
    
    if [ "$HW_ACCEL_OPTION" = "nvidia" ]; then
        sed -i 's/# deploy:/deploy:/g' docker-compose.yml
        sed -i 's/#   resources:/  resources:/g' docker-compose.yml
        sed -i 's/#     reservations:/    reservations:/g' docker-compose.yml
        sed -i 's/#       devices:/      devices:/g' docker-compose.yml
        sed -i 's/#         - driver: nvidia/        - driver: nvidia/g' docker-compose.yml
        sed -i 's/#           count: all/          count: all/g' docker-compose.yml
        sed -i 's/#           capabilities: \[gpu\]/          capabilities: [gpu]/g' docker-compose.yml
    elif [ "$HW_ACCEL_OPTION" = "intel" ]; then
        sed -i 's/# devices:/devices:/g' docker-compose.yml
        sed -i 's/#   - \/dev\/dri:\/dev\/dri/  - \/dev\/dri:\/dev\/dri/g' docker-compose.yml
    elif [ "$HW_ACCEL_OPTION" = "amd" ]; then
        sed -i 's/# devices:/devices:/g' docker-compose.yml
        sed -i 's/#   - \/dev\/kfd:\/dev\/kfd/  - \/dev\/kfd:\/dev\/kfd/g' docker-compose.yml
        sed -i 's/#   - \/dev\/dri:\/dev\/dri/  - \/dev\/dri:\/dev\/dri/g' docker-compose.yml
    fi
    
    echo "Hardware acceleration enabled in docker-compose.yml."
else
    echo "No compatible GPU detected for hardware acceleration."
    echo "The bot will use software encoding."
fi

echo
echo "Setup complete!"
echo

# Build and start the container
if [ "$USE_COMPOSE" = true ]; then
    echo "Building and starting the container with Docker Compose..."
    docker-compose up -d
    echo
    echo "StreamBot is now running in a Docker container."
    echo "You can view the logs with: docker-compose logs -f"
else
    echo "Building the Docker image..."
    docker build -t streambot .
    
    echo "Starting the container..."
    if [ "$HW_ACCEL_OPTION" = "nvidia" ]; then
        docker run -d \
            --name streambot \
            --gpus all \
            -v $(pwd)/config.json:/app/config.json \
            -v $(pwd)/streambot.db:/app/streambot.db \
            -v $(pwd)/videos:/app/videos \
            -v $(pwd)/tmp:/app/tmp \
            --restart unless-stopped \
            streambot
    elif [ "$HW_ACCEL_OPTION" = "intel" ] || [ "$HW_ACCEL_OPTION" = "amd" ]; then
        docker run -d \
            --name streambot \
            --device /dev/dri:/dev/dri \
            -v $(pwd)/config.json:/app/config.json \
            -v $(pwd)/streambot.db:/app/streambot.db \
            -v $(pwd)/videos:/app/videos \
            -v $(pwd)/tmp:/app/tmp \
            --restart unless-stopped \
            streambot
    else
        docker run -d \
            --name streambot \
            -v $(pwd)/config.json:/app/config.json \
            -v $(pwd)/streambot.db:/app/streambot.db \
            -v $(pwd)/videos:/app/videos \
            -v $(pwd)/tmp:/app/tmp \
            --restart unless-stopped \
            streambot
    fi
    
    echo
    echo "StreamBot is now running in a Docker container."
    echo "You can view the logs with: docker logs -f streambot"
fi

echo
echo "Put your videos in the 'videos' directory."
echo "The bot will automatically detect and categorize them."
echo
echo "Remember to edit config.json with your Discord token before starting the bot!"
