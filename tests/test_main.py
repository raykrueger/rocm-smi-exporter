import json
import os
from subprocess import CalledProcessError
from unittest.mock import patch, MagicMock

import pytest
from prometheus_client import generate_latest, REGISTRY

from rocm_smi_exporter import main

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")


def load_fixture(name):
    with open(os.path.join(FIXTURES_DIR, name)) as f:
        return json.load(f)


def get_metric_value(metric_name, labels):
    """Query the Prometheus registry and return a metric value for given labels."""
    for collector in REGISTRY._names_to_collectors.values():
        for family in collector.collect():
            if family.name != metric_name:
                continue
            for sample in family.samples:
                if sample.labels == labels:
                    return sample.value
    return None


# --- floatOrZero ---

class TestFloatOrZero:
    def test_normal_number(self):
        assert main.floatOrZero(42) == 42.0

    def test_string_number(self):
        assert main.floatOrZero("33") == 33.0

    def test_float_string(self):
        assert main.floatOrZero("3.14") == 3.14

    def test_na_string(self):
        assert main.floatOrZero("N/A") == 0.0

    def test_none(self):
        assert main.floatOrZero(None) == 0.0

    def test_empty_string(self):
        assert main.floatOrZero("") == 0.0

    def test_zero(self):
        assert main.floatOrZero(0) == 0.0


# --- resolveDeviceName ---

class TestResolveDeviceName:
    def test_specific_name_passthrough(self):
        card = {"Device Name": "AMD Radeon AI PRO R9700", "Device ID": "0x7551"}
        assert main.resolveDeviceName(card) == "AMD Radeon AI PRO R9700"

    def test_na_name_with_fallback(self):
        card = {"Device Name": "N/A", "Device ID": "0x7551"}
        assert main.resolveDeviceName(card) == "AMD Radeon AI PRO R9700"

    def test_generic_name_with_fallback(self):
        card = {"Device Name": "AMD Radeon Graphics", "Device ID": "0x7551"}
        assert main.resolveDeviceName(card) == "AMD Radeon AI PRO R9700"

    def test_na_name_no_fallback(self):
        card = {"Device Name": "N/A", "Device ID": "0xdead"}
        assert main.resolveDeviceName(card) == "N/A"

    def test_missing_device_name(self):
        card = {"Device ID": "0x7551"}
        assert main.resolveDeviceName(card) == "AMD Radeon AI PRO R9700"

    def test_missing_device_id(self):
        card = {"Device Name": "N/A"}
        assert main.resolveDeviceName(card) == "N/A"


# --- safeJsonOutput ---

class TestSafeJsonOutput:
    @patch("rocm_smi_exporter.main.check_output")
    def test_success(self, mock_output):
        mock_output.return_value = b'{"key": "value"}'
        result = main.safeJsonOutput(["rocm-smi", "-a", "--json"])
        assert result == {"key": "value"}

    @patch("rocm_smi_exporter.main.check_output")
    def test_empty_output(self, mock_output):
        mock_output.return_value = b""
        result = main.safeJsonOutput(["rocm-smi", "-a", "--json"])
        assert result is None

    @patch("rocm_smi_exporter.main.check_output")
    def test_whitespace_only(self, mock_output):
        mock_output.return_value = b"   \n  "
        result = main.safeJsonOutput(["rocm-smi", "-a", "--json"])
        assert result is None

    @patch("rocm_smi_exporter.main.check_output")
    def test_invalid_json(self, mock_output):
        mock_output.return_value = b"not json"
        result = main.safeJsonOutput(["rocm-smi", "-a", "--json"])
        assert result is None

    @patch("rocm_smi_exporter.main.check_output")
    def test_called_process_error(self, mock_output):
        mock_output.side_effect = CalledProcessError(1, "rocm-smi")
        result = main.safeJsonOutput(["rocm-smi", "-a", "--json"])
        assert result is None


# --- getGPUMetrics ---

class TestGetGPUMetrics:
    @patch("rocm_smi_exporter.main.safeJsonOutput")
    def test_success_with_vram_merge(self, mock_safe):
        all_data = load_fixture("rocm_smi_all.json")
        vram_data = load_fixture("rocm_smi_vram.json")

        mock_safe.side_effect = [all_data, vram_data]
        result = main.getGPUMetrics()

        assert "node[0]" in result
        assert "node[1]" in result
        assert result["node[0]"]["VRAM Total Used Memory (B)"] == "21216985088"
        assert result["node[1]"]["VRAM Total Used Memory (B)"] == "22884802560"
        assert result["node[0]"]["Temperature (Sensor edge) (C)"] == "33"

    @patch("rocm_smi_exporter.main.safeJsonOutput")
    def test_success_without_vram(self, mock_safe):
        all_data = load_fixture("rocm_smi_all.json")

        mock_safe.side_effect = [all_data, None]
        result = main.getGPUMetrics()

        assert "node[0]" in result
        assert "VRAM Total Used Memory (B)" not in result["node[0]"]

    @patch("rocm_smi_exporter.main.safeJsonOutput")
    def test_rocm_smi_failure(self, mock_safe):
        mock_safe.return_value = None
        result = main.getGPUMetrics()
        assert result == {}

    @patch("rocm_smi_exporter.main.safeJsonOutput")
    def test_system_key_preserved_but_skippable(self, mock_safe):
        all_data = load_fixture("rocm_smi_all.json")
        vram_data = load_fixture("rocm_smi_vram.json")

        mock_safe.side_effect = [all_data, vram_data]
        result = main.getGPUMetrics()

        assert "system" in result


# --- setMetrics ---

class TestSetMetrics:
    def test_sets_all_metrics(self):
        all_data = load_fixture("rocm_smi_all.json")
        vram_data = load_fixture("rocm_smi_vram.json")
        for card in vram_data:
            if card != "system" and card in all_data:
                all_data[card].update(vram_data[card])

        main.setMetrics(all_data)

        labels0 = {
            "device_name": "AMD Radeon AI PRO R9700",
            "device_id": "0x7551",
            "subsystem_id": "-0x1b67",
        }
        labels1 = {
            "device_name": "AMD Radeon AI PRO R9700",
            "device_id": "0x7551",
            "subsystem_id": "-0x67ff",
        }

        # Temperatures
        assert get_metric_value("rocm_smi_edge_temperature", labels0) == 33.0
        assert get_metric_value("rocm_smi_edge_temperature", labels1) == 35.0
        assert get_metric_value("rocm_smi_junction_temperature", labels0) == 44.0
        assert get_metric_value("rocm_smi_junction_temperature", labels1) == 49.0
        assert get_metric_value("rocm_smi_memory_temperature", labels0) == 35.0
        assert get_metric_value("rocm_smi_memory_temperature", labels1) == 36.0

        # Power
        assert get_metric_value("rocm_smi_socket_power", labels0) == 276.0
        assert get_metric_value("rocm_smi_socket_power", labels1) == 300.0
        assert get_metric_value("rocm_smi_power_cap", labels0) == 300.0
        assert get_metric_value("rocm_smi_power_cap", labels1) == 300.0

        # Usage
        assert get_metric_value("rocm_smi_gpu_usage", labels0) == 100.0
        assert get_metric_value("rocm_smi_gpu_usage", labels1) == 100.0
        assert get_metric_value("rocm_smi_gpu_vram_allocation", labels0) == 62.0
        assert get_metric_value("rocm_smi_gpu_vram_allocation", labels1) == 66.0
        assert get_metric_value("rocm_smi_memory_activity", labels0) == 4.0
        assert get_metric_value("rocm_smi_memory_activity", labels1) == 63.0

        # Fan
        assert get_metric_value("rocm_smi_fan_rpm", labels0) == 893.0
        assert get_metric_value("rocm_smi_fan_rpm", labels1) == 893.0
        assert get_metric_value("rocm_smi_fan_speed", labels0) == 21.0
        assert get_metric_value("rocm_smi_fan_speed", labels1) == 16.0

        # Clocks
        assert get_metric_value("rocm_smi_gfx_clock", labels0) == 2844.0
        assert get_metric_value("rocm_smi_gfx_clock", labels1) == 2769.0
        assert get_metric_value("rocm_smi_memory_clock", labels0) == 1258.0
        assert get_metric_value("rocm_smi_memory_clock", labels1) == 1258.0

        # Throttle
        assert get_metric_value("rocm_smi_throttle_status", labels0) == 0.0
        assert get_metric_value("rocm_smi_throttle_status", labels1) == 16384.0

        # VRAM (bytes)
        assert get_metric_value("rocm_smi_vram_used_bytes", labels0) == 21216985088.0
        assert get_metric_value("rocm_smi_vram_used_bytes", labels1) == 22884802560.0
        assert get_metric_value("rocm_smi_vram_total_bytes", labels0) == 34208743424.0
        assert get_metric_value("rocm_smi_vram_total_bytes", labels1) == 34208743424.0

    def test_skips_system_key(self):
        metrics = {"system": {"Device Name": "foo", "Device ID": "0x0000", "Subsystem ID": "-0x0000"}}
        main.setMetrics(metrics)

        val = get_metric_value("rocm_smi_edge_temperature", {
            "device_name": "foo",
            "device_id": "0x0000",
            "subsystem_id": "-0x0000",
        })
        assert val is None

    def test_na_device_name_fallback(self):
        metrics = load_fixture("rocm_smi_na_name.json")
        main.setMetrics(metrics)

        labels = {
            "device_name": "AMD Radeon AI PRO R9700",
            "device_id": "0x7551",
            "subsystem_id": "-0x1b67",
        }
        assert get_metric_value("rocm_smi_edge_temperature", labels) == 30.0
        assert get_metric_value("rocm_smi_gpu_usage", labels) == 50.0

    def test_missing_fields_default_to_zero(self):
        metrics = {
            "node[0]": {
                "Device Name": "Test GPU",
                "Device ID": "0xbeef",
                "Subsystem ID": "-0xbeef",
            }
        }
        main.setMetrics(metrics)

        labels = {
            "device_name": "Test GPU",
            "device_id": "0xbeef",
            "subsystem_id": "-0xbeef",
        }
        assert get_metric_value("rocm_smi_edge_temperature", labels) == 0.0
        assert get_metric_value("rocm_smi_socket_power", labels) == 0.0
        assert get_metric_value("rocm_smi_gpu_usage", labels) == 0.0
        assert get_metric_value("rocm_smi_fan_rpm", labels) == 0.0

    def test_na_values_default_to_zero(self):
        metrics = {
            "node[0]": {
                "Device Name": "Test GPU",
                "Device ID": "0xface",
                "Subsystem ID": "-0xface",
                "Temperature (Sensor edge) (C)": "N/A",
                "Current Socket Graphics Package Power (W)": "N/A",
                "GPU use (%)": "N/A",
            }
        }
        main.setMetrics(metrics)

        labels = {
            "device_name": "Test GPU",
            "device_id": "0xface",
            "subsystem_id": "-0xface",
        }
        assert get_metric_value("rocm_smi_edge_temperature", labels) == 0.0
        assert get_metric_value("rocm_smi_socket_power", labels) == 0.0
        assert get_metric_value("rocm_smi_gpu_usage", labels) == 0.0

    def test_power_fallback_fields(self):
        metrics = {
            "node[0]": {
                "Device Name": "Test GPU",
                "Device ID": "0xfall",
                "Subsystem ID": "-0xfall",
                "Average Graphics Package Power (W)": "150",
            }
        }
        main.setMetrics(metrics)

        labels = {
            "device_name": "Test GPU",
            "device_id": "0xfall",
            "subsystem_id": "-0xfall",
        }
        assert get_metric_value("rocm_smi_socket_power", labels) == 150.0

    def test_power_fallback_second_field(self):
        metrics = {
            "node[0]": {
                "Device Name": "Test GPU",
                "Device ID": "0xfall",
                "Subsystem ID": "-0xfall",
                "average_socket_power (W)": "200",
            }
        }
        main.setMetrics(metrics)

        labels = {
            "device_name": "Test GPU",
            "device_id": "0xfall",
            "subsystem_id": "-0xfall",
        }
        assert get_metric_value("rocm_smi_socket_power", labels) == 200.0
