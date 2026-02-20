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

# Run the container
docker run -v $(pwd):/app $IMAGE_NAME
