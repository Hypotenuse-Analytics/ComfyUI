FROM nvidia/cuda:12.1.1-cudnn8-runtime-ubuntu22.04

# Prevent interactive prompts during installation
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

# Install system dependencies & Python 3.10
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    python3-dev \
    git \
    wget \
    curl \
    ffmpeg \
    libsm6 \
    libxext6 \
    glib2.0-0 \
    libgl1-mesa-glx \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Set python alias
RUN ln -s /usr/bin/python3 /usr/bin/python

# Set working directory
WORKDIR /app

# Upgrade pip, setuptools, wheel
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Pre-install PyTorch with CUDA 12.1 support for optimal GPU performance
RUN pip install --no-cache-dir torch torchvision torchaudio --extra-index-url https://download.pytorch.org/whl/cu121

# Copy requirements file first for layer caching
COPY requirements.txt .

# Install ComfyUI dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy source repository
COPY . .

# Comfy CLI (permanent, installed into the container's Python env)
RUN pip install --no-cache-dir comfy-cli && comfy set-default /app

# ComfyUI-Manager v4 (required by current ComfyUI core)
RUN pip install --no-cache-dir "comfyui-manager>=4.2.1"

# Expose default ComfyUI port
EXPOSE 8188

# Entrypoint to start ComfyUI listening on all interfaces
CMD ["python", "main.py", "--listen", "0.0.0.0", "--port", "8188", "--enable-cors-header", "--enable-manager", "--preview-method", "auto", "--use-pytorch-cross-attention"]
