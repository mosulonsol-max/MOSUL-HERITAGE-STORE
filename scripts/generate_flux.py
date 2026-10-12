#!/usr/bin/env python3
"""Run FLUX.1-schnell locally, optionally using a licensed Commons reference.

No paid image API is called. Model weights are downloaded from the official
Hugging Face model repository on first run and cached by Hugging Face Hub.
"""
import argparse
import html
import json
import os
import re
import sys
import tempfile
import urllib.parse
import urllib.request
from pathlib import Path

MODEL_ID = "black-forest-labs/FLUX.1-schnell"
COMMONS_API = "https://commons.wikimedia.org/w/api.php"
ALLOWED_LICENSES = {
    "cc0-1.0", "cc by 4.0", "cc by 3.0", "public domain",
    "public domain mark", "cc pd mark",
}
MAX_REFERENCE_BYTES = 12_000_000


def commons_reference(query):
    """Return one Commons reference only when metadata says reuse/adaptation is allowed."""
    if not query:
        return None
    params = {
        "action": "query", "generator": "search", "gsrsearch": query,
        "gsrnamespace": "6", "gsrlimit": "12", "prop": "imageinfo",
        "iiprop": "url|extmetadata", "iiurlwidth": "1024", "format": "json",
    }
    request = urllib.request.Request(
        COMMONS_API + "?" + urllib.parse.urlencode(params),
        headers={"User-Agent": "MosulHeritageStudio/1.0 (open-license reference lookup)"},
    )
    with urllib.request.urlopen(request, timeout=25) as response:
        data = json.loads(response.read(2_000_000))
    pages = data.get("query", {}).get("pages", {})
    for page in pages.values():
        infos = page.get("imageinfo") or []
        if not infos:
            continue
        info = infos[0]
        metadata = info.get("extmetadata") or {}
        raw_license = metadata.get("LicenseShortName", {}).get("value", "")
        short_name = html.unescape(re.sub(r"<[^>]*>", " ", str(raw_license))).strip()
        license_key = " ".join(short_name.lower().replace("-", " ").split())
        if license_key not in ALLOWED_LICENSES:
            continue
        thumb = info.get("thumburl") or info.get("url")
        if not isinstance(thumb, str) or urllib.parse.urlparse(thumb).hostname != "upload.wikimedia.org" or urllib.parse.urlparse(thumb).scheme != "https":
            continue
        def metadata_text(key, fallback):
            value = metadata.get(key, {}).get("value", fallback)
            return html.unescape(re.sub(r"<[^>]*>", " ", str(value))).strip()[:1200]
        return {
            "title": page.get("title", ""),
            "page_url": "https://commons.wikimedia.org/wiki/" + urllib.parse.quote(page.get("title", "").replace(" ", "_")),
            "image_url": thumb,
            "license": short_name,
            "license_url": metadata.get("LicenseUrl", {}).get("value", ""),
            "creator": metadata_text("Artist", "Unknown / not supplied"),
            "attribution": metadata_text("Attribution", ""),
        }
    return None


def download_reference(source, destination):
    parsed = urllib.parse.urlparse(source["image_url"])
    if parsed.scheme != "https" or parsed.hostname != "upload.wikimedia.org":
        raise RuntimeError("Reference host is not an approved Wikimedia upload domain")
    request = urllib.request.Request(source["image_url"], headers={"User-Agent": "MosulHeritageStudio/1.0"})
    with urllib.request.urlopen(request, timeout=30) as response:
        final = urllib.parse.urlparse(response.geturl())
        if response.status != 200 or final.scheme != "https" or final.hostname != "upload.wikimedia.org":
            raise RuntimeError("Reference image download failed")
        raw = response.read(MAX_REFERENCE_BYTES + 1)
    if len(raw) > MAX_REFERENCE_BYTES:
        raise RuntimeError("Reference image exceeded the configured size limit")
    destination.write_bytes(raw)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--prompt", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--reference-query", default=os.environ.get("ARTWORK_REFERENCE_QUERY", ""))
    args = parser.parse_args()

    import torch
    from diffusers import FluxImg2ImgPipeline
    from diffusers.utils import load_image

    if not torch.cuda.is_available():
        raise RuntimeError("FLUX local generation requires an available CUDA GPU runner")
    dtype = torch.bfloat16 if torch.cuda.is_bf16_supported() else torch.float16
    pipe = FluxImg2ImgPipeline.from_pretrained(MODEL_ID, torch_dtype=dtype)
    pipe.enable_model_cpu_offload()
    source = commons_reference(args.reference_query)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    generation_prompt = args.prompt
    with tempfile.TemporaryDirectory(prefix="mosul-reference-") as scratch:
        if source:
            reference_path = Path(scratch) / "reference"
            download_reference(source, reference_path)
            image = load_image(str(reference_path)).convert("RGB").resize((1024, 1024))
            result = pipe(
                prompt=generation_prompt,
                image=image,
                num_inference_steps=4,
                strength=0.82,
                guidance_scale=0.0,
                max_sequence_length=256,
            ).images[0]
        else:
            result = pipe(
                prompt=generation_prompt,
                num_inference_steps=4,
                guidance_scale=0.0,
                max_sequence_length=256,
                height=1024,
                width=1024,
            ).images[0]
        result.save(output, format="PNG")
    print(json.dumps({"model": MODEL_ID, "reference": source}, ensure_ascii=False))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print("Local FLUX generation stopped safely: " + str(exc), file=sys.stderr)
        raise SystemExit(1)
