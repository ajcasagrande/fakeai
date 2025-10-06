# Image Generation Module

FakeAI now includes a comprehensive image generation module that creates **actual placeholder images** using PIL (Pillow) instead of just returning fake URLs.

## Features

- **Actual Image Generation**: Uses PIL to generate real PNG images with:
  - Solid color or gradient backgrounds
  - Random geometric patterns (grid, circles, triangles, lines, dots, waves)
  - Text overlay with prompt
  - Model name + timestamp watermark

- **Full DALL-E Compatibility**: Supports all DALL-E sizes
  - DALL-E 2: 256×256, 512×512, 1024×1024
  - DALL-E 3: 1024×1024, 1792×1024, 1024×1792

- **Quality Modes**:
  - **Standard**: Simple solid color backgrounds
  - **HD**: Gradient backgrounds with pattern overlays and better antialiasing

- **Style Support**:
  - **Vivid**: Bright, saturated colors
  - **Natural**: Muted, earth tones

- **Response Formats**:
  - **URL**: Returns URL to generated image (served via `/images/{id}.png`)
  - **b64_json**: Returns base64-encoded PNG data

- **Multiple Images**: Generate n different images with varied colors/patterns

- **In-Memory Storage**:
  - Images stored in memory for quick retrieval
  - Automatic cleanup after retention period (default: 1 hour)
  - Background cleanup thread

## Configuration

Enable image generation with environment variables:

```bash
# Enable actual image generation (default: true)
export FAKEAI_GENERATE_ACTUAL_IMAGES=true

# Storage backend (default: memory)
export FAKEAI_IMAGE_STORAGE_BACKEND=memory

# Retention period in hours (default: 1)
export FAKEAI_IMAGE_RETENTION_HOURS=1
```

## Usage

### With OpenAI Client

```python
from openai import OpenAI

client = OpenAI(
    api_key="test",
    base_url="http://localhost:8000/v1"
)

# Generate image with URL
response = client.images.generate(
    model="dall-e-3",
    prompt="A beautiful sunset over mountains",
    size="1024x1024",
    quality="hd",
    style="vivid",
    n=2,
)

for img in response.data:
    print(f"Image URL: {img.url}")
    # Open in browser or download

# Generate image with base64
response = client.images.generate(
    model="dall-e-3",
    prompt="A futuristic city skyline",
    size="512x512",
    quality="standard",
    style="natural",
    response_format="b64_json",
)

# Decode and save
import base64
from PIL import Image
import io

img_data = base64.b64decode(response.data[0].b64_json)
img = Image.open(io.BytesIO(img_data))
img.save("output.png")
```

### Direct API

```bash
# Generate image
curl -X POST http://localhost:8000/v1/images/generations \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer test" \
  -d '{
    "model": "dall-e-3",
    "prompt": "A serene lake at sunset",
    "size": "1024x1024",
    "quality": "hd",
    "style": "vivid",
    "n": 1
  }'

# Response includes URL like:
# {"data": [{"url": "http://localhost:8000/images/abc123.png"}]}

# Retrieve the generated image
curl http://localhost:8000/images/abc123.png -o output.png
```

## Architecture

### ImageGenerator Class

```python
class ImageGenerator:
    def generate(
        self,
        prompt: str,
        size: str = "1024x1024",
        quality: str = "standard",
        style: str = "vivid",
        n: int = 1,
        response_format: str = "url",
        model: str = "dall-e-3",
    ) -> list[dict]:
        """Generate n images based on the prompt."""

    def create_image(
        self,
        size: tuple[int, int],
        prompt: str,
        quality: str,
        style: str,
        model: str,
        index: int = 0,
    ) -> bytes:
        """Create actual PNG image with PIL."""

    def store_image(self, image_bytes: bytes) -> str:
        """Store generated image in memory."""

    def get_image(self, image_id: str) -> bytes | None:
        """Retrieve stored image."""
```

### Integration Points

1. **FakeAIService**: Initializes ImageGenerator in `__init__` if enabled
2. **generate_images()**: Uses ImageGenerator if available, fallback to fake URLs
3. **FastAPI Endpoint**: `GET /images/{image_id}.png` serves generated images
4. **Automatic Cleanup**: Background thread removes expired images

### Image Generation Process

1. **Color Selection**: Based on style (vivid/natural), select from palette
2. **Background**: Solid color (standard) or gradient (HD)
3. **Pattern Overlay**: HD quality adds geometric patterns
4. **Text Overlay**: Prompt text centered with shadow
5. **Watermark**: Model name + timestamp in bottom-right
6. **Storage**: Store PNG bytes with UUID, return URL or base64

## Testing

### Unit Tests

```bash
# Run all image generator tests (25 tests)
pytest tests/test_image_generator.py -v

# Test coverage includes:
# - All supported sizes
# - Quality modes (standard/HD)
# - Style modes (vivid/natural)
# - Multiple images (n parameter)
# - Response formats (URL/base64)
# - Image storage and retrieval
# - Expiration and cleanup
# - Reproducibility
# - Concurrent generation
```

### Manual Testing

```bash
# Start server with image generation
python -m fakeai server --generate-actual-images

# Run manual test script
python test_image_manual.py
```

## Examples

### All Sizes

```python
sizes = ["256x256", "512x512", "1024x1024", "1792x1024", "1024x1792"]

for size in sizes:
    response = client.images.generate(
        prompt=f"Test image for {size}",
        size=size,
    )
    print(f"{size}: {response.data[0].url}")
```

### Quality Comparison

```python
# Standard quality
standard = client.images.generate(
    prompt="Mountain landscape",
    quality="standard",
)

# HD quality (with gradient and patterns)
hd = client.images.generate(
    prompt="Mountain landscape",
    quality="hd",
)
```

### Style Comparison

```python
# Vivid style (bright colors)
vivid = client.images.generate(
    prompt="Abstract art",
    style="vivid",
)

# Natural style (muted colors)
natural = client.images.generate(
    prompt="Abstract art",
    style="natural",
)
```

### Multiple Images

```python
# Generate 5 variations
response = client.images.generate(
    prompt="Diverse landscape scenes",
    n=5,
)

# Each image has unique colors and patterns
for i, img in enumerate(response.data, 1):
    print(f"Image {i}: {img.url}")
```

## Storage Statistics

```python
# Get storage stats from FakeAIService
stats = fakeai_service.image_generator.get_storage_stats()

print(f"Total images: {stats['total_images']}")
print(f"Total size: {stats['total_size_mb']} MB")
print(f"Backend: {stats['backend']}")
print(f"Retention: {stats['retention_hours']} hours")
```

## Limitations

- **In-Memory Only**: Currently only supports in-memory storage
- **Placeholder Images**: Not actual AI-generated images, just styled placeholders
- **Font Dependency**: Requires system fonts (falls back to default if not available)
- **No Persistence**: Images are lost on server restart
- **No Edit/Variations**: Only supports generation, not editing or variations

## Future Enhancements

- Disk-based storage backend
- Redis caching support
- Image editing endpoints
- Image variations
- Upscaling
- Custom templates
- More pattern types
- Animation/GIF support

## Dependencies

- **Pillow (PIL)**: Core image generation library
- **Python 3.10+**: Type hints and modern syntax

## File Locations

- **Module**: `/home/anthony/projects/fakeai/fakeai/image_generator.py`
- **Tests**: `/home/anthony/projects/fakeai/tests/test_image_generator.py`
- **Config**: `fakeai/config.py` (FAKEAI_GENERATE_ACTUAL_IMAGES, etc.)
- **Integration**: `fakeai/fakeai_service.py` (ImageGenerator initialization)
- **Endpoint**: `fakeai/app.py` (GET /images/{image_id}.png)

## Performance

- **Generation Time**: ~0.1-0.5s per image (depending on size and quality)
- **Memory Usage**: ~10-50KB per 1024×1024 image (PNG compression)
- **Concurrent Safe**: Thread-safe storage with locks
- **Cleanup**: Background thread runs every 5 minutes

## Troubleshooting

### Images Not Generating

```bash
# Check if enabled
echo $FAKEAI_GENERATE_ACTUAL_IMAGES

# Enable if needed
export FAKEAI_GENERATE_ACTUAL_IMAGES=true

# Restart server
python -m fakeai server
```

### Image Not Found (404)

- Images expire after retention period (default: 1 hour)
- Check retention settings: `FAKEAI_IMAGE_RETENTION_HOURS`
- Images are not persisted across server restarts

### Font Issues

If fonts are not available, the module falls back to PIL's default font. Install system fonts for better results:

```bash
# Ubuntu/Debian
sudo apt-get install fonts-dejavu-core

# Fedora/RHEL
sudo dnf install dejavu-sans-fonts

# macOS
# DejaVu fonts included by default
```

## Related Documentation

- [CLAUDE.md](../../development/CLAUDE.md) - Main project documentation
- [README.md](/home/anthony/projects/fakeai/README.md) - Project README
- [tests/test_image_generator.py](/home/anthony/projects/fakeai/tests/test_image_generator.py) - Test suite
