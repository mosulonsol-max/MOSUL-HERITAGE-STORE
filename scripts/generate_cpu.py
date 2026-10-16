#!/usr/bin/env python3
"""Generate one bounded 512px artwork on a CPU-only GitHub runner."""
import argparse
import hashlib
import json
import os
import sys
import urllib.parse
import urllib.request
import io
from pathlib import Path

from PIL import Image, ImageOps

MODEL_ID = "segmind/small-sd"
MODEL_REVISION = "728f8b598d7d305bd30c20cbdfbaa6ffa7eec9cc"
MODEL_LICENSE = "CreativeML Open RAIL-M"
MAX_REFERENCE_BYTES = 12_000_000
REFERENCE_HOSTS = {"tile.loc.gov", "cdn.loc.gov"}


def download_reference(url: str) -> tuple[Image.Image, str]:
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme != "https" or parsed.hostname not in REFERENCE_HOSTS:
        raise ValueError("reference must be an HTTPS Library of Congress image")
    request = urllib.request.Request(url, headers={
        "User-Agent": "MosulHeritageStudio/1.0 (archival reference generation)"
    })
    with urllib.request.urlopen(request, timeout=45) as response:
        final = urllib.parse.urlparse(response.geturl())
        if response.status != 200 or final.scheme != "https" or final.hostname not in REFERENCE_HOSTS:
            raise ValueError("archival reference download was redirected outside the allow-list")
        raw = response.read(MAX_REFERENCE_BYTES + 1)
    if len(raw) > MAX_REFERENCE_BYTES:
        raise ValueError("archival reference exceeds the 12 MB limit")
    try:
        with Image.open(io.BytesIO(raw)) as opened:
            reference = ImageOps.fit(opened.convert("RGB"), (512, 512),
                                     method=Image.Resampling.LANCZOS,
                                     centering=(0.5, 0.5))
    except OSError:
        raise ValueError("archival reference is not a supported image") from None
    return reference, hashlib.sha256(raw).hexdigest()


def prompt_seed(prompt: str) -> int:
    configured = os.environ.get("ARTWORK_SEED", "").strip()
    if configured:
        value = int(configured)
        if value < 0 or value > 2**32 - 1:
            raise ValueError("ARTWORK_SEED must be between 0 and 2^32-1")
        return value
    return int.from_bytes(hashlib.sha256(prompt.encode("utf-8")).digest()[:4], "big")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--prompt", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--reference-url")
    args = parser.parse_args()

    import torch
    from diffusers import DiffusionPipeline, StableDiffusionImg2ImgPipeline

    torch.set_num_threads(max(1, min(4, os.cpu_count() or 1)))
    seed = prompt_seed(args.prompt)
    pipeline_class = StableDiffusionImg2ImgPipeline if args.reference_url else DiffusionPipeline
    pipeline = pipeline_class.from_pretrained(
        MODEL_ID,
        revision=MODEL_REVISION,
        torch_dtype=torch.float32,
        use_safetensors=True,
        low_cpu_mem_usage=True,
    )
    pipeline = pipeline.to("cpu")
    pipeline.enable_attention_slicing()
    negative = (
        "people, person, face, child, nudity, violence, weapon, hate symbol, "
        "religious text, political symbol, words, letters, signature, watermark, logo"
    )
    generator = torch.Generator(device="cpu").manual_seed(seed)
    reference_sha256 = None
    reference = None
    if args.reference_url:
        reference, reference_sha256 = download_reference(args.reference_url)
    parameters = {
        "prompt": args.prompt, "negative_prompt": negative,
        "num_inference_steps": 24, "guidance_scale": 7.0,
        "generator": generator,
    }
    if reference is None:
        parameters.update({"width": 512, "height": 512})
    else:
        parameters.update({"image": reference, "strength": 0.58})
    with torch.inference_mode():
        result = pipeline(**parameters).images[0]

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    result.convert("RGB").save(output, format="PNG", optimize=True)
    metadata = {
        "model": MODEL_ID,
        "model_revision": MODEL_REVISION,
        "model_license": MODEL_LICENSE,
        "compute": "github-hosted-cpu",
        "seed": seed,
    }
    if args.reference_url:
        metadata.update({
            "reference_url": args.reference_url,
            "reference_sha256": reference_sha256,
            "reference_mode": "image-to-image",
            "reference_strength": 0.58,
        })
    print(json.dumps(metadata, sort_keys=True))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print("CPU generation stopped safely: " + str(exc), file=sys.stderr)
        raise SystemExit(1)

