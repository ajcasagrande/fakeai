"""
Admin Configuration API Handler.

Provides HTTP endpoints for runtime configuration management.
"""

from typing import Optional

from fastapi import HTTPException, status
from pydantic import BaseModel, Field

from fakeai.config.live_config import ConfigUpdateError, LiveConfigManager


# Request/Response models
class KVCacheConfigUpdate(BaseModel):
    """KV cache configuration update request."""

    enabled: Optional[bool] = Field(
        None, description="Enable/disable KV cache")
    block_size: Optional[int] = Field(
        None, description="Cache block size (8-64, power of 2)"
    )
    overlap_weight: Optional[float] = Field(
        None, ge=0.0, le=2.0, description="Cache overlap weight"
    )
    load_balance_weight: Optional[float] = Field(
        None, ge=0.0, le=2.0, description="Load balance weight"
    )


class DynamoConfigUpdate(BaseModel):
    """Dynamo/worker configuration update request."""

    num_workers: Optional[int] = Field(
        None, ge=1, le=32, description="Number of workers")
    worker_timeout: Optional[float] = Field(
        None, ge=1.0, le=300.0, description="Worker timeout (seconds)"
    )
    queue_depth_limit: Optional[int] = Field(
        None, ge=1, le=10000, description="Max queue depth"
    )


class GenerationConfigUpdate(BaseModel):
    """Generation/timing configuration update request."""

    ttft_ms: Optional[float] = Field(
        None, ge=0.0, le=10000.0, description="Time to first token (ms)"
    )
    ttft_variance_percent: Optional[float] = Field(
        None, ge=0.0, le=100.0, description="TTFT variance (%)"
    )
    itl_ms: Optional[float] = Field(
        None, ge=0.0, le=1000.0, description="Inter-token latency (ms)"
    )
    itl_variance_percent: Optional[float] = Field(
        None, ge=0.0, le=100.0, description="ITL variance (%)"
    )
    response_delay: Optional[float] = Field(
        None, ge=0.0, le=10.0, description="Base response delay (seconds)"
    )
    random_delay: Optional[bool] = Field(
        None, description="Enable random delay variation"
    )
    max_variance: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="Max variance factor"
    )


class GPUConfigUpdate(BaseModel):
    """GPU/DCGM configuration update request."""

    num_gpus: Optional[int] = Field(
        None, ge=1, le=8, description="Number of GPUs")
    gpu_model: Optional[str] = Field(
        None, description="GPU model (A100-80GB, H100-80GB, H200-141GB)"
    )
    simulate_dcgm: Optional[bool] = Field(
        None, description="Enable/disable DCGM simulation"
    )


class ConfigResponse(BaseModel):
    """Configuration response."""

    success: bool
    message: str
    config: dict


class ErrorResponse(BaseModel):
    """Error response."""

    success: bool = False
    error: str


# Handler functions
async def get_all_config(live_config_manager: LiveConfigManager) -> dict:
    """
    Get all current configuration.

    Args:
        live_config_manager: The live config manager instance

    Returns:
        Dict with all configuration sections
    """
    try:
        config = live_config_manager.get_all_config()
        return {
            "success": True,
            "config": config,
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve configuration: {str(e)}",
        )


async def update_kv_cache_config(
    update: KVCacheConfigUpdate, live_config_manager: LiveConfigManager
) -> ConfigResponse:
    """
    Update KV cache configuration.

    Args:
        update: KV cache configuration updates
        live_config_manager: The live config manager instance

    Returns:
        ConfigResponse with updated configuration
    """
    try:
        config = live_config_manager.update_kv_cache_config(
            enabled=update.enabled,
            block_size=update.block_size,
            overlap_weight=update.overlap_weight,
            load_balance_weight=update.load_balance_weight,
        )
        return ConfigResponse(
            success=True,
            message="KV cache configuration updated successfully",
            config=config,
        )
    except ConfigUpdateError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update KV cache configuration: {str(e)}",
        )


async def update_dynamo_config(
    update: DynamoConfigUpdate, live_config_manager: LiveConfigManager
) -> ConfigResponse:
    """
    Update Dynamo/worker configuration.

    Args:
        update: Dynamo configuration updates
        live_config_manager: The live config manager instance

    Returns:
        ConfigResponse with updated configuration
    """
    try:
        config = live_config_manager.update_dynamo_config(
            num_workers=update.num_workers,
            worker_timeout=update.worker_timeout,
            queue_depth_limit=update.queue_depth_limit,
        )
        return ConfigResponse(
            success=True,
            message="Dynamo configuration updated successfully",
            config=config,
        )
    except ConfigUpdateError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update Dynamo configuration: {str(e)}",
        )


async def update_generation_config(
    update: GenerationConfigUpdate, live_config_manager: LiveConfigManager
) -> ConfigResponse:
    """
    Update generation/timing configuration.

    Args:
        update: Generation configuration updates
        live_config_manager: The live config manager instance

    Returns:
        ConfigResponse with updated configuration
    """
    try:
        config = live_config_manager.update_generation_config(
            ttft_ms=update.ttft_ms,
            ttft_variance_percent=update.ttft_variance_percent,
            itl_ms=update.itl_ms,
            itl_variance_percent=update.itl_variance_percent,
            response_delay=update.response_delay,
            random_delay=update.random_delay,
            max_variance=update.max_variance,
        )
        return ConfigResponse(
            success=True,
            message="Generation configuration updated successfully",
            config=config,
        )
    except ConfigUpdateError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update generation configuration: {str(e)}",
        )


async def update_gpu_config(
    update: GPUConfigUpdate, live_config_manager: LiveConfigManager
) -> ConfigResponse:
    """
    Update GPU/DCGM configuration.

    Args:
        update: GPU configuration updates
        live_config_manager: The live config manager instance

    Returns:
        ConfigResponse with updated configuration
    """
    try:
        config = live_config_manager.update_gpu_config(
            num_gpus=update.num_gpus,
            gpu_model=update.gpu_model,
            simulate_dcgm=update.simulate_dcgm,
        )
        return ConfigResponse(
            success=True,
            message="GPU configuration updated successfully",
            config=config,
        )
    except ConfigUpdateError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update GPU configuration: {str(e)}",
        )


async def reset_config(
        live_config_manager: LiveConfigManager) -> ConfigResponse:
    """
    Reset all configuration to defaults.

    Args:
        live_config_manager: The live config manager instance

    Returns:
        ConfigResponse with default configuration
    """
    try:
        config = live_config_manager.reset_to_defaults()
        return ConfigResponse(
            success=True,
            message="Configuration reset to defaults successfully",
            config=config,
        )
    except ConfigUpdateError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reset configuration: {str(e)}",
        )


async def get_change_history(
    live_config_manager: LiveConfigManager, limit: int = 50
) -> dict:
    """
    Get configuration change audit trail.

    Args:
        live_config_manager: The live config manager instance
        limit: Maximum number of changes to return

    Returns:
        Dict with change history
    """
    try:
        history = live_config_manager.get_change_history(limit=limit)
        return {
            "success": True,
            "history": history,
            "count": len(history),
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve change history: {str(e)}",
        )
