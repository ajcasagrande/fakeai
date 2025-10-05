"""
DCGM (Data Center GPU Manager) Metrics Simulator.

Simulates NVIDIA DCGM metrics for GPU monitoring without requiring actual GPUs.
Generates realistic GPU utilization, temperature, power, memory, and health metrics
based on simulated workload characteristics.
"""
import random
import threading
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class GPUArchitecture(Enum):
    """GPU architecture types."""
    AMPERE = "ampere"    # A100, A10, A30
    HOPPER = "hopper"    # H100, H200
    BLACKWELL = "blackwell"  # B100, B200


@dataclass
class GPUSpec:
    """GPU specifications."""
    name: str
    architecture: GPUArchitecture
    memory_total_mib: int
    sm_count: int
    base_clock_mhz: int
    memory_clock_mhz: int
    power_limit_watts: float
    max_temp_celsius: int
    nvlink_count: int = 0


# GPU model specifications
GPU_SPECS = {
    "A100-80GB": GPUSpec("NVIDIA A100-SXM4-80GB", GPUArchitecture.AMPERE, 81920, 108, 1410, 1512, 400.0, 90, 12),
    "H100-80GB": GPUSpec("NVIDIA H100 80GB HBM3", GPUArchitecture.HOPPER, 81920, 132, 1830, 2619, 700.0, 90, 18),
    "H200-141GB": GPUSpec("NVIDIA H200 141GB HBM3e", GPUArchitecture.HOPPER, 144896, 132, 1980, 4800, 700.0, 90, 18),
}


@dataclass
class DCGMFieldValue:
    """DCGM field value with timestamp."""
    field_id: int
    value: Any
    timestamp: int  # Unix timestamp in microseconds
    field_type: str  # 'd' (double), 'i' (int64), 's' (string)


class SimulatedGPU:
    """
    Simulated GPU with DCGM-compatible metrics.

    Generates realistic metrics based on workload simulation and maintains
    consistency between related metrics (e.g., utilization affects temperature).
    """

    def __init__(self, gpu_id: int, spec: GPUSpec):
        self.gpu_id = gpu_id
        self.spec = spec
        self.uuid = f"GPU-{gpu_id:08x}-simulated"
        self.device_name = f"nvidia{gpu_id}"

        # Current state
        self.workload_utilization = 0.0  # 0.0-1.0
        self.memory_utilization = 0.0
        self.base_temperature = 40.0  # Idle temperature
        self.current_temperature = 40.0
        self.current_power = 50.0  # Idle power

        # Accumulated metrics
        self.total_energy_mj = 0  # millijoules
        self.pcie_replay_count = 0
        self.ecc_sbe_total = 0
        self.ecc_dbe_total = 0

        # Performance state
        self.current_sm_clock = spec.base_clock_mhz
        self.current_mem_clock = spec.memory_clock_mhz

        self._lock = threading.Lock()

    def set_workload(self, compute_intensity: float, memory_intensity: float):
        """
        Set simulated workload characteristics.

        Args:
            compute_intensity: 0.0-1.0 (GPU compute utilization)
            memory_intensity: 0.0-1.0 (Memory utilization)
        """
        with self._lock:
            self.workload_utilization = max(0.0, min(1.0, compute_intensity))
            self.memory_utilization = max(0.0, min(1.0, memory_intensity))

    def update_metrics(self, delta_seconds: float = 1.0):
        """
        Update all metrics based on elapsed time.

        Args:
            delta_seconds: Time elapsed since last update
        """
        with self._lock:
            # Update temperature (thermal inertia)
            target_temp = self.base_temperature + (self.workload_utilization * 45.0)
            temp_diff = target_temp - self.current_temperature
            self.current_temperature += temp_diff * 0.3  # 30% movement per second

            # Add thermal noise
            self.current_temperature += random.uniform(-0.5, 0.5)
            self.current_temperature = max(30.0, min(self.spec.max_temp_celsius, self.current_temperature))

            # Update power consumption
            idle_power = 50.0
            active_power = self.spec.power_limit_watts
            self.current_power = idle_power + (active_power - idle_power) * self.workload_utilization
            self.current_power += random.uniform(-10, 10)  # Power variation

            # Update total energy (power * time)
            energy_joules = self.current_power * delta_seconds
            self.total_energy_mj += int(energy_joules * 1000)  # Convert to millijoules

            # Simulate rare errors
            if random.random() < 0.00001:  # Very rare
                self.ecc_sbe_total += 1
            if random.random() < 0.0000001:  # Extremely rare
                self.ecc_dbe_total += 1

    def get_field_value(self, field_id: int) -> DCGMFieldValue:
        """
        Get current value for a DCGM field ID.

        Args:
            field_id: DCGM field identifier

        Returns:
            DCGMFieldValue with current value
        """
        timestamp = int(time.time() * 1_000_000)  # Microseconds

        with self._lock:
            # Device information (50-99)
            if field_id == 50:  # DCGM_FI_DEV_NAME
                return DCGMFieldValue(field_id, self.spec.name, timestamp, 's')
            elif field_id == 54:  # DCGM_FI_DEV_UUID
                return DCGMFieldValue(field_id, self.uuid, timestamp, 's')

            # Clocks (100-109)
            elif field_id == 100:  # DCGM_FI_DEV_SM_CLOCK
                clock_variation = int(self.workload_utilization * 100)
                return DCGMFieldValue(field_id, self.current_sm_clock + clock_variation, timestamp, 'i')
            elif field_id == 101:  # DCGM_FI_DEV_MEM_CLOCK
                return DCGMFieldValue(field_id, self.current_mem_clock, timestamp, 'i')

            # Temperature (150-159)
            elif field_id == 150:  # DCGM_FI_DEV_GPU_TEMP
                return DCGMFieldValue(field_id, int(self.current_temperature), timestamp, 'i')

            # Power (155-159)
            elif field_id == 155:  # DCGM_FI_DEV_POWER_USAGE
                return DCGMFieldValue(field_id, self.current_power, timestamp, 'd')
            elif field_id == 156:  # DCGM_FI_DEV_TOTAL_ENERGY_CONSUMPTION
                return DCGMFieldValue(field_id, self.total_energy_mj, timestamp, 'i')

            # Utilization (203-209)
            elif field_id == 203:  # DCGM_FI_DEV_GPU_UTIL
                util_pct = int(self.workload_utilization * 100)
                return DCGMFieldValue(field_id, util_pct, timestamp, 'i')
            elif field_id == 204:  # DCGM_FI_DEV_MEM_COPY_UTIL
                mem_util_pct = int(self.memory_utilization * 100)
                return DCGMFieldValue(field_id, mem_util_pct, timestamp, 'i')
            elif field_id == 208:  # DCGM_FI_DEV_PCIE_REPLAY_COUNTER
                return DCGMFieldValue(field_id, self.pcie_replay_count, timestamp, 'i')

            # Memory (250-259)
            elif field_id == 250:  # DCGM_FI_DEV_FB_FREE
                used_mib = int(self.spec.memory_total_mib * self.memory_utilization)
                free_mib = self.spec.memory_total_mib - used_mib
                return DCGMFieldValue(field_id, free_mib, timestamp, 'i')
            elif field_id == 251:  # DCGM_FI_DEV_FB_USED
                used_mib = int(self.spec.memory_total_mib * self.memory_utilization)
                return DCGMFieldValue(field_id, used_mib, timestamp, 'i')
            elif field_id == 253:  # DCGM_FI_DEV_FB_TOTAL
                return DCGMFieldValue(field_id, self.spec.memory_total_mib, timestamp, 'i')

            # ECC Errors (600-650)
            elif field_id == 610:  # DCGM_FI_DEV_ECC_SBE_VOL_TOTAL
                return DCGMFieldValue(field_id, self.ecc_sbe_total, timestamp, 'i')
            elif field_id == 620:  # DCGM_FI_DEV_ECC_DBE_VOL_TOTAL
                return DCGMFieldValue(field_id, self.ecc_dbe_total, timestamp, 'i')

            # Profiling metrics (1001-1012)
            elif field_id == 1002:  # DCGM_FI_PROF_SM_ACTIVE
                sm_active = self.workload_utilization * 100
                return DCGMFieldValue(field_id, sm_active, timestamp, 'd')
            elif field_id == 1003:  # DCGM_FI_PROF_SM_OCCUPANCY
                occupancy = self.workload_utilization * random.uniform(0.6, 0.9) * 100
                return DCGMFieldValue(field_id, occupancy, timestamp, 'd')
            elif field_id == 1004:  # DCGM_FI_PROF_PIPE_TENSOR_ACTIVE
                # Tensor cores active when doing AI/ML work
                tensor_active = self.workload_utilization * random.uniform(0.7, 0.95) * 100
                return DCGMFieldValue(field_id, tensor_active, timestamp, 'd')
            elif field_id == 1005:  # DCGM_FI_PROF_DRAM_ACTIVE
                dram_active = self.memory_utilization * 100
                return DCGMFieldValue(field_id, dram_active, timestamp, 'd')
            elif field_id == 1009:  # DCGM_FI_PROF_PCIE_TX_BYTES
                # PCIe TX increases with memory transfers
                pcie_tx = int(self.memory_utilization * 10_000_000_000)  # Up to 10 GB/s
                return DCGMFieldValue(field_id, pcie_tx, timestamp, 'i')
            elif field_id == 1010:  # DCGM_FI_PROF_PCIE_RX_BYTES
                pcie_rx = int(self.memory_utilization * 5_000_000_000)  # Up to 5 GB/s
                return DCGMFieldValue(field_id, pcie_rx, timestamp, 'i')
            elif field_id == 1011:  # DCGM_FI_PROF_NVLINK_TX_BYTES
                if self.spec.nvlink_count > 0:
                    nvlink_tx = int(self.memory_utilization * 50_000_000_000)  # Up to 50 GB/s
                    return DCGMFieldValue(field_id, nvlink_tx, timestamp, 'i')
                return DCGMFieldValue(field_id, 0, timestamp, 'i')
            elif field_id == 1012:  # DCGM_FI_PROF_NVLINK_RX_BYTES
                if self.spec.nvlink_count > 0:
                    nvlink_rx = int(self.memory_utilization * 50_000_000_000)
                    return DCGMFieldValue(field_id, nvlink_rx, timestamp, 'i')
                return DCGMFieldValue(field_id, 0, timestamp, 'i')

            else:
                # Unknown field - return blank
                return DCGMFieldValue(field_id, 0, timestamp, 'i')


class DCGMMetricsSimulator:
    """
    Simulates NVIDIA DCGM GPU metrics for testing and development.

    Creates virtual GPUs and generates realistic metrics based on
    simulated workload characteristics.
    """

    def __init__(self, num_gpus: int = 4, gpu_model: str = "H100-80GB"):
        """
        Initialize DCGM metrics simulator.

        Args:
            num_gpus: Number of GPUs to simulate
            gpu_model: GPU model spec (A100-80GB, H100-80GB, H200-141GB)
        """
        self.num_gpus = num_gpus
        self.gpu_spec = GPU_SPECS.get(gpu_model, GPU_SPECS["H100-80GB"])

        # Create simulated GPUs
        self.gpus = [SimulatedGPU(i, self.gpu_spec) for i in range(num_gpus)]

        # Background update thread
        self._stop_event = threading.Event()
        self._update_thread = threading.Thread(target=self._update_loop, daemon=True)
        self._update_thread.start()

        self._lock = threading.Lock()

    def set_workload(self, gpu_id: int, compute_intensity: float, memory_intensity: float):
        """Set workload for specific GPU."""
        if 0 <= gpu_id < self.num_gpus:
            self.gpus[gpu_id].set_workload(compute_intensity, memory_intensity)

    def set_global_workload(self, compute_intensity: float, memory_intensity: float):
        """Set workload for all GPUs."""
        for gpu in self.gpus:
            gpu.set_workload(compute_intensity, memory_intensity)

    def _update_loop(self):
        """Background thread to update GPU metrics."""
        last_update = time.time()

        while not self._stop_event.is_set():
            time.sleep(1.0)  # Update every second

            current_time = time.time()
            delta = current_time - last_update

            # Update all GPUs
            for gpu in self.gpus:
                gpu.update_metrics(delta)

            last_update = current_time

    def get_field_value(self, gpu_id: int, field_id: int) -> DCGMFieldValue:
        """Get current field value for specific GPU."""
        if 0 <= gpu_id < self.num_gpus:
            return self.gpus[gpu_id].get_field_value(field_id)
        return DCGMFieldValue(field_id, 0, int(time.time() * 1_000_000), 'i')

    def get_all_gpu_field_values(self, field_id: int) -> dict[int, DCGMFieldValue]:
        """Get field value from all GPUs."""
        return {gpu.gpu_id: gpu.get_field_value(field_id) for gpu in self.gpus}

    def get_prometheus_metrics(self) -> str:
        """Export metrics in Prometheus/DCGM-exporter format."""
        lines = []

        # Field ID definitions
        fields = {
            100: ("DCGM_FI_DEV_SM_CLOCK", "gauge", "SM clock frequency (MHz)"),
            101: ("DCGM_FI_DEV_MEM_CLOCK", "gauge", "Memory clock frequency (MHz)"),
            150: ("DCGM_FI_DEV_GPU_TEMP", "gauge", "GPU temperature (C)"),
            155: ("DCGM_FI_DEV_POWER_USAGE", "gauge", "Power draw (W)"),
            156: ("DCGM_FI_DEV_TOTAL_ENERGY_CONSUMPTION", "counter", "Total energy consumption (mJ)"),
            203: ("DCGM_FI_DEV_GPU_UTIL", "gauge", "GPU utilization (%)"),
            204: ("DCGM_FI_DEV_MEM_COPY_UTIL", "gauge", "Memory utilization (%)"),
            208: ("DCGM_FI_DEV_PCIE_REPLAY_COUNTER", "counter", "PCIe replay counter"),
            250: ("DCGM_FI_DEV_FB_FREE", "gauge", "Framebuffer memory free (MiB)"),
            251: ("DCGM_FI_DEV_FB_USED", "gauge", "Framebuffer memory used (MiB)"),
            253: ("DCGM_FI_DEV_FB_TOTAL", "gauge", "Framebuffer memory total (MiB)"),
            610: ("DCGM_FI_DEV_ECC_SBE_VOL_TOTAL", "counter", "Total single-bit ECC errors"),
            620: ("DCGM_FI_DEV_ECC_DBE_VOL_TOTAL", "counter", "Total double-bit ECC errors"),
            1002: ("DCGM_FI_PROF_SM_ACTIVE", "gauge", "SM active (%)"),
            1003: ("DCGM_FI_PROF_SM_OCCUPANCY", "gauge", "SM occupancy (%)"),
            1004: ("DCGM_FI_PROF_PIPE_TENSOR_ACTIVE", "gauge", "Tensor pipe active (%)"),
            1005: ("DCGM_FI_PROF_DRAM_ACTIVE", "gauge", "DRAM active (%)"),
            1009: ("DCGM_FI_PROF_PCIE_TX_BYTES", "gauge", "PCIe TX (bytes)"),
            1010: ("DCGM_FI_PROF_PCIE_RX_BYTES", "gauge", "PCIe RX (bytes)"),
        }

        # Generate metrics
        for field_id, (name, metric_type, help_text) in fields.items():
            # Add TYPE and HELP
            lines.append(f"# TYPE {name} {metric_type}")
            lines.append(f"# HELP {name} {help_text}")

            # Add values for each GPU
            for gpu in self.gpus:
                field_value = gpu.get_field_value(field_id)
                labels = f'gpu="{gpu.gpu_id}",UUID="{gpu.uuid}",device="{gpu.device_name}",modelName="{self.gpu_spec.name}"'
                lines.append(f"{name}{{{labels}}} {field_value.value}")

            lines.append("")  # Blank line between metrics

        return "\n".join(lines)

    def get_metrics_dict(self) -> dict[str, Any]:
        """Export metrics as dictionary."""
        metrics = {}

        for gpu in self.gpus:
            gpu_metrics = {
                "gpu_id": gpu.gpu_id,
                "uuid": gpu.uuid,
                "name": self.gpu_spec.name,
                "architecture": self.gpu_spec.architecture.value,
                "sm_clock_mhz": gpu.get_field_value(100).value,
                "memory_clock_mhz": gpu.get_field_value(101).value,
                "temperature_c": gpu.get_field_value(150).value,
                "power_usage_w": gpu.get_field_value(155).value,
                "total_energy_mj": gpu.get_field_value(156).value,
                "gpu_utilization_pct": gpu.get_field_value(203).value,
                "memory_utilization_pct": gpu.get_field_value(204).value,
                "memory_free_mib": gpu.get_field_value(250).value,
                "memory_used_mib": gpu.get_field_value(251).value,
                "memory_total_mib": gpu.get_field_value(253).value,
                "ecc_sbe_total": gpu.get_field_value(610).value,
                "ecc_dbe_total": gpu.get_field_value(620).value,
                "sm_active_pct": gpu.get_field_value(1002).value,
                "sm_occupancy_pct": gpu.get_field_value(1003).value,
                "tensor_active_pct": gpu.get_field_value(1004).value,
                "dram_active_pct": gpu.get_field_value(1005).value,
                "pcie_tx_bytes": gpu.get_field_value(1009).value,
                "pcie_rx_bytes": gpu.get_field_value(1010).value,
            }

            metrics[f"gpu_{gpu.gpu_id}"] = gpu_metrics

        return metrics

    def shutdown(self):
        """Stop background metric updates."""
        self._stop_event.set()
        self._update_thread.join(timeout=2.0)


# DCGM Field ID constants (subset of most important)
DCGM_FI_DEV_NAME = 50
DCGM_FI_DEV_UUID = 54
DCGM_FI_DEV_SM_CLOCK = 100
DCGM_FI_DEV_MEM_CLOCK = 101
DCGM_FI_DEV_GPU_TEMP = 150
DCGM_FI_DEV_POWER_USAGE = 155
DCGM_FI_DEV_TOTAL_ENERGY_CONSUMPTION = 156
DCGM_FI_DEV_GPU_UTIL = 203
DCGM_FI_DEV_MEM_COPY_UTIL = 204
DCGM_FI_DEV_PCIE_REPLAY_COUNTER = 208
DCGM_FI_DEV_FB_FREE = 250
DCGM_FI_DEV_FB_USED = 251
DCGM_FI_DEV_FB_TOTAL = 253
DCGM_FI_DEV_ECC_SBE_VOL_TOTAL = 610
DCGM_FI_DEV_ECC_DBE_VOL_TOTAL = 620
DCGM_FI_PROF_SM_ACTIVE = 1002
DCGM_FI_PROF_SM_OCCUPANCY = 1003
DCGM_FI_PROF_PIPE_TENSOR_ACTIVE = 1004
DCGM_FI_PROF_DRAM_ACTIVE = 1005
DCGM_FI_PROF_PCIE_TX_BYTES = 1009
DCGM_FI_PROF_PCIE_RX_BYTES = 1010
DCGM_FI_PROF_NVLINK_TX_BYTES = 1011
DCGM_FI_PROF_NVLINK_RX_BYTES = 1012
