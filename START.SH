#!/bin/bash

# Define image name
IMAGE_NAME="audio-transcriber"

# Check if image already exists
if [[ "$(docker images -q $IMAGE_NAME 2>/dev/null)" == "" ]]; then
  echo "Image $IMAGE_NAME not found. Building image..."
  docker build -t $IMAGE_NAME .
else
  echo "Image $IMAGE_NAME already exists. Skipping build..."
fi

# Check if current directory is valid for Docker volume
if [[ ! -d $(pwd) ]]; then
  echo "Error: Current directory does not exist."
  exit 1
fi

# Run the web server
docker run -p 5000:5000 -v "$(pwd)/DATA:/app/DATA" \
  -e TRANSCRIPTION_ENGINE="${TRANSCRIPTION_ENGINE:-faster-whisper}" \
  -e REDIS_URL="${REDIS_URL:-redis://localhost:6379}" \
  $IMAGE_NAME
