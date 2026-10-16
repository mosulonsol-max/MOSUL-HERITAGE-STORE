#!/usr/bin/env python3
"""Generate one watermarked public preview; never enable checkout or minting."""
import argparse
import base64
import datetime as dt
import hashlib
import math
import io
import json
import os
import statistics
import sys
import subprocess
import tempfile
import urllib.error
import urllib.parse
import urllib.request
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "ai-engine"))
from mosul_ai.provenance import sign_record

from PIL import Image, ImageDraw, ImageFont

MAX_ITEMS = 120
MIN_SALES = 5
MAX_AGE_DAYS = 90
DIRECTIONS = [
    ("Courtyard Light Study", "A quiet courtyard inspired by Mosul, geometric brickwork, warm limestone, late afternoon light, contemporary editorial composition."),
    ("River Memory Study", "An abstract view of the Tigris as a ribbon of blue and gold through layered Mosul-inspired forms, contemporary fine-art print."),
    ("Brick and Shadow Study", "A sculptural arrangement of sunlit brick arches and long shadows, inspired by northern Iraqi craft, modern museum-quality art."),
    ("Garden After Rain", "A peaceful garden courtyard after rain, stone, water reflections and native greenery, Mosul-inspired contemporary art."),
]

def utc_now():
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0)

def request_json(url, method="GET", payload=None, api_key=None):
    if urllib.parse.urlparse(url).scheme != "https":
        raise ValueError("Configured API endpoints must use HTTPS")
    body = json.dumps(payload).encode() if payload is not None else None
    headers = {"Accept": "application/json"}
    if body is not None:
        headers["Content-Type"] = "application/json"
    if api_key:
        headers["Authorization"] = "Bearer " + api_key
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=90) as response:
            if response.status < 200 or response.status >= 300:
                raise ValueError("Provider returned an unsuccessful status")
            return json.loads(response.read(32_000_000))
    except urllib.error.HTTPError as exc:
        raise ValueError("Provider request failed with HTTP " + str(exc.code)) from None
    except urllib.error.URLError:
        raise ValueError("Provider endpoint could not be reached") from None

def prompt_for(now):
    index = now.hour % len(DIRECTIONS)
    title, direction = DIRECTIONS[index]
    prompt = (
        "Create one original, high-quality digital artwork for a cultural collectibles preview. "
        + direction + " The scene is interpretive contemporary art, not a documentary photograph, "
        "verified reconstruction, or claim about an exact historical site. No words, letters, logos, "
        "watermarks, signatures, or invented historical details. Square image, refined color and texture."
    )
    return title, prompt

GENERATION_DETAILS = {}

def get_png(prompt, output_file):
    backend = os.environ.get("ARTWORK_BACKEND", "cpu-free").strip().casefold()
    if backend in {"flux-local", "cpu-free"}:
        generator_name = "generate_flux.py" if backend == "flux-local" else "generate_cpu.py"
        generator = Path(__file__).with_name(generator_name)
        command = [sys.executable, str(generator), "--prompt", prompt, "--output", str(output_file)]
        reference_query = os.environ.get("ARTWORK_REFERENCE_QUERY", "").strip()
        if backend == "flux-local" and reference_query:
            command.extend(["--reference-query", reference_query])
        completed = subprocess.run(command, check=True, capture_output=True, text=True, timeout=3600)
        for line in reversed(completed.stdout.splitlines()):
            try:
                details = json.loads(line)
                if isinstance(details, dict) and details.get("model"):
                    GENERATION_DETAILS.update(details)
                    break
            except json.JSONDecodeError:
                continue
        raw = Path(output_file).read_bytes()
        if len(raw) > 20_000_000 or raw[:8].hex() != "89504e470d0a1a0a":
            raise ValueError("Local generator must produce a PNG under 20 MB")
        with Image.open(io.BytesIO(raw)) as image:
            width, height = image.size
        if width < 512 or height < 512 or width > 8192 or height > 8192:
            raise ValueError("Local generator produced dimensions outside the accepted range")
        return raw
    if backend != "openai-compatible":
        raise ValueError("ARTWORK_BACKEND must be cpu-free, flux-local, or openai-compatible")
    endpoint = os.environ.get("ARTWORK_API_URL", "").strip()
    key = os.environ.get("ARTWORK_API_KEY", "").strip()
    model = os.environ.get("ARTWORK_MODEL", "").strip()
    if not endpoint or not key:
        return None
    payload = {"prompt": prompt, "size": "1024x1024", "n": 1, "response_format": "b64_json"}
    if model:
        payload["model"] = model
    result = request_json(endpoint, "POST", payload, key)
    data = result.get("data") if isinstance(result, dict) else None
    encoded = data[0].get("b64_json") if isinstance(data, list) and data and isinstance(data[0], dict) else None
    if not encoded:
        raise ValueError("Image API did not return a base64 image")
    raw = base64.b64decode(encoded, validate=True)
    if len(raw) > 20_000_000 or raw[:8].hex() != "89504e470d0a1a0a":
        raise ValueError("Image must be a PNG under 20 MB")
    width, height = int.from_bytes(raw[16:20], "big"), int.from_bytes(raw[20:24], "big")
    if width < 512 or height < 512 or width > 8192 or height > 8192:
        raise ValueError("Image dimensions are outside the accepted range")
    return raw


def validate_visual_quality(raw):
    """Reject corrupt, blank, or nearly uniform outputs before publication."""
    with Image.open(io.BytesIO(raw)) as source:
        image = source.convert("RGB")
    sample = image.resize((128, 128))
    pixels = list(sample.get_flattened_data() if hasattr(sample, "get_flattened_data") else sample.getdata())
    means = [sum(pixel[channel] for pixel in pixels) / len(pixels) for channel in range(3)]
    variances = [
        sum((pixel[channel] - means[channel]) ** 2 for pixel in pixels) / len(pixels)
        for channel in range(3)
    ]
    contrast = sum(value ** 0.5 for value in variances) / 3
    colors = len(set(pixels))
    if contrast < 8 or colors < 256:
        raise ValueError("Generated image failed the automatic visual-quality gate")
    return {"status": "passed", "contrast": round(contrast, 2), "sampled_colors": colors}

def watermark_preview(raw):
    with Image.open(io.BytesIO(raw)) as source:
        image = source.convert("RGBA")
    band_height = max(54, image.width // 13)
    band = Image.new("RGBA", (image.width, band_height), (20, 33, 29, 210))
    draw = ImageDraw.Draw(band)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", max(18, image.width // 44))
    except OSError:
        font = ImageFont.load_default()
    label = "MOSUL HERITAGE  |  PREVIEW  |  NOT FOR SALE"
    draw.text((image.width // 30, band_height // 3), label, font=font, fill=(255, 250, 239, 255))
    image.alpha_composite(band, (0, image.height - band_height))
    output = io.BytesIO()
    image.convert("RGB").save(output, format="PNG", optimize=True)
    return output.getvalue()

def estimate_price(category):
    endpoint = os.environ.get("MARKET_COMPS_API_URL", "").strip()
    key = os.environ.get("MARKET_COMPS_API_KEY", "").strip()
    if not endpoint:
        return {"status": "unavailable", "reason": "Comparable-sales source is not configured."}
    response = request_json(endpoint, api_key=key)
    rows = response.get("comparables", []) if isinstance(response, dict) else []
    cutoff = utc_now() - dt.timedelta(days=MAX_AGE_DAYS)
    sales = []
    sources = set()
    seen_sales = set()
    for row in rows:
        if not isinstance(row, dict):
            continue
        status = row.get("status")
        row_category = row.get("category")
        transaction_id = row.get("transaction_id")
        if not isinstance(status, str) or status.casefold() != "sold":
            continue
        if not isinstance(row_category, str) or row_category.strip().casefold() != category.casefold():
            continue
        if not isinstance(transaction_id, str) or not transaction_id.strip() or transaction_id in seen_sales:
            continue
        try:
            sold_at = dt.datetime.fromisoformat(str(row["sold_at"]).replace("Z", "+00:00"))
            amount = float(row["price_usd"])
        except (KeyError, TypeError, ValueError):
            continue
        if sold_at.tzinfo is None or sold_at < cutoff or sold_at > utc_now() or amount <= 0 or not math.isfinite(amount):
            continue
        seen_sales.add(transaction_id)
        sales.append(amount)
        source = row.get("source")
        if isinstance(source, str):
            parsed_source = urllib.parse.urlparse(source)
            if parsed_source.scheme == "https" and parsed_source.hostname:
                sources.add(parsed_source.hostname.lower())
    if len(sales) < MIN_SALES:
        return {"status": "unavailable", "reason": "Fewer than five valid, recent completed sales matched this category.", "sale_count": len(sales)}
    sales.sort()
    median = statistics.median(sales)
    return {
        "status": "benchmark_only",
        "currency": "USD",
        "median_completed_sale": round(median, 2),
        "observed_range": [round(sales[0], 2), round(sales[-1], 2)],
        "sale_count": len(sales),
        "window_days": MAX_AGE_DAYS,
        "sources": sorted(sources)[:5],
        "disclaimer": "Historical comparable-sales benchmark only; not an offer, appraisal, or sale price.",
    }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    out = Path(args.output_dir)
    output_file = os.environ.get("GITHUB_OUTPUT")
    backend = os.environ.get("ARTWORK_BACKEND", "cpu-free").strip().casefold()
    api_ready = bool(os.environ.get("ARTWORK_API_URL") and os.environ.get("ARTWORK_API_KEY"))
    if backend == "openai-compatible" and not api_ready:
        print("Image provider is not configured; no image was generated.")
        if output_file:
            Path(output_file).write_text("ready=false\n", encoding="utf-8")
        return 0
    now = utc_now()
    title, prompt = prompt_for(now)
    prompt += " Variation key " + now.strftime("%Y-%m-%dT%H") + " UTC; create a distinct composition."
    title += " — " + now.strftime("%Y-%m-%d %H:00 UTC")
    with tempfile.TemporaryDirectory(prefix="mosul-artwork-") as temp_dir:
        raw_path = Path(temp_dir) / "unwatermarked.png"
        raw = get_png(prompt, raw_path)
    if raw is None:
        print("Image provider is not configured; no image was generated.")
        if output_file:
            Path(output_file).write_text("ready=false\n", encoding="utf-8")
        return 0
    quality = validate_visual_quality(raw)
    image = watermark_preview(raw)
    category = "digital-art-one-of-one"
    identifier = "MH-" + now.strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:8]
    generated = out / "generated"
    generated.mkdir(parents=True, exist_ok=True)
    image_path = generated / (identifier + ".png")
    image_path.write_bytes(image)
    try:
        price = estimate_price(category)
    except Exception as exc:
        price = {"status": "unavailable", "reason": "Comparable-sales request failed; no benchmark is shown."}
        print("Comparable-sales source unavailable: " + type(exc).__name__)
    record = {
        "id": identifier,
        "title": title,
        "prompt": prompt,
        "model": GENERATION_DETAILS.get("model", os.environ.get("ARTWORK_MODEL", "provider-default")),
        "model_revision": GENERATION_DETAILS.get("model_revision"),
        "model_license": GENERATION_DETAILS.get("model_license"),
        "generation_compute": GENERATION_DETAILS.get("compute", backend),
        "generation_seed": GENERATION_DETAILS.get("seed"),
        "automated_quality_gate": quality,
        "category": category,
        "created_at": now.isoformat().replace("+00:00", "Z"),
        "image": "generated/" + image_path.name,
        "sha256": hashlib.sha256(image).hexdigest(),
        "classification": "AI-generated, heritage-inspired contemporary artwork; not historical evidence.",
        "status": "PUBLIC PREVIEW — NOT FOR SALE",
        "price_benchmark": price,
        "watermark_status": "Unverified preview; no signed authenticity claim.",
        "mint_status": "Not minted",
    }
    if GENERATION_DETAILS.get("reference"):
        record["reference_provenance"] = GENERATION_DETAILS["reference"]
    signing_key = os.environ.get("ARTWORK_SIGNING_KEY_B64", "").strip()
    if signing_key:
        try:
            record["provenance_signature"] = sign_record(record, signing_key)
            record["watermark_status"] = "Watermarked public preview with a signed provenance record."
        except ValueError:
            raise ValueError("ARTWORK_SIGNING_KEY_B64 is not a valid Ed25519 seed") from None
    else:
        record["provenance_signature_status"] = "not_configured"
    catalog_path = out / "catalog.json"
    try:
        catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
        items = catalog.get("items", [])
        if not isinstance(items, list):
            items = []
    except (FileNotFoundError, json.JSONDecodeError):
        items = []
    items = [record] + [item for item in items if item.get("id") != identifier]
    removed = items[MAX_ITEMS:]
    items = items[:MAX_ITEMS]
    catalog_path.write_text(json.dumps({"items": items}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for old in removed:
        old_image = old.get("image", "")
        if old_image.startswith("generated/"):
            try:
                (out / old_image).unlink(missing_ok=True)
            except OSError:
                pass
    if output_file:
        Path(output_file).write_text("ready=true\n", encoding="utf-8")
    print("Generated preview " + identifier + "; sale and mint remain disabled.")
    return 0

if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print("Artwork pipeline stopped safely: " + str(exc), file=sys.stderr)
        raise SystemExit(1)

