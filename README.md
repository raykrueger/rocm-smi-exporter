![GitHub Release](https://img.shields.io/github/v/release/raykrueger/rocm-smi-exporter)

![GitHub Actions Workflow Status](https://img.shields.io/github/actions/workflow/status/raykrueger/rocm-smi-exporter/build.yml)

# rocm-smi-exporter
A Prometheus exporter for rocm-smi

## This fork

Forked from [rudimk/rocm-smi-exporter](https://github.com/rudimk/rocm-smi-exporter) — thanks to Rudi MK for the original work. The upstream project appears unmaintained as of late 2024. This fork adds:

- **Power metric fix** — the original hardcodes `Current Socket Graphics Package Power (W)`, which is absent on RDNA GPUs (e.g. Radeon RX/Pro). This fork falls back to `Average Graphics Package Power (W)` and `average_socket_power (W)` before defaulting to 0. Backwards compatible with Instinct cards that expose the original field.
- **Dockerfile** — run the exporter as a container based on `debian:trixie-slim` with AMD's ROCm apt repo. AMD GPU access via Docker's `driver=amd` device reservation; no privileged mode required.
- **Device name fallback** — newer RDNA GPUs (e.g. Radeon AI PRO R9700) may return generic names inside containers. A hardcoded fallback table keyed by device ID fills in the correct name when `rocm-smi` can't resolve it.

This exporter piggybacks on `rocm-smi` and exports the following metrics as Prometheus `Gauges` for AMD GPUs:

| Metric | Description | Unit |
|--------|-------------|------|
| `rocm_smi_edge_temperature` | GPU edge temperature | °C |
| `rocm_smi_junction_temperature` | GPU junction/hotspot temperature | °C |
| `rocm_smi_memory_temperature` | GPU memory temperature | °C |
| `rocm_smi_socket_power` | GPU socket power consumption | W |
| `rocm_smi_power_cap` | GPU maximum power cap | W |
| `rocm_smi_gpu_usage` | GPU utilization | % |
| `rocm_smi_gpu_vram_allocation` | VRAM allocation | % |
| `rocm_smi_memory_activity` | Memory read/write bus activity | % |
| `rocm_smi_fan_rpm` | Fan speed | RPM |
| `rocm_smi_fan_speed` | Fan speed | % |
| `rocm_smi_gfx_clock` | Shader (GFX) clock | MHz |
| `rocm_smi_memory_clock` | Memory clock | MHz |
| `rocm_smi_throttle_status` | Throttle status (0 = normal) | — |
| `rocm_smi_vram_used_bytes` | VRAM used | bytes |
| `rocm_smi_vram_total_bytes` | VRAM total capacity | bytes |

All gauges carry the following labels:
- `device_id`
- `device_name`
- `subsystem_id`

## Docker

### Build

```sh
docker build -t rocm-smi-exporter .
```

### Run

```sh
docker run -d --gpus driver=amd,count=all,capabilities=gpu -p 9393:9393 rocm-smi-exporter
```

### Docker Compose

```yaml
services:
  rocm-smi-exporter:
    image: rocm-smi-exporter
    restart: unless-stopped
    ports:
      - "9393:9393"
    deploy:
      resources:
        reservations:
          devices:
            - driver: amd
              count: all
              capabilities: [gpu]
```

No privileged mode required.

## Prerequisites

1. A Linux server with an AMD iGPU/GPU present.
2. ROCm installed. You can refer to the official docs maintained by AMD [here](https://rocm.docs.amd.com/projects/install-on-linux/en/latest/install/quick-start.html#rocm-install-quick).
3. For container use: Docker with AMD GPU support configured. See [Running ROCm Docker containers](https://rocm.docs.amd.com/projects/install-on-linux/en/latest/how-to/docker.html).



## Running

You can find the latest release at [https://github.com/raykrueger/rocm-smi-exporter/releases](https://github.com/raykrueger/rocm-smi-exporter/releases). Download the tarball, extract the exporter to `/usr/local/bin/` and you're good to go. To run the exporter as a `systemd` job, feel free to use the following template:

```
[Unit]
Description=ROCm SMI Exporter
Wants=network-online.target
After=network-online.target

[Service]
ExecStart=/usr/local/bin/rocm-smi-exporter
Restart=always

[Install]
WantedBy=multi-user.target
```

Also, don't forget to add a rule for scraping the exporter from Prometheus:

```yaml
scrape_configs:
# Existing configuration
  - job_name: "rocm-smi-exporter"
    static_configs:
      - targets: ["localhost:9393"]
```

## Build instructions

1. Clone this repo
2. Install runtime dependencies: `pip install -r requirements.txt`
3. Run: `python main.py`
4. To compile a binary: `pip install -r requirements-build.txt && pyinstaller main.spec`

The compiled binary can be found in `dist/` — move it to `/usr/local/bin`.

## Grafana Dashboard

A sample Grafana dashboard's available inside the `grafana/` directory. 

![real-time-metrics](https://github.com/user-attachments/assets/f0d39a79-bc9c-4d93-ae98-d20df6a43b1f)

![historical-metrics](https://github.com/user-attachments/assets/bbd77548-0088-4802-bf4b-c281e4f6ae22)