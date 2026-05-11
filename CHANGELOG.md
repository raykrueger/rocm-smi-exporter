# Changelog

## [2.4.1](https://github.com/raykrueger/rocm-smi-exporter/compare/v2.4.0...v2.4.1) (2026-05-11)


### Bug Fixes

* use PAT in release-please to trigger downstream workflows ([ae1fc71](https://github.com/raykrueger/rocm-smi-exporter/commit/ae1fc718c8b715387d9659a1975a11962f6f0eab))


### Documentation

* fix README install instructions to use git clone ([374d664](https://github.com/raykrueger/rocm-smi-exporter/commit/374d664011f486c7bd4bf680406bd9b61682acf2))

## [2.4.0](https://github.com/raykrueger/rocm-smi-exporter/compare/v2.3.1...v2.4.0) (2026-05-11)


### Features

* convert to pip-installable package with pyproject.toml ([8f0b35d](https://github.com/raykrueger/rocm-smi-exporter/commit/8f0b35d70b2b20f424e07ab398facc2d9c1b022d))


### Bug Fixes

* trigger build workflow on tag push instead of release event ([38dc5c2](https://github.com/raykrueger/rocm-smi-exporter/commit/38dc5c2bde5a8d814071bdd871eda4d898a64860))

## [2.3.1](https://github.com/raykrueger/rocm-smi-exporter/compare/v2.3.0...v2.3.1) (2026-05-11)


### Bug Fixes

* handle SIGTERM/SIGINT for graceful shutdown ([1dc79d5](https://github.com/raykrueger/rocm-smi-exporter/commit/1dc79d5a2a2919f4b2ea2054729602d3a4dfc260))

## [2.3.0](https://github.com/raykrueger/rocm-smi-exporter/compare/v2.2.2...v2.3.0) (2026-05-10)


### Features

* add fan, clock, temperature, throttle, and power cap metrics ([dd392a6](https://github.com/raykrueger/rocm-smi-exporter/commit/dd392a685dea696a30828dd5d01564902508e219))
* add VRAM used/total byte metrics ([d52a60a](https://github.com/raykrueger/rocm-smi-exporter/commit/d52a60a9b4b673c3c398f2892e374834820de7d3))


### Bug Fixes

* handle empty/invalid JSON from rocm-smi when GPU is in BACO state ([4c62932](https://github.com/raykrueger/rocm-smi-exporter/commit/4c62932f164c46a74b867d4624297b06f1cc1012))
* handle empty/invalid JSON from rocm-smi when GPU is in BACO state ([fef220a](https://github.com/raykrueger/rocm-smi-exporter/commit/fef220a73b0413fe1e52ea27718d7df5bbe33e2f)), closes [#1](https://github.com/raykrueger/rocm-smi-exporter/issues/1)
* trigger build and release on GitHub release event, update Grafana dashboard ([3b68d4f](https://github.com/raykrueger/rocm-smi-exporter/commit/3b68d4fce6313b630e6c016e197e25c45d5ea5e1))

## [2.2.2](https://github.com/raykrueger/rocm-smi-exporter/compare/v2.2.1...v2.2.2) (2026-05-10)


### Bug Fixes

* handle empty/invalid JSON from rocm-smi when GPU is in BACO state ([4c62932](https://github.com/raykrueger/rocm-smi-exporter/commit/4c62932f164c46a74b867d4624297b06f1cc1012))
* handle empty/invalid JSON from rocm-smi when GPU is in BACO state ([fef220a](https://github.com/raykrueger/rocm-smi-exporter/commit/fef220a73b0413fe1e52ea27718d7df5bbe33e2f)), closes [#1](https://github.com/raykrueger/rocm-smi-exporter/issues/1)
* trigger build and release on GitHub release event, update Grafana dashboard ([3b68d4f](https://github.com/raykrueger/rocm-smi-exporter/commit/3b68d4fce6313b630e6c016e197e25c45d5ea5e1))

## [2.2.1](https://github.com/raykrueger/rocm-smi-exporter/compare/v2.2.0...v2.2.1) (2026-04-29)

### Chores

- Bump `prometheus_client` 0.20.0 → 0.25.0
- Bump `pyinstaller` 6.10.0 → 6.20.0
- Bump `pyinstaller-hooks-contrib` 2024.8 → 2026.4
- Bump `packaging` 24.1 → 26.2
- Bump `setuptools` 74.1.2 → 82.0.1
- Bump `altgraph` 0.17.4 → 0.17.5

## [2.2.0](https://github.com/raykrueger/rocm-smi-exporter/compare/v2.1.0...v2.2.0) (2026-04-29)

### Features

- `rocm_smi_vram_used_bytes` — VRAM used in bytes
- `rocm_smi_vram_total_bytes` — VRAM total capacity in bytes

## [2.1.0](https://github.com/raykrueger/rocm-smi-exporter/compare/v2.0.1...v2.1.0) (2026-04-29)

### Features

- `rocm_smi_junction_temperature` — GPU junction/hotspot temperature (°C)
- `rocm_smi_memory_temperature` — GPU memory temperature (°C)
- `rocm_smi_power_cap` — GPU maximum power cap (W)
- `rocm_smi_memory_activity` — Memory read/write bus activity (%)
- `rocm_smi_fan_rpm` — Fan speed (RPM)
- `rocm_smi_fan_speed` — Fan speed (%)
- `rocm_smi_gfx_clock` — Shader/GFX clock (MHz)
- `rocm_smi_memory_clock` — Memory clock (MHz)
- `rocm_smi_throttle_status` — Throttle status (0 = normal)
- `floatOrZero()` helper to safely handle N/A values from rocm-smi

## [2.0.1](https://github.com/raykrueger/rocm-smi-exporter/compare/v2.0.0...v2.0.1) (2026-04-29)

### Features

- Dockerfile: install `pciutils` and `libdrm-amdgpu1` with `.so` symlink for GPU device name resolution
- Device name fallback table (`DEVICE_NAME_FALLBACKS`) keyed by device ID for GPUs that return generic names inside containers (e.g. Radeon AI PRO R9700 → `0x7551`)

### Bug Fixes

- Device name reported as `N/A` or `AMD Radeon Graphics` in containers — resolved via libdrm + fallback table

## [2.0.0](https://github.com/raykrueger/rocm-smi-exporter/releases/tag/v2.0.0) (2026-04-29)

### Features

- Dockerfile based on `debian:trixie-slim` with AMD ROCm apt repo (noble channel)
- GitHub Actions workflow to build and push Docker image to GHCR on tag
- GitHub Actions workflow to build PyInstaller binary and publish to GitHub Releases
- Power metric fallback chain: tries `Current Socket Graphics Package Power (W)`, then `Average Graphics Package Power (W)`, then `average_socket_power (W)` — fixes crash on RDNA GPUs where the original field is absent

### Chores

- Forked from [rudimk/rocm-smi-exporter](https://github.com/rudimk/rocm-smi-exporter)
- Label dict refactored — built once per card and splatted with `**labels`
