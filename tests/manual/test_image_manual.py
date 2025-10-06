#!/usr/bin/env python3
"""
Manual test script for image generation module.

Run this while the FakeAI server is running to test image generation.
"""

import base64
import io
import sys

from PIL import Image

try:
    from openai import OpenAI
except ImportError:
    print("ERROR: openai package not installed")
    print("Install with: pip install openai")
    sys.exit(1)


def test_url_generation():
    """Test URL-based image generation."""
    print("=" * 60)
    print("Testing URL-based image generation...")
    print("=" * 60)

    client = OpenAI(
        api_key="test",
        base_url="http://localhost:8000/v1"
    )

    response = client.images.generate(
        model="dall-e-3",
        prompt="A beautiful sunset over mountains with vivid colors",
        size="1024x1024",
        quality="hd",
        style="vivid",
        n=2,
    )

    print(f"\nGenerated {len(response.data)} images:")
    for i, img in enumerate(response.data, 1):
        print(f"  {i}. {img.url}")

    print("\nYou can open these URLs in a browser to view the images!")
    print("✓ URL generation test passed\n")

    return response.data[0].url


def test_base64_generation():
    """Test base64-based image generation."""
    print("=" * 60)
    print("Testing base64-based image generation...")
    print("=" * 60)

    client = OpenAI(
        api_key="test",
        base_url="http://localhost:8000/v1"
    )

    response = client.images.generate(
        model="dall-e-3",
        prompt="A futuristic city skyline at night",
        size="512x512",
        quality="standard",
        style="natural",
        n=1,
        response_format="b64_json",
    )

    print(f"\nGenerated base64 image: {len(response.data[0].b64_json)} characters")

    # Decode and verify
    img_data = base64.b64decode(response.data[0].b64_json)
    img = Image.open(io.BytesIO(img_data))

    print(f"Image format: {img.format}")
    print(f"Image size: {img.size}")
    print(f"Image mode: {img.mode}")

    # Optionally save to disk
    output_path = "/tmp/fakeai_test_image.png"
    img.save(output_path)
    print(f"\nImage saved to: {output_path}")
    print("✓ Base64 generation test passed\n")


def test_all_sizes():
    """Test all supported DALL-E sizes."""
    print("=" * 60)
    print("Testing all supported sizes...")
    print("=" * 60)

    client = OpenAI(
        api_key="test",
        base_url="http://localhost:8000/v1"
    )

    sizes = [
        "256x256",
        "512x512",
        "1024x1024",
        "1792x1024",
        "1024x1792",
    ]

    for size in sizes:
        response = client.images.generate(
            model="dall-e-3",
            prompt=f"Test image for {size}",
            size=size,
            n=1,
        )
        print(f"  ✓ {size}: {response.data[0].url}")

    print("\n✓ All sizes test passed\n")


def test_quality_and_style():
    """Test different quality and style combinations."""
    print("=" * 60)
    print("Testing quality and style combinations...")
    print("=" * 60)

    client = OpenAI(
        api_key="test",
        base_url="http://localhost:8000/v1"
    )

    combinations = [
        ("standard", "vivid"),
        ("standard", "natural"),
        ("hd", "vivid"),
        ("hd", "natural"),
    ]

    for quality, style in combinations:
        response = client.images.generate(
            model="dall-e-3",
            prompt=f"Landscape with {quality} quality and {style} style",
            size="512x512",
            quality=quality,
            style=style,
            n=1,
        )
        print(f"  ✓ {quality}/{style}: {response.data[0].url}")

    print("\n✓ Quality and style test passed\n")


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("FakeAI Image Generation Manual Tests")
    print("=" * 60)
    print("\nMake sure the FakeAI server is running:")
    print("  python -m fakeai server --generate-actual-images")
    print("=" * 60 + "\n")

    try:
        # Run tests
        test_url_generation()
        test_base64_generation()
        test_all_sizes()
        test_quality_and_style()

        print("=" * 60)
        print("✓ ALL TESTS PASSED!")
        print("=" * 60)

    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
