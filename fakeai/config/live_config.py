"""
Live Configuration Manager.

Allows runtime configuration changes WITHOUT server restart.
Provides thread-safe updates with validation and immediate application.
"""

import logging
import threading
from collections import deque
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)


class ConfigUpdateError(Exception):
    """Raised when configuration update fails."""


class LiveConfigManager:
    """
    Manages runtime configuration changes without server restart.

    Features:
    - Thread-safe updates using RLock
    - Configuration validation before applying
    - Immediate propagation to running services
    - Rollback support on failure
    - Audit trail of changes
    """

    def __init__(self, app_config):
        """
        Initialize live config manager.

        Args:
            app_config: The application's AppConfig instance
        """
        self.app_config = app_config
        self._lock = threading.RLock()
        self._update_callbacks: dict[str, list[Callable]] = {}
        self._change_history: deque[dict] = deque(maxlen=100)  # Use deque with maxlen for auto-cleanup
        self._max_history = 100

        logger.info("Live configuration manager initialized")

    def register_callback(self, config_section: str, callback: Callable):
        """
        Register a callback to be notified when a config section changes.

        Args:
            config_section: Name of config section (e.g., 'kv_cache', 'dynamo')
            callback: Function to call with (old_value, new_value)
        """
        with self._lock:
            if config_section not in self._update_callbacks:
                self._update_callbacks[config_section] = []
            self._update_callbacks[config_section].append(callback)
            logger.debug(
                f"Registered callback for config section: {config_section}")

    def _notify_callbacks(
            self,
            config_section: str,
            old_value: Any,
            new_value: Any):
        """Notify all registered callbacks for a config section."""
        callbacks = self._update_callbacks.get(config_section, [])
        for callback in callbacks:
            try:
                callback(old_value, new_value)
            except Exception as e:
                logger.error(
                    f"Error in config update callback for {config_section}: {e}")

    def _record_change(
            self,
            section: str,
            field: str,
            old_value: Any,
            new_value: Any):
        """Record configuration change in audit trail."""
        import time

        change_record = {
            "timestamp": time.time(),
            "section": section,
            "field": field,
            "old_value": old_value,
            "new_value": new_value,
        }
        self._change_history.append(change_record)  # deque with maxlen auto-removes oldest

    def update_kv_cache_config(
        self,
        enabled: Optional[bool] = None,
        block_size: Optional[int] = None,
        overlap_weight: Optional[float] = None,
        load_balance_weight: Optional[float] = None,
    ) -> dict:
        """
        Update KV cache configuration at runtime.

        Args:
            enabled: Enable/disable KV cache
            block_size: Cache block size (must be power of 2, 8-64)
            overlap_weight: Weight for cache overlap scoring (0.0-2.0)
            load_balance_weight: Weight for load balancing (0.0-2.0)

        Returns:
            Dict with updated configuration

        Raises:
            ConfigUpdateError: If validation fails
        """
        with self._lock:
            changes = {}
            old_values = {}

            try:
                # Validate and collect changes
                if enabled is not None:
                    if not isinstance(enabled, bool):
                        raise ConfigUpdateError("enabled must be a boolean")
                    old_values["kv_cache_enabled"] = self.app_config.kv_cache_enabled
                    changes["kv_cache_enabled"] = enabled

                if block_size is not None:
                    if not isinstance(block_size, int):
                        raise ConfigUpdateError(
                            "block_size must be an integer")
                    if block_size < 8 or block_size > 64:
                        raise ConfigUpdateError(
                            "block_size must be between 8 and 64")
                    if not (block_size & (block_size - 1) == 0):
                        raise ConfigUpdateError(
                            "block_size must be a power of 2")
                    old_values["kv_cache_block_size"] = (
                        self.app_config.kv_cache_block_size
                    )
                    changes["kv_cache_block_size"] = block_size

                if overlap_weight is not None:
                    if not isinstance(overlap_weight, (int, float)):
                        raise ConfigUpdateError(
                            "overlap_weight must be a number")
                    if overlap_weight < 0.0 or overlap_weight > 2.0:
                        raise ConfigUpdateError(
                            "overlap_weight must be between 0.0 and 2.0")
                    old_values["kv_overlap_weight"] = self.app_config.kv_overlap_weight
                    changes["kv_overlap_weight"] = float(overlap_weight)

                if load_balance_weight is not None:
                    if not isinstance(load_balance_weight, (int, float)):
                        raise ConfigUpdateError(
                            "load_balance_weight must be a number")
                    if load_balance_weight < 0.0 or load_balance_weight > 2.0:
                        raise ConfigUpdateError(
                            "load_balance_weight must be between 0.0 and 2.0"
                        )
                    old_values["load_balance_weight"] = (
                        self.app_config.load_balance_weight
                    )
                    changes["load_balance_weight"] = float(load_balance_weight)

                if not changes:
                    raise ConfigUpdateError(
                        "No valid configuration changes provided")

                # Apply changes
                for key, value in changes.items():
                    setattr(self.app_config, key, value)
                    self._record_change(
                        "kv_cache", key, old_values[key], value)

                # Notify callbacks
                self._notify_callbacks("kv_cache", old_values, changes)

                logger.info(f"KV cache configuration updated: {changes}")
                return self.get_kv_cache_config()

            except Exception as e:
                # Rollback on error
                for key, value in old_values.items():
                    setattr(self.app_config, key, value)
                raise ConfigUpdateError(
                    f"Failed to update KV cache config: {
                        str(e)}")

    def update_dynamo_config(
        self,
        num_workers: Optional[int] = None,
        worker_timeout: Optional[float] = None,
        queue_depth_limit: Optional[int] = None,
    ) -> dict:
        """
        Update Dynamo/worker configuration at runtime.

        Args:
            num_workers: Number of workers (1-32)
            worker_timeout: Worker timeout in seconds (1.0-300.0)
            queue_depth_limit: Max queue depth (1-10000)

        Returns:
            Dict with updated configuration

        Raises:
            ConfigUpdateError: If validation fails
        """
        with self._lock:
            changes = {}
            old_values = {}

            try:
                if num_workers is not None:
                    if not isinstance(num_workers, int):
                        raise ConfigUpdateError(
                            "num_workers must be an integer")
                    if num_workers < 1 or num_workers > 32:
                        raise ConfigUpdateError(
                            "num_workers must be between 1 and 32")
                    old_values["dynamo_num_workers"] = self.app_config.dynamo_num_workers
                    changes["dynamo_num_workers"] = num_workers

                if worker_timeout is not None:
                    if not isinstance(worker_timeout, (int, float)):
                        raise ConfigUpdateError(
                            "worker_timeout must be a number")
                    if worker_timeout < 1.0 or worker_timeout > 300.0:
                        raise ConfigUpdateError(
                            "worker_timeout must be between 1.0 and 300.0"
                        )
                    old_values["dynamo_worker_timeout"] = (
                        self.app_config.dynamo_worker_timeout
                    )
                    changes["dynamo_worker_timeout"] = float(worker_timeout)

                if queue_depth_limit is not None:
                    if not isinstance(queue_depth_limit, int):
                        raise ConfigUpdateError(
                            "queue_depth_limit must be an integer")
                    if queue_depth_limit < 1 or queue_depth_limit > 10000:
                        raise ConfigUpdateError(
                            "queue_depth_limit must be between 1 and 10000"
                        )
                    old_values["queue_depth_limit"] = self.app_config.queue_depth_limit
                    changes["queue_depth_limit"] = queue_depth_limit

                if not changes:
                    raise ConfigUpdateError(
                        "No valid configuration changes provided")

                # Apply changes
                for key, value in changes.items():
                    setattr(self.app_config, key, value)
                    self._record_change("dynamo", key, old_values[key], value)

                # Notify callbacks
                self._notify_callbacks("dynamo", old_values, changes)

                logger.info(f"Dynamo configuration updated: {changes}")
                return self.get_dynamo_config()

            except Exception as e:
                # Rollback on error
                for key, value in old_values.items():
                    setattr(self.app_config, key, value)
                raise ConfigUpdateError(
                    f"Failed to update Dynamo config: {
                        str(e)}")

    def update_generation_config(
        self,
        ttft_ms: Optional[float] = None,
        ttft_variance_percent: Optional[float] = None,
        itl_ms: Optional[float] = None,
        itl_variance_percent: Optional[float] = None,
        response_delay: Optional[float] = None,
        random_delay: Optional[bool] = None,
        max_variance: Optional[float] = None,
    ) -> dict:
        """
        Update token generation timing configuration at runtime.

        Args:
            ttft_ms: Time to first token in milliseconds (0.0-10000.0)
            ttft_variance_percent: TTFT variance as percentage (0.0-100.0)
            itl_ms: Inter-token latency in milliseconds (0.0-1000.0)
            itl_variance_percent: ITL variance as percentage (0.0-100.0)
            response_delay: Base response delay in seconds (0.0-10.0)
            random_delay: Enable random delay variation
            max_variance: Max variance factor (0.0-1.0)

        Returns:
            Dict with updated configuration

        Raises:
            ConfigUpdateError: If validation fails
        """
        with self._lock:
            changes = {}
            old_values = {}

            try:
                if ttft_ms is not None:
                    if not isinstance(ttft_ms, (int, float)):
                        raise ConfigUpdateError("ttft_ms must be a number")
                    if ttft_ms < 0.0 or ttft_ms > 10000.0:
                        raise ConfigUpdateError(
                            "ttft_ms must be between 0.0 and 10000.0")
                    old_values["ttft_ms"] = self.app_config.generation.ttft_ms
                    changes["ttft_ms"] = float(ttft_ms)

                if ttft_variance_percent is not None:
                    if not isinstance(ttft_variance_percent, (int, float)):
                        raise ConfigUpdateError(
                            "ttft_variance_percent must be a number")
                    if ttft_variance_percent < 0.0 or ttft_variance_percent > 100.0:
                        raise ConfigUpdateError(
                            "ttft_variance_percent must be between 0.0 and 100.0"
                        )
                    old_values["ttft_variance_percent"] = (
                        self.app_config.generation.ttft_variance_percent
                    )
                    changes["ttft_variance_percent"] = float(
                        ttft_variance_percent)

                if itl_ms is not None:
                    if not isinstance(itl_ms, (int, float)):
                        raise ConfigUpdateError("itl_ms must be a number")
                    if itl_ms < 0.0 or itl_ms > 1000.0:
                        raise ConfigUpdateError(
                            "itl_ms must be between 0.0 and 1000.0")
                    old_values["itl_ms"] = self.app_config.generation.itl_ms
                    changes["itl_ms"] = float(itl_ms)

                if itl_variance_percent is not None:
                    if not isinstance(itl_variance_percent, (int, float)):
                        raise ConfigUpdateError(
                            "itl_variance_percent must be a number")
                    if itl_variance_percent < 0.0 or itl_variance_percent > 100.0:
                        raise ConfigUpdateError(
                            "itl_variance_percent must be between 0.0 and 100.0"
                        )
                    old_values["itl_variance_percent"] = (
                        self.app_config.generation.itl_variance_percent
                    )
                    changes["itl_variance_percent"] = float(
                        itl_variance_percent)

                if response_delay is not None:
                    if not isinstance(response_delay, (int, float)):
                        raise ConfigUpdateError(
                            "response_delay must be a number")
                    if response_delay < 0.0 or response_delay > 10.0:
                        raise ConfigUpdateError(
                            "response_delay must be between 0.0 and 10.0"
                        )
                    old_values["response_delay"] = (
                        self.app_config.generation.response_delay
                    )
                    changes["response_delay"] = float(response_delay)

                if random_delay is not None:
                    if not isinstance(random_delay, bool):
                        raise ConfigUpdateError(
                            "random_delay must be a boolean")
                    old_values["random_delay"] = self.app_config.generation.random_delay
                    changes["random_delay"] = random_delay

                if max_variance is not None:
                    if not isinstance(max_variance, (int, float)):
                        raise ConfigUpdateError(
                            "max_variance must be a number")
                    if max_variance < 0.0 or max_variance > 1.0:
                        raise ConfigUpdateError(
                            "max_variance must be between 0.0 and 1.0")
                    old_values["max_variance"] = self.app_config.generation.max_variance
                    changes["max_variance"] = float(max_variance)

                if not changes:
                    raise ConfigUpdateError(
                        "No valid configuration changes provided")

                # Apply changes to generation config
                for key, value in changes.items():
                    setattr(self.app_config.generation, key, value)
                    self._record_change(
                        "generation", key, old_values[key], value)

                # Notify callbacks
                self._notify_callbacks("generation", old_values, changes)

                logger.info(f"Generation configuration updated: {changes}")
                return self.get_generation_config()

            except Exception as e:
                # Rollback on error
                for key, value in old_values.items():
                    setattr(self.app_config.generation, key, value)
                raise ConfigUpdateError(
                    f"Failed to update generation config: {
                        str(e)}")

    def update_gpu_config(
        self,
        num_gpus: Optional[int] = None,
        gpu_model: Optional[str] = None,
        simulate_dcgm: Optional[bool] = None,
    ) -> dict:
        """
        Update GPU/DCGM configuration at runtime.

        Args:
            num_gpus: Number of GPUs (1-8)
            gpu_model: GPU model (A100-80GB, H100-80GB, H200-141GB)
            simulate_dcgm: Enable/disable DCGM simulation

        Returns:
            Dict with updated configuration

        Raises:
            ConfigUpdateError: If validation fails
        """
        with self._lock:
            changes = {}
            old_values = {}

            try:
                if num_gpus is not None:
                    if not isinstance(num_gpus, int):
                        raise ConfigUpdateError("num_gpus must be an integer")
                    if num_gpus < 1 or num_gpus > 8:
                        raise ConfigUpdateError(
                            "num_gpus must be between 1 and 8")
                    old_values["dcgm_num_gpus"] = self.app_config.dcgm_num_gpus
                    changes["dcgm_num_gpus"] = num_gpus

                if gpu_model is not None:
                    valid_models = ["A100-80GB", "H100-80GB", "H200-141GB"]
                    if gpu_model not in valid_models:
                        raise ConfigUpdateError(
                            f"gpu_model must be one of: {
                                ', '.join(valid_models)}")
                    old_values["dcgm_gpu_model"] = self.app_config.dcgm_gpu_model
                    changes["dcgm_gpu_model"] = gpu_model

                if simulate_dcgm is not None:
                    if not isinstance(simulate_dcgm, bool):
                        raise ConfigUpdateError(
                            "simulate_dcgm must be a boolean")
                    old_values["simulate_dcgm"] = self.app_config.simulate_dcgm
                    changes["simulate_dcgm"] = simulate_dcgm

                if not changes:
                    raise ConfigUpdateError(
                        "No valid configuration changes provided")

                # Apply changes
                for key, value in changes.items():
                    setattr(self.app_config, key, value)
                    self._record_change("gpu", key, old_values[key], value)

                # Notify callbacks
                self._notify_callbacks("gpu", old_values, changes)

                logger.info(f"GPU configuration updated: {changes}")
                return self.get_gpu_config()

            except Exception as e:
                # Rollback on error
                for key, value in old_values.items():
                    setattr(self.app_config, key, value)
                raise ConfigUpdateError(
                    f"Failed to update GPU config: {str(e)}")

    def get_all_config(self) -> dict:
        """Get all current configuration values."""
        with self._lock:
            return {
                "kv_cache": self.get_kv_cache_config(),
                "dynamo": self.get_dynamo_config(),
                "generation": self.get_generation_config(),
                "gpu": self.get_gpu_config(),
            }

    def get_kv_cache_config(self) -> dict:
        """Get current KV cache configuration."""
        with self._lock:
            return {
                "enabled": self.app_config.kv_cache_enabled,
                "block_size": self.app_config.kv_cache_block_size,
                "overlap_weight": self.app_config.kv_overlap_weight,
                "load_balance_weight": self.app_config.load_balance_weight,
            }

    def get_dynamo_config(self) -> dict:
        """Get current Dynamo configuration."""
        with self._lock:
            return {
                "num_workers": self.app_config.dynamo_num_workers,
                "worker_timeout": self.app_config.dynamo_worker_timeout,
                "queue_depth_limit": self.app_config.queue_depth_limit,
            }

    def get_generation_config(self) -> dict:
        """Get current generation configuration."""
        with self._lock:
            return {
                "ttft_ms": self.app_config.generation.ttft_ms,
                "ttft_variance_percent": self.app_config.generation.ttft_variance_percent,
                "itl_ms": self.app_config.generation.itl_ms,
                "itl_variance_percent": self.app_config.generation.itl_variance_percent,
                "response_delay": self.app_config.generation.response_delay,
                "random_delay": self.app_config.generation.random_delay,
                "max_variance": self.app_config.generation.max_variance,
            }

    def get_gpu_config(self) -> dict:
        """Get current GPU configuration."""
        with self._lock:
            return {
                "num_gpus": self.app_config.dcgm_num_gpus,
                "gpu_model": self.app_config.dcgm_gpu_model,
                "simulate_dcgm": self.app_config.simulate_dcgm,
            }

    def reset_to_defaults(self) -> dict:
        """
        Reset all configuration to defaults.

        Returns:
            Dict with default configuration values

        Raises:
            ConfigUpdateError: If reset fails
        """
        with self._lock:
            try:
                # Create a new default config instance
                from fakeai.config import AppConfig

                default_config = AppConfig()

                # Store old values for rollback
                old_config_snapshot = self.get_all_config()

                # Reset KV cache
                self.app_config.kv_cache_enabled = default_config.kv_cache_enabled
                self.app_config.kv_cache_block_size = (
                    default_config.kv_cache_block_size
                )
                self.app_config.kv_overlap_weight = default_config.kv_overlap_weight
                self.app_config.load_balance_weight = default_config.load_balance_weight

                # Reset Dynamo
                self.app_config.dynamo_num_workers = default_config.dynamo_num_workers
                self.app_config.dynamo_worker_timeout = (
                    default_config.dynamo_worker_timeout
                )
                self.app_config.queue_depth_limit = default_config.queue_depth_limit

                # Reset Generation
                self.app_config.generation.ttft_ms = default_config.generation.ttft_ms
                self.app_config.generation.ttft_variance_percent = (
                    default_config.generation.ttft_variance_percent
                )
                self.app_config.generation.itl_ms = default_config.generation.itl_ms
                self.app_config.generation.itl_variance_percent = (
                    default_config.generation.itl_variance_percent
                )
                self.app_config.generation.response_delay = (
                    default_config.generation.response_delay
                )
                self.app_config.generation.random_delay = (
                    default_config.generation.random_delay
                )
                self.app_config.generation.max_variance = (
                    default_config.generation.max_variance
                )

                # Reset GPU
                self.app_config.dcgm_num_gpus = default_config.dcgm_num_gpus
                self.app_config.dcgm_gpu_model = default_config.dcgm_gpu_model
                self.app_config.simulate_dcgm = default_config.simulate_dcgm

                # Record reset
                import time

                self._change_history.append(
                    {
                        "timestamp": time.time(),
                        "section": "all",
                        "field": "reset",
                        "old_value": old_config_snapshot,
                        "new_value": "defaults",
                    }
                )

                # Notify all callbacks
                for section in ["kv_cache", "dynamo", "generation", "gpu"]:
                    self._notify_callbacks(
                        section, old_config_snapshot, "reset")

                logger.info("Configuration reset to defaults")
                return self.get_all_config()

            except Exception as e:
                raise ConfigUpdateError(
                    f"Failed to reset configuration: {
                        str(e)}")

    def get_change_history(self, limit: int = 50) -> list[dict]:
        """
        Get configuration change audit trail.

        Args:
            limit: Maximum number of changes to return

        Returns:
            List of change records (most recent first)
        """
        with self._lock:
            return list(reversed(self._change_history[-limit:]))
