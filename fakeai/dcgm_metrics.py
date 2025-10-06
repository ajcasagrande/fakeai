"""
DCGM (Data Center GPU Manager) Metrics Simulator - EXTREME Edition.

Simulates NVIDIA DCGM metrics for GPU monitoring without requiring actual GPUs.
Generates EXTREMELY realistic GPU utilization, temperature, power, memory, health,
NVLink traffic, ECC errors, throttling, multi-GPU coordination, and historical tracking
based on simulated workload characteristics.

Features:
- 100+ DCGM fields (comprehensive coverage)
- Multi-GPU coordination with NVLink traffic
- Thermal throttling and power limits
- Workload-based memory, temperature, and power dynamics
- ECC error simulation under stress
- Historical tracking (60s window) with percentiles
- Per-process GPU/memory tracking
- PCIe replay counters and bandwidth saturation
- NCCL collective operations simulation
- P2P memory transfers
"""

import collections
import math
import random
import threading
import time
from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Deque


class GPUArchitecture(Enum):
    """GPU architecture types."""

    AMPERE = "ampere"  # A100, A10, A30
    HOPPER = "hopper"  # H100, H200
    BLACKWELL = "blackwell"  # B100, B200


@dataclass
class GPUSpec:
    """GPU specifications."""

    name: str
    architecture: GPUArchitecture
    memory_total_mib: int
    sm_count: int
    base_clock_mhz: int
    max_clock_mhz: int
    memory_clock_mhz: int
    power_limit_watts: float
    max_temp_celsius: int
    throttle_temp_celsius: int
    nvlink_count: int = 0
    nvlink_bandwidth_gbps: float = 0.0  # Per-link bandwidth
    pcie_gen: int = 4
    pcie_lanes: int = 16
    fan_count: int = 1


# GPU model specifications
GPU_SPECS = {
    "A100-80GB": GPUSpec(
        "NVIDIA A100-SXM4-80GB",
        GPUArchitecture.AMPERE,
        81920,
        108,
        1410,
        1410,
        1512,
        400.0,
        90,
        85,
        12,
        600.0,
        4,
        16,
        2,
    ),
    "H100-80GB": GPUSpec(
        "NVIDIA H100 80GB HBM3",
        GPUArchitecture.HOPPER,
        81920,
        132,
        1830,
        1980,
        2619,
        700.0,
        90,
        85,
        18,
        900.0,
        5,
        16,
        2,
    ),
    "H200-141GB": GPUSpec(
        "NVIDIA H200 141GB HBM3e",
        GPUArchitecture.HOPPER,
        144896,
        132,
        1980,
        2100,
        4800,
        700.0,
        90,
        85,
        18,
        900.0,
        5,
        16,
        2,
    ),
}


@dataclass
class DCGMFieldValue:
    """DCGM field value with timestamp."""

    field_id: int
    value: Any
    timestamp: int  # Unix timestamp in microseconds
    field_type: str  # 'd' (double), 'i' (int64), 's' (string)


@dataclass
class HistoricalMetric:
    """Historical tracking for a single metric."""

    values: Deque[float] = field(default_factory=lambda: deque(maxlen=60))  # 60 seconds

    def add(self, value: float):
        self.values.append(value)

    def get_min(self) -> float:
        return min(self.values) if self.values else 0.0

    def get_max(self) -> float:
        return max(self.values) if self.values else 0.0

    def get_avg(self) -> float:
        return sum(self.values) / len(self.values) if self.values else 0.0

    def get_percentile(self, p: int) -> float:
        """Get percentile (p=50 for median, p=90, p=99, etc.)"""
        if not self.values:
            return 0.0
        sorted_vals = sorted(self.values)
        idx = int(len(sorted_vals) * p / 100.0)
        return sorted_vals[min(idx, len(sorted_vals) - 1)]


@dataclass
class ProcessInfo:
    """Per-process GPU/memory usage."""

    pid: int
    name: str
    gpu_utilization: float  # 0.0-1.0
    memory_mib: int
    sm_utilization: float
    encoder_utilization: float
    decoder_utilization: float


@dataclass
class ThrottleReason:
    """GPU throttling reasons."""

    thermal: bool = False
    power: bool = False
    hw_slowdown: bool = False
    sw_thermal: bool = False
    sync_boost: bool = False


class SlowdownReason(Enum):
    """Why GPU is running slower than expected."""

    NONE = 0
    HW_THERMAL = 1  # Hardware thermal protection
    HW_POWER_BRAKE = 2  # Hardware power brake
    SW_THERMAL = 4  # Software thermal slowdown
    IDLE = 8  # GPU idle
    APP_CLOCK = 16  # Application clock setting


class SimulatedGPU:
    """
    Simulated GPU with DCGM-compatible metrics - EXTREME REALISM.

    Generates realistic metrics based on workload simulation with:
    - Thermal inertia and throttling
    - Power settling and correlation
    - ECC errors under stress
    - NVLink traffic coordination
    - Historical tracking
    - Process-level stats

    Uses lock-free snapshot pattern: background thread updates state and publishes
    complete snapshots; readers access latest snapshot without blocking.
    """

    def __init__(self, gpu_id: int, spec: GPUSpec, simulator: "DCGMMetricsSimulator"):
        self.gpu_id = gpu_id
        self.spec = spec
        self.simulator = simulator
        self.uuid = f"GPU-{gpu_id:08x}-{random.randint(0, 0xffffff):06x}-simulated"
        self.device_name = f"nvidia{gpu_id}"
        self.pci_bus_id = f"00000000:{gpu_id:02X}:00.0"

        # Current state (written by background thread only)
        self.workload_utilization = 0.0  # 0.0-1.0
        self.memory_utilization = 0.0
        self.base_temperature = 40.0  # Idle temperature
        self.current_temperature = 40.0
        self.current_power = 50.0  # Idle power
        self.memory_temp = 35.0
        self.hotspot_temp = 45.0

        # Thermal inertia parameters
        self.thermal_mass = 200.0  # Higher = slower temperature changes
        self.thermal_conductivity = 0.3  # Heat transfer rate

        # Power settling
        self.power_target = 50.0
        self.power_settling_rate = 0.4  # How fast power converges to target

        # Accumulated metrics
        self.total_energy_mj = 0  # millijoules
        self.pcie_replay_count = 0
        self.ecc_sbe_total = 0
        self.ecc_dbe_total = 0
        self.ecc_sbe_l1 = 0
        self.ecc_sbe_l2 = 0
        self.ecc_sbe_device = 0
        self.ecc_sbe_register = 0
        self.ecc_sbe_texture = 0
        self.xid_errors = 0

        # Memory bandwidth tracking
        self.memory_bandwidth_utilized = 0.0  # GB/s
        self.memory_bandwidth_max = self._calculate_max_memory_bandwidth()

        # NVLink per-link stats
        self.nvlink_tx_bytes = [0] * spec.nvlink_count
        self.nvlink_rx_bytes = [0] * spec.nvlink_count
        self.nvlink_crc_errors = [0] * spec.nvlink_count
        self.nvlink_recovery_errors = [0] * spec.nvlink_count
        self.nvlink_replay_errors = [0] * spec.nvlink_count

        # PCIe stats
        self.pcie_tx_bytes = 0
        self.pcie_rx_bytes = 0
        self.pcie_tx_throughput = 0.0  # Current throughput GB/s
        self.pcie_rx_throughput = 0.0

        # Performance state
        self.current_sm_clock = spec.base_clock_mhz
        self.current_mem_clock = spec.memory_clock_mhz
        self.target_sm_clock = spec.base_clock_mhz
        self.throttle_reasons = ThrottleReason()
        self.slowdown_reason = SlowdownReason.NONE
        self.performance_state = 0  # P0-P12, 0=max performance

        # Fan control
        self.fan_speeds = [40] * spec.fan_count  # Percentage 0-100

        # Process tracking
        self.processes: list[ProcessInfo] = []

        # Historical tracking (60 seconds)
        self.history = {
            "temperature": HistoricalMetric(),
            "power": HistoricalMetric(),
            "utilization": HistoricalMetric(),
            "memory_util": HistoricalMetric(),
            "sm_clock": HistoricalMetric(),
        }

        # NCCL and collective operations
        self.nccl_active = False
        self.collective_op_count = 0
        self.p2p_bytes_sent = [0] * 8  # To other GPUs
        self.p2p_bytes_received = [0] * 8

        # Published snapshot (lock-free read, atomic write)
        self._snapshot_cache: dict[int, DCGMFieldValue] = {}
        self._write_lock = threading.Lock()  # Only for workload updates

        # Initialize snapshot immediately
        self._publish_snapshot()

    def _calculate_max_memory_bandwidth(self) -> float:
        """Calculate theoretical max memory bandwidth in GB/s."""
        if self.spec.architecture == GPUArchitecture.HOPPER:
            return 3350.0  # H100: ~3.35 TB/s
        elif self.spec.architecture == GPUArchitecture.AMPERE:
            return 2039.0  # A100: ~2 TB/s
        return 1555.0  # Default

    def set_workload(
        self, compute_intensity: float, memory_intensity: float, batch_size: int = 1
    ):
        """
        Set simulated workload characteristics.

        Args:
            compute_intensity: 0.0-1.0 (GPU compute utilization)
            memory_intensity: 0.0-1.0 (Memory utilization)
            batch_size: Batch size affects memory growth
        """
        with self._write_lock:
            self.workload_utilization = max(0.0, min(1.0, compute_intensity))
            # Memory grows with batch size (logarithmically)
            base_memory = max(0.0, min(1.0, memory_intensity))
            memory_multiplier = 1.0 + (math.log(batch_size) / 10.0)
            self.memory_utilization = min(1.0, base_memory * memory_multiplier)

    def start_collective_operation(self, op_type: str = "allreduce"):
        """Start a NCCL collective operation."""
        with self._write_lock:
            self.nccl_active = True
            self.collective_op_count += 1

    def end_collective_operation(self):
        """End NCCL collective operation."""
        with self._write_lock:
            self.nccl_active = False

    def add_process(self, pid: int, name: str, gpu_util: float, mem_mib: int):
        """Add or update process GPU usage."""
        with self._write_lock:
            # Update existing or add new
            for proc in self.processes:
                if proc.pid == pid:
                    proc.gpu_utilization = gpu_util
                    proc.memory_mib = mem_mib
                    return

            # Add new process
            self.processes.append(
                ProcessInfo(
                    pid=pid,
                    name=name,
                    gpu_utilization=gpu_util,
                    memory_mib=mem_mib,
                    sm_utilization=gpu_util * random.uniform(0.8, 1.0),
                    encoder_utilization=random.uniform(0.0, 0.3),
                    decoder_utilization=random.uniform(0.0, 0.2),
                )
            )

    def remove_process(self, pid: int):
        """Remove process from tracking."""
        with self._write_lock:
            self.processes = [p for p in self.processes if p.pid != pid]

    def update_metrics(self, delta_seconds: float = 1.0):
        """
        Update all metrics based on elapsed time and publish snapshot.
        Called by background thread only - no locking needed for reads.

        Args:
            delta_seconds: Time elapsed since last update
        """
        # Update thermal dynamics with inertia
        target_temp = self._calculate_target_temperature()
        temp_diff = target_temp - self.current_temperature
        thermal_response = self.thermal_conductivity / self.thermal_mass
        self.current_temperature += temp_diff * thermal_response * delta_seconds * 10

        # Add thermal noise
        self.current_temperature += random.uniform(-0.5, 0.5)
        self.current_temperature = max(
            30.0, min(self.spec.max_temp_celsius + 5, self.current_temperature)
        )

        # Memory temperature follows GPU temp with lag
        self.memory_temp = self.current_temperature * 0.85 + random.uniform(-2, 2)
        self.hotspot_temp = self.current_temperature * 1.1 + random.uniform(0, 5)

        # Check for thermal throttling
        self._update_throttling()

        # Update clocks based on throttling
        self._update_clock_frequencies()

        # Update power consumption with settling
        self._update_power_consumption(delta_seconds)

        # Update total energy (power * time)
        energy_joules = self.current_power * delta_seconds
        self.total_energy_mj += int(energy_joules * 1000)  # Convert to millijoules

        # Update memory bandwidth utilization
        self._update_memory_bandwidth()

        # Update PCIe traffic
        self._update_pcie_traffic(delta_seconds)

        # Update NVLink traffic (coordinated with other GPUs)
        self._update_nvlink_traffic(delta_seconds)

        # Update fan speeds based on temperature
        self._update_fan_speeds()

        # Simulate ECC errors under stress
        self._simulate_ecc_errors()

        # Simulate PCIe replays (rare)
        if random.random() < 0.0001:
            self.pcie_replay_count += 1

        # Simulate XID errors (very rare)
        if random.random() < 0.00001:
            self.xid_errors += 1

        # Update historical tracking
        self.history["temperature"].add(self.current_temperature)
        self.history["power"].add(self.current_power)
        self.history["utilization"].add(self.workload_utilization * 100)
        self.history["memory_util"].add(self.memory_utilization * 100)
        self.history["sm_clock"].add(float(self.current_sm_clock))

        # Publish complete snapshot (atomic replacement)
        self._publish_snapshot()

    def _calculate_target_temperature(self) -> float:
        """Calculate target temperature based on workload and throttling."""
        # Base temperature increases with utilization
        target = self.base_temperature + (self.workload_utilization * 45.0)

        # Memory operations add heat
        target += self.memory_utilization * 5.0

        # NVLink activity adds heat
        if self.nccl_active:
            target += 3.0

        # Throttling reduces target
        if self.throttle_reasons.thermal:
            target = min(target, self.spec.throttle_temp_celsius - 2)

        return target

    def _update_throttling(self):
        """Update throttling state based on temperature and power."""
        # Thermal throttling
        if self.current_temperature >= self.spec.throttle_temp_celsius:
            self.throttle_reasons.thermal = True
            self.slowdown_reason = SlowdownReason.HW_THERMAL
        elif self.current_temperature < self.spec.throttle_temp_celsius - 3:
            self.throttle_reasons.thermal = False
            if self.slowdown_reason == SlowdownReason.HW_THERMAL:
                self.slowdown_reason = SlowdownReason.NONE

        # Power throttling
        if self.current_power >= self.spec.power_limit_watts * 0.98:
            self.throttle_reasons.power = True
            self.slowdown_reason = SlowdownReason.HW_POWER_BRAKE
        else:
            self.throttle_reasons.power = False
            if self.slowdown_reason == SlowdownReason.HW_POWER_BRAKE:
                self.slowdown_reason = SlowdownReason.NONE

        # HW slowdown (random rare event)
        if random.random() < 0.0001:
            self.throttle_reasons.hw_slowdown = True
        elif random.random() < 0.01:
            self.throttle_reasons.hw_slowdown = False

        # Update performance state based on throttling
        if self.throttle_reasons.thermal or self.throttle_reasons.power:
            self.performance_state = min(12, self.performance_state + 1)
        elif self.workload_utilization > 0.8:
            self.performance_state = max(0, self.performance_state - 1)
        else:
            self.performance_state = min(8, self.performance_state + 1)

    def _update_clock_frequencies(self):
        """Update clock frequencies based on workload and throttling."""
        # Target clock based on utilization
        if self.workload_utilization > 0.5:
            self.target_sm_clock = self.spec.max_clock_mhz
        else:
            self.target_sm_clock = self.spec.base_clock_mhz

        # Reduce clocks if throttling
        if self.throttle_reasons.thermal:
            self.target_sm_clock = int(self.spec.base_clock_mhz * 0.85)
        if self.throttle_reasons.power:
            self.target_sm_clock = int(self.spec.base_clock_mhz * 0.90)

        # Clock frequency changes gradually
        clock_diff = self.target_sm_clock - self.current_sm_clock
        self.current_sm_clock += int(clock_diff * 0.2)

    def _update_power_consumption(self, delta_seconds: float):
        """Update power consumption with realistic settling."""
        idle_power = 50.0
        active_power = self.spec.power_limit_watts

        # Calculate target power
        self.power_target = (
            idle_power + (active_power - idle_power) * self.workload_utilization
        )

        # Add power for memory operations
        self.power_target += self.memory_utilization * 30.0

        # Add power for NVLink
        if self.nccl_active:
            self.power_target += 20.0

        # Power settles gradually toward target
        power_diff = self.power_target - self.current_power
        self.current_power += power_diff * self.power_settling_rate

        # Add power variation/noise
        self.current_power += random.uniform(-10, 10)

        # Clamp to valid range
        self.current_power = max(
            30.0, min(self.spec.power_limit_watts * 1.05, self.current_power)
        )

    def _update_memory_bandwidth(self):
        """Update memory bandwidth utilization."""
        # Bandwidth scales with memory utilization
        utilization_factor = self.memory_utilization * random.uniform(0.8, 1.0)
        self.memory_bandwidth_utilized = self.memory_bandwidth_max * utilization_factor

        # Memory bandwidth saturates at high utilization
        if self.memory_utilization > 0.9:
            self.memory_bandwidth_utilized = self.memory_bandwidth_max * 0.95

    def _update_pcie_traffic(self, delta_seconds: float):
        """Update PCIe traffic based on memory operations."""
        # PCIe Gen4 x16: ~32 GB/s bidirectional
        pcie_max_bandwidth = (
            32.0 * (self.spec.pcie_gen / 4.0) * (self.spec.pcie_lanes / 16.0)
        )

        # TX: Host to device transfers
        if self.memory_utilization > 0.3:
            tx_factor = self.memory_utilization * random.uniform(0.3, 0.6)
            self.pcie_tx_throughput = pcie_max_bandwidth * tx_factor
        else:
            self.pcie_tx_throughput = random.uniform(0.1, 1.0)

        # RX: Device to host transfers
        rx_factor = self.memory_utilization * random.uniform(0.2, 0.5)
        self.pcie_rx_throughput = pcie_max_bandwidth * rx_factor

        # Accumulate bytes transferred
        self.pcie_tx_bytes += int(self.pcie_tx_throughput * 1e9 * delta_seconds)
        self.pcie_rx_bytes += int(self.pcie_rx_throughput * 1e9 * delta_seconds)

    def _update_nvlink_traffic(self, delta_seconds: float):
        """Update NVLink traffic (coordinated between GPUs)."""
        if self.spec.nvlink_count == 0:
            return

        # NVLink bandwidth per link (e.g., 900 GB/s for H100 across 18 links)
        per_link_bandwidth = self.spec.nvlink_bandwidth_gbps / self.spec.nvlink_count

        # NCCL operations use NVLink heavily
        if self.nccl_active:
            # All-reduce pattern: communicate with neighbors
            for link_id in range(self.spec.nvlink_count):
                utilization = random.uniform(0.7, 0.95)
                bytes_per_second = per_link_bandwidth * 1e9 * utilization

                tx_bytes = int(bytes_per_second * delta_seconds)
                rx_bytes = int(
                    bytes_per_second * delta_seconds * random.uniform(0.9, 1.1)
                )

                self.nvlink_tx_bytes[link_id] += tx_bytes
                self.nvlink_rx_bytes[link_id] += rx_bytes

                # Track P2P transfers to specific GPUs
                target_gpu = (self.gpu_id + link_id) % self.simulator.num_gpus
                if target_gpu < len(self.p2p_bytes_sent):
                    self.p2p_bytes_sent[target_gpu] += tx_bytes

                # Rare NVLink errors
                if random.random() < 0.00001:
                    self.nvlink_crc_errors[link_id] += 1
                if random.random() < 0.000001:
                    self.nvlink_recovery_errors[link_id] += 1
        else:
            # P2P memory transfers (lower utilization)
            if self.memory_utilization > 0.5:
                for link_id in range(min(4, self.spec.nvlink_count)):
                    utilization = random.uniform(0.2, 0.4)
                    bytes_per_second = per_link_bandwidth * 1e9 * utilization

                    self.nvlink_tx_bytes[link_id] += int(
                        bytes_per_second * delta_seconds
                    )
                    self.nvlink_rx_bytes[link_id] += int(
                        bytes_per_second * delta_seconds
                    )

    def _update_fan_speeds(self):
        """Update fan speeds based on temperature."""
        for i in range(self.spec.fan_count):
            # Target fan speed based on temperature
            temp_ratio = (self.current_temperature - 30) / (
                self.spec.max_temp_celsius - 30
            )
            target_speed = 30 + int(temp_ratio * 70)  # 30-100%
            target_speed = max(30, min(100, target_speed))

            # Fan speed changes gradually
            speed_diff = target_speed - self.fan_speeds[i]
            self.fan_speeds[i] += int(speed_diff * 0.3)
            self.fan_speeds[i] = max(0, min(100, self.fan_speeds[i]))

    def _simulate_ecc_errors(self):
        """Simulate ECC errors - increase with memory stress."""
        # Base error rate increases with memory utilization and temperature
        stress_factor = self.memory_utilization * (self.current_temperature / 70.0)

        # Single-bit errors (correctable)
        sbe_probability = 0.00001 * (1.0 + stress_factor * 5.0)
        if random.random() < sbe_probability:
            self.ecc_sbe_total += 1

            # Distribute across memory locations
            location = random.choice(["l1", "l2", "device", "register", "texture"])
            if location == "l1":
                self.ecc_sbe_l1 += 1
            elif location == "l2":
                self.ecc_sbe_l2 += 1
            elif location == "device":
                self.ecc_sbe_device += 1
            elif location == "register":
                self.ecc_sbe_register += 1
            else:
                self.ecc_sbe_texture += 1

        # Double-bit errors (uncorrectable) - much rarer
        dbe_probability = 0.0000001 * (1.0 + stress_factor * 10.0)
        if random.random() < dbe_probability:
            self.ecc_dbe_total += 1

    def _publish_snapshot(self):
        """Publish complete snapshot of all metrics (called by background thread)."""
        timestamp = int(time.time() * 1_000_000)

        # Build complete snapshot with 100+ fields
        snapshot = {}

        # All field IDs to publish
        field_ids = [
            # Device info (50-99)
            50,
            54,
            59,
            60,
            61,
            # Clocks (100-109)
            100,
            101,
            102,
            103,
            # Temperature (150-159)
            150,
            151,
            152,
            # Power (155-159)
            155,
            156,
            157,
            158,
            159,
            # Utilization (200-209)
            203,
            204,
            205,
            206,
            207,
            208,
            209,
            # Memory (250-259)
            250,
            251,
            252,
            253,
            # ECC (600-650)
            610,
            611,
            612,
            613,
            614,
            615,
            620,
            621,
            632,
            641,
            642,
            # Performance state (700-710)
            700,
            701,
            # Profiling (1001-1100)
            1002,
            1003,
            1004,
            1005,
            1006,
            1007,
            1008,
            1009,
            1010,
            1011,
            1012,
            # NVLink per-link (1090-1095)
            1090,
            1091,
            1092,
            1093,
            1094,
            1095,
            # NVLink errors (1096-1110)
            1096,
            1097,
            1098,
            1099,
            1100,
            1101,
            # Fan speed (1567)
            1567,
            1568,
            # Throttle reasons (1570-1580)
            1570,
            1571,
            1572,
            1573,
            1574,
            # XID errors (1590)
            1590,
            # Process stats (2000-2010)
            2000,
            2001,
            2002,
            # Historical percentiles (2100-2120)
            2100,
            2101,
            2102,
            2103,
            2104,
            2105,
        ]

        for field_id in field_ids:
            snapshot[field_id] = self._compute_field_value(field_id, timestamp)

        # Atomic replacement (dict assignment is atomic in CPython)
        self._snapshot_cache = snapshot

    def get_snapshot(
        self, field_ids: list[int] | None = None
    ) -> dict[int, DCGMFieldValue]:
        """
        Get metrics snapshot (lock-free read).

        Args:
            field_ids: Optional list of specific field IDs (None = all cached fields)

        Returns:
            Dict mapping field_id to DCGMFieldValue
        """
        snapshot = self._snapshot_cache  # Atomic read

        if field_ids is None:
            return snapshot

        return {
            fid: snapshot.get(
                fid, DCGMFieldValue(fid, 0, int(time.time() * 1_000_000), "i")
            )
            for fid in field_ids
        }

    def _compute_field_value(self, field_id: int, timestamp: int) -> DCGMFieldValue:
        """Get field value without acquiring lock (must be called with lock held)."""
        # Device information (50-99)
        if field_id == 50:  # DCGM_FI_DEV_NAME
            return DCGMFieldValue(field_id, self.spec.name, timestamp, "s")
        elif field_id == 54:  # DCGM_FI_DEV_UUID
            return DCGMFieldValue(field_id, self.uuid, timestamp, "s")
        elif field_id == 59:  # DCGM_FI_DEV_PCI_BUSID
            return DCGMFieldValue(field_id, self.pci_bus_id, timestamp, "s")
        elif field_id == 60:  # DCGM_FI_DEV_SERIAL
            return DCGMFieldValue(field_id, f"SIM{self.gpu_id:010d}", timestamp, "s")
        elif field_id == 61:  # DCGM_FI_DEV_COUNT
            return DCGMFieldValue(field_id, self.simulator.num_gpus, timestamp, "i")

        # Clocks (100-109)
        elif field_id == 100:  # DCGM_FI_DEV_SM_CLOCK
            return DCGMFieldValue(field_id, self.current_sm_clock, timestamp, "i")
        elif field_id == 101:  # DCGM_FI_DEV_MEM_CLOCK
            return DCGMFieldValue(field_id, self.current_mem_clock, timestamp, "i")
        elif field_id == 102:  # DCGM_FI_DEV_VIDEO_CLOCK
            video_clock = int(self.current_sm_clock * 0.8)
            return DCGMFieldValue(field_id, video_clock, timestamp, "i")
        elif field_id == 103:  # DCGM_FI_DEV_APP_SM_CLOCK (application clock)
            return DCGMFieldValue(field_id, self.target_sm_clock, timestamp, "i")

        # Temperature (150-159)
        elif field_id == 150:  # DCGM_FI_DEV_GPU_TEMP
            return DCGMFieldValue(
                field_id, int(self.current_temperature), timestamp, "i"
            )
        elif field_id == 151:  # DCGM_FI_DEV_MEMORY_TEMP
            return DCGMFieldValue(field_id, int(self.memory_temp), timestamp, "i")
        elif field_id == 152:  # DCGM_FI_DEV_GPU_MAX_OP_TEMP (hotspot)
            return DCGMFieldValue(field_id, int(self.hotspot_temp), timestamp, "i")

        # Power (155-159)
        elif field_id == 155:  # DCGM_FI_DEV_POWER_USAGE
            return DCGMFieldValue(field_id, self.current_power, timestamp, "d")
        elif field_id == 156:  # DCGM_FI_DEV_TOTAL_ENERGY_CONSUMPTION
            return DCGMFieldValue(field_id, self.total_energy_mj, timestamp, "i")
        elif field_id == 157:  # DCGM_FI_DEV_POWER_MGMT_LIMIT
            return DCGMFieldValue(field_id, self.spec.power_limit_watts, timestamp, "d")
        elif field_id == 158:  # DCGM_FI_DEV_POWER_MGMT_LIMIT_MIN
            return DCGMFieldValue(
                field_id, self.spec.power_limit_watts * 0.5, timestamp, "d"
            )
        elif field_id == 159:  # DCGM_FI_DEV_POWER_MGMT_LIMIT_MAX
            return DCGMFieldValue(
                field_id, self.spec.power_limit_watts * 1.2, timestamp, "d"
            )

        # Utilization (203-209)
        elif field_id == 203:  # DCGM_FI_DEV_GPU_UTIL
            util_pct = int(self.workload_utilization * 100)
            return DCGMFieldValue(field_id, util_pct, timestamp, "i")
        elif field_id == 204:  # DCGM_FI_DEV_MEM_COPY_UTIL
            mem_util_pct = int(self.memory_utilization * 100)
            return DCGMFieldValue(field_id, mem_util_pct, timestamp, "i")
        elif field_id == 205:  # DCGM_FI_DEV_ENC_UTIL (encoder)
            enc_util = int(self.workload_utilization * random.uniform(0.1, 0.3) * 100)
            return DCGMFieldValue(field_id, enc_util, timestamp, "i")
        elif field_id == 206:  # DCGM_FI_DEV_DEC_UTIL (decoder)
            dec_util = int(self.workload_utilization * random.uniform(0.1, 0.2) * 100)
            return DCGMFieldValue(field_id, dec_util, timestamp, "i")
        elif field_id == 207:  # DCGM_FI_DEV_XID_ERRORS
            return DCGMFieldValue(field_id, self.xid_errors, timestamp, "i")
        elif field_id == 208:  # DCGM_FI_DEV_PCIE_REPLAY_COUNTER
            return DCGMFieldValue(field_id, self.pcie_replay_count, timestamp, "i")
        elif field_id == 209:  # DCGM_FI_DEV_NVLINK_CRC_FLIT_ERROR_COUNT_TOTAL
            total_crc = sum(self.nvlink_crc_errors)
            return DCGMFieldValue(field_id, total_crc, timestamp, "i")

        # Memory (250-259)
        elif field_id == 250:  # DCGM_FI_DEV_FB_FREE
            used_mib = int(self.spec.memory_total_mib * self.memory_utilization)
            free_mib = self.spec.memory_total_mib - used_mib
            return DCGMFieldValue(field_id, free_mib, timestamp, "i")
        elif field_id == 251:  # DCGM_FI_DEV_FB_USED
            used_mib = int(self.spec.memory_total_mib * self.memory_utilization)
            return DCGMFieldValue(field_id, used_mib, timestamp, "i")
        elif field_id == 252:  # DCGM_FI_DEV_FB_RESERVED
            reserved_mib = int(self.spec.memory_total_mib * 0.02)  # 2% reserved
            return DCGMFieldValue(field_id, reserved_mib, timestamp, "i")
        elif field_id == 253:  # DCGM_FI_DEV_FB_TOTAL
            return DCGMFieldValue(field_id, self.spec.memory_total_mib, timestamp, "i")

        # ECC Errors (600-650)
        elif field_id == 610:  # DCGM_FI_DEV_ECC_SBE_VOL_TOTAL
            return DCGMFieldValue(field_id, self.ecc_sbe_total, timestamp, "i")
        elif field_id == 611:  # DCGM_FI_DEV_ECC_SBE_VOL_L1
            return DCGMFieldValue(field_id, self.ecc_sbe_l1, timestamp, "i")
        elif field_id == 612:  # DCGM_FI_DEV_ECC_SBE_VOL_L2
            return DCGMFieldValue(field_id, self.ecc_sbe_l2, timestamp, "i")
        elif field_id == 613:  # DCGM_FI_DEV_ECC_SBE_VOL_DEV
            return DCGMFieldValue(field_id, self.ecc_sbe_device, timestamp, "i")
        elif field_id == 614:  # DCGM_FI_DEV_ECC_SBE_VOL_REG
            return DCGMFieldValue(field_id, self.ecc_sbe_register, timestamp, "i")
        elif field_id == 615:  # DCGM_FI_DEV_ECC_SBE_VOL_TEX
            return DCGMFieldValue(field_id, self.ecc_sbe_texture, timestamp, "i")
        elif field_id == 620:  # DCGM_FI_DEV_ECC_DBE_VOL_TOTAL
            return DCGMFieldValue(field_id, self.ecc_dbe_total, timestamp, "i")
        elif field_id == 621:  # DCGM_FI_DEV_ECC_DBE_VOL_L1
            dbe_l1 = int(self.ecc_dbe_total * 0.2)
            return DCGMFieldValue(field_id, dbe_l1, timestamp, "i")
        elif field_id == 632:  # DCGM_FI_DEV_ECC_DBE_AGG_TOTAL
            return DCGMFieldValue(field_id, self.ecc_dbe_total, timestamp, "i")
        elif field_id == 641:  # DCGM_FI_DEV_RETIRED_SBE
            retired_sbe = int(self.ecc_sbe_total * 0.01)  # 1% require retirement
            return DCGMFieldValue(field_id, retired_sbe, timestamp, "i")
        elif field_id == 642:  # DCGM_FI_DEV_RETIRED_DBE
            retired_dbe = int(self.ecc_dbe_total * 0.5)  # 50% require retirement
            return DCGMFieldValue(field_id, retired_dbe, timestamp, "i")

        # Performance state (700-710)
        elif field_id == 700:  # DCGM_FI_DEV_PSTATE
            return DCGMFieldValue(field_id, self.performance_state, timestamp, "i")
        elif field_id == 701:  # DCGM_FI_DEV_SLOWDOWN_TEMP
            return DCGMFieldValue(
                field_id, self.spec.throttle_temp_celsius, timestamp, "i"
            )

        # Profiling metrics (1001-1012)
        elif field_id == 1002:  # DCGM_FI_PROF_SM_ACTIVE
            sm_active = self.workload_utilization * 100
            return DCGMFieldValue(field_id, sm_active, timestamp, "d")
        elif field_id == 1003:  # DCGM_FI_PROF_SM_OCCUPANCY
            occupancy = self.workload_utilization * random.uniform(0.6, 0.9) * 100
            return DCGMFieldValue(field_id, occupancy, timestamp, "d")
        elif field_id == 1004:  # DCGM_FI_PROF_PIPE_TENSOR_ACTIVE
            tensor_active = self.workload_utilization * random.uniform(0.7, 0.95) * 100
            return DCGMFieldValue(field_id, tensor_active, timestamp, "d")
        elif field_id == 1005:  # DCGM_FI_PROF_DRAM_ACTIVE
            dram_active = self.memory_utilization * 100
            return DCGMFieldValue(field_id, dram_active, timestamp, "d")
        elif field_id == 1006:  # DCGM_FI_PROF_PIPE_FP64_ACTIVE
            fp64_active = self.workload_utilization * random.uniform(0.3, 0.6) * 100
            return DCGMFieldValue(field_id, fp64_active, timestamp, "d")
        elif field_id == 1007:  # DCGM_FI_PROF_PIPE_FP32_ACTIVE
            fp32_active = self.workload_utilization * random.uniform(0.5, 0.8) * 100
            return DCGMFieldValue(field_id, fp32_active, timestamp, "d")
        elif field_id == 1008:  # DCGM_FI_PROF_PIPE_FP16_ACTIVE
            fp16_active = self.workload_utilization * random.uniform(0.8, 0.95) * 100
            return DCGMFieldValue(field_id, fp16_active, timestamp, "d")
        elif field_id == 1009:  # DCGM_FI_PROF_PCIE_TX_BYTES
            return DCGMFieldValue(field_id, self.pcie_tx_bytes, timestamp, "i")
        elif field_id == 1010:  # DCGM_FI_PROF_PCIE_RX_BYTES
            return DCGMFieldValue(field_id, self.pcie_rx_bytes, timestamp, "i")
        elif field_id == 1011:  # DCGM_FI_PROF_NVLINK_TX_BYTES (total)
            total_nvlink_tx = sum(self.nvlink_tx_bytes)
            return DCGMFieldValue(field_id, total_nvlink_tx, timestamp, "i")
        elif field_id == 1012:  # DCGM_FI_PROF_NVLINK_RX_BYTES (total)
            total_nvlink_rx = sum(self.nvlink_rx_bytes)
            return DCGMFieldValue(field_id, total_nvlink_rx, timestamp, "i")

        # NVLink per-link TX (1090-1095)
        elif 1090 <= field_id <= 1095:
            link_id = field_id - 1090
            if link_id < len(self.nvlink_tx_bytes):
                return DCGMFieldValue(
                    field_id, self.nvlink_tx_bytes[link_id], timestamp, "i"
                )
            return DCGMFieldValue(field_id, 0, timestamp, "i")

        # NVLink per-link errors (1096-1110)
        elif 1096 <= field_id <= 1101:
            link_id = field_id - 1096
            if link_id < len(self.nvlink_crc_errors):
                return DCGMFieldValue(
                    field_id, self.nvlink_crc_errors[link_id], timestamp, "i"
                )
            return DCGMFieldValue(field_id, 0, timestamp, "i")

        # Fan speed (1567-1568)
        elif field_id == 1567:  # DCGM_FI_DEV_FAN_SPEED
            avg_fan = (
                sum(self.fan_speeds) // len(self.fan_speeds) if self.fan_speeds else 0
            )
            return DCGMFieldValue(field_id, avg_fan, timestamp, "i")
        elif field_id == 1568:  # DCGM_FI_DEV_FAN_SPEED_0 (first fan)
            fan_speed = self.fan_speeds[0] if self.fan_speeds else 0
            return DCGMFieldValue(field_id, fan_speed, timestamp, "i")

        # Throttle reasons (1570-1580)
        elif field_id == 1570:  # DCGM_FI_DEV_CLOCK_THROTTLE_REASONS
            reasons = 0
            if self.throttle_reasons.thermal:
                reasons |= 0x1
            if self.throttle_reasons.power:
                reasons |= 0x2
            if self.throttle_reasons.hw_slowdown:
                reasons |= 0x4
            if self.throttle_reasons.sw_thermal:
                reasons |= 0x8
            if self.throttle_reasons.sync_boost:
                reasons |= 0x10
            return DCGMFieldValue(field_id, reasons, timestamp, "i")
        elif field_id == 1571:  # Thermal throttle (bool)
            return DCGMFieldValue(
                field_id, 1 if self.throttle_reasons.thermal else 0, timestamp, "i"
            )
        elif field_id == 1572:  # Power throttle (bool)
            return DCGMFieldValue(
                field_id, 1 if self.throttle_reasons.power else 0, timestamp, "i"
            )
        elif field_id == 1573:  # HW slowdown (bool)
            return DCGMFieldValue(
                field_id, 1 if self.throttle_reasons.hw_slowdown else 0, timestamp, "i"
            )
        elif field_id == 1574:  # Slowdown reason enum
            return DCGMFieldValue(field_id, self.slowdown_reason.value, timestamp, "i")

        # XID errors (1590)
        elif field_id == 1590:  # DCGM_FI_DEV_XID_ERRORS_TOTAL
            return DCGMFieldValue(field_id, self.xid_errors, timestamp, "i")

        # Process stats (2000-2010)
        elif field_id == 2000:  # Process count
            return DCGMFieldValue(field_id, len(self.processes), timestamp, "i")
        elif field_id == 2001:  # Total process memory
            total_mem = sum(p.memory_mib for p in self.processes)
            return DCGMFieldValue(field_id, total_mem, timestamp, "i")
        elif field_id == 2002:  # Max process utilization
            max_util = (
                max((p.gpu_utilization for p in self.processes), default=0.0) * 100
            )
            return DCGMFieldValue(field_id, max_util, timestamp, "d")

        # Historical percentiles (2100-2120)
        elif field_id == 2100:  # Temperature P50
            return DCGMFieldValue(
                field_id, self.history["temperature"].get_percentile(50), timestamp, "d"
            )
        elif field_id == 2101:  # Temperature P90
            return DCGMFieldValue(
                field_id, self.history["temperature"].get_percentile(90), timestamp, "d"
            )
        elif field_id == 2102:  # Temperature P99
            return DCGMFieldValue(
                field_id, self.history["temperature"].get_percentile(99), timestamp, "d"
            )
        elif field_id == 2103:  # Power P50
            return DCGMFieldValue(
                field_id, self.history["power"].get_percentile(50), timestamp, "d"
            )
        elif field_id == 2104:  # Power P90
            return DCGMFieldValue(
                field_id, self.history["power"].get_percentile(90), timestamp, "d"
            )
        elif field_id == 2105:  # Power P99
            return DCGMFieldValue(
                field_id, self.history["power"].get_percentile(99), timestamp, "d"
            )

        else:
            # Unknown field - return blank
            return DCGMFieldValue(field_id, 0, timestamp, "i")

    def get_field_value(self, field_id: int) -> DCGMFieldValue:
        """
        Get current value for a DCGM field ID (lock-free).

        Args:
            field_id: DCGM field identifier

        Returns:
            DCGMFieldValue with current value
        """
        snapshot = self._snapshot_cache  # Atomic read
        return snapshot.get(
            field_id, DCGMFieldValue(field_id, 0, int(time.time() * 1_000_000), "i")
        )


class DCGMMetricsSimulator:
    """
    Simulates NVIDIA DCGM GPU metrics for testing and development - EXTREME REALISM.

    Creates virtual GPUs and generates realistic metrics based on
    simulated workload characteristics with multi-GPU coordination,
    thermal throttling, ECC errors, NVLink traffic, and historical tracking.
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
        self.gpus = [SimulatedGPU(i, self.gpu_spec, self) for i in range(num_gpus)]

        # Multi-GPU coordination
        self.active_collective_op = None
        self.collective_start_time = 0.0

        # Background update thread
        self._stop_event = threading.Event()
        self._update_thread = threading.Thread(target=self._update_loop, daemon=True)
        self._update_thread.start()

    def set_workload(
        self,
        gpu_id: int,
        compute_intensity: float,
        memory_intensity: float,
        batch_size: int = 1,
    ):
        """Set workload for specific GPU."""
        if 0 <= gpu_id < self.num_gpus:
            self.gpus[gpu_id].set_workload(
                compute_intensity, memory_intensity, batch_size
            )

    def set_global_workload(
        self, compute_intensity: float, memory_intensity: float, batch_size: int = 1
    ):
        """Set workload for all GPUs."""
        for gpu in self.gpus:
            gpu.set_workload(compute_intensity, memory_intensity, batch_size)

    def start_collective_operation(self, op_type: str = "allreduce"):
        """Start a NCCL collective operation across all GPUs."""
        self.active_collective_op = op_type
        self.collective_start_time = time.time()
        for gpu in self.gpus:
            gpu.start_collective_operation(op_type)

    def end_collective_operation(self):
        """End NCCL collective operation."""
        self.active_collective_op = None
        for gpu in self.gpus:
            gpu.end_collective_operation()

    def simulate_p2p_transfer(self, src_gpu: int, dst_gpu: int, bytes_transferred: int):
        """Simulate P2P memory transfer between GPUs."""
        if 0 <= src_gpu < self.num_gpus and 0 <= dst_gpu < self.num_gpus:
            if dst_gpu < len(self.gpus[src_gpu].p2p_bytes_sent):
                self.gpus[src_gpu].p2p_bytes_sent[dst_gpu] += bytes_transferred
            if src_gpu < len(self.gpus[dst_gpu].p2p_bytes_received):
                self.gpus[dst_gpu].p2p_bytes_received[src_gpu] += bytes_transferred

    def add_process(
        self, gpu_id: int, pid: int, name: str, gpu_util: float, mem_mib: int
    ):
        """Add process to specific GPU."""
        if 0 <= gpu_id < self.num_gpus:
            self.gpus[gpu_id].add_process(pid, name, gpu_util, mem_mib)

    def remove_process(self, gpu_id: int, pid: int):
        """Remove process from GPU."""
        if 0 <= gpu_id < self.num_gpus:
            self.gpus[gpu_id].remove_process(pid)

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

            # Coordinate NCCL operations (end after 5 seconds)
            if (
                self.active_collective_op
                and (current_time - self.collective_start_time) > 5.0
            ):
                self.end_collective_operation()

            last_update = current_time

    def get_field_value(self, gpu_id: int, field_id: int) -> DCGMFieldValue:
        """Get current field value for specific GPU."""
        if 0 <= gpu_id < self.num_gpus:
            return self.gpus[gpu_id].get_field_value(field_id)
        return DCGMFieldValue(field_id, 0, int(time.time() * 1_000_000), "i")

    def get_all_gpu_field_values(self, field_id: int) -> dict[int, DCGMFieldValue]:
        """Get field value from all GPUs."""
        return {gpu.gpu_id: gpu.get_field_value(field_id) for gpu in self.gpus}

    def get_prometheus_metrics(self) -> str:
        """Export metrics in Prometheus/DCGM-exporter format (lock-free, reads cached snapshots)."""
        lines = []

        # Extended field ID definitions
        fields = {
            100: ("DCGM_FI_DEV_SM_CLOCK", "gauge", "SM clock frequency (MHz)"),
            101: ("DCGM_FI_DEV_MEM_CLOCK", "gauge", "Memory clock frequency (MHz)"),
            150: ("DCGM_FI_DEV_GPU_TEMP", "gauge", "GPU temperature (C)"),
            151: ("DCGM_FI_DEV_MEMORY_TEMP", "gauge", "Memory temperature (C)"),
            152: (
                "DCGM_FI_DEV_GPU_MAX_OP_TEMP",
                "gauge",
                "GPU hotspot temperature (C)",
            ),
            155: ("DCGM_FI_DEV_POWER_USAGE", "gauge", "Power draw (W)"),
            156: (
                "DCGM_FI_DEV_TOTAL_ENERGY_CONSUMPTION",
                "counter",
                "Total energy consumption (mJ)",
            ),
            203: ("DCGM_FI_DEV_GPU_UTIL", "gauge", "GPU utilization (%)"),
            204: ("DCGM_FI_DEV_MEM_COPY_UTIL", "gauge", "Memory utilization (%)"),
            208: ("DCGM_FI_DEV_PCIE_REPLAY_COUNTER", "counter", "PCIe replay counter"),
            209: (
                "DCGM_FI_DEV_NVLINK_CRC_FLIT_ERROR_COUNT_TOTAL",
                "counter",
                "NVLink CRC errors",
            ),
            250: ("DCGM_FI_DEV_FB_FREE", "gauge", "Framebuffer memory free (MiB)"),
            251: ("DCGM_FI_DEV_FB_USED", "gauge", "Framebuffer memory used (MiB)"),
            253: ("DCGM_FI_DEV_FB_TOTAL", "gauge", "Framebuffer memory total (MiB)"),
            610: (
                "DCGM_FI_DEV_ECC_SBE_VOL_TOTAL",
                "counter",
                "Total single-bit ECC errors",
            ),
            611: ("DCGM_FI_DEV_ECC_SBE_VOL_L1", "counter", "L1 single-bit ECC errors"),
            612: ("DCGM_FI_DEV_ECC_SBE_VOL_L2", "counter", "L2 single-bit ECC errors"),
            620: (
                "DCGM_FI_DEV_ECC_DBE_VOL_TOTAL",
                "counter",
                "Total double-bit ECC errors",
            ),
            700: ("DCGM_FI_DEV_PSTATE", "gauge", "Performance state (P0-P12)"),
            1002: ("DCGM_FI_PROF_SM_ACTIVE", "gauge", "SM active (%)"),
            1003: ("DCGM_FI_PROF_SM_OCCUPANCY", "gauge", "SM occupancy (%)"),
            1004: (
                "DCGM_FI_PROF_PIPE_TENSOR_ACTIVE",
                "gauge",
                "Tensor pipe active (%)",
            ),
            1005: ("DCGM_FI_PROF_DRAM_ACTIVE", "gauge", "DRAM active (%)"),
            1009: ("DCGM_FI_PROF_PCIE_TX_BYTES", "counter", "PCIe TX (bytes)"),
            1010: ("DCGM_FI_PROF_PCIE_RX_BYTES", "counter", "PCIe RX (bytes)"),
            1011: (
                "DCGM_FI_PROF_NVLINK_TX_BYTES",
                "counter",
                "NVLink TX total (bytes)",
            ),
            1012: (
                "DCGM_FI_PROF_NVLINK_RX_BYTES",
                "counter",
                "NVLink RX total (bytes)",
            ),
            1567: ("DCGM_FI_DEV_FAN_SPEED", "gauge", "Fan speed (%)"),
            1570: (
                "DCGM_FI_DEV_CLOCK_THROTTLE_REASONS",
                "gauge",
                "Clock throttle reasons bitmask",
            ),
            1571: ("DCGM_FI_DEV_THERMAL_THROTTLE", "gauge", "Thermal throttle active"),
            1572: ("DCGM_FI_DEV_POWER_THROTTLE", "gauge", "Power throttle active"),
        }

        # Read cached snapshots (no locks, no blocking)
        gpu_snapshots = [gpu.get_snapshot() for gpu in self.gpus]

        # Generate metrics
        for field_id, (name, metric_type, help_text) in fields.items():
            # Add TYPE and HELP
            lines.append(f"# TYPE {name} {metric_type}")
            lines.append(f"# HELP {name} {help_text}")

            # Add values for each GPU
            for gpu, snapshot in zip(self.gpus, gpu_snapshots):
                if field_id in snapshot:
                    field_value = snapshot[field_id]
                    labels = f'gpu="{gpu.gpu_id}",UUID="{gpu.uuid}",device="{gpu.device_name}",modelName="{self.gpu_spec.name}"'
                    lines.append(f"{name}{{{labels}}} {field_value.value}")

            lines.append("")  # Blank line between metrics

        return "\n".join(lines)

    def get_metrics_dict(self) -> dict[str, Any]:
        """Export metrics as dictionary (lock-free)."""
        metrics = {}

        for gpu in self.gpus:
            snapshot = gpu.get_snapshot()  # Lock-free read

            gpu_metrics = {
                "gpu_id": gpu.gpu_id,
                "uuid": gpu.uuid,
                "name": self.gpu_spec.name,
                "architecture": self.gpu_spec.architecture.value,
                "sm_clock_mhz": snapshot.get(100).value if 100 in snapshot else 0,
                "memory_clock_mhz": snapshot.get(101).value if 101 in snapshot else 0,
                "temperature_c": snapshot.get(150).value if 150 in snapshot else 0,
                "memory_temp_c": snapshot.get(151).value if 151 in snapshot else 0,
                "hotspot_temp_c": snapshot.get(152).value if 152 in snapshot else 0,
                "power_usage_w": snapshot.get(155).value if 155 in snapshot else 0,
                "total_energy_mj": snapshot.get(156).value if 156 in snapshot else 0,
                "gpu_utilization_pct": (
                    snapshot.get(203).value if 203 in snapshot else 0
                ),
                "memory_utilization_pct": (
                    snapshot.get(204).value if 204 in snapshot else 0
                ),
                "memory_free_mib": snapshot.get(250).value if 250 in snapshot else 0,
                "memory_used_mib": snapshot.get(251).value if 251 in snapshot else 0,
                "memory_total_mib": snapshot.get(253).value if 253 in snapshot else 0,
                "ecc_sbe_total": snapshot.get(610).value if 610 in snapshot else 0,
                "ecc_sbe_l1": snapshot.get(611).value if 611 in snapshot else 0,
                "ecc_sbe_l2": snapshot.get(612).value if 612 in snapshot else 0,
                "ecc_dbe_total": snapshot.get(620).value if 620 in snapshot else 0,
                "performance_state": snapshot.get(700).value if 700 in snapshot else 0,
                "sm_active_pct": snapshot.get(1002).value if 1002 in snapshot else 0,
                "sm_occupancy_pct": snapshot.get(1003).value if 1003 in snapshot else 0,
                "tensor_active_pct": (
                    snapshot.get(1004).value if 1004 in snapshot else 0
                ),
                "dram_active_pct": snapshot.get(1005).value if 1005 in snapshot else 0,
                "pcie_tx_bytes": snapshot.get(1009).value if 1009 in snapshot else 0,
                "pcie_rx_bytes": snapshot.get(1010).value if 1010 in snapshot else 0,
                "nvlink_tx_bytes": snapshot.get(1011).value if 1011 in snapshot else 0,
                "nvlink_rx_bytes": snapshot.get(1012).value if 1012 in snapshot else 0,
                "fan_speed_pct": snapshot.get(1567).value if 1567 in snapshot else 0,
                "throttle_reasons": snapshot.get(1570).value if 1570 in snapshot else 0,
                "thermal_throttle": snapshot.get(1571).value if 1571 in snapshot else 0,
                "power_throttle": snapshot.get(1572).value if 1572 in snapshot else 0,
                # Historical percentiles
                "temp_p50": snapshot.get(2100).value if 2100 in snapshot else 0,
                "temp_p90": snapshot.get(2101).value if 2101 in snapshot else 0,
                "temp_p99": snapshot.get(2102).value if 2102 in snapshot else 0,
                "power_p50": snapshot.get(2103).value if 2103 in snapshot else 0,
                "power_p90": snapshot.get(2104).value if 2104 in snapshot else 0,
                "power_p99": snapshot.get(2105).value if 2105 in snapshot else 0,
            }

            metrics[f"gpu_{gpu.gpu_id}"] = gpu_metrics

        return metrics

    def get_kv_cache_metrics(self) -> dict[str, Any]:
        """Get KV cache and smart routing statistics."""
        # This is a placeholder - would integrate with actual KV cache system
        return {
            "cache_hit_rate": random.uniform(0.6, 0.9),
            "token_reuse_rate": random.uniform(0.5, 0.8),
            "avg_prefix_length": random.randint(50, 200),
            "total_cached_blocks": sum(
                random.randint(100, 500) for _ in range(self.num_gpus)
            ),
        }

    def shutdown(self):
        """Stop background metric updates."""
        self._stop_event.set()
        self._update_thread.join(timeout=2.0)


# DCGM Field ID constants (comprehensive)
# Device info (50-99)
DCGM_FI_DEV_NAME = 50
DCGM_FI_DEV_UUID = 54
DCGM_FI_DEV_PCI_BUSID = 59
DCGM_FI_DEV_SERIAL = 60
DCGM_FI_DEV_COUNT = 61

# Clocks (100-109)
DCGM_FI_DEV_SM_CLOCK = 100
DCGM_FI_DEV_MEM_CLOCK = 101
DCGM_FI_DEV_VIDEO_CLOCK = 102
DCGM_FI_DEV_APP_SM_CLOCK = 103

# Temperature (150-159)
DCGM_FI_DEV_GPU_TEMP = 150
DCGM_FI_DEV_MEMORY_TEMP = 151
DCGM_FI_DEV_GPU_MAX_OP_TEMP = 152

# Power (155-159)
DCGM_FI_DEV_POWER_USAGE = 155
DCGM_FI_DEV_TOTAL_ENERGY_CONSUMPTION = 156
DCGM_FI_DEV_POWER_MGMT_LIMIT = 157
DCGM_FI_DEV_POWER_MGMT_LIMIT_MIN = 158
DCGM_FI_DEV_POWER_MGMT_LIMIT_MAX = 159

# Utilization (203-209)
DCGM_FI_DEV_GPU_UTIL = 203
DCGM_FI_DEV_MEM_COPY_UTIL = 204
DCGM_FI_DEV_ENC_UTIL = 205
DCGM_FI_DEV_DEC_UTIL = 206
DCGM_FI_DEV_XID_ERRORS = 207
DCGM_FI_DEV_PCIE_REPLAY_COUNTER = 208
DCGM_FI_DEV_NVLINK_CRC_FLIT_ERROR_COUNT_TOTAL = 209

# Memory (250-259)
DCGM_FI_DEV_FB_FREE = 250
DCGM_FI_DEV_FB_USED = 251
DCGM_FI_DEV_FB_RESERVED = 252
DCGM_FI_DEV_FB_TOTAL = 253

# ECC (600-650)
DCGM_FI_DEV_ECC_SBE_VOL_TOTAL = 610
DCGM_FI_DEV_ECC_SBE_VOL_L1 = 611
DCGM_FI_DEV_ECC_SBE_VOL_L2 = 612
DCGM_FI_DEV_ECC_SBE_VOL_DEV = 613
DCGM_FI_DEV_ECC_SBE_VOL_REG = 614
DCGM_FI_DEV_ECC_SBE_VOL_TEX = 615
DCGM_FI_DEV_ECC_DBE_VOL_TOTAL = 620
DCGM_FI_DEV_ECC_DBE_VOL_L1 = 621
DCGM_FI_DEV_ECC_DBE_AGG_TOTAL = 632
DCGM_FI_DEV_RETIRED_SBE = 641
DCGM_FI_DEV_RETIRED_DBE = 642

# Performance state (700-710)
DCGM_FI_DEV_PSTATE = 700
DCGM_FI_DEV_SLOWDOWN_TEMP = 701

# Profiling (1001-1012)
DCGM_FI_PROF_SM_ACTIVE = 1002
DCGM_FI_PROF_SM_OCCUPANCY = 1003
DCGM_FI_PROF_PIPE_TENSOR_ACTIVE = 1004
DCGM_FI_PROF_DRAM_ACTIVE = 1005
DCGM_FI_PROF_PIPE_FP64_ACTIVE = 1006
DCGM_FI_PROF_PIPE_FP32_ACTIVE = 1007
DCGM_FI_PROF_PIPE_FP16_ACTIVE = 1008
DCGM_FI_PROF_PCIE_TX_BYTES = 1009
DCGM_FI_PROF_PCIE_RX_BYTES = 1010
DCGM_FI_PROF_NVLINK_TX_BYTES = 1011
DCGM_FI_PROF_NVLINK_RX_BYTES = 1012

# NVLink per-link (1090-1110)
DCGM_FI_PROF_NVLINK_L0_TX_BYTES = 1090
DCGM_FI_PROF_NVLINK_L1_TX_BYTES = 1091
DCGM_FI_PROF_NVLINK_L2_TX_BYTES = 1092
DCGM_FI_PROF_NVLINK_L3_TX_BYTES = 1093
DCGM_FI_PROF_NVLINK_L4_TX_BYTES = 1094
DCGM_FI_PROF_NVLINK_L5_TX_BYTES = 1095

# Fan speed (1567-1568)
DCGM_FI_DEV_FAN_SPEED = 1567
DCGM_FI_DEV_FAN_SPEED_0 = 1568

# Throttle reasons (1570-1580)
DCGM_FI_DEV_CLOCK_THROTTLE_REASONS = 1570
DCGM_FI_DEV_THERMAL_THROTTLE = 1571
DCGM_FI_DEV_POWER_THROTTLE = 1572
DCGM_FI_DEV_HW_SLOWDOWN = 1573
DCGM_FI_DEV_SLOWDOWN_REASON = 1574

# XID errors (1590)
DCGM_FI_DEV_XID_ERRORS_TOTAL = 1590

# Process stats (2000-2010)
DCGM_FI_PROCESS_COUNT = 2000
DCGM_FI_PROCESS_TOTAL_MEMORY = 2001
DCGM_FI_PROCESS_MAX_UTILIZATION = 2002

# Historical percentiles (2100-2120)
DCGM_FI_HIST_TEMP_P50 = 2100
DCGM_FI_HIST_TEMP_P90 = 2101
DCGM_FI_HIST_TEMP_P99 = 2102
DCGM_FI_HIST_POWER_P50 = 2103
DCGM_FI_HIST_POWER_P90 = 2104
DCGM_FI_HIST_POWER_P99 = 2105
