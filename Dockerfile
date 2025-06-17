# Use official Python 3.11 slim image (this has Python 3.11.13)
FROM python:3.11-slim

# Avoid warnings by setting env vars
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies Streamlit needs (including imghdr deps)
RUN apt-get update && apt-get install -y \
    build-essential \
    libjpeg-dev \
    libpng-dev \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user "vscode"
RUN useradd -ms /bin/bash vscode

USER vscode
WORKDIR /workspace

# Upgrade pip (will be run again in postCreateCommand, but harmless here)
RUN python3 -m pip install --upgrade pip

# Copy requirements so devcontainer.json can run pip install on them
COPY --chown=vscode:vscode requirements.txt /workspace/

# Default command
CMD ["bash"]
