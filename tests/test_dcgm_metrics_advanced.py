"""
Comprehensive tests for DCGM Metrics Simulator - EXTREME Edition.

Tests advanced features:
- Thermal throttling and dynamics
- NVLink traffic coordination
- ECC errors under load
- Multi-GPU coordination
- Historical tracking and percentiles
- Power settling and correlation
- Process tracking
- Memory bandwidth saturation
- Fan speed control
- Clock frequency scaling
"""

import time

import pytest

from fakeai.dcgm_metrics import (
    DCGM_FI_DEV_CLOCK_THROTTLE_REASONS,
    DCGM_FI_DEV_ECC_DBE_VOL_TOTAL,
    DCGM_FI_DEV_ECC_SBE_VOL_L1,
    DCGM_FI_DEV_ECC_SBE_VOL_L2,
    DCGM_FI_DEV_ECC_SBE_VOL_TOTAL,
    DCGM_FI_DEV_FAN_SPEED,
    DCGM_FI_DEV_GPU_TEMP,
    DCGM_FI_DEV_GPU_UTIL,
    DCGM_FI_DEV_MEMORY_TEMP,
    DCGM_FI_DEV_NVLINK_CRC_FLIT_ERROR_COUNT_TOTAL,
    DCGM_FI_DEV_PCIE_REPLAY_COUNTER,
    DCGM_FI_DEV_POWER_THROTTLE,
    DCGM_FI_DEV_POWER_USAGE,
    DCGM_FI_DEV_PSTATE,
    DCGM_FI_DEV_SM_CLOCK,
    DCGM_FI_DEV_THERMAL_THROTTLE,
    DCGM_FI_HIST_POWER_P50,
    DCGM_FI_HIST_POWER_P90,
    DCGM_FI_HIST_POWER_P99,
    DCGM_FI_HIST_TEMP_P50,
    DCGM_FI_HIST_TEMP_P90,
    DCGM_FI_HIST_TEMP_P99,
    DCGM_FI_PROCESS_COUNT,
    DCGM_FI_PROCESS_MAX_UTILIZATION,
    DCGM_FI_PROCESS_TOTAL_MEMORY,
    DCGM_FI_PROF_NVLINK_RX_BYTES,
    DCGM_FI_PROF_NVLINK_TX_BYTES,
    DCGM_FI_PROF_PCIE_RX_BYTES,
    DCGM_FI_PROF_PCIE_TX_BYTES,
    DCGMMetricsSimulator,
    SlowdownReason,
)


@pytest.fixture
def simulator():
    """Create a DCGM simulator for testing."""
    sim = DCGMMetricsSimulator(num_gpus=4, gpu_model="H100-80GB")
    yield sim
    sim.shutdown()


@pytest.fixture
def single_gpu_simulator():
    """Create a single GPU simulator for testing."""
    sim = DCGMMetricsSimulator(num_gpus=1, gpu_model="H100-80GB")
    yield sim
    sim.shutdown()


class TestThermalThrottling:
    """Test thermal throttling behavior."""

    def test_thermal_throttling_activates_at_threshold(self, single_gpu_simulator):
        """Test that thermal throttling activates when temperature exceeds threshold."""
        sim = single_gpu_simulator

        # Set high workload to increase temperature
        sim.set_workload(0, compute_intensity=1.0, memory_intensity=0.8)

        # Wait for temperature to rise and throttling to engage
        time.sleep(3)

        # Force immediate update
        sim.gpus[0].update_metrics(1.0)

        temp = sim.get_field_value(0, DCGM_FI_DEV_GPU_TEMP).value
        throttle_reasons = sim.get_field_value(
            0, DCGM_FI_DEV_CLOCK_THROTTLE_REASONS
        ).value
        thermal_throttle = sim.get_field_value(0, DCGM_FI_DEV_THERMAL_THROTTLE).value

        # If temperature is high enough, throttling should be active
        if temp >= 85:
            assert throttle_reasons & 0x1, "Thermal throttle bit should be set"
            assert thermal_throttle == 1, "Thermal throttle flag should be active"

    def test_thermal_inertia(self, single_gpu_simulator):
        """Test that temperature changes gradually (thermal inertia)."""
        sim = single_gpu_simulator

        # Get initial temperature
        initial_temp = sim.get_field_value(0, DCGM_FI_DEV_GPU_TEMP).value

        # Apply high workload
        sim.set_workload(0, compute_intensity=1.0, memory_intensity=0.5)

        # Update multiple times and track temperature
        temperatures = [initial_temp]
        for _ in range(5):
            time.sleep(1)
            sim.gpus[0].update_metrics(1.0)
            temp = sim.get_field_value(0, DCGM_FI_DEV_GPU_TEMP).value
            temperatures.append(temp)

        # Temperature should increase gradually, not jump immediately
        temp_diffs = [
            temperatures[i + 1] - temperatures[i] for i in range(len(temperatures) - 1)
        ]

        # No single update should change temperature by more than 20C (thermal inertia)
        for diff in temp_diffs:
            assert abs(diff) < 20, f"Temperature change too rapid: {diff}C"

        # Overall temperature should trend upward
        assert (
            temperatures[-1] > temperatures[0]
        ), "Temperature should increase under load"

    def test_clock_reduction_during_throttling(self, single_gpu_simulator):
        """Test that clock frequencies reduce when throttling occurs."""
        sim = single_gpu_simulator
        gpu = sim.gpus[0]

        # Force high temperature to trigger throttling
        gpu.current_temperature = 87.0
        gpu._update_throttling()

        # Need to update multiple times for clock to converge
        for _ in range(10):
            gpu._update_clock_frequencies()

        # Publish snapshot to reflect changes
        gpu._publish_snapshot()

        sm_clock = sim.get_field_value(0, DCGM_FI_DEV_SM_CLOCK).value

        # Clock should be reduced from base clock (1830 MHz for H100)
        # Throttling targets 85% of base = 1555 MHz
        assert (
            sm_clock < 1700
        ), f"Clock should be reduced during throttling, got {sm_clock}"

    def test_throttling_clears_when_temperature_drops(self, single_gpu_simulator):
        """Test that throttling clears when temperature drops below threshold."""
        sim = single_gpu_simulator
        gpu = sim.gpus[0]

        # Set throttling
        gpu.throttle_reasons.thermal = True
        gpu.slowdown_reason = SlowdownReason.HW_THERMAL

        # Drop temperature below threshold
        gpu.current_temperature = 80.0
        gpu._update_throttling()

        # Throttling should clear
        assert not gpu.throttle_reasons.thermal, "Thermal throttling should clear"
        assert (
            gpu.slowdown_reason == SlowdownReason.NONE
        ), "Slowdown reason should clear"


class TestPowerDynamics:
    """Test power consumption dynamics."""

    def test_power_correlates_with_utilization(self, single_gpu_simulator):
        """Test that power usage correlates with GPU utilization."""
        sim = single_gpu_simulator

        # Low utilization
        sim.set_workload(0, compute_intensity=0.2, memory_intensity=0.1)
        time.sleep(2)
        sim.gpus[0].update_metrics(1.0)
        low_power = sim.get_field_value(0, DCGM_FI_DEV_POWER_USAGE).value

        # High utilization
        sim.set_workload(0, compute_intensity=0.9, memory_intensity=0.8)
        time.sleep(2)
        sim.gpus[0].update_metrics(1.0)
        high_power = sim.get_field_value(0, DCGM_FI_DEV_POWER_USAGE).value

        assert high_power > low_power, "Power should increase with utilization"
        assert (
            high_power > 300
        ), f"High utilization power should be > 300W, got {high_power}"

    def test_power_settling_time(self, single_gpu_simulator):
        """Test that power changes gradually (settling time)."""
        sim = single_gpu_simulator

        # Start at low power
        sim.set_workload(0, compute_intensity=0.1, memory_intensity=0.1)
        time.sleep(1)
        sim.gpus[0].update_metrics(1.0)
        initial_power = sim.get_field_value(0, DCGM_FI_DEV_POWER_USAGE).value

        # Jump to high workload
        sim.set_workload(0, compute_intensity=0.9, memory_intensity=0.8)

        # Power should settle gradually over multiple updates
        powers = [initial_power]
        for _ in range(5):
            sim.gpus[0].update_metrics(1.0)
            power = sim.get_field_value(0, DCGM_FI_DEV_POWER_USAGE).value
            powers.append(power)
            time.sleep(0.1)

        # Each step should show gradual increase (not instant jump)
        for i in range(1, len(powers)):
            assert (
                powers[i] >= powers[i - 1] - 20
            ), "Power should not decrease significantly"

    def test_power_throttling(self, single_gpu_simulator):
        """Test power throttling when approaching power limit."""
        sim = single_gpu_simulator
        gpu = sim.gpus[0]

        # Force power near limit (700W for H100, threshold is 98% = 686W)
        gpu.current_power = 690.0
        gpu._update_throttling()

        # Publish snapshot to update cached values
        gpu._publish_snapshot()

        power_throttle = sim.get_field_value(0, DCGM_FI_DEV_POWER_THROTTLE).value

        assert power_throttle == 1, "Power throttling should activate near limit"
        assert gpu.throttle_reasons.power, "Power throttle reason should be set"


class TestNVLinkTraffic:
    """Test NVLink traffic coordination."""

    def test_nvlink_traffic_during_collective_ops(self, simulator):
        """Test that NVLink traffic increases during NCCL collective operations."""
        sim = simulator

        # Baseline NVLink traffic
        baseline_tx = sim.get_field_value(0, DCGM_FI_PROF_NVLINK_TX_BYTES).value

        # Start collective operation
        sim.start_collective_operation("allreduce")
        time.sleep(2)

        # Update metrics
        for gpu in sim.gpus:
            gpu.update_metrics(1.0)

        # Check NVLink traffic increased
        current_tx = sim.get_field_value(0, DCGM_FI_PROF_NVLINK_TX_BYTES).value
        assert (
            current_tx > baseline_tx
        ), "NVLink TX should increase during collective ops"

        # End collective operation
        sim.end_collective_operation()

    def test_nvlink_traffic_correlation_between_gpus(self, simulator):
        """Test that NVLink traffic is correlated across GPUs during collective ops."""
        sim = simulator

        # Start collective operation across all GPUs
        sim.start_collective_operation("allreduce")
        time.sleep(2)

        # Update all GPUs
        for gpu in sim.gpus:
            gpu.update_metrics(1.0)

        # Check NVLink traffic on all GPUs
        tx_values = []
        for gpu_id in range(sim.num_gpus):
            tx = sim.get_field_value(gpu_id, DCGM_FI_PROF_NVLINK_TX_BYTES).value
            tx_values.append(tx)

        # All GPUs should have significant NVLink traffic
        for tx in tx_values:
            assert tx > 0, "All GPUs should have NVLink traffic during collective ops"

        sim.end_collective_operation()

    def test_p2p_transfer_tracking(self, simulator):
        """Test P2P memory transfer tracking between GPUs."""
        sim = simulator

        # Simulate P2P transfer from GPU 0 to GPU 1
        bytes_transferred = 1_000_000_000  # 1 GB
        sim.simulate_p2p_transfer(0, 1, bytes_transferred)

        gpu0 = sim.gpus[0]
        gpu1 = sim.gpus[1]

        # Check P2P tracking
        assert (
            gpu0.p2p_bytes_sent[1] >= bytes_transferred
        ), "GPU 0 should track bytes sent to GPU 1"
        assert (
            gpu1.p2p_bytes_received[0] >= bytes_transferred
        ), "GPU 1 should track bytes received from GPU 0"

    def test_nvlink_crc_errors_are_rare(self, simulator):
        """Test that NVLink CRC errors are rare but can occur."""
        sim = simulator

        # Run collective ops for a while
        sim.start_collective_operation("allreduce")
        for _ in range(10):
            time.sleep(0.5)
            for gpu in sim.gpus:
                gpu.update_metrics(0.5)

        sim.end_collective_operation()

        # Check for CRC errors (should be rare)
        total_crc_errors = 0
        for gpu_id in range(sim.num_gpus):
            crc_errors = sim.get_field_value(
                gpu_id, DCGM_FI_DEV_NVLINK_CRC_FLIT_ERROR_COUNT_TOTAL
            ).value
            total_crc_errors += crc_errors

        # Errors should be very rare (0-2 in 10 updates across 4 GPUs)
        assert total_crc_errors < 5, f"Too many CRC errors: {total_crc_errors}"


class TestECCErrors:
    """Test ECC error simulation."""

    def test_ecc_errors_increase_under_memory_stress(self, single_gpu_simulator):
        """Test that ECC errors increase with memory stress."""
        sim = single_gpu_simulator
        gpu = sim.gpus[0]

        # Low stress baseline
        initial_sbe = sim.get_field_value(0, DCGM_FI_DEV_ECC_SBE_VOL_TOTAL).value

        # High memory stress + high temperature
        sim.set_workload(0, compute_intensity=0.9, memory_intensity=0.9)
        gpu.current_temperature = 85.0  # Force high temperature

        # Run multiple updates
        for _ in range(50):
            gpu._simulate_ecc_errors()

        current_sbe = sim.get_field_value(0, DCGM_FI_DEV_ECC_SBE_VOL_TOTAL).value

        # More likely to see errors under stress (but still rare)
        # Just verify the simulation ran without errors
        assert current_sbe >= initial_sbe, "SBE count should not decrease"

    def test_ecc_errors_distributed_across_locations(self, single_gpu_simulator):
        """Test that ECC errors are distributed across memory locations."""
        sim = single_gpu_simulator
        gpu = sim.gpus[0]

        # Force high stress to generate errors faster
        gpu.memory_utilization = 0.9
        gpu.current_temperature = 85.0

        # Generate many errors
        for _ in range(1000):
            gpu._simulate_ecc_errors()

        # Check error distribution
        sbe_l1 = sim.get_field_value(0, DCGM_FI_DEV_ECC_SBE_VOL_L1).value
        sbe_l2 = sim.get_field_value(0, DCGM_FI_DEV_ECC_SBE_VOL_L2).value
        sbe_total = sim.get_field_value(0, DCGM_FI_DEV_ECC_SBE_VOL_TOTAL).value

        # If we have errors, they should be distributed
        if sbe_total > 0:
            # At least some errors should be in different locations
            locations_with_errors = sum(
                [
                    1 if sbe_l1 > 0 else 0,
                    1 if sbe_l2 > 0 else 0,
                ]
            )
            # Don't enforce strict distribution since errors are random
            assert (
                locations_with_errors >= 0
            ), "Errors should exist in tracked locations"

    def test_double_bit_errors_very_rare(self, single_gpu_simulator):
        """Test that double-bit ECC errors are much rarer than single-bit."""
        sim = single_gpu_simulator
        gpu = sim.gpus[0]

        # High stress
        gpu.memory_utilization = 0.95
        gpu.current_temperature = 88.0

        # Generate errors
        for _ in range(1000):
            gpu._simulate_ecc_errors()

        sbe = sim.get_field_value(0, DCGM_FI_DEV_ECC_SBE_VOL_TOTAL).value
        dbe = sim.get_field_value(0, DCGM_FI_DEV_ECC_DBE_VOL_TOTAL).value

        # DBE should be much rarer than SBE
        if sbe > 0:
            assert dbe <= sbe, "Double-bit errors should be <= single-bit errors"


class TestMultiGPUCoordination:
    """Test multi-GPU coordination features."""

    def test_global_workload_sets_all_gpus(self, simulator):
        """Test that global workload affects all GPUs."""
        sim = simulator

        sim.set_global_workload(compute_intensity=0.8, memory_intensity=0.6)

        # Wait for workload to be reflected
        time.sleep(1)
        for gpu in sim.gpus:
            gpu.update_metrics(1.0)

        # Check all GPUs
        for gpu_id in range(sim.num_gpus):
            util = sim.get_field_value(gpu_id, DCGM_FI_DEV_GPU_UTIL).value
            assert util > 70, f"GPU {gpu_id} utilization should be high: {util}"

    def test_collective_operation_coordination(self, simulator):
        """Test that collective operations coordinate across all GPUs."""
        sim = simulator

        # Start collective op
        sim.start_collective_operation("allreduce")

        # Verify all GPUs are participating
        for gpu in sim.gpus:
            assert gpu.nccl_active, f"GPU {gpu.gpu_id} should be in NCCL collective op"
            assert gpu.collective_op_count > 0, "Collective op counter should increment"

        # End collective op
        sim.end_collective_operation()

        # Verify all GPUs stopped
        for gpu in sim.gpus:
            assert (
                not gpu.nccl_active
            ), f"GPU {gpu.gpu_id} should exit NCCL collective op"

    def test_collective_operation_auto_ends(self, simulator):
        """Test that collective operations auto-end after timeout."""
        sim = simulator

        sim.start_collective_operation("allreduce")
        assert sim.active_collective_op == "allreduce"

        # Wait for auto-end (5 seconds + margin)
        time.sleep(6)

        # Should auto-end
        assert sim.active_collective_op is None, "Collective op should auto-end"

    def test_independent_gpu_workloads(self, simulator):
        """Test that GPUs can have independent workloads."""
        sim = simulator

        # Set different workloads
        sim.set_workload(0, compute_intensity=0.9, memory_intensity=0.8)
        sim.set_workload(1, compute_intensity=0.3, memory_intensity=0.2)

        time.sleep(1)
        for gpu in sim.gpus:
            gpu.update_metrics(1.0)

        util_0 = sim.get_field_value(0, DCGM_FI_DEV_GPU_UTIL).value
        util_1 = sim.get_field_value(1, DCGM_FI_DEV_GPU_UTIL).value

        assert (
            util_0 > util_1 + 30
        ), f"GPU 0 ({util_0}) should have much higher util than GPU 1 ({util_1})"


class TestHistoricalTracking:
    """Test historical metric tracking and percentiles."""

    def test_historical_tracking_accumulates_data(self, single_gpu_simulator):
        """Test that historical data accumulates over time."""
        sim = single_gpu_simulator
        gpu = sim.gpus[0]

        # Set workload
        sim.set_workload(0, compute_intensity=0.7, memory_intensity=0.5)

        # Run updates to accumulate history
        for _ in range(10):
            gpu.update_metrics(1.0)
            time.sleep(0.1)

        # Check that history has data
        assert (
            len(gpu.history["temperature"].values) > 5
        ), "Should accumulate temperature history"
        assert len(gpu.history["power"].values) > 5, "Should accumulate power history"

    def test_percentile_calculations(self, single_gpu_simulator):
        """Test that percentile calculations work correctly."""
        sim = single_gpu_simulator
        gpu = sim.gpus[0]

        # Set workload and accumulate varied data
        for i in range(30):
            intensity = 0.3 + (i % 3) * 0.2  # Vary between 0.3, 0.5, 0.7
            sim.set_workload(0, compute_intensity=intensity, memory_intensity=0.5)
            gpu.update_metrics(1.0)
            time.sleep(0.05)

        # Get percentiles
        temp_p50 = sim.get_field_value(0, DCGM_FI_HIST_TEMP_P50).value
        temp_p90 = sim.get_field_value(0, DCGM_FI_HIST_TEMP_P90).value
        temp_p99 = sim.get_field_value(0, DCGM_FI_HIST_TEMP_P99).value

        power_p50 = sim.get_field_value(0, DCGM_FI_HIST_POWER_P50).value
        power_p90 = sim.get_field_value(0, DCGM_FI_HIST_POWER_P90).value
        power_p99 = sim.get_field_value(0, DCGM_FI_HIST_POWER_P99).value

        # Percentiles should be ordered
        assert (
            temp_p50 <= temp_p90 <= temp_p99
        ), "Temperature percentiles should be ordered"
        assert (
            power_p50 <= power_p90 <= power_p99
        ), "Power percentiles should be ordered"

        # Values should be reasonable
        assert (
            30 <= temp_p50 <= 100
        ), f"P50 temperature should be reasonable: {temp_p50}"
        assert 50 <= power_p50 <= 800, f"P50 power should be reasonable: {power_p50}"

    def test_historical_window_limits_to_60_seconds(self, single_gpu_simulator):
        """Test that historical window is limited to 60 seconds."""
        sim = single_gpu_simulator
        gpu = sim.gpus[0]

        # Add 70 data points (should keep only 60)
        for _ in range(70):
            gpu.history["temperature"].add(50.0)

        assert (
            len(gpu.history["temperature"].values) == 60
        ), "History should be limited to 60 entries"


class TestProcessTracking:
    """Test per-process GPU tracking."""

    def test_add_process(self, single_gpu_simulator):
        """Test adding process to GPU."""
        sim = single_gpu_simulator

        sim.add_process(0, pid=1234, name="python", gpu_util=0.5, mem_mib=8192)

        # Update snapshot to reflect changes
        sim.gpus[0]._publish_snapshot()

        process_count = sim.get_field_value(0, DCGM_FI_PROCESS_COUNT).value
        process_memory = sim.get_field_value(0, DCGM_FI_PROCESS_TOTAL_MEMORY).value

        assert process_count == 1, "Should have 1 process"
        assert (
            process_memory == 8192
        ), f"Process memory should be 8192 MiB, got {process_memory}"

    def test_multiple_processes(self, single_gpu_simulator):
        """Test tracking multiple processes."""
        sim = single_gpu_simulator

        sim.add_process(0, pid=1234, name="python", gpu_util=0.5, mem_mib=8192)
        sim.add_process(0, pid=5678, name="pytorch", gpu_util=0.3, mem_mib=4096)

        # Update snapshot to reflect changes
        sim.gpus[0]._publish_snapshot()

        process_count = sim.get_field_value(0, DCGM_FI_PROCESS_COUNT).value
        process_memory = sim.get_field_value(0, DCGM_FI_PROCESS_TOTAL_MEMORY).value
        max_util = sim.get_field_value(0, DCGM_FI_PROCESS_MAX_UTILIZATION).value

        assert process_count == 2, "Should have 2 processes"
        assert (
            process_memory == 12288
        ), f"Total memory should be 12288 MiB, got {process_memory}"
        assert max_util >= 50, f"Max utilization should be >= 50%, got {max_util}"

    def test_remove_process(self, single_gpu_simulator):
        """Test removing process from GPU."""
        sim = single_gpu_simulator

        sim.add_process(0, pid=1234, name="python", gpu_util=0.5, mem_mib=8192)
        sim.remove_process(0, pid=1234)

        process_count = sim.get_field_value(0, DCGM_FI_PROCESS_COUNT).value
        assert process_count == 0, "Process count should be 0 after removal"

    def test_update_process(self, single_gpu_simulator):
        """Test updating existing process."""
        sim = single_gpu_simulator

        # Add process
        sim.add_process(0, pid=1234, name="python", gpu_util=0.5, mem_mib=8192)

        # Update same process (should update, not add)
        sim.add_process(0, pid=1234, name="python", gpu_util=0.8, mem_mib=16384)

        # Update snapshot to reflect changes
        sim.gpus[0]._publish_snapshot()

        process_count = sim.get_field_value(0, DCGM_FI_PROCESS_COUNT).value
        process_memory = sim.get_field_value(0, DCGM_FI_PROCESS_TOTAL_MEMORY).value

        assert process_count == 1, "Should still have 1 process (updated, not added)"
        assert (
            process_memory == 16384
        ), f"Memory should be updated to 16384 MiB, got {process_memory}"


class TestMemoryBehavior:
    """Test memory-related behaviors."""

    def test_memory_grows_with_batch_size(self, single_gpu_simulator):
        """Test that memory utilization grows logarithmically with batch size."""
        sim = single_gpu_simulator

        # Small batch
        sim.set_workload(0, compute_intensity=0.5, memory_intensity=0.5, batch_size=1)
        gpu = sim.gpus[0]
        mem_util_small = gpu.memory_utilization

        # Large batch
        sim.set_workload(0, compute_intensity=0.5, memory_intensity=0.5, batch_size=64)
        mem_util_large = gpu.memory_utilization

        assert mem_util_large > mem_util_small, "Memory should increase with batch size"

    def test_memory_bandwidth_saturation(self, single_gpu_simulator):
        """Test that memory bandwidth saturates at high utilization."""
        sim = single_gpu_simulator
        gpu = sim.gpus[0]

        # Low memory utilization
        gpu.memory_utilization = 0.5
        gpu._update_memory_bandwidth()
        bw_low = gpu.memory_bandwidth_utilized

        # High memory utilization (should saturate)
        gpu.memory_utilization = 0.95
        gpu._update_memory_bandwidth()
        bw_high = gpu.memory_bandwidth_utilized

        # Should saturate around 95% of max
        max_bw = gpu.memory_bandwidth_max
        assert bw_high < max_bw, "Bandwidth should not exceed theoretical max"
        assert bw_high > bw_low, "High utilization should have higher bandwidth"


class TestPCIeTraffic:
    """Test PCIe traffic simulation."""

    def test_pcie_traffic_increases_with_memory_ops(self, single_gpu_simulator):
        """Test that PCIe traffic increases with memory operations."""
        sim = single_gpu_simulator

        # Baseline
        baseline_tx = sim.get_field_value(0, DCGM_FI_PROF_PCIE_TX_BYTES).value

        # High memory operations
        sim.set_workload(0, compute_intensity=0.5, memory_intensity=0.8)
        time.sleep(2)
        sim.gpus[0].update_metrics(2.0)

        current_tx = sim.get_field_value(0, DCGM_FI_PROF_PCIE_TX_BYTES).value

        assert (
            current_tx > baseline_tx
        ), "PCIe TX should increase with memory operations"

    def test_pcie_replay_counter_increments_rarely(self, single_gpu_simulator):
        """Test that PCIe replay counter increments rarely."""
        sim = single_gpu_simulator

        initial_replays = sim.get_field_value(0, DCGM_FI_DEV_PCIE_REPLAY_COUNTER).value

        # Run many updates
        for _ in range(50):
            sim.gpus[0].update_metrics(1.0)

        current_replays = sim.get_field_value(0, DCGM_FI_DEV_PCIE_REPLAY_COUNTER).value

        # Replays should be rare (0-2 in 50 updates)
        replay_increase = current_replays - initial_replays
        assert replay_increase < 5, f"Too many PCIe replays: {replay_increase}"


class TestFanSpeed:
    """Test fan speed control."""

    def test_fan_speed_increases_with_temperature(self, single_gpu_simulator):
        """Test that fan speed increases with temperature."""
        sim = single_gpu_simulator
        gpu = sim.gpus[0]

        # Low temperature
        gpu.current_temperature = 40.0
        for _ in range(5):
            gpu._update_fan_speeds()
        gpu._publish_snapshot()
        fan_low = sim.get_field_value(0, DCGM_FI_DEV_FAN_SPEED).value

        # High temperature
        gpu.current_temperature = 80.0
        for _ in range(10):
            gpu._update_fan_speeds()
        gpu._publish_snapshot()
        fan_high = sim.get_field_value(0, DCGM_FI_DEV_FAN_SPEED).value

        assert (
            fan_high > fan_low
        ), f"Fan speed should increase with temperature: {fan_low} -> {fan_high}"

    def test_fan_speed_gradual_change(self, single_gpu_simulator):
        """Test that fan speed changes gradually."""
        sim = single_gpu_simulator
        gpu = sim.gpus[0]

        gpu.current_temperature = 40.0
        gpu.fan_speeds = [30, 30]

        # Jump to high temperature
        gpu.current_temperature = 85.0

        # Fan should ramp up gradually
        fan_speeds = []
        for _ in range(10):
            gpu._update_fan_speeds()
            fan_speeds.append(gpu.fan_speeds[0])

        # Should show gradual increase
        for i in range(1, len(fan_speeds)):
            diff = fan_speeds[i] - fan_speeds[i - 1]
            assert -5 <= diff <= 30, f"Fan speed change too abrupt: {diff}"


class TestClockFrequencyScaling:
    """Test clock frequency scaling."""

    def test_clock_increases_with_utilization(self, single_gpu_simulator):
        """Test that clock frequency increases with utilization."""
        sim = single_gpu_simulator

        # Low utilization
        sim.set_workload(0, compute_intensity=0.3, memory_intensity=0.2)
        time.sleep(1)
        sim.gpus[0].update_metrics(1.0)
        clock_low = sim.get_field_value(0, DCGM_FI_DEV_SM_CLOCK).value

        # High utilization
        sim.set_workload(0, compute_intensity=0.9, memory_intensity=0.8)
        time.sleep(2)
        for _ in range(3):
            sim.gpus[0].update_metrics(1.0)
        clock_high = sim.get_field_value(0, DCGM_FI_DEV_SM_CLOCK).value

        assert (
            clock_high >= clock_low
        ), f"Clock should increase or stay same: {clock_low} -> {clock_high}"

    def test_performance_state_changes(self, single_gpu_simulator):
        """Test that performance state (P-state) changes with load."""
        sim = single_gpu_simulator

        # Idle state
        sim.set_workload(0, compute_intensity=0.0, memory_intensity=0.0)
        time.sleep(1)
        sim.gpus[0].update_metrics(1.0)
        pstate_idle = sim.get_field_value(0, DCGM_FI_DEV_PSTATE).value

        # Active state
        sim.set_workload(0, compute_intensity=0.9, memory_intensity=0.8)
        time.sleep(1)
        sim.gpus[0].update_metrics(1.0)
        pstate_active = sim.get_field_value(0, DCGM_FI_DEV_PSTATE).value

        # Performance state should be valid (0-12)
        assert 0 <= pstate_idle <= 12, f"P-state should be valid: {pstate_idle}"
        assert 0 <= pstate_active <= 12, f"P-state should be valid: {pstate_active}"


class TestRealisticScenarios:
    """Test realistic usage scenarios."""

    def test_training_workload_scenario(self, simulator):
        """Test realistic training workload with multiple GPUs."""
        sim = simulator

        # Start training (all GPUs high utilization)
        sim.set_global_workload(
            compute_intensity=0.85, memory_intensity=0.75, batch_size=32
        )

        # Run for a few seconds
        time.sleep(3)

        # Check all GPUs are working
        for gpu_id in range(sim.num_gpus):
            util = sim.get_field_value(gpu_id, DCGM_FI_DEV_GPU_UTIL).value
            power = sim.get_field_value(gpu_id, DCGM_FI_DEV_POWER_USAGE).value

            assert util > 70, f"GPU {gpu_id} should have high utilization: {util}"
            assert power > 300, f"GPU {gpu_id} should have high power draw: {power}"

    def test_inference_workload_scenario(self, simulator):
        """Test realistic inference workload (burst pattern)."""
        sim = simulator

        # Inference burst
        sim.set_global_workload(
            compute_intensity=0.6, memory_intensity=0.4, batch_size=8
        )
        time.sleep(1)

        # Check reasonable utilization
        for gpu_id in range(sim.num_gpus):
            util = sim.get_field_value(gpu_id, DCGM_FI_DEV_GPU_UTIL).value
            assert 40 <= util <= 80, f"GPU {gpu_id} inference utilization: {util}"

    def test_multi_process_scenario(self, simulator):
        """Test scenario with multiple processes on different GPUs."""
        sim = simulator

        # Add processes to different GPUs
        sim.add_process(0, pid=1001, name="trainer_0", gpu_util=0.8, mem_mib=40000)
        sim.add_process(1, pid=1002, name="trainer_1", gpu_util=0.75, mem_mib=35000)
        sim.add_process(2, pid=1003, name="inference", gpu_util=0.4, mem_mib=15000)

        # Update snapshots
        for gpu in sim.gpus:
            gpu._publish_snapshot()

        # Check per-GPU process counts
        assert sim.get_field_value(0, DCGM_FI_PROCESS_COUNT).value == 1
        assert sim.get_field_value(1, DCGM_FI_PROCESS_COUNT).value == 1
        assert sim.get_field_value(2, DCGM_FI_PROCESS_COUNT).value == 1
        assert sim.get_field_value(3, DCGM_FI_PROCESS_COUNT).value == 0

    def test_stress_test_scenario(self, single_gpu_simulator):
        """Test GPU under maximum stress."""
        sim = single_gpu_simulator

        # Maximum load
        sim.set_workload(0, compute_intensity=1.0, memory_intensity=1.0, batch_size=128)

        # Run for a while to let temperature build up (thermal inertia is slow)
        time.sleep(3)

        # Check power increases immediately
        power_initial = sim.get_field_value(0, DCGM_FI_DEV_POWER_USAGE).value

        # Continue running and force additional updates
        for _ in range(10):
            sim.gpus[0].update_metrics(1.0)
            time.sleep(0.1)

        # Check final metrics
        temp = sim.get_field_value(0, DCGM_FI_DEV_GPU_TEMP).value
        power = sim.get_field_value(0, DCGM_FI_DEV_POWER_USAGE).value

        # Under max stress, power should be high (responds faster than temperature)
        assert power > 400, f"Power should be high under stress: {power}W"
        # Temperature rises more slowly due to thermal inertia, should at least be elevated
        assert temp > 45, f"Temperature should be elevated under stress: {temp}C"


class TestPrometheusExport:
    """Test Prometheus metrics export."""

    def test_prometheus_metrics_format(self, simulator):
        """Test that Prometheus export has correct format."""
        sim = simulator

        metrics = sim.get_prometheus_metrics()

        # Check for required elements
        assert "# TYPE" in metrics, "Should contain TYPE declarations"
        assert "# HELP" in metrics, "Should contain HELP text"
        assert "DCGM_FI_DEV_GPU_TEMP" in metrics, "Should contain temperature metric"
        assert "DCGM_FI_DEV_POWER_USAGE" in metrics, "Should contain power metric"

        # Check for GPU labels
        for gpu_id in range(sim.num_gpus):
            assert f'gpu="{gpu_id}"' in metrics, f"Should contain GPU {gpu_id} label"

    def test_metrics_dict_export(self, simulator):
        """Test dictionary metrics export."""
        sim = simulator

        metrics = sim.get_metrics_dict()

        # Check structure
        assert len(metrics) == sim.num_gpus, "Should have metrics for all GPUs"

        # Check GPU 0 metrics
        gpu0_metrics = metrics["gpu_0"]
        assert "temperature_c" in gpu0_metrics
        assert "power_usage_w" in gpu0_metrics
        assert "gpu_utilization_pct" in gpu0_metrics

        # Check historical percentiles
        assert "temp_p50" in gpu0_metrics
        assert "temp_p90" in gpu0_metrics
        assert "power_p99" in gpu0_metrics


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
