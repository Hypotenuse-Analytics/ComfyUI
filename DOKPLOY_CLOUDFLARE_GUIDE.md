# Deploying Hypotenuse-Analytics/ComfyUI with Dokploy & Cloudflare Zero Trust

This guide explains how to deploy **Hypotenuse-Analytics/ComfyUI** on an AWS EC2 `g5.2xlarge` instance using **Dokploy** and securing public access via **Cloudflare Zero Trust / Access**.

---

## 1. AWS EC2 `g5.2xlarge` Instance Setup (GPU Prerequisites)

Ensure your target VM (where Dokploy runs or your application server VM) has the **NVIDIA Container Toolkit** installed so Docker containers can access the A10G GPU (24GB VRAM).

```bash
# 1. Update system & verify GPU presence
sudo apt update && sudo apt install -y nvidia-driver-535 nvidia-utils-535
nvidia-smi

# 2. Install NVIDIA Container Toolkit for Docker
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg \
  && curl -s -L https://nvidia.github.io/libnvidia-container/experimental/ubuntu22.04/nvidia-container-toolkit.list | \
    sed 's#deb [^ ]* #&[signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] #' | \
    sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list

sudo apt update && sudo apt install -y nvidia-container-toolkit

# 3. Configure Docker runtime for NVIDIA & restart Docker
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker
```

---

## 2. Dokploy Deployment Steps

1. **Push Changes to GitHub**:
   Ensure [`Dockerfile`](file:///e:/ha_others/comfyui/Dockerfile), [`docker-compose.yml`](file:///e:/ha_others/comfyui/docker-compose.yml), and [`.dockerignore`](file:///e:/ha_others/comfyui/.dockerignore) are committed and pushed to `https://github.com/Hypotenuse-Analytics/ComfyUI.git`.

2. **Create Compose Application in Dokploy**:
   - In Dokploy, click **Create Application** -> **Compose**.
   - Provider: **GitHub**.
   - Repository: `Hypotenuse-Analytics/ComfyUI`.
   - Branch: `master` (or main).
   - Docker Compose Path: `docker-compose.yml`.

3. **Configure Domain & Ports**:
   - Domain: e.g. `comfyui.hypotenuse.ai` (or your Cloudflare-connected domain).
   - Container Port: `8188`.
   - Enable SSL / Traefik routing in Dokploy.

4. **Deploy**:
   - Click **Deploy**. Dokploy will build the Docker container with CUDA 12.1 + PyTorch, reserve the NVIDIA A10G GPU, and launch ComfyUI on port 8188.

---

## 3. Securing ComfyUI with Cloudflare Zero Trust / Access

Since standard ComfyUI lacks user authentication, using Cloudflare Access ensures **only authorized team members or authenticated users** can access the website.

### Step A: Point Domain to Dokploy VM
1. In **Cloudflare DNS**, add an `A` record pointing `comfyui.yourdomain.com` to your EC2 / Dokploy Public IP (or set up a Cloudflare Tunnel `cloudflared`).
2. Ensure proxy status is set to **Proxied (Orange Cloud)**.

### Step B: Create a Cloudflare Access Application
1. Go to **Cloudflare Zero Trust Dashboard** (`dash.teams.cloudflare.com`).
2. Navigate to **Access** -> **Applications** -> **Add an Application**.
3. Choose **Self-hosted**.
4. Configure Application Details:
   - **Application Name**: `ComfyUI`
   - **Session Duration**: e.g., 24 hours
   - **Application Domain**: `comfyui.yourdomain.com`
5. Create an **Access Policy**:
   - **Policy Name**: `Team Access`
   - **Action**: `Allow`
   - **Include Rule**: Emails (`@yourdomain.com`), Specific Email Addresses, or GitHub/Google SSO Identity Providers.
6. Save Application.

Now, whenever anyone navigates to `https://comfyui.yourdomain.com`, Cloudflare Zero Trust will intercept the request and demand a secure login (One-Time PIN or SSO) before forwarding traffic to your ComfyUI server!

---

## 4. EBS Model Volume Storage (Optional but Recommended)

To ensure large checkpoint models (SDXL, Flux, Wan 2.1) do not get deleted when rebuilding containers:
- Mount an AWS EBS volume (e.g. 500GB GP3) to `/mnt/comfy_models` on the EC2 host.
- In `docker-compose.yml`, map `/mnt/comfy_models:/app/models`.
