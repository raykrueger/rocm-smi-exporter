"""Integration tests that require Docker."""
import re
import subprocess
import time

import pytest

IMAGE_TAG = "rocm-smi-exporter:integration-test"
PORT = 9395

# Matches: metric_name{key="val",...} value
_METRIC_RE = re.compile(
    r'^(\w+)\{([^}]*)\}\s+([\d.eE+\-]+)$'
)


def _parse_label_pair(raw):
    k, _, v = raw.partition("=")
    return k.strip(), v.strip('"')


def _parse_labels(raw):
    return dict(_parse_label_pair(p) for p in raw.split(",")) if raw else {}


def build_image():
    result = subprocess.run(
        ["docker", "build", "--build-arg", "USE_MOCK_DATA=1", "-t", IMAGE_TAG, "."],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        pytest.skip(f"Docker build failed: {result.stderr}")


@pytest.fixture(scope="module", autouse=True)
def container():
    """Build image, start container, yield, then stop and remove."""
    build_image()

    result = subprocess.run(
        ["docker", "run", "-d", "--name", "integration-test", f"-p{PORT}:9393", IMAGE_TAG],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        pytest.skip(f"Docker run failed: {result.stderr}")

    # Wait for the server to be ready
    for _ in range(10):
        time.sleep(1)
        try:
            subprocess.run(
                ["curl", "-sf", f"http://localhost:{PORT}/metrics"],
                capture_output=True,
                timeout=5,
            )
            break
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            continue
    else:
        logs = subprocess.run(
            ["docker", "logs", "integration-test"], capture_output=True, text=True
        ).stdout
        subprocess.run(["docker", "stop", "integration-test"], capture_output=True)
        subprocess.run(["docker", "rm", "integration-test"], capture_output=True)
        pytest.skip(f"Server did not start. Logs: {logs}")

    yield

    subprocess.run(["docker", "stop", "integration-test"], capture_output=True)
    subprocess.run(["docker", "rm", "integration-test"], capture_output=True)


def fetch_metrics():
    result = subprocess.run(
        ["curl", "-sf", f"http://localhost:{PORT}/metrics"],
        capture_output=True,
        text=True,
        timeout=10,
    )
    return result.stdout


def metric_value(output, metric_name, labels):
    """Parse Prometheus text output and return value for matching labels."""
    for line in output.splitlines():
        m = _METRIC_RE.match(line)
        if not m:
            continue
        name, raw_labels, raw_value = m.groups()
        if name == metric_name and _parse_labels(raw_labels) == labels:
            return float(raw_value)
    return None


@pytest.mark.integration
class TestDockerIntegration:
    def test_metrics_endpoint_returns_data(self):
        output = fetch_metrics()
        assert "rocm_smi_edge_temperature" in output

    def test_two_gpus_exposed(self):
        output = fetch_metrics()
        count = sum(1 for line in output.splitlines() if line.startswith("rocm_smi_edge_temperature{"))
        assert count == 2

    def test_device_labels_correct(self):
        output = fetch_metrics()
        labels = {
            "card": "card0",
            "pci_bus": "0000:03:00.0",
            "device_id": "0x7551",
            "device_name": "AMD Radeon AI PRO R9700",
            "subsystem_id": "-0x1b67",
        }
        assert metric_value(output, "rocm_smi_edge_temperature", labels) == 33.0

    def test_all_metric_types_present(self):
        output = fetch_metrics()
        expected = [
            "rocm_smi_edge_temperature",
            "rocm_smi_junction_temperature",
            "rocm_smi_memory_temperature",
            "rocm_smi_socket_power",
            "rocm_smi_power_cap",
            "rocm_smi_gpu_usage",
            "rocm_smi_gpu_vram_allocation",
            "rocm_smi_memory_activity",
            "rocm_smi_fan_rpm",
            "rocm_smi_fan_speed",
            "rocm_smi_gfx_clock",
            "rocm_smi_memory_clock",
            "rocm_smi_throttle_status",
            "rocm_smi_vram_used_bytes",
            "rocm_smi_vram_total_bytes",
        ]
        for metric in expected:
            assert metric in output, f"Missing metric: {metric}"

    def test_vram_bytes_correct(self):
        output = fetch_metrics()
        labels = {
            "card": "card0",
            "pci_bus": "0000:03:00.0",
            "device_id": "0x7551",
            "device_name": "AMD Radeon AI PRO R9700",
            "subsystem_id": "-0x1b67",
        }
        assert metric_value(output, "rocm_smi_vram_used_bytes", labels) == 21216985088.0
        assert metric_value(output, "rocm_smi_vram_total_bytes", labels) == 34208743424.0

    def test_help_and_type_comments_present(self):
        output = fetch_metrics()
        assert "# HELP rocm_smi_edge_temperature" in output
        assert "# TYPE rocm_smi_edge_temperature gauge" in output
