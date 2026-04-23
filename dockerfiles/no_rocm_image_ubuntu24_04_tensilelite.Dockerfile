FROM ghcr.io/rocm/no_rocm_image_ubuntu24_04:latest

# HIP headers, compiler, and runtime for rocisa/origami compile-time use (no GPU driver).
# Pin ROCm repo priority higher than Ubuntu to get version-matched hipcc.
RUN curl -sL https://repo.radeon.com/rocm/rocm.gpg.key | sudo gpg --dearmor -o /etc/apt/keyrings/rocm.gpg \
    && echo "deb [arch=amd64 signed-by=/etc/apt/keyrings/rocm.gpg] https://repo.radeon.com/rocm/apt/latest noble main" \
        | sudo tee /etc/apt/sources.list.d/rocm.list \
    && echo 'Package: *\nPin: origin repo.radeon.com\nPin-Priority: 600' \
        | sudo tee /etc/apt/preferences.d/rocm-pin-600 \
    && sudo apt-get update -y \
    && sudo apt-get install -y --no-install-recommends \
        hip-dev hip-runtime-amd hipcc rocm-core rocm-device-libs rocminfo libclang-rt-18-dev \
    && sudo rm -rf /var/lib/apt/lists/*
