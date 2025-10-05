#!/usr/bin/env python3
"""
Example demonstrating video input support in chat completions (NVIDIA Cosmos extension).

This example shows how to use FakeAI with video inputs for physical AI applications.
Based on NVIDIA Cosmos world foundation models for video understanding.
"""
import asyncio

from fakeai import AppConfig, FakeAIService
from fakeai.models import (
    ChatCompletionRequest,
    Message,
    Role,
    TextContent,
    VideoContent,
    VideoUrl,
)


async def example_single_video():
    """Example with single video input."""
    print("=" * 70)
    print("Example 1: Single Video Input (NVIDIA Cosmos)")
    print("=" * 70)

    config = AppConfig(response_delay=0.0)
    service = FakeAIService(config)

    # Small synthetic video (typical for Cosmos benchmarking)
    # 5 seconds at 4 fps, 512×288 resolution
    request = ChatCompletionRequest(
        model="nvidia/cosmos-reason1-7b",
        messages=[
            Message(
                role=Role.USER,
                content=[
                    TextContent(
                        type="text",
                        text="Describe what you see in this video."
                    ),
                    VideoContent(
                        type="video_url",
                        video_url=VideoUrl(
                            url="https://example.com/video.mp4?width=512&height=288&duration=5.0&fps=4",
                            detail="high"
                        )
                    )
                ]
            )
        ],
        max_tokens=150,
    )

    response = await service.create_chat_completion(request)

    print(f"Response: {response.choices[0].message.content}\n")
    print(f"Token Usage:")
    print(f"  - Prompt tokens: {response.usage.prompt_tokens}")
    print(f"  - Completion tokens: {response.usage.completion_tokens}")
    print(f"  - Total tokens: {response.usage.total_tokens}")
    print()


async def example_multiple_videos():
    """Example with multiple video inputs."""
    print("=" * 70)
    print("Example 2: Multiple Video Comparison")
    print("=" * 70)

    config = AppConfig(response_delay=0.0)
    service = FakeAIService(config)

    request = ChatCompletionRequest(
        model="nvidia/cosmos-reason1-7b",
        messages=[
            Message(
                role=Role.USER,
                content=[
                    TextContent(
                        type="text",
                        text="Compare these two driving scenarios:"
                    ),
                    VideoContent(
                        type="video_url",
                        video_url=VideoUrl(
                            url="https://example.com/512x288_5.0s_4.0fps/scenario1.mp4",
                            detail="high"
                        )
                    ),
                    VideoContent(
                        type="video_url",
                        video_url=VideoUrl(
                            url="https://example.com/512x288_5.0s_4.0fps/scenario2.mp4",
                            detail="high"
                        )
                    )
                ]
            )
        ],
        max_tokens=200,
    )

    response = await service.create_chat_completion(request)

    print(f"Response: {response.choices[0].message.content}\n")
    print(f"Token Usage:")
    print(f"  - Prompt tokens: {response.usage.prompt_tokens}")
    print(f"  - Completion tokens: {response.usage.completion_tokens}")
    print(f"  - Total tokens: {response.usage.total_tokens}")
    print()


async def example_multimodal_video_and_image():
    """Example combining video with images and text."""
    print("=" * 70)
    print("Example 3: Video + Image + Text (Full Multimodal)")
    print("=" * 70)

    config = AppConfig(response_delay=0.0)
    service = FakeAIService(config)

    from fakeai.models import ImageContent, ImageUrl

    request = ChatCompletionRequest(
        model="nvidia/cosmos-reason1-7b",
        messages=[
            Message(
                role=Role.USER,
                content=[
                    TextContent(
                        type="text",
                        text="Compare the video sequence with this reference image:"
                    ),
                    VideoContent(
                        type="video_url",
                        video_url=VideoUrl(
                            url="https://example.com/512x288_5.0s_4.0fps/robot_motion.mp4",
                            detail="high"
                        )
                    ),
                    ImageContent(
                        type="image_url",
                        image_url=ImageUrl(
                            url="https://example.com/1024x1024/reference_pose.jpg",
                            detail="high"
                        )
                    ),
                    TextContent(
                        type="text",
                        text="Did the robot achieve the target pose?"
                    )
                ]
            )
        ],
        max_tokens=150,
    )

    response = await service.create_chat_completion(request)

    print(f"Response: {response.choices[0].message.content}\n")
    print(f"Token Usage:")
    print(f"  - Total prompt tokens: {response.usage.prompt_tokens}")
    print(f"    - Includes video, image, and text tokens")
    print(f"  - Completion tokens: {response.usage.completion_tokens}")
    print(f"  - Total tokens: {response.usage.total_tokens}")
    print()


async def example_low_detail_video():
    """Example with low detail for faster processing."""
    print("=" * 70)
    print("Example 4: Low Detail Video (Faster Processing)")
    print("=" * 70)

    config = AppConfig(response_delay=0.0)
    service = FakeAIService(config)

    request = ChatCompletionRequest(
        model="nvidia/cosmos-reason1-7b",
        messages=[
            Message(
                role=Role.USER,
                content=[
                    TextContent(
                        type="text",
                        text="Quick summary of this video:"
                    ),
                    VideoContent(
                        type="video_url",
                        video_url=VideoUrl(
                            url="https://example.com/512x288_5.0s_4.0fps/quick_scan.mp4",
                            detail="low"  # Low detail = fewer tokens, faster
                        )
                    )
                ]
            )
        ],
        max_tokens=100,
    )

    response = await service.create_chat_completion(request)

    print(f"Response: {response.choices[0].message.content}\n")
    print(f"Token Usage (Low Detail):")
    print(f"  - Prompt tokens: {response.usage.prompt_tokens}")
    print(f"  - Completion tokens: {response.usage.completion_tokens}")
    print(f"  - Total tokens: {response.usage.total_tokens}")
    print()


async def example_data_uri_video():
    """Example with data URI (base64 encoded video)."""
    print("=" * 70)
    print("Example 5: Data URI Video (Base64 Encoded)")
    print("=" * 70)

    config = AppConfig(response_delay=0.0)
    service = FakeAIService(config)

    # Data URI with metadata in the format:
    # data:video/mp4;meta=WIDTHxHEIGHT:DURATIONs@FPSfps;base64,DATA
    request = ChatCompletionRequest(
        model="nvidia/cosmos-reason1-7b",
        messages=[
            Message(
                role=Role.USER,
                content=[
                    TextContent(
                        type="text",
                        text="Analyze this embedded video:"
                    ),
                    VideoContent(
                        type="video_url",
                        video_url=VideoUrl(
                            url="data:video/mp4;meta=512x288:5.0s@4fps;base64,AAAAA...",
                            detail="high"
                        )
                    )
                ]
            )
        ],
        max_tokens=100,
    )

    response = await service.create_chat_completion(request)

    print(f"Response: {response.choices[0].message.content}\n")
    print(f"Token Usage:")
    print(f"  - Prompt tokens: {response.usage.prompt_tokens}")
    print(f"  - Completion tokens: {response.usage.completion_tokens}")
    print(f"  - Total tokens: {response.usage.total_tokens}")
    print()


async def main():
    """Run all video examples."""
    await example_single_video()
    await example_multiple_videos()
    await example_multimodal_video_and_image()
    await example_low_detail_video()
    await example_data_uri_video()

    print("=" * 70)
    print("All video examples completed successfully! ✅")
    print("=" * 70)
    print()
    print("Note: Video support uses the NVIDIA Cosmos extension format:")
    print('  {"type": "video_url", "video_url": {"url": "...", "detail": "..."}}"')
    print()
    print("Typical video parameters (for benchmarking):")
    print("  - Resolution: 512×288 (low latency)")
    print("  - Duration: 5 seconds")
    print("  - FPS: 4 frames per second")
    print("  - Detail: 'low' (fast) or 'high' (accurate)")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
