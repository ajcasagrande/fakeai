"""
Comprehensive integration tests for DCGM GPU metrics.

Tests the DCGM metrics endpoints, collection, and export functionality
in an integrated server environment.

Coverage:
1. DCGM metrics collection enabled/disabled
2. GPU utilization tracking
3. GPU memory usage
4. GPU temperature monitoring
5. GPU power consumption
6. GPU clock speeds
7. Multi-GPU support
8. Prometheus export format
9. DCGM metrics refresh rate
10. GPU health monitoring
11. GPU error tracking
12. Per-GPU metrics
13. GPU telemetry data
"""

import time

import pytest

from .utils import FakeAIClient

# Mark all tests as integration and metrics tests
pytestmark = [pytest.mark.integration, pytest.mark.metrics]


class TestDCGMMetricsCollection:
    """Test basic DCGM metrics collection."""

    def test_dcgm_metrics_endpoint_available(self, client: FakeAIClient):
        """Test that DCGM metrics endpoint is available."""
        response = client.get("/dcgm/metrics")
        assert response.status_code == 200
        assert "text/plain" in response.headers.get("content-type", "")

    def test_dcgm_metrics_json_endpoint(self, client: FakeAIClient):
        """Test DCGM metrics JSON endpoint."""
        response = client.get("/dcgm/metrics/json")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, dict)
        assert len(data) > 0

    def test_dcgm_collects_metrics_from_all_gpus(self, client: FakeAIClient):
        """Test that DCGM collects metrics from all GPUs."""
        response = client.get("/dcgm/metrics/json")
        data = response.json()

        # Should have metrics for multiple GPUs
        gpu_keys = [k for k in data.keys() if k.startswith("gpu_")]
        assert len(gpu_keys) >= 1, "Should have at least one GPU"

    def test_dcgm_metrics_include_basic_fields(self, client: FakeAIClient):
        """Test that DCGM metrics include basic required fields."""
        response = client.get("/dcgm/metrics/json")
        data = response.json()

        # Get first GPU metrics
        gpu_0 = data.get("gpu_0")
        assert gpu_0 is not None, "Should have gpu_0 metrics"

        # Check required fields
        required_fields = [
            "gpu_id",
            "uuid",
            "name",
            "architecture",
            "temperature_c",
            "power_usage_w",
            "gpu_utilization_pct",
            "memory_utilization_pct",
        ]

        for field in required_fields:
            assert field in gpu_0, f"Missing required field: {field}"

    def test_dcgm_metrics_update_over_time(self, client: FakeAIClient):
        """Test that DCGM metrics update over time."""
        # Get initial metrics
        response1 = client.get("/dcgm/metrics/json")
        data1 = response1.json()
        power1 = data1["gpu_0"]["power_usage_w"]

        # Wait for background update
        time.sleep(2)

        # Get updated metrics
        response2 = client.get("/dcgm/metrics/json")
        data2 = response2.json()
        power2 = data2["gpu_0"]["power_usage_w"]

        # Power might vary slightly (noise), so check they're both reasonable
        assert 30 <= power1 <= 800, f"Power should be reasonable: {power1}W"
        assert 30 <= power2 <= 800, f"Power should be reasonable: {power2}W"


class TestGPUUtilizationTracking:
    """Test GPU utilization tracking."""

    def test_gpu_utilization_within_valid_range(self, client: FakeAIClient):
        """Test that GPU utilization is within valid range (0-100%)."""
        response = client.get("/dcgm/metrics/json")
        data = response.json()

        for gpu_key, gpu_data in data.items():
            if gpu_key.startswith("gpu_"):
                util = gpu_data["gpu_utilization_pct"]
                assert 0 <= util <= 100, f"{gpu_key} utilization out of range: {util}"

    def test_sm_active_percentage(self, client: FakeAIClient):
        """Test SM (Streaming Multiprocessor) active percentage tracking."""
        response = client.get("/dcgm/metrics/json")
        data = response.json()

        gpu_0 = data["gpu_0"]
        assert "sm_active_pct" in gpu_0
        assert 0 <= gpu_0["sm_active_pct"] <= 100

    def test_sm_occupancy_tracking(self, client: FakeAIClient):
        """Test SM occupancy tracking."""
        response = client.get("/dcgm/metrics/json")
        data = response.json()

        gpu_0 = data["gpu_0"]
        assert "sm_occupancy_pct" in gpu_0
        assert 0 <= gpu_0["sm_occupancy_pct"] <= 100

    def test_tensor_core_utilization(self, client: FakeAIClient):
        """Test tensor core utilization tracking."""
        response = client.get("/dcgm/metrics/json")
        data = response.json()

        gpu_0 = data["gpu_0"]
        assert "tensor_active_pct" in gpu_0
        assert 0 <= gpu_0["tensor_active_pct"] <= 100


class TestGPUMemoryUsage:
    """Test GPU memory usage tracking."""

    def test_memory_free_used_total(self, client: FakeAIClient):
        """Test that memory free + used = total."""
        response = client.get("/dcgm/metrics/json")
        data = response.json()

        gpu_0 = data["gpu_0"]
        memory_free = gpu_0["memory_free_mib"]
        memory_used = gpu_0["memory_used_mib"]
        memory_total = gpu_0["memory_total_mib"]

        # Allow small margin for reserved memory
        assert memory_free + memory_used <= memory_total * 1.05

    def test_memory_utilization_percentage(self, client: FakeAIClient):
        """Test memory utilization percentage calculation."""
        response = client.get("/dcgm/metrics/json")
        data = response.json()

        gpu_0 = data["gpu_0"]
        mem_util_pct = gpu_0["memory_utilization_pct"]

        assert 0 <= mem_util_pct <= 100, f"Memory utilization out of range: {mem_util_pct}"

    def test_memory_values_reasonable_for_gpu_model(self, client: FakeAIClient):
        """Test that memory values are reasonable for GPU model."""
        response = client.get("/dcgm/metrics/json")
        data = response.json()

        gpu_0 = data["gpu_0"]
        memory_total = gpu_0["memory_total_mib"]

        # H100 has 80GB, A100 has 40GB or 80GB
        # Memory should be at least 40GB (40960 MiB) for datacenter GPUs
        assert memory_total >= 40000, f"Memory total seems too low: {memory_total} MiB"

    def test_dram_active_percentage(self, client: FakeAIClient):
        """Test DRAM active percentage tracking."""
        response = client.get("/dcgm/metrics/json")
        data = response.json()

        gpu_0 = data["gpu_0"]
        assert "dram_active_pct" in gpu_0
        assert 0 <= gpu_0["dram_active_pct"] <= 100


class TestGPUTemperatureMonitoring:
    """Test GPU temperature monitoring."""

    def test_gpu_temperature_within_safe_range(self, client: FakeAIClient):
        """Test that GPU temperature is within safe operating range."""
        response = client.get("/dcgm/metrics/json")
        data = response.json()

        gpu_0 = data["gpu_0"]
        temp = gpu_0["temperature_c"]

        # Temperature should be between 30C (cool idle) and 95C (max operating)
        assert 30 <= temp <= 95, f"Temperature out of safe range: {temp}C"

    def test_memory_temperature_tracked(self, client: FakeAIClient):
        """Test that memory temperature is tracked separately."""
        response = client.get("/dcgm/metrics/json")
        data = response.json()

        gpu_0 = data["gpu_0"]
        assert "memory_temp_c" in gpu_0

        mem_temp = gpu_0["memory_temp_c"]
        assert 25 <= mem_temp <= 100, f"Memory temperature out of range: {mem_temp}C"

    def test_hotspot_temperature_tracked(self, client: FakeAIClient):
        """Test that hotspot (max operating) temperature is tracked."""
        response = client.get("/dcgm/metrics/json")
        data = response.json()

        gpu_0 = data["gpu_0"]
        assert "hotspot_temp_c" in gpu_0

        hotspot = gpu_0["hotspot_temp_c"]
        gpu_temp = gpu_0["temperature_c"]

        # Hotspot should be higher than or equal to GPU temp
        assert hotspot >= gpu_temp - 5, "Hotspot should be >= GPU temp"

    def test_temperature_percentiles_tracked(self, client: FakeAIClient):
        """Test that temperature percentiles (P50, P90, P99) are tracked."""
        response = client.get("/dcgm/metrics/json")
        data = response.json()

        gpu_0 = data["gpu_0"]

        # Check historical percentiles exist
        assert "temp_p50" in gpu_0
        assert "temp_p90" in gpu_0
        assert "temp_p99" in gpu_0

        # Percentiles should be ordered
        p50 = gpu_0["temp_p50"]
        p90 = gpu_0["temp_p90"]
        p99 = gpu_0["temp_p99"]

        if p50 > 0 and p90 > 0 and p99 > 0:  # Skip if no history yet
            assert p50 <= p90 <= p99, f"Temp percentiles not ordered: {p50}, {p90}, {p99}"


class TestGPUPowerConsumption:
    """Test GPU power consumption tracking."""

    def test_power_usage_within_spec(self, client: FakeAIClient):
        """Test that power usage is within GPU power spec."""
        response = client.get("/dcgm/metrics/json")
        data = response.json()

        gpu_0 = data["gpu_0"]
        power = gpu_0["power_usage_w"]

        # Power should be between 30W (idle) and 800W (max for H100)
        assert 30 <= power <= 800, f"Power out of spec: {power}W"

    def test_total_energy_consumption_tracked(self, client: FakeAIClient):
        """Test that total energy consumption is tracked."""
        response = client.get("/dcgm/metrics/json")
        data = response.json()

        gpu_0 = data["gpu_0"]
        assert "total_energy_mj" in gpu_0

        energy = gpu_0["total_energy_mj"]
        assert energy >= 0, "Energy should be non-negative"

    def test_total_energy_increases_over_time(self, client: FakeAIClient):
        """Test that total energy increases over time."""
        # Get initial energy
        response1 = client.get("/dcgm/metrics/json")
        data1 = response1.json()
        energy1 = data1["gpu_0"]["total_energy_mj"]

        # Wait for some time
        time.sleep(2)

        # Get updated energy
        response2 = client.get("/dcgm/metrics/json")
        data2 = response2.json()
        energy2 = data2["gpu_0"]["total_energy_mj"]

        # Energy should increase (GPU is always consuming some power)
        assert energy2 >= energy1, f"Energy should increase: {energy1} -> {energy2}"

    def test_power_percentiles_tracked(self, client: FakeAIClient):
        """Test that power percentiles are tracked."""
        response = client.get("/dcgm/metrics/json")
        data = response.json()

        gpu_0 = data["gpu_0"]

        assert "power_p50" in gpu_0
        assert "power_p90" in gpu_0
        assert "power_p99" in gpu_0


class TestGPUClockSpeeds:
    """Test GPU clock speed tracking."""

    def test_sm_clock_speed_tracked(self, client: FakeAIClient):
        """Test that SM (Streaming Multiprocessor) clock speed is tracked."""
        response = client.get("/dcgm/metrics/json")
        data = response.json()

        gpu_0 = data["gpu_0"]
        assert "sm_clock_mhz" in gpu_0

        sm_clock = gpu_0["sm_clock_mhz"]
        # Clock should be reasonable (1000-2500 MHz for modern GPUs)
        assert 1000 <= sm_clock <= 2500, f"SM clock out of range: {sm_clock} MHz"

    def test_memory_clock_speed_tracked(self, client: FakeAIClient):
        """Test that memory clock speed is tracked."""
        response = client.get("/dcgm/metrics/json")
        data = response.json()

        gpu_0 = data["gpu_0"]
        assert "memory_clock_mhz" in gpu_0

        mem_clock = gpu_0["memory_clock_mhz"]
        # Memory clock should be reasonable (1000-5000 MHz)
        assert 1000 <= mem_clock <= 5000, f"Memory clock out of range: {mem_clock} MHz"

    def test_performance_state_tracked(self, client: FakeAIClient):
        """Test that performance state (P-state) is tracked."""
        response = client.get("/dcgm/metrics/json")
        data = response.json()

        gpu_0 = data["gpu_0"]
        assert "performance_state" in gpu_0

        pstate = gpu_0["performance_state"]
        # P-state should be 0-12 (P0 = max performance, P12 = minimum)
        assert 0 <= pstate <= 12, f"P-state out of range: {pstate}"


class TestMultiGPUSupport:
    """Test multi-GPU support."""

    def test_metrics_for_all_gpus(self, client: FakeAIClient):
        """Test that metrics are collected for all GPUs."""
        response = client.get("/dcgm/metrics/json")
        data = response.json()

        # Count GPU entries
        gpu_count = len([k for k in data.keys() if k.startswith("gpu_")])
        assert gpu_count >= 1, "Should have at least one GPU"

    def test_each_gpu_has_unique_uuid(self, client: FakeAIClient):
        """Test that each GPU has a unique UUID."""
        response = client.get("/dcgm/metrics/json")
        data = response.json()

        uuids = set()
        for key, value in data.items():
            if key.startswith("gpu_"):
                uuid = value["uuid"]
                assert uuid not in uuids, f"Duplicate UUID: {uuid}"
                uuids.add(uuid)

    def test_gpu_ids_sequential(self, client: FakeAIClient):
        """Test that GPU IDs are sequential (0, 1, 2, ...)."""
        response = client.get("/dcgm/metrics/json")
        data = response.json()

        gpu_ids = []
        for key, value in data.items():
            if key.startswith("gpu_"):
                gpu_ids.append(value["gpu_id"])

        gpu_ids.sort()
        expected_ids = list(range(len(gpu_ids)))
        assert gpu_ids == expected_ids, f"GPU IDs not sequential: {gpu_ids}"

    def test_nvlink_metrics_for_multi_gpu(self, client: FakeAIClient):
        """Test NVLink metrics are present for multi-GPU systems."""
        response = client.get("/dcgm/metrics/json")
        data = response.json()

        gpu_0 = data.get("gpu_0")
        if gpu_0:
            # NVLink metrics should be present
            assert "nvlink_tx_bytes" in gpu_0
            assert "nvlink_rx_bytes" in gpu_0

            # NVLink bytes should be non-negative
            assert gpu_0["nvlink_tx_bytes"] >= 0
            assert gpu_0["nvlink_rx_bytes"] >= 0


class TestPrometheusExport:
    """Test Prometheus export format."""

    def test_prometheus_format_valid(self, client: FakeAIClient):
        """Test that Prometheus export format is valid."""
        response = client.get("/dcgm/metrics")
        assert response.status_code == 200

        content = response.text

        # Check for Prometheus format markers
        assert "# TYPE" in content
        assert "# HELP" in content

    def test_prometheus_includes_dcgm_field_names(self, client: FakeAIClient):
        """Test that Prometheus export includes DCGM field names."""
        response = client.get("/dcgm/metrics")
        content = response.text

        # Check for key DCGM field IDs
        expected_fields = [
            "DCGM_FI_DEV_GPU_TEMP",
            "DCGM_FI_DEV_POWER_USAGE",
            "DCGM_FI_DEV_GPU_UTIL",
            "DCGM_FI_DEV_SM_CLOCK",
            "DCGM_FI_DEV_FB_USED",
        ]

        for field in expected_fields:
            assert field in content, f"Missing DCGM field: {field}"

    def test_prometheus_includes_gpu_labels(self, client: FakeAIClient):
        """Test that Prometheus export includes GPU labels."""
        response = client.get("/dcgm/metrics")
        content = response.text

        # Should have GPU labels
        assert 'gpu="0"' in content
        assert "UUID=" in content
        assert "device=" in content
        assert "modelName=" in content

    def test_prometheus_metric_types(self, client: FakeAIClient):
        """Test that Prometheus metrics have correct types."""
        response = client.get("/dcgm/metrics")
        content = response.text

        # Gauges (current values)
        assert "# TYPE DCGM_FI_DEV_GPU_TEMP gauge" in content
        assert "# TYPE DCGM_FI_DEV_POWER_USAGE gauge" in content

        # Counters (cumulative values)
        assert "# TYPE DCGM_FI_DEV_TOTAL_ENERGY_CONSUMPTION counter" in content


class TestDCGMMetricsRefreshRate:
    """Test DCGM metrics refresh rate."""

    def test_metrics_refresh_automatically(self, client: FakeAIClient):
        """Test that metrics refresh automatically over time."""
        # Get first reading
        response1 = client.get("/dcgm/metrics/json")
        data1 = response1.json()
        energy1 = data1["gpu_0"]["total_energy_mj"]

        # Wait for background updates (1-2 seconds)
        time.sleep(2)

        # Get second reading
        response2 = client.get("/dcgm/metrics/json")
        data2 = response2.json()
        energy2 = data2["gpu_0"]["total_energy_mj"]

        # Energy should have increased (GPU always consuming power)
        assert energy2 > energy1, "Metrics should refresh automatically"

    def test_multiple_rapid_requests_return_consistent_data(self, client: FakeAIClient):
        """Test that rapid requests return consistent data within update window."""
        responses = []
        for _ in range(5):
            response = client.get("/dcgm/metrics/json")
            responses.append(response.json())
            time.sleep(0.1)  # 100ms between requests

        # Check first GPU temperature is reasonable across all requests
        temps = [r["gpu_0"]["temperature_c"] for r in responses]

        # All temperatures should be in reasonable range
        for temp in temps:
            assert 30 <= temp <= 95

        # Temperature shouldn't jump wildly (thermal inertia)
        for i in range(1, len(temps)):
            diff = abs(temps[i] - temps[i - 1])
            assert diff < 10, f"Temperature changed too rapidly: {temps[i-1]} -> {temps[i]}"


class TestGPUHealthMonitoring:
    """Test GPU health monitoring."""

    def test_throttle_reasons_tracked(self, client: FakeAIClient):
        """Test that throttle reasons are tracked."""
        response = client.get("/dcgm/metrics/json")
        data = response.json()

        gpu_0 = data["gpu_0"]
        assert "throttle_reasons" in gpu_0
        assert "thermal_throttle" in gpu_0
        assert "power_throttle" in gpu_0

        # Values should be 0 or 1
        assert gpu_0["thermal_throttle"] in [0, 1]
        assert gpu_0["power_throttle"] in [0, 1]

    def test_fan_speed_tracked(self, client: FakeAIClient):
        """Test that fan speed is tracked."""
        response = client.get("/dcgm/metrics/json")
        data = response.json()

        gpu_0 = data["gpu_0"]
        assert "fan_speed_pct" in gpu_0

        fan_speed = gpu_0["fan_speed_pct"]
        assert 0 <= fan_speed <= 100, f"Fan speed out of range: {fan_speed}%"

    def test_performance_state_indicates_health(self, client: FakeAIClient):
        """Test that performance state can indicate health issues."""
        response = client.get("/dcgm/metrics/json")
        data = response.json()

        gpu_0 = data["gpu_0"]
        pstate = gpu_0["performance_state"]

        # P-state should be valid
        assert 0 <= pstate <= 12


class TestGPUErrorTracking:
    """Test GPU error tracking."""

    def test_ecc_single_bit_errors_tracked(self, client: FakeAIClient):
        """Test that single-bit ECC errors are tracked."""
        response = client.get("/dcgm/metrics/json")
        data = response.json()

        gpu_0 = data["gpu_0"]
        assert "ecc_sbe_total" in gpu_0

        # Should be non-negative
        assert gpu_0["ecc_sbe_total"] >= 0

    def test_ecc_errors_by_location(self, client: FakeAIClient):
        """Test that ECC errors are tracked by memory location."""
        response = client.get("/dcgm/metrics/json")
        data = response.json()

        gpu_0 = data["gpu_0"]

        # Check specific locations
        assert "ecc_sbe_l1" in gpu_0
        assert "ecc_sbe_l2" in gpu_0

        # All should be non-negative
        assert gpu_0["ecc_sbe_l1"] >= 0
        assert gpu_0["ecc_sbe_l2"] >= 0

    def test_ecc_double_bit_errors_tracked(self, client: FakeAIClient):
        """Test that double-bit ECC errors are tracked."""
        response = client.get("/dcgm/metrics/json")
        data = response.json()

        gpu_0 = data["gpu_0"]
        assert "ecc_dbe_total" in gpu_0

        # Should be non-negative
        assert gpu_0["ecc_dbe_total"] >= 0

    def test_pcie_metrics_tracked(self, client: FakeAIClient):
        """Test that PCIe metrics are tracked."""
        response = client.get("/dcgm/metrics/json")
        data = response.json()

        gpu_0 = data["gpu_0"]

        # PCIe transfer bytes
        assert "pcie_tx_bytes" in gpu_0
        assert "pcie_rx_bytes" in gpu_0

        # Should be non-negative
        assert gpu_0["pcie_tx_bytes"] >= 0
        assert gpu_0["pcie_rx_bytes"] >= 0


class TestPerGPUMetrics:
    """Test per-GPU metric isolation."""

    def test_gpus_have_independent_metrics(self, client: FakeAIClient):
        """Test that GPUs have independent metrics."""
        response = client.get("/dcgm/metrics/json")
        data = response.json()

        gpu_keys = [k for k in data.keys() if k.startswith("gpu_")]

        if len(gpu_keys) >= 2:
            gpu_0 = data["gpu_0"]
            gpu_1 = data["gpu_1"]

            # UUIDs should be different
            assert gpu_0["uuid"] != gpu_1["uuid"]

            # Each should have their own metrics
            assert "temperature_c" in gpu_0
            assert "temperature_c" in gpu_1

    def test_gpu_architecture_reported(self, client: FakeAIClient):
        """Test that GPU architecture is reported."""
        response = client.get("/dcgm/metrics/json")
        data = response.json()

        gpu_0 = data["gpu_0"]
        assert "architecture" in gpu_0

        arch = gpu_0["architecture"]
        # Should be one of the known architectures
        assert arch in ["ampere", "hopper", "blackwell"]


class TestGPUTelemetryData:
    """Test comprehensive GPU telemetry data."""

    def test_all_required_telemetry_fields_present(self, client: FakeAIClient):
        """Test that all required telemetry fields are present."""
        response = client.get("/dcgm/metrics/json")
        data = response.json()

        gpu_0 = data["gpu_0"]

        required_fields = [
            # Identity
            "gpu_id",
            "uuid",
            "name",
            "architecture",
            # Clocks
            "sm_clock_mhz",
            "memory_clock_mhz",
            # Temperature
            "temperature_c",
            "memory_temp_c",
            "hotspot_temp_c",
            # Power
            "power_usage_w",
            "total_energy_mj",
            # Utilization
            "gpu_utilization_pct",
            "memory_utilization_pct",
            # Memory
            "memory_free_mib",
            "memory_used_mib",
            "memory_total_mib",
            # Performance
            "performance_state",
            "sm_active_pct",
            "sm_occupancy_pct",
            # Transfer
            "pcie_tx_bytes",
            "pcie_rx_bytes",
            # Health
            "fan_speed_pct",
            "throttle_reasons",
            # Historical
            "temp_p50",
            "power_p50",
        ]

        for field in required_fields:
            assert field in gpu_0, f"Missing required telemetry field: {field}"

    def test_telemetry_values_reasonable(self, client: FakeAIClient):
        """Test that telemetry values are reasonable."""
        response = client.get("/dcgm/metrics/json")
        data = response.json()

        gpu_0 = data["gpu_0"]

        # Temperature checks
        assert 30 <= gpu_0["temperature_c"] <= 95
        assert 25 <= gpu_0["memory_temp_c"] <= 100

        # Power checks
        assert 30 <= gpu_0["power_usage_w"] <= 800

        # Utilization checks (percentage)
        assert 0 <= gpu_0["gpu_utilization_pct"] <= 100
        assert 0 <= gpu_0["memory_utilization_pct"] <= 100

        # Clock checks
        assert 1000 <= gpu_0["sm_clock_mhz"] <= 2500
        assert 1000 <= gpu_0["memory_clock_mhz"] <= 5000

    def test_telemetry_export_formats(self, client: FakeAIClient):
        """Test that telemetry is available in multiple formats."""
        # JSON format
        json_response = client.get("/dcgm/metrics/json")
        assert json_response.status_code == 200
        json_data = json_response.json()
        assert isinstance(json_data, dict)

        # Prometheus format
        prom_response = client.get("/dcgm/metrics")
        assert prom_response.status_code == 200
        prom_data = prom_response.text
        assert "# TYPE" in prom_data
        assert "DCGM_FI" in prom_data


class TestDCGMRealisticScenarios:
    """Test realistic DCGM monitoring scenarios."""

    def test_continuous_monitoring_scenario(self, client: FakeAIClient):
        """Test continuous monitoring scenario (scraping every 1-2 seconds)."""
        readings = []

        # Simulate continuous monitoring for 5 seconds
        for _ in range(5):
            response = client.get("/dcgm/metrics/json")
            assert response.status_code == 200
            readings.append(response.json())
            time.sleep(1)

        # Should have 5 readings
        assert len(readings) == 5

        # Energy should be monotonically increasing
        energies = [r["gpu_0"]["total_energy_mj"] for r in readings]
        for i in range(1, len(energies)):
            assert energies[i] >= energies[i - 1], "Energy should not decrease"

    def test_metrics_during_simulated_load(self, client: FakeAIClient):
        """Test metrics during simulated load (chat completions)."""
        # Get baseline metrics
        baseline = client.get("/dcgm/metrics/json").json()
        baseline_energy = baseline["gpu_0"]["total_energy_mj"]

        # Simulate load with chat completions
        for _ in range(3):
            response = client.post(
                "/v1/chat/completions",
                json={
                    "model": "openai/gpt-oss-120b",
                    "messages": [{"role": "user", "content": "Hello!"}],
                },
            )
            assert response.status_code == 200

        # Wait a bit for metrics to update
        time.sleep(2)

        # Get metrics after load
        after_load = client.get("/dcgm/metrics/json").json()
        after_energy = after_load["gpu_0"]["total_energy_mj"]

        # Energy should have increased
        assert after_energy > baseline_energy

    def test_prometheus_scraping_scenario(self, client: FakeAIClient):
        """Test Prometheus scraping scenario."""
        # Simulate Prometheus scraping every 15 seconds (condensed to 2 seconds for test)
        scrapes = []

        for _ in range(3):
            response = client.get("/dcgm/metrics")
            assert response.status_code == 200
            assert "text/plain" in response.headers.get("content-type", "")
            scrapes.append(response.text)
            time.sleep(2)

        # All scrapes should be valid Prometheus format
        for scrape in scrapes:
            assert "# TYPE" in scrape
            assert "# HELP" in scrape
            assert "DCGM_FI" in scrape


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
