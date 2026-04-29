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
COPY requirements.txt .
RUN pip3 install --no-cache-dir --break-system-packages prometheus_client

COPY main.py .

EXPOSE 9393
CMD ["python3", "main.py"]
