/**
 * DCGM GPU Metrics Dashboard Types
 */

export interface GPUMetrics {
  gpu_id: number;
  uuid: string;
  name: string;
  architecture: string;
  sm_clock_mhz: number;
  memory_clock_mhz: number;
  temperature_c: number;
  memory_temp_c: number;
  hotspot_temp_c: number;
  power_usage_w: number;
  total_energy_mj: number;
  gpu_utilization_pct: number;
  memory_utilization_pct: number;
  memory_free_mib: number;
  memory_used_mib: number;
  memory_total_mib: number;
  ecc_sbe_total: number;
  ecc_sbe_l1: number;
  ecc_sbe_l2: number;
  ecc_dbe_total: number;
  performance_state: number;
  sm_active_pct: number;
  sm_occupancy_pct: number;
  tensor_active_pct: number;
  dram_active_pct: number;
  pcie_tx_bytes: number;
  pcie_rx_bytes: number;
  nvlink_tx_bytes: number;
  nvlink_rx_bytes: number;
  fan_speed_pct: number;
  throttle_reasons: number;
  thermal_throttle: number;
  power_throttle: number;
  temp_p50: number;
  temp_p90: number;
  temp_p99: number;
  power_p50: number;
  power_p90: number;
  power_p99: number;
}

export interface DCGMData {
  [key: string]: GPUMetrics;
}

export interface HistoricalDataPoint {
  timestamp: number;
  value: number;
  gpu_id: number;
}
