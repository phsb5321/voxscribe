# Stage 1: Build dependencies
FROM ubuntu:22.04 as builder

# Set non-interactive installation
ENV DEBIAN_FRONTEND=noninteractive

# Setup DNS and apt configuration
RUN echo "nameserver 8.8.8.8" > /etc/resolv.conf && \
  echo "nameserver 8.8.4.4" >> /etc/resolv.conf

# Install Python and build dependencies
RUN apt-get update && apt-get install -y \
  python3.11 \
  python3-pip \
  python3-venv \
  gcc \
  libc6-dev \
  libportaudio2 \
  libsndfile1 \
  ffmpeg \
  libasound2-dev \
  && rm -rf /var/lib/apt/lists/*

# Set up virtual environment
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Stage 2: Runtime image
FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

# Setup DNS
RUN echo "nameserver 8.8.8.8" > /etc/resolv.conf && \
  echo "nameserver 8.8.4.4" >> /etc/resolv.conf

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
  python3.11 \
  libportaudio2 \
  libsndfile1 \
  ffmpeg \
  && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder stage
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH" \
  PYTHONUNBUFFERED=1 \
  PYTHONIOENCODING=utf8

WORKDIR /app

# Copy application code
COPY main.py /app/

# Create data directory
RUN mkdir -p /app/DATA && \
  chown -R 1000:1000 /app && \
  chmod 755 /app/DATA

# Create and switch to non-root user
RUN useradd -u 1000 -m appuser && \
  chown -R appuser:appuser /app
USER appuser

CMD ["python3", "main.py"]