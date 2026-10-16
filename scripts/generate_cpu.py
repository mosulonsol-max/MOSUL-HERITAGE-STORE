#!/usr/bin/env python3
"""Generate one bounded 512px artwork on a CPU-only GitHub runner."""
import argparse
import hashlib
import json
import os
import sys
from pathlib import Path

MODEL_ID = "segmind/small-sd"
MODEL_REVISION = "728f8b598d7d305bd30c20cbdfbaa6ffa7eec9cc"
MODEL_LICENSE = "CreativeML Open RAIL-M"


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
    args = parser.parse_args()

    import torch
    from diffusers import DiffusionPipeline

    torch.set_num_threads(max(1, min(4, os.cpu_count() or 1)))
    seed = prompt_seed(args.prompt)
    pipeline = DiffusionPipeline.from_pretrained(
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
    with torch.inference_mode():
        result = pipeline(
            prompt=args.prompt,
            negative_prompt=negative,
            width=512,
            height=512,
            num_inference_steps=20,
            guidance_scale=7.0,
            generator=generator,
        ).images[0]

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    result.convert("RGB").save(output, format="PNG", optimize=True)
    print(json.dumps({
        "model": MODEL_ID,
        "model_revision": MODEL_REVISION,
        "model_license": MODEL_LICENSE,
        "compute": "github-hosted-cpu",
        "seed": seed,
    }, sort_keys=True))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print("CPU generation stopped safely: " + str(exc), file=sys.stderr)
        raise SystemExit(1)

