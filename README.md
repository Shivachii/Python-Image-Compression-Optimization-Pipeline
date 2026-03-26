# Image Compression & Optimization Pipeline

This script processes images in bulk, converts them to optimized JPEGs, and reduces file size while preserving visual quality using perceptual compression (SSIM).

It's ideal for e-commerce workflows (e.g. Shopify), especially when optimizing product images for performance and SEO.

## Features

- Supports multiple formats: `.heic`, `.jpg`, `.jpeg`, `.png`, `.webp`
- Auto-rotates images using EXIF data
- Resizes images to a maximum dimension (default: 1200px)
- Converts all images to optimized progressive JPEG
- Uses SSIM (Structural Similarity Index) to maintain visual quality
- Binary search to find the best compression quality
- Preserves ICC color profiles
- Batch processing with summary report

### Optional Features

- Dominant color extraction
- Blur placeholder generation (for lazy loading / LQIP)

## Installation

1. **Clone or copy the script**

   ```bash
   git clone <your-repo>
   cd <your-project>
   ```

2. **Install dependencies**

   ```bash
   pip install pillow numpy scikit-image pillow-heif
   ```

## Project Structure

```
/your-folder
│
├── script.py
├── image1.jpg
├── image2.png
├── image3.heic
│
└── results/          ← Output folder (auto-created)
    ├── image1.jpg
    ├── image2.jpg
    └── image3.jpg
```

## How It Works

### 1. Image Preprocessing

- Loads image
- Fixes orientation (EXIF transpose)
- Converts to RGB
- Resizes to fit within specified dimensions

### 2. Perceptual Compression

- Uses SSIM to compare original vs compressed image
- Binary search finds optimal JPEG quality
- Target SSIM default: 0.93

### 3. Output

- Saves compressed JPEG in output folder
- Logs:
  - Original size
  - Compressed size
  - Compression %
  - Image dimensions
  - Quality used

## 🧪 Usage

Run the script from the folder containing your images:

```bash
python script.py
```

### Optional: Change Image Size

```python
batch(script_dir, size=1200)
```

You can adjust size to:

- `800` → smaller, faster loading
- `1600` → higher quality

## Example Output

```
✓ image1.png  1200 KB → 180.5 KB (q82) (1200×900px) 85% smaller
✓ image2.heic 2400 KB → 210.3 KB (q78) (1200×1200px) 91% smaller

──────────── SUMMARY ────────────
Processed : 2 images
Failed : 0
Original : 3.52 MB
JPEG : 0.38 MB (89% smaller)
```

## Advanced Features

### 🔹 Dominant Color Extraction

Uncomment in `process_image()`:

```python
dominant_color = get_dominant_color(img)
```

**Useful for:**

- Placeholder backgrounds
- UI theming

### 🔹 Blur Placeholder (LQIP)

```python
blur_placeholder = get_blur_placeholder(img)
```

Returns a base64 image like:

```
data:image/jpeg;base64,...
```

**Perfect for:**

- Next.js `<Image placeholder="blur" />`
- Shopify metafields

### 🔹 JSON Metadata Output

You can enable metadata export:

```python
meta = {
    "file": f"{name}.jpg",
    "dominantColor": dominant_color,
    "blurDataURL": blur_placeholder,
    "width": final_w,
    "height": final_h,
    "size_kb": round(jpg_kb, 1),
    "quality": jpg_q,
}
```

## Notes

- Images above 250KB after compression are flagged as `⚠ large` — complex image
- HEIC support requires `pillow-heif`
- SSIM ensures visual quality over raw compression

## Use Cases

- Shopify product image optimization
- Website performance improvement (Core Web Vitals)
- Mobile-first image delivery
- Generating placeholders for lazy loading
- Bulk image processing pipelines

## Customization Ideas

- Convert to WebP/AVIF instead of JPEG
- Upload directly to Shopify via API
- Parallel processing for speed
- Integrate into CI/CD pipeline

## License

MIT License — free to use and modify.
