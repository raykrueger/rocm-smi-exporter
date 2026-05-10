# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A Prometheus exporter for AMD GPUs via `rocm-smi`. Runs as a container or standalone binary. Exposes metrics on port `9393`.

The entire exporter logic is in `main.py`. There are no tests.

## Development workflow

**Local run** (requires ROCm on the host):
```sh
pip install -r requirements.txt
python main.py
```

**Build and test via Docker** (preferred — no local ROCm needed):
```sh
# Sync to a machine with an AMD GPU and build there
rsync -av --exclude='.git' ./ <host>:/tmp/rocm-smi-exporter/
ssh <host> "docker build -t rocm-smi-exporter:test /tmp/rocm-smi-exporter/"
ssh <host> "docker run --rm --gpus driver=amd,count=all,capabilities=gpu -p 9394:9393 rocm-smi-exporter:test"
ssh <host> "curl -s http://localhost:9394/metrics | grep rocm_smi"
```

**Build standalone binary**:
```sh
pip install -r requirements-build.txt
pyinstaller main.spec
# Binary lands in dist/rocm-smi-exporter
```

## Releases

Releases are managed by [release-please](https://github.com/googleapis/release-please). Use conventional commits on `main` — release-please opens a PR that bumps the version and updates `CHANGELOG.md` automatically. Merging that PR creates a GitHub Release, which triggers both CI workflows.

- `build.yml` — builds Docker image, pushes to GHCR (`ghcr.io/raykrueger/rocm-smi-exporter`)
- `release.yml` — builds PyInstaller binary, creates GitHub Release tarball

Do not manually tag or edit `CHANGELOG.md`.

## Adding metrics

`rocm-smi -a --json` is the primary data source. A second call `rocm-smi --showmeminfo vram --json` provides VRAM byte counts; its output is merged into the same card dict in `getGPUMetrics()`.

To add a new metric:
1. Check `rocm-smi -a --json` output for the field name (run on a machine with an AMD GPU)
2. Add a `Gauge(...)` at module level with `LABELS`
3. Call `.labels(**labels).set(floatOrZero(c.get('Field Name')))` in the main loop
4. If the field may be `'N/A'`, `floatOrZero()` handles it safely

## Device name resolution

`rocm-smi` may return `'N/A'` or `'AMD Radeon Graphics'` inside containers. `resolveDeviceName()` falls back to `DEVICE_NAME_FALLBACKS` keyed by lowercase device ID hex string (e.g. `'0x7551'`). Add entries there for any GPU that returns a generic name.

## Docker notes

GPU access uses `deploy.resources.reservations.devices` with `driver: amd` — no privileged mode needed. The Dockerfile installs `rocm-smi-lib` from AMD's Ubuntu `noble` apt repo (same channel the host uses), despite the `debian:trixie-slim` base. The `libdrm_amdgpu.so` symlink is required for device name resolution.
