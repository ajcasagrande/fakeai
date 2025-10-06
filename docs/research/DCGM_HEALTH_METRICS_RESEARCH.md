# NVIDIA DCGM Health and Diagnostics Metrics Research

**Version:** 1.0
**Date:** 2025-10-04
**Purpose:** Comprehensive catalog of NVIDIA DCGM health metrics, error codes, and alerting thresholds for production monitoring

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [DCGM Overview](#dcgm-overview)
3. [Health Monitoring Systems](#health-monitoring-systems)
4. [ECC Error Metrics](#ecc-error-metrics)
5. [XID Error Codes](#xid-error-codes)
6. [Thermal Monitoring](#thermal-monitoring)
7. [Power Monitoring](#power-monitoring)
8. [PCIe Health Monitoring](#pcie-health-monitoring)
9. [Memory Error Management](#memory-error-management)
10. [GPU Driver Status](#gpu-driver-status)
11. [Alert Thresholds and Best Practices](#alert-thresholds-and-best-practices)
12. [Health Check Intervals](#health-check-intervals)
13. [DCGM Field IDs Reference](#dcgm-field-ids-reference)
14. [Production Monitoring Patterns](#production-monitoring-patterns)
15. [Diagnostic Workflows](#diagnostic-workflows)

---

## 1. Executive Summary

NVIDIA Data Center GPU Manager (DCGM) is a comprehensive suite of tools for managing and monitoring NVIDIA datacenter GPUs in cluster environments. It provides:

- **Active and passive health monitoring** across 11+ health watch systems
- **Comprehensive diagnostics** with multiple test levels and plugins
- **Real-time alerting** with configurable thresholds
- **Production-grade monitoring** compatible with Prometheus, Grafana, and other tools

### Key Findings

1. **Default monitoring interval**: 20 seconds (configurable as low as 1 second)
2. **11 health watch systems**: PCIe, NVLink, PMU, MCU, Memory, SM, Inforom, Thermal, Power, Driver, NVSwitch
3. **Critical error metrics**: Any non-zero value for ECC errors, PCIe replays, or XID errors warrants investigation
4. **Memory page retirement threshold**: 60 retired pages (pre-A100) or row-remapping failure (A100+)
5. **PCIe alert threshold**: >8 replays per minute triggers warning

---

## 2. DCGM Overview

### 2.1 What is DCGM?

NVIDIA Data Center GPU Manager (DCGM) is a project for gathering telemetry and measuring the health of NVIDIA GPUs. It provides:

- **Continuous GPU telemetry** and job-level statistics
- **Active health monitoring** across multiple subsystems
- **Comprehensive diagnostics** with plugin-based testing
- **System alerts** and governance policies
- **Integration support** for Kubernetes, Prometheus, and monitoring platforms

### 2.2 Architecture

DCGM can run in two modes:

1. **Embedded Mode**: Agent loaded as a shared library
2. **Standalone Mode**: Agent embedded in a daemon (recommended for flexibility)

### 2.3 Key Components

- **dcgmi**: Command-line interface for GPU management and monitoring
- **DCGM Exporter**: Prometheus exporter for GPU metrics
- **DCGM API**: Go, Python, and C APIs for programmatic access
- **Health Monitoring**: Background and active health checks
- **Policy Engine**: Configurable actions on health violations

---

## 3. Health Monitoring Systems

DCGM monitors 11 distinct health watch systems:

### 3.1 Health Watch Systems

| System | Field ID | Description | Criticality |
|--------|----------|-------------|-------------|
| **PCIe** | `DCGM_HEALTH_WATCH_PCIE` | PCIe link and connection errors | High |
| **NVLink** | `DCGM_HEALTH_WATCH_NVLINK` | NVLink connection and error states | High |
| **PMU** | `DCGM_HEALTH_WATCH_PMU` | Performance Monitoring Unit | Medium |
| **MCU** | `DCGM_HEALTH_WATCH_MCU` | Memory Controller Unit | High |
| **Memory** | `DCGM_HEALTH_WATCH_MEM` | Memory errors and performance | Critical |
| **SM** | `DCGM_HEALTH_WATCH_SM` | Streaming Multiprocessor | Medium |
| **Inforom** | `DCGM_HEALTH_WATCH_INFOROM` | GPU firmware and configuration | High |
| **Thermal** | `DCGM_HEALTH_WATCH_THERMAL` | Temperature and thermal throttling | Critical |
| **Power** | `DCGM_HEALTH_WATCH_POWER` | Power consumption and violations | Critical |
| **Driver** | `DCGM_HEALTH_WATCH_DRIVER` | Driver-related issues | High |
| **NVSwitch** | `DCGM_HEALTH_WATCH_NVSWITCH_*` | NVSwitch fatal and non-fatal errors | High |

### 3.2 Health Result Levels

| Level | Constant | Description | Action Required |
|-------|----------|-------------|-----------------|
| **Pass** | `DCGM_HEALTH_RESULT_PASS` | No issues detected | None |
| **Warning** | `DCGM_HEALTH_RESULT_WARN` | Issues that won't prevent current work but should be addressed | Investigation |
| **Failure** | `DCGM_HEALTH_RESULT_FAIL` | Critical issues where current work is likely compromised | Immediate action |

### 3.3 Monitoring Modes

#### Passive Health Monitoring
- Background monitoring without impact on application performance
- Detects unresponsive GPUs, corrupted firmware, thermal escapes
- Continuous telemetry collection

#### Active Health Monitoring
- On-demand diagnostic tests
- Comprehensive plugin-based testing
- Multi-level diagnostics (quick, medium, extended)

---

## 4. ECC Error Metrics

Error-Correcting Code (ECC) memory errors are critical indicators of GPU memory health.

### 4.1 ECC Error Types

#### Single-Bit Errors (SBE)
- **Correctable errors** - Hardware can correct the error
- **Impact**: No immediate data corruption
- **Monitoring**: Track rate of increase
- **Action threshold**: >0 per day warrants investigation

#### Double-Bit Errors (DBE)
- **Uncorrectable errors** - Cannot be corrected by hardware
- **Impact**: Application abort, potential data corruption
- **Monitoring**: Any DBE is critical
- **Action threshold**: >0 requires immediate attention

### 4.2 ECC Error Field IDs

#### Volatile Errors (Since Last Reboot/Reset)

**Total Counters:**
- `DCGM_FI_DEV_ECC_SBE_VOL_TOTAL` (Field ID: 310) - Total single-bit volatile errors
- `DCGM_FI_DEV_ECC_DBE_VOL_TOTAL` (Field ID: 311) - Total double-bit volatile errors

**Location-Specific Counters:**

| Location | SBE Field | DBE Field | Description |
|----------|-----------|-----------|-------------|
| **L1 Cache** | `DCGM_FI_DEV_ECC_SBE_VOL_L1` | `DCGM_FI_DEV_ECC_DBE_VOL_L1` | L1 cache errors |
| **L2 Cache** | `DCGM_FI_DEV_ECC_SBE_VOL_L2` | `DCGM_FI_DEV_ECC_DBE_VOL_L2` | L2 cache errors |
| **Device Memory** | `DCGM_FI_DEV_ECC_SBE_VOL_DEV` | `DCGM_FI_DEV_ECC_DBE_VOL_DEV` | DRAM errors |
| **Register File** | `DCGM_FI_DEV_ECC_SBE_VOL_REG` | `DCGM_FI_DEV_ECC_DBE_VOL_REG` | Register file errors |
| **Texture Memory** | `DCGM_FI_DEV_ECC_SBE_VOL_TEX` | `DCGM_FI_DEV_ECC_DBE_VOL_TEX` | Texture memory errors |

#### Aggregate Errors (Since GPU First Used)

**Total Counters:**
- `DCGM_FI_DEV_ECC_SBE_AGG_TOTAL` (Field ID: 312) - Total single-bit aggregate errors (monotonic)
- `DCGM_FI_DEV_ECC_DBE_AGG_TOTAL` (Field ID: 313) - Total double-bit aggregate errors (monotonic)

**Location-Specific Counters:**
- `DCGM_FI_DEV_ECC_SBE_AGG_L1` - L1 cache aggregate SBE
- `DCGM_FI_DEV_ECC_SBE_AGG_L2` - L2 cache aggregate SBE
- `DCGM_FI_DEV_ECC_SBE_AGG_DEV` - Device memory aggregate SBE
- `DCGM_FI_DEV_ECC_SBE_AGG_REG` - Register file aggregate SBE
- `DCGM_FI_DEV_ECC_SBE_AGG_TEX` - Texture memory aggregate SBE
- (Corresponding DBE fields for each location)

### 4.3 Page Retirement Fields

- `DCGM_FI_DEV_RETIRED_SBE` - Number of retired pages due to SBE (monotonic)
- `DCGM_FI_DEV_RETIRED_DBE` - Number of retired pages due to DBE (monotonic)
- `DCGM_FI_DEV_RETIRED_PENDING` - Pages pending retirement

### 4.4 ECC Error Monitoring Best Practices

**Critical Thresholds:**
- **DBE Count**: Alert on any non-zero value (critical)
- **SBE Count**: Alert if >10 per hour (warning), >100 per hour (critical)
- **Retired Pages**: Alert if >15 pages and increasing weekly (warning), >60 pages (critical)

**Monitoring Pattern:**
```
# Alert Logic
IF DCGM_FI_DEV_ECC_DBE_VOL_TOTAL > 0:
    SEVERITY: CRITICAL
    ACTION: GPU reset or node reboot required

IF DCGM_FI_DEV_ECC_SBE_VOL_TOTAL rate > 100/hour:
    SEVERITY: CRITICAL
    ACTION: Schedule maintenance

IF DCGM_FI_DEV_RETIRED_SBE + DCGM_FI_DEV_RETIRED_DBE > 60:
    SEVERITY: CRITICAL
    ACTION: RMA evaluation required
```

---

## 5. XID Error Codes

XID (eXecution IDentifier) messages are error reports from the NVIDIA driver indicating general GPU errors.

### 5.1 Critical XID Error Codes

#### Memory-Related XID Errors

| XID Code | Name | Severity | Description | Recovery Action |
|----------|------|----------|-------------|-----------------|
| **48** | DBE ECC Error | Critical | Double-bit uncorrectable ECC error | GPU reset or node reboot |
| **63** | Row Remapping | High | ECC page retirement or row remapping | Reboot to retire bad memory |
| **64** | Row Remapping | High | ECC page retirement or row remapping | Reboot to retire bad memory |
| **92** | High-Priority XID | High | Generic high-priority GPU error | Investigation required |
| **94** | Contained ECC | Medium | Contained ECC error (single app) | App restart, GPU reset when convenient |
| **95** | Uncontained ECC | Critical | Uncontained ECC error (multi-app) | Immediate GPU reset required |

#### Other Important XID Codes

| XID Code | Name | Severity | Description | Recovery Action |
|----------|------|----------|-------------|-----------------|
| **13** | Graphics Engine Exception | High | Graphics engine fault | Driver restart |
| **31** | GPU Memory Test Failed | Critical | Memory test failure | RMA evaluation |
| **43** | GPU Stopped Responding | Critical | GPU hang/crash | GPU reset |
| **45** | Preemption Timeout | Medium | GPU preemption timeout | Monitor, may self-recover |
| **54** | Power Cable Unplugged | Critical | Power delivery issue | Check power connections |
| **56** | Display Engine Error | Medium | Display subsystem fault | Driver restart |
| **61** | Internal Micro-controller Halt | Critical | Firmware crash | GPU reset, potential RMA |
| **62** | Internal Micro-controller Breakpoint | High | Firmware debug state | GPU reset |
| **68** | Video Processor Exception | Medium | Video engine fault | App restart |
| **69** | Video Processor Exception | Medium | Video engine fault | App restart |
| **74** | NVLink Error | High | NVLink communication error | Check NVLink connections |
| **79** | GPU Falling Off Bus | Critical | PCIe connection lost | Reseat GPU, check PCIe slot |

### 5.2 XID Error Field ID

**DCGM Field:**
- `DCGM_FI_DEV_XID_ERRORS` (Field ID: 230) - Value of last XID error encountered

**Monitoring Pattern:**
```
# Alert Logic for XID Errors
CRITICAL_XIDS = [48, 63, 64, 79, 95, 31, 43, 61]
HIGH_XIDS = [13, 62, 74, 92]
MEDIUM_XIDS = [45, 56, 68, 69, 94]

IF DCGM_FI_DEV_XID_ERRORS in CRITICAL_XIDS:
    SEVERITY: CRITICAL
    ACTION: Immediate GPU reset, investigate hardware

IF DCGM_FI_DEV_XID_ERRORS in HIGH_XIDS:
    SEVERITY: HIGH
    ACTION: Schedule GPU reset, monitor for recurrence

IF DCGM_FI_DEV_XID_ERRORS in MEDIUM_XIDS:
    SEVERITY: MEDIUM
    ACTION: Log and monitor, restart affected applications
```

### 5.3 XID Error Investigation Steps

1. **Check dmesg/kernel logs**: `dmesg | grep -i xid`
2. **Run nvidia-smi**: Verify GPU status and error counts
3. **Check DCGM health**: `dcgmi diag -r 1` (quick diagnostic)
4. **Review application logs**: Correlate with workload failures
5. **Consult official docs**: https://docs.nvidia.com/deploy/xid-errors/

---

## 6. Thermal Monitoring

GPU temperature monitoring is critical for preventing thermal throttling and hardware damage.

### 6.1 Thermal Field IDs

| Field Name | Field ID | Unit | Description |
|------------|----------|------|-------------|
| `DCGM_FI_DEV_GPU_TEMP` | - | °C | GPU core temperature |
| `DCGM_FI_DEV_MEMORY_TEMP` | - | °C | Memory temperature |
| `DCGM_FI_DEV_THERMAL_VIOLATION` | 241 | ns | Throttling duration due to thermal constraints |

### 6.2 Temperature Thresholds

#### Typical GPU Temperature Ranges (Vary by Model)

| Temperature Range | Status | Action |
|-------------------|--------|--------|
| **< 60°C** | Optimal | None |
| **60-80°C** | Normal | None |
| **80-90°C** | Elevated | Monitor cooling |
| **90-95°C** | High | Check cooling system |
| **95-100°C** | Warning | Thermal throttling begins |
| **> 100°C** | Critical | Automatic shutdown may occur |

#### Reference Thresholds (NVIDIA Networking Equipment)

- **Warning**: 105°C - Warning threshold message
- **Critical**: 120°C - Automatic shutdown
- **Emergency**: 130°C - Failsafe shutdown

**Note**: Consumer and datacenter GPU thresholds vary by model. Check specific GPU documentation.

### 6.3 Thermal Throttling

**Throttle Reason Bitmap:**
- `DCGM_FI_DEV_CLOCK_THROTTLE_REASONS` - Bitmap of throttle reasons

**Thermal Throttle Masks:**
- `DCGM_CLOCKS_THROTTLE_REASON_HW_THERMAL` (0x0000000000000040) - Hardware thermal slowdown
- `DCGM_CLOCKS_THROTTLE_REASON_SW_THERMAL` (0x0000000000000020) - Software thermal slowdown

### 6.4 Thermal Monitoring Best Practices

**Alert Thresholds:**
```
# Warning - Elevated Temperature
IF DCGM_FI_DEV_GPU_TEMP > 85°C for 5 minutes:
    SEVERITY: WARNING
    ACTION: Check cooling system, monitor trend

# Critical - High Temperature
IF DCGM_FI_DEV_GPU_TEMP > 95°C:
    SEVERITY: CRITICAL
    ACTION: Reduce load, check cooling immediately

# Thermal Throttling
IF DCGM_FI_DEV_THERMAL_VIOLATION > 0:
    SEVERITY: WARNING
    ACTION: Investigate thermal management, cooling insufficient
```

**Monitoring Pattern:**
- **Sample interval**: 5-20 seconds
- **Alert on sustained high temps**: >90°C for >5 minutes
- **Alert on thermal violations**: Any non-zero thermal violation time
- **Track trends**: Temperature increasing >10°C per hour

---

## 7. Power Monitoring

Power monitoring tracks GPU power consumption and power-related throttling.

### 7.1 Power Field IDs

| Field Name | Field ID | Unit | Description |
|------------|----------|------|-------------|
| `DCGM_FI_DEV_POWER_USAGE` | - | W | Current power draw |
| `DCGM_FI_DEV_TOTAL_ENERGY_CONSUMPTION` | - | mJ | Total energy since boot |
| `DCGM_FI_DEV_POWER_VIOLATION` | 240 | ns | Throttling duration due to power constraints |

### 7.2 Power Throttling

**Throttle Reason Masks:**
- `DCGM_CLOCKS_THROTTLE_REASON_SW_POWER_CAP` (0x0000000000000004) - Software power cap
- `DCGM_CLOCKS_THROTTLE_REASON_HW_POWER_BRAKE` (0x0000000000000080) - Hardware power brake

### 7.3 Power Monitoring Best Practices

**Alert Thresholds:**
```
# Power Limit Throttling
IF DCGM_FI_DEV_POWER_VIOLATION > 0:
    SEVERITY: WARNING
    ACTION: Review power budget, increase power limit if needed

# Sustained High Power
IF DCGM_FI_DEV_POWER_USAGE > (TDP * 0.95) for 10 minutes:
    SEVERITY: INFO
    ACTION: Normal under load, monitor for throttling

# Power Cable Issue
IF XID_ERROR == 54:
    SEVERITY: CRITICAL
    ACTION: Check power cable connections immediately
```

**Monitoring Pattern:**
- **Sample interval**: 20 seconds
- **Alert on power violations**: Any non-zero power violation time
- **Track power trends**: Sudden drops may indicate hardware issues
- **Monitor PSU capacity**: Ensure adequate power delivery

---

## 8. PCIe Health Monitoring

PCIe errors indicate communication issues between GPU and host system.

### 8.1 PCIe Field IDs

| Field Name | Field ID | Description |
|------------|----------|-------------|
| `DCGM_FI_DEV_PCIE_REPLAY_COUNTER` | 202 | Total PCIe retries/replays |
| `DCGM_FI_DEV_NVLINK_CRC_FLIT_ERROR_COUNT_TOTAL` | - | NVLink CRC errors |
| `DCGM_FI_DEV_PCIE_RX_BYTES` | - | PCIe receive throughput (bytes) |
| `DCGM_FI_DEV_PCIE_TX_BYTES` | - | PCIe transmit throughput (bytes) |

### 8.2 PCIe Error Thresholds

**DCGM Default Alert Thresholds:**
- **Warning**: >8 PCIe replays per minute
- **Failure**: User-configurable threshold exceeded

### 8.3 PCIe Monitoring Best Practices

**Alert Thresholds:**
```
# PCIe Replay Errors
IF DCGM_FI_DEV_PCIE_REPLAY_COUNTER rate > 8/minute:
    SEVERITY: WARNING
    ACTION: Check PCIe connection, reseat GPU if needed

IF DCGM_FI_DEV_PCIE_REPLAY_COUNTER rate > 100/minute:
    SEVERITY: CRITICAL
    ACTION: Failing PCIe bus, investigate immediately

# PCIe Connection Lost (XID 79)
IF XID_ERROR == 79:
    SEVERITY: CRITICAL
    ACTION: GPU falling off bus, reseat GPU, check PCIe slot

# NVLink CRC Errors
IF DCGM_FI_DEV_NVLINK_CRC_FLIT_ERROR_COUNT_TOTAL > 0:
    SEVERITY: WARNING
    ACTION: Check NVLink connections
```

**Monitoring Pattern:**
- **Sample interval**: 20 seconds
- **Alert on any PCIe replays**: Healthy GPUs should have 0
- **Track replay rate**: Increasing rate indicates degrading connection
- **Monitor PCIe bandwidth**: Sudden drops may indicate lane degradation

---

## 9. Memory Error Management

GPU memory errors are managed through page retirement (pre-A100) or row remapping (A100+).

### 9.1 Memory Error Management by Architecture

#### Pre-A100 GPUs: Dynamic Page Retirement

**Mechanism:**
- Pages with errors are retired (marked as unusable)
- Combined total of 64 pages can be retired (SBE + DBE)
- Retirement occurs on: 1 DBE or 2 SBE on same address

**RMA Thresholds:**
- **60 retired pages**: RMA evaluation recommended
- **15+ pages + 1/week new retirements**: Early RMA evaluation

#### A100 and Later: Row Remapping

**Mechanism:**
- Rows with uncorrectable errors are remapped
- Up to 8 rows per memory bank can be remapped
- More robust than page retirement

**RMA Triggers:**
- Row-remapping failure flag set
- Remapping attempt on bank with 8 rows already remapped
- Remapping attempt on already-remapped row

### 9.2 Memory Error Field IDs

| Field Name | Description |
|------------|-------------|
| `DCGM_FI_DEV_RETIRED_SBE` | Pages retired due to SBE (monotonic) |
| `DCGM_FI_DEV_RETIRED_DBE` | Pages retired due to DBE (monotonic) |
| `DCGM_FI_DEV_RETIRED_PENDING` | Pages pending retirement |
| `DCGM_FI_DEV_UNCORRECTABLE_REMAPPED_ROWS` | Remapped rows (A100+) |
| `DCGM_FI_DEV_CORRECTABLE_REMAPPED_ROWS` | Correctable remapped rows (A100+) |
| `DCGM_FI_DEV_ROW_REMAP_FAILURE` | Row remapping failure flag (A100+) |

### 9.3 Memory Error Monitoring Best Practices

**Alert Thresholds:**
```
# Pre-A100 GPUs
total_retired = DCGM_FI_DEV_RETIRED_SBE + DCGM_FI_DEV_RETIRED_DBE

IF total_retired > 60:
    SEVERITY: CRITICAL
    ACTION: RMA evaluation required

IF total_retired > 15 AND weekly_increase > 1:
    SEVERITY: WARNING
    ACTION: Early RMA evaluation, monitor closely

# A100+ GPUs
IF DCGM_FI_DEV_ROW_REMAP_FAILURE == True:
    SEVERITY: CRITICAL
    ACTION: RMA evaluation required, run field diagnostic

IF DCGM_FI_DEV_UNCORRECTABLE_REMAPPED_ROWS > 6:
    SEVERITY: WARNING
    ACTION: Approaching remapping limit, monitor closely
```

**Monitoring Pattern:**
- **Sample interval**: 60 seconds (low frequency, monotonic counter)
- **Alert on any retired pages**: Track rate of increase
- **Alert on pending retirements**: Reboot required to complete retirement
- **Track historical trend**: Accelerating retirement rate indicates failing memory

---

## 10. GPU Driver Status

Driver health monitoring ensures the GPU driver is functioning correctly.

### 10.1 Driver Health Watch

**DCGM Health Watch System:**
- `DCGM_HEALTH_WATCH_DRIVER` - Driver-related issues

**Common Driver Issues:**
- Driver crashes or hangs
- Communication timeouts
- Version mismatches
- Module load failures

### 10.2 Driver Monitoring Best Practices

**Monitoring Pattern:**
- Monitor driver version: Ensure consistency across cluster
- Check driver load status: Verify driver loaded correctly
- Monitor driver errors: Check dmesg for NVIDIA driver errors
- Track driver restarts: Frequent restarts indicate instability

**Alert Thresholds:**
```
# Driver Crash/Restart
IF driver_restart_count > 0:
    SEVERITY: HIGH
    ACTION: Investigate driver stability, check logs

# Version Mismatch
IF driver_version != expected_version:
    SEVERITY: MEDIUM
    ACTION: Update or rollback driver to match cluster
```

---

## 11. Alert Thresholds and Best Practices

### 11.1 Summary of Critical Alert Thresholds

| Metric | Warning Threshold | Critical Threshold | Action |
|--------|-------------------|--------------------| -------|
| **DBE ECC Errors** | >0 | >1 per hour | GPU reset, investigate |
| **SBE ECC Errors** | >10/hour | >100/hour | Monitor, schedule maintenance |
| **Retired Pages** | >15 (increasing) | >60 | Early RMA / RMA required |
| **Row Remap Failure** | N/A | Flag set | RMA evaluation |
| **PCIe Replays** | >8/minute | >100/minute | Check connection / Critical |
| **GPU Temperature** | >85°C | >95°C | Check cooling / Immediate action |
| **Thermal Violation** | >0 ns | >60s/hour | Check cooling / Critical cooling issue |
| **Power Violation** | >0 ns | >60s/hour | Review power / Increase power limit |
| **XID Errors** | Medium XIDs | Critical XIDs | See XID table |
| **NVLink CRC Errors** | >0 | >100/hour | Check connections / Replace cable |

### 11.2 Alerting Best Practices

#### Alert Severity Levels

**Critical (P1):**
- DBE ECC errors
- XID errors: 48, 63, 64, 79, 95, 31, 43, 61
- GPU temperature >95°C
- Row remapping failure (A100+)
- Retired pages >60 (pre-A100)
- PCIe replays >100/minute

**High (P2):**
- SBE ECC errors >100/hour
- XID errors: 13, 62, 74, 92
- GPU temperature >90°C sustained
- PCIe replays >8/minute
- Thermal or power violations

**Medium (P3):**
- SBE ECC errors 10-100/hour
- XID errors: 45, 56, 68, 69, 94
- Retired pages >15 and increasing
- NVLink CRC errors

**Info:**
- Normal operational metrics
- Baseline establishment
- Trend tracking

#### Alert Aggregation

**Group related metrics:**
- Memory health: ECC errors + retired pages + XID 48/63/64/94/95
- Thermal health: Temperature + thermal violations + thermal throttling
- Power health: Power usage + power violations + power throttling
- PCIe health: Replay counter + XID 79 + bandwidth degradation
- Driver health: XID errors + driver restarts + communication timeouts

**Alert deduplication:**
- Single alert for multiple related symptoms
- Suppress downstream alerts when root cause identified
- Time-based aggregation (e.g., max 1 alert per 5 minutes per issue)

#### Alert Notification Strategy

**Critical alerts:**
- Immediate notification (page/SMS)
- Alert operations team
- Auto-ticket creation
- Escalation after 15 minutes

**High alerts:**
- Email + Slack notification
- Alert on-call engineer
- Auto-ticket creation
- Escalation after 1 hour

**Medium alerts:**
- Email notification
- Dashboard visibility
- Daily digest
- No auto-escalation

---

## 12. Health Check Intervals

### 12.1 Default Intervals

**DCGM Exporter Default:**
- **Scrape interval**: 20 seconds
- **Update frequency**: Every 20 seconds
- **Prometheus scrape**: Every 20 seconds (configurable)

**Customizable Intervals:**
- **High resolution**: 1 second (high cost, detailed visibility)
- **Standard**: 20 seconds (recommended for production)
- **Low frequency**: 60 seconds (cost-optimized, low churn metrics)

### 12.2 Interval Recommendations by Metric Type

| Metric Category | Recommended Interval | Rationale |
|-----------------|----------------------|-----------|
| **ECC Errors** | 60 seconds | Monotonic counters, low churn |
| **Temperature** | 5-20 seconds | Fast-changing, critical for thermal events |
| **Power Usage** | 20 seconds | Moderate change rate |
| **PCIe Replays** | 20 seconds | Low frequency events |
| **GPU Utilization** | 1-20 seconds | Fast-changing, workload dependent |
| **Memory Usage** | 20 seconds | Moderate change rate |
| **XID Errors** | Event-driven | Polled every 20s, but logged immediately |
| **Retired Pages** | 300 seconds | Rare changes, monotonic counter |

### 12.3 Diagnostic Test Intervals

**Quick Diagnostic (Level 1):**
- **Duration**: 2-3 minutes
- **Frequency**: Every 24 hours or on-demand
- **Tests**: Basic GPU health, PCIe, memory access

**Medium Diagnostic (Level 2):**
- **Duration**: 10-15 minutes
- **Frequency**: Weekly or on suspicious metrics
- **Tests**: Extended memory tests, bandwidth tests, stress tests

**Long Diagnostic (Level 3):**
- **Duration**: 30-60 minutes
- **Frequency**: Monthly or before deployment
- **Tests**: Comprehensive memory tests, sustained power tests, thermal tests

### 12.4 Production Monitoring Pattern

**Continuous Monitoring (Background):**
```
Every 20 seconds:
  - Collect core metrics (temperature, power, utilization)
  - Track ECC errors, XID errors, PCIe replays
  - Update Prometheus/monitoring platform

Every 60 seconds:
  - Collect low-churn metrics (retired pages, driver version)
  - Calculate rates (errors per minute)

Every 5 minutes:
  - Aggregate and analyze trends
  - Evaluate alert thresholds
  - Update dashboards
```

**Periodic Diagnostics:**
```
Daily (non-peak hours):
  - Run quick diagnostic (2-3 min)
  - Verify GPU health before workload

Weekly (maintenance window):
  - Run medium diagnostic (10-15 min)
  - Review historical metrics
  - Check for degradation trends

Monthly (planned maintenance):
  - Run long diagnostic (30-60 min)
  - Comprehensive health assessment
  - Plan hardware refreshes if needed
```

---

## 13. DCGM Field IDs Reference

### 13.1 Health and Error Metrics

| Field Name | Field ID | Type | Unit | Description |
|------------|----------|------|------|-------------|
| `DCGM_FI_DEV_XID_ERRORS` | 230 | Gauge | - | Last XID error |
| `DCGM_FI_DEV_ECC_SBE_VOL_TOTAL` | 310 | Counter | - | Total volatile SBE |
| `DCGM_FI_DEV_ECC_DBE_VOL_TOTAL` | 311 | Counter | - | Total volatile DBE |
| `DCGM_FI_DEV_ECC_SBE_AGG_TOTAL` | 312 | Counter | - | Total aggregate SBE |
| `DCGM_FI_DEV_ECC_DBE_AGG_TOTAL` | 313 | Counter | - | Total aggregate DBE |
| `DCGM_FI_DEV_RETIRED_SBE` | - | Counter | - | Pages retired (SBE) |
| `DCGM_FI_DEV_RETIRED_DBE` | - | Counter | - | Pages retired (DBE) |
| `DCGM_FI_DEV_RETIRED_PENDING` | - | Gauge | - | Pending retirements |
| `DCGM_FI_DEV_PCIE_REPLAY_COUNTER` | 202 | Counter | - | PCIe replays |
| `DCGM_FI_DEV_THERMAL_VIOLATION` | 241 | Counter | ns | Thermal throttle time |
| `DCGM_FI_DEV_POWER_VIOLATION` | 240 | Counter | ns | Power throttle time |

### 13.2 Temperature and Power Metrics

| Field Name | Field ID | Type | Unit | Description |
|------------|----------|------|------|-------------|
| `DCGM_FI_DEV_GPU_TEMP` | - | Gauge | °C | GPU core temperature |
| `DCGM_FI_DEV_MEMORY_TEMP` | - | Gauge | °C | Memory temperature |
| `DCGM_FI_DEV_POWER_USAGE` | - | Gauge | W | Current power draw |
| `DCGM_FI_DEV_TOTAL_ENERGY_CONSUMPTION` | - | Counter | mJ | Total energy |
| `DCGM_FI_DEV_CLOCK_THROTTLE_REASONS` | - | Bitmap | - | Throttle reasons |

### 13.3 Utilization Metrics

| Field Name | Field ID | Type | Unit | Description |
|------------|----------|------|------|-------------|
| `DCGM_FI_DEV_GPU_UTIL` | - | Gauge | % | GPU utilization |
| `DCGM_FI_DEV_MEM_COPY_UTIL` | - | Gauge | % | Memory utilization |
| `DCGM_FI_DEV_ENC_UTIL` | - | Gauge | % | Encoder utilization |
| `DCGM_FI_DEV_DEC_UTIL` | - | Gauge | % | Decoder utilization |

### 13.4 Profiling Metrics (Advanced)

| Field Name | Type | Unit | Description |
|------------|------|------|-------------|
| `DCGM_FI_PROF_GR_ENGINE_ACTIVE` | Gauge | % | Graphics engine active ratio |
| `DCGM_FI_PROF_SM_ACTIVE` | Gauge | % | SM active ratio |
| `DCGM_FI_PROF_SM_OCCUPANCY` | Gauge | % | SM occupancy |
| `DCGM_FI_PROF_PIPE_TENSOR_ACTIVE` | Gauge | % | Tensor core active ratio |
| `DCGM_FI_PROF_DRAM_ACTIVE` | Gauge | % | DRAM active ratio |
| `DCGM_FI_PROF_PCIE_RX_BYTES` | Counter | bytes | PCIe receive throughput |
| `DCGM_FI_PROF_PCIE_TX_BYTES` | Counter | bytes | PCIe transmit throughput |

### 13.5 NVLink Metrics

| Field Name | Type | Description |
|------------|------|-------------|
| `DCGM_FI_DEV_NVLINK_CRC_FLIT_ERROR_COUNT_TOTAL` | Counter | NVLink CRC errors |
| `DCGM_FI_DEV_NVLINK_RECOVERY_ERROR_COUNT_TOTAL` | Counter | NVLink recovery errors |
| `DCGM_FI_DEV_NVLINK_BANDWIDTH_TOTAL` | Gauge | Total NVLink bandwidth |

### 13.6 Complete Field ID Documentation

**Official Reference:**
- https://docs.nvidia.com/datacenter/dcgm/latest/dcgm-api/dcgm-api-field-ids.html
- https://github.com/NVIDIA/DCGM/blob/master/dcgmlib/dcgm_fields.h

---

## 14. Production Monitoring Patterns

### 14.1 Metrics Collection Architecture

**Recommended Stack:**
```

         Visualization Layer              
  (Grafana, Kibana, Custom Dashboards)    

                   

        Metrics Storage Layer             
  (Prometheus, InfluxDB, Elasticsearch)   

                   

        Metrics Collection Layer          
  (DCGM Exporter, Telegraf, Beats)        

                   

              DCGM Agent                  
  (Standalone Daemon on each GPU node)    

                   

           NVIDIA GPU Driver              
  (nvml library, GPU hardware access)     

```

### 14.2 Dashboard Design

#### Primary Health Dashboard

**Key Panels:**
1. **GPU Fleet Overview**
   - Total GPUs
   - Healthy GPUs (green)
   - Warning GPUs (yellow)
   - Critical GPUs (red)
   - Offline GPUs (gray)

2. **Critical Errors (Real-time)**
   - DBE ECC errors in last 1 hour
   - Critical XID errors in last 1 hour
   - GPUs with >60 retired pages
   - GPUs with temperature >90°C

3. **Error Trends (24 hours)**
   - ECC error rate over time
   - PCIe replay rate over time
   - XID error frequency
   - Temperature trends

4. **Resource Utilization**
   - GPU utilization heatmap
   - Memory utilization by GPU
   - Power consumption by GPU
   - Temperature by GPU

5. **Health Score**
   - Per-GPU health percentage
   - Fleet average health
   - Trend (improving/degrading)

#### GPU Detail Dashboard

**Per-GPU Metrics:**
1. **Identification**
   - GPU ID, model, driver version
   - Hostname, slot, UUID

2. **Current Status**
   - Temperature, power, utilization
   - Memory used/free
   - Clock speeds

3. **Error Counters**
   - ECC errors (SBE/DBE volatile and aggregate)
   - Retired pages
   - PCIe replays
   - Last XID error

4. **Historical Trends**
   - Temperature over 24h
   - Power consumption over 24h
   - Error rate trends
   - Utilization patterns

5. **Throttling Events**
   - Thermal violations
   - Power violations
   - Throttle reasons breakdown

### 14.3 Alert Rules (Prometheus Format)

```yaml
groups:
- name: gpu_health_critical
  interval: 30s
  rules:

  # Critical: Double-Bit ECC Errors
  - alert: GPUDoubleBitECCError
    expr: DCGM_FI_DEV_ECC_DBE_VOL_TOTAL > 0
    for: 0m
    labels:
      severity: critical
    annotations:
      summary: "GPU {{ $labels.gpu }} has {{ $value }} double-bit ECC errors"
      description: "Uncorrectable memory error detected. GPU reset required."

  # Critical: High Temperature
  - alert: GPUHighTemperature
    expr: DCGM_FI_DEV_GPU_TEMP > 95
    for: 1m
    labels:
      severity: critical
    annotations:
      summary: "GPU {{ $labels.gpu }} temperature {{ $value }}°C exceeds 95°C"
      description: "Critical temperature. Check cooling system immediately."

  # Critical: Memory Retirement Limit
  - alert: GPUMemoryRetirementLimitReached
    expr: (DCGM_FI_DEV_RETIRED_SBE + DCGM_FI_DEV_RETIRED_DBE) > 60
    for: 0m
    labels:
      severity: critical
    annotations:
      summary: "GPU {{ $labels.gpu }} has {{ $value }} retired pages"
      description: "RMA evaluation required. GPU approaching memory retirement limit."

  # Critical: PCIe Errors High Rate
  - alert: GPUPCIeErrorsHighRate
    expr: rate(DCGM_FI_DEV_PCIE_REPLAY_COUNTER[1m]) > 100
    for: 5m
    labels:
      severity: critical
    annotations:
      summary: "GPU {{ $labels.gpu }} PCIe replays {{ $value }}/min"
      description: "High PCIe error rate. Investigate bus connection."

- name: gpu_health_warning
  interval: 60s
  rules:

  # Warning: Single-Bit ECC Errors High Rate
  - alert: GPUSingleBitECCErrorsHigh
    expr: rate(DCGM_FI_DEV_ECC_SBE_VOL_TOTAL[1h]) > 100
    for: 10m
    labels:
      severity: warning
    annotations:
      summary: "GPU {{ $labels.gpu }} has high SBE rate {{ $value }}/hour"
      description: "Monitor for increasing error rate. Schedule maintenance."

  # Warning: Elevated Temperature
  - alert: GPUElevatedTemperature
    expr: DCGM_FI_DEV_GPU_TEMP > 85
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "GPU {{ $labels.gpu }} temperature {{ $value }}°C exceeds 85°C"
      description: "Elevated temperature. Monitor cooling system."

  # Warning: Thermal Throttling
  - alert: GPUThermalThrottling
    expr: rate(DCGM_FI_DEV_THERMAL_VIOLATION[5m]) > 0
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "GPU {{ $labels.gpu }} experiencing thermal throttling"
      description: "GPU throttled due to thermal constraints. Check cooling."

  # Warning: PCIe Errors
  - alert: GPUPCIeErrors
    expr: rate(DCGM_FI_DEV_PCIE_REPLAY_COUNTER[1m]) > 8
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "GPU {{ $labels.gpu }} PCIe replays {{ $value }}/min"
      description: "PCIe errors detected. Monitor connection health."
```

### 14.4 Runbook Examples

#### Runbook: Double-Bit ECC Error (Critical)

**Alert:** `GPUDoubleBitECCError`

**Investigation Steps:**
1. Check alert details for GPU ID and error count
2. SSH to affected node: `ssh gpu-node-<id>`
3. Verify with nvidia-smi: `nvidia-smi -q -d MEMORY`
4. Check kernel logs: `dmesg | grep -i xid | tail -20`
5. Check DCGM health: `dcgmi diag -r 1`

**Immediate Actions:**
1. Mark GPU as unavailable in scheduler
2. Drain active workloads from GPU
3. Reset GPU: `nvidia-smi -r -i <gpu_id>`
4. If error persists, reboot node
5. Run extended diagnostics: `dcgmi diag -r 3`

**Resolution:**
- If error clears: Return GPU to service, monitor closely
- If error persists: Remove from service, initiate RMA

**Escalation:**
- If multiple GPUs affected: Page infrastructure team
- If cluster-wide pattern: Emergency incident, all hands

#### Runbook: High Temperature (Critical)

**Alert:** `GPUHighTemperature`

**Investigation Steps:**
1. Check current temperature: `nvidia-smi --query-gpu=temperature.gpu --format=csv`
2. Check cooling system status
3. Verify room/rack temperature
4. Check for blocked airflow
5. Check thermal history: Grafana GPU detail dashboard

**Immediate Actions:**
1. Reduce GPU load if possible
2. Increase cooling (fans, AC)
3. Check thermal paste (if accessible)
4. Monitor for thermal throttling

**Resolution:**
- If temperature drops below 85°C: Continue monitoring
- If remains high: Reduce load or take offline for maintenance

**Prevention:**
- Review cooling system maintenance schedule
- Check for dust buildup
- Verify proper rack airflow design

### 14.5 Integration Patterns

#### Kubernetes Integration

**DaemonSet Deployment:**
```yaml
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: dcgm-exporter
  namespace: gpu-monitoring
spec:
  selector:
    matchLabels:
      app: dcgm-exporter
  template:
    metadata:
      labels:
        app: dcgm-exporter
    spec:
      nodeSelector:
        accelerator: nvidia-gpu
      containers:
      - name: dcgm-exporter
        image: nvcr.io/nvidia/k8s/dcgm-exporter:latest
        securityContext:
          runAsNonRoot: false
          runAsUser: 0
        volumeMounts:
        - name: pod-gpu-resources
          readOnly: true
          mountPath: /var/lib/kubelet/pod-resources
      volumes:
      - name: pod-gpu-resources
        hostPath:
          path: /var/lib/kubelet/pod-resources
```

#### Prometheus Scrape Config

```yaml
scrape_configs:
  - job_name: 'dcgm-exporter'
    scrape_interval: 20s
    kubernetes_sd_configs:
    - role: pod
      namespaces:
        names:
        - gpu-monitoring
    relabel_configs:
    - source_labels: [__meta_kubernetes_pod_label_app]
      action: keep
      regex: dcgm-exporter
```

---

## 15. Diagnostic Workflows

### 15.1 Quick Health Check (2-3 minutes)

**Purpose:** Daily verification of GPU health

**Command:**
```bash
dcgmi diag -r 1
```

**Tests Performed:**
- GPU presence and responsiveness
- PCIe connectivity
- NVML library access
- Basic memory access
- ECC error check

**Pass/Fail Criteria:**
- All GPUs responsive
- No ECC errors
- PCIe link active
- Driver communication successful

### 15.2 Medium Diagnostic (10-15 minutes)

**Purpose:** Weekly health check or issue investigation

**Command:**
```bash
dcgmi diag -r 2
```

**Tests Performed:**
- All quick diagnostic tests
- Memory bandwidth test
- PCIe bandwidth test
- SM stress test
- Power and thermal stress test
- ECC error scan

**Pass/Fail Criteria:**
- All quick diagnostic tests pass
- Memory bandwidth within spec
- PCIe bandwidth within spec
- No thermal throttling under load
- No power violations under load

### 15.3 Extended Diagnostic (30-60 minutes)

**Purpose:** Monthly maintenance or pre-deployment validation

**Command:**
```bash
dcgmi diag -r 3
```

**Tests Performed:**
- All medium diagnostic tests
- Extended memory test (memtest-like)
- Sustained power test
- Sustained thermal test
- Error injection test (if supported)
- Long-running stability test

**Pass/Fail Criteria:**
- All medium diagnostic tests pass
- No memory errors in extended test
- Sustained power and thermal stability
- No errors over 30+ minute stress test

### 15.4 Diagnostic Plugin Details

| Plugin Name | Duration | Purpose |
|-------------|----------|---------|
| **Deployment** | 30s | Quick GPU presence and health |
| **PCIe** | 2m | PCIe bandwidth and connectivity |
| **SM Stress** | 5m | Streaming multiprocessor stability |
| **Targeted Power** | 5m | Power delivery and stability |
| **Memory Bandwidth** | 3m | Memory subsystem performance |
| **Memtest** | 10-30m | Comprehensive memory error detection |
| **NVBandwidth** | 5m | NVLink and PCIe bandwidth validation |
| **EUD** | 15m | Extended utility diagnostics |

### 15.5 Automated Diagnostic Scheduling

**Recommended Schedule:**

```bash
# Daily quick diagnostic (non-peak hours)
0 2 * * * /usr/bin/dcgmi diag -r 1 >> /var/log/dcgm-diag-daily.log 2>&1

# Weekly medium diagnostic (maintenance window)
0 3 * * 0 /usr/bin/dcgm diag -r 2 >> /var/log/dcgm-diag-weekly.log 2>&1

# Monthly extended diagnostic (planned maintenance)
0 4 1 * * /usr/bin/dcgmi diag -r 3 >> /var/log/dcgm-diag-monthly.log 2>&1
```

**Integration with Job Scheduler:**
```bash
# Slurm prologue script (before job starts)
#!/bin/bash
# Quick health check before job
dcgmi diag -r 1 -i $CUDA_VISIBLE_DEVICES
if [ $? -ne 0 ]; then
    echo "GPU health check failed. Job aborted."
    exit 1
fi
```

### 15.6 Diagnostic Failure Response

**Level 1 Failure (Quick Diagnostic):**
- Run medium diagnostic for detailed analysis
- Check kernel logs for XID errors
- Verify driver version and load status
- If persistent, mark GPU as unavailable

**Level 2 Failure (Medium Diagnostic):**
- Run extended diagnostic to isolate issue
- Review specific plugin failures
- Check thermal and power history
- Consider GPU reset or node reboot

**Level 3 Failure (Extended Diagnostic):**
- GPU likely has hardware issue
- Remove from service immediately
- Initiate RMA process
- Run NVIDIA Field Diagnostic tool for validation

---

## Appendix A: Quick Reference Tables

### A.1 Critical Error Quick Reference

| Error Type | Severity | First Action |
|------------|----------|--------------|
| DBE ECC Error | Critical | GPU reset |
| XID 48, 95 | Critical | GPU reset |
| XID 79 | Critical | Reseat GPU |
| Temp >95°C | Critical | Reduce load |
| 60+ Retired Pages | Critical | RMA evaluation |
| PCIe Replays >100/min | Critical | Check connection |

### A.2 Monitoring Interval Quick Reference

| Metric | Interval | Type |
|--------|----------|------|
| Temperature | 5-20s | Fast-changing |
| Power | 20s | Moderate |
| Utilization | 1-20s | Fast-changing |
| ECC Errors | 60s | Monotonic |
| Retired Pages | 300s | Rare |
| PCIe Replays | 20s | Event-based |

### A.3 Alert Severity Quick Reference

| Severity | Response Time | Notification |
|----------|---------------|--------------|
| Critical | Immediate | Page/SMS |
| High | 15 minutes | Email + Slack |
| Medium | 1 hour | Email |
| Info | None | Dashboard |

---

## Appendix B: Resources and Documentation

### Official NVIDIA Documentation

- **DCGM User Guide**: https://docs.nvidia.com/datacenter/dcgm/latest/user-guide/
- **DCGM API Reference**: https://docs.nvidia.com/datacenter/dcgm/latest/dcgm-api/
- **Field IDs**: https://docs.nvidia.com/datacenter/dcgm/latest/dcgm-api/dcgm-api-field-ids.html
- **XID Errors**: https://docs.nvidia.com/deploy/xid-errors/
- **GPU Memory Error Management**: https://docs.nvidia.com/deploy/a100-gpu-mem-error-mgmt/
- **GPU Debug Guidelines**: https://docs.nvidia.com/deploy/gpu-debug-guidelines/

### Open Source Projects

- **DCGM**: https://github.com/NVIDIA/DCGM
- **DCGM Exporter**: https://github.com/NVIDIA/dcgm-exporter
- **Go DCGM**: https://github.com/NVIDIA/go-dcgm

### Community Resources

- **NVIDIA Developer Forums**: https://forums.developer.nvidia.com/
- **DCGM Documentation (Latest)**: https://docs.nvidia.com/datacenter/dcgm/latest/
- **Monitoring Best Practices**: Various cloud provider documentation (GCP, AWS, Azure)

---

## Appendix C: Glossary

| Term | Definition |
|------|------------|
| **DCGM** | Data Center GPU Manager - NVIDIA's GPU monitoring and management toolkit |
| **ECC** | Error-Correcting Code - Memory error detection and correction |
| **SBE** | Single-Bit Error - Correctable memory error |
| **DBE** | Double-Bit Error - Uncorrectable memory error |
| **XID** | eXecution IDentifier - GPU error report from driver |
| **PCIe** | Peripheral Component Interconnect Express - GPU connection interface |
| **NVLink** | NVIDIA's high-speed GPU-to-GPU interconnect |
| **NVML** | NVIDIA Management Library - Low-level GPU management API |
| **RMA** | Return Merchandise Authorization - Hardware replacement process |
| **TTFT** | Time To First Token - Latency metric for ML inference |
| **Profiling** | Advanced performance metrics from GPU hardware counters |
| **Row Remapping** | A100+ memory error recovery mechanism |
| **Page Retirement** | Pre-A100 memory error recovery mechanism |

---

**End of DCGM Health Metrics Research Document**

This document provides comprehensive knowledge for implementing production-grade NVIDIA GPU health monitoring using DCGM. For questions or updates, consult official NVIDIA documentation or the DCGM GitHub repository.
