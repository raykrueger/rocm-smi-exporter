FROM debian:trixie-slim

RUN apt-get update && apt-get install -y curl gnupg python3 python3-pip libdrm-amdgpu1 pciutils && \
    ln -s /usr/lib/x86_64-linux-gnu/libdrm_amdgpu.so.1 /usr/lib/x86_64-linux-gnu/libdrm_amdgpu.so && \
    mkdir -p /etc/apt/keyrings && \
    curl -fsSL https://repo.radeon.com/rocm/rocm.gpg.key | gpg --dearmor -o /etc/apt/keyrings/rocm.gpg && \
    echo "deb [arch=amd64 signed-by=/etc/apt/keyrings/rocm.gpg] https://repo.radeon.com/rocm/apt/latest noble main" > /etc/apt/sources.list.d/rocm.list && \
    apt-get update && apt-get install -y rocm-smi-lib && \
    rm -rf /var/lib/apt/lists/*

ENV PATH="/opt/rocm/bin:${PATH}"

WORKDIR /app
COPY pyproject.toml ./
COPY rocm_smi_exporter/ ./rocm_smi_exporter/
RUN pip3 install --no-cache-dir --break-system-packages .

EXPOSE 9393
CMD ["rocm-smi-exporter"]

# Optional: activate mock rocm-smi for testing without GPU hardware.
ARG USE_MOCK_DATA
COPY tests/fixtures/rocm_smi_all.json tests/fixtures/rocm_smi_vram.json /mock-data/
COPY tests/fixtures/rocm-smi /mock-rocm-smi
RUN if [ -n "$USE_MOCK_DATA" ]; then \
    cp /mock-rocm-smi /opt/rocm/bin/rocm-smi && \
    chmod +x /opt/rocm/bin/rocm-smi; \
    fi
