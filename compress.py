import os
import io
import base64
import pathlib
import numpy as np
from PIL import Image, ImageOps
from skimage.metrics import structural_similarity as ssim
from pillow_heif import register_heif_opener

register_heif_opener()

SUPPORTED_FORMATS = (".heic", ".jpg", ".jpeg", ".png", ".webp")


def compute_ssim(img1, img2):
    small1 = img1.resize((400, 400), Image.Resampling.LANCZOS)
    small2 = img2.resize((400, 400), Image.Resampling.LANCZOS)
    a = np.array(small1)
    b = np.array(small2)
    score, _ = ssim(a, b, channel_axis=2, full=True)
    return score


def get_dominant_color(img):
    tiny = img.resize((1, 1), Image.Resampling.LANCZOS)
    r, g, b = tiny.getpixel((0, 0))
    return f"#{r:02x}{g:02x}{b:02x}"


def get_blur_placeholder(img):
    # 8x8 encodes to ~300 bytes — tiny enough to inline in JSON/metafield
    tiny = img.resize((8, 8), Image.Resampling.LANCZOS)
    buffer = io.BytesIO()
    tiny.save(buffer, format="JPEG", quality=50)
    b64 = base64.b64encode(buffer.getvalue()).decode()
    return f"data:image/jpeg;base64,{b64}"


def compress_perceptual(img, path, target_ssim=0.93):
    icc = img.info.get("icc_profile")
    low, high = 10, 90
    best_quality = 10
    original = img.copy()

    for _ in range(10):
        mid = (low + high) // 2
        params = {
            "optimize": True,
            "quality": mid,
            "progressive": True,
        }
        if icc:
            params["icc_profile"] = icc

        img.save(path, "JPEG", **params)
        compressed = Image.open(path).convert("RGB")
        score = compute_ssim(original, compressed)

        if score >= target_ssim:
            best_quality = mid
            low = mid + 1
        else:
            high = mid - 1

    # Final save at best quality found
    params = {
        "optimize": True,
        "quality": best_quality,
        "progressive": True,
    }
    if icc:
        params["icc_profile"] = icc

    img.save(path, "JPEG", **params)
    return os.path.getsize(path) / 1024, best_quality


def process_image(path, jpg_folder, size=1200):
    filename = os.path.basename(path)
    name = os.path.splitext(filename)[0]

    img = Image.open(path)
    img = ImageOps.exif_transpose(img)
    img = img.convert("RGB")
    original_kb = os.path.getsize(path) / 1024

    img.thumbnail((size, size), Image.Resampling.LANCZOS)
    final_w, final_h = img.size

    # ── Generate placeholders from resized image ──────────────────────────
    # dominant_color  = get_dominant_color(img)
    # blur_placeholder = get_blur_placeholder(img)

    # ── Compress ──────────────────────────────────────────────────────────
    jpg_path = os.path.join(jpg_folder, f"{name}.jpg")
    jpg_kb, jpg_q = compress_perceptual(img, jpg_path, target_ssim=0.93)

    # ── Write sidecar JSON ────────────────────────────────────────────────
    # Upload blurDataURL and dominantColor to Shopify metafields
    # meta = {
    #     "file":           f"{name}.jpg",
    #     "dominantColor":  dominant_color,
    #     "blurDataURL":    blur_placeholder,
    #     "width":          final_w,
    #     "height":         final_h,
    #     "size_kb":        round(jpg_kb, 1),
    #     "quality":        jpg_q,
    # }
    meta_path = os.path.join(jpg_folder )
 

    reduction = ((original_kb - jpg_kb) / original_kb) * 100
    size_flag = " ⚠ large — complex image" if jpg_kb > 250 else ""
    print(
        f"✓ {filename:<40} "
        f"{original_kb:>7.0f} KB → {jpg_kb:>6.1f} KB (q{jpg_q})  "
        f"({final_w}×{final_h}px)  {reduction:.0f}% smaller  "
        # f"colour: {dominant_color}"
        f"{size_flag}"
    )
    return original_kb, jpg_kb


def batch(folder, size=1200):
    jpg_folder = os.path.join(folder, "swimshorts")
    os.makedirs(jpg_folder, exist_ok=True)

    image_files = [f for f in os.listdir(folder) if f.lower().endswith(SUPPORTED_FORMATS)]

    print(f"  Scanning : {os.path.abspath(folder)}")
    print(f"  Found    : {len(image_files)} images")
  
    print(f"  Output   : {os.path.abspath(jpg_folder)}\n")

    if not image_files:
        print("  ⚠ No images found. Check the folder path.")
        return

    total_orig, total_jpg, count, failed = 0, 0, 0, 0

    for file in sorted(image_files):
        path = os.path.join(folder, file)
        try:
            orig, jpg_kb = process_image(path, jpg_folder, size)
            total_orig += orig
            total_jpg  += jpg_kb
            count += 1
        except Exception as e:
            print(f"✗ Failed: {file} → {e}")
            failed += 1

    print("\n──────────── SUMMARY ────────────")
    print(f"  Processed : {count} images")
    print(f"  Failed    : {failed}")
    if count:
        print(f"  Original  : {total_orig / 1024:.2f} MB")
        print(f"  JPEG      : {total_jpg  / 1024:.2f} MB  ({(1 - total_jpg / total_orig) * 100:.0f}% smaller)")
        # print(f"\n  Each image has a matching .json with dominantColor + blurDataURL")
        # print(f"  Upload these values to Shopify product metafields.")


script_dir = str(pathlib.Path(__file__).parent)
batch(script_dir, size=1200)
