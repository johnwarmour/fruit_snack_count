import base64
import json
import os
import re

import anthropic
from PIL import Image

from storage import FLAVORS

MAX_DIMENSION = 1568  # Claude's recommended max for image analysis


def _resize_if_needed(image_path: str) -> bytes:
    with Image.open(image_path) as img:
        img = img.convert("RGB")
        w, h = img.size
        if max(w, h) > MAX_DIMENSION:
            scale = MAX_DIMENSION / max(w, h)
            img = img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)
        import io
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=90)
        return buf.getvalue()


def encode_image_base64(image_path: str) -> tuple[str, str]:
    """Returns (base64_data, media_type)."""
    data = _resize_if_needed(image_path)
    return base64.standard_b64encode(data).decode("utf-8"), "image/jpeg"


SYSTEM_PROMPT = """You are an expert at identifying Welch's fruit snack pieces by color and flavor.

This specific bag contains ONLY these five flavors — do not report any other flavors:
- concord_grape: deep purple/dark red, almost maroon or dark violet
- strawberry: bright red or pinkish-red
- white_grape_raspberry: dark pink or magenta/fuchsia (a blend flavor, appears pink-purple)
- orange: orange
- white_grape_peach: light peach, soft yellow-orange, pale yellowish, or cream

When analyzing an image, count every individual fruit snack piece visible. Be thorough and systematic — scan the whole image.

Return ONLY a valid JSON object with exactly these keys: concord_grape, strawberry, white_grape_raspberry, orange, white_grape_peach.
Each value must be a non-negative integer representing the count of that flavor.
Do not include any other text, explanation, or markdown — just the raw JSON object."""

USER_PROMPT = """Count each Welch's fruit snack piece in this image by flavor/color.
Return only a JSON object with keys: concord_grape, strawberry, white_grape_raspberry, orange, white_grape_peach."""


def analyze_image(image_path: str) -> tuple[dict, str]:
    """
    Returns (counts_dict, notes) where counts_dict maps flavor -> int
    and notes is any extra text returned by the model (usually empty).
    """
    client = anthropic.Anthropic()

    b64_data, media_type = encode_image_base64(image_path)

    message = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=256,
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": b64_data,
                        },
                    },
                    {"type": "text", "text": USER_PROMPT},
                ],
            }
        ],
    )

    raw = message.content[0].text.strip()

    # Extract JSON block even if the model wraps it in markdown fences
    json_match = re.search(r"\{[^}]+\}", raw, re.DOTALL)
    if json_match:
        raw = json_match.group(0)

    try:
        counts = json.loads(raw)
        # Sanitize: keep only known flavors, coerce to non-negative int
        counts = {f: max(0, int(counts.get(f, 0))) for f in FLAVORS}
        notes = ""
    except (json.JSONDecodeError, ValueError):
        counts = {f: 0 for f in FLAVORS}
        notes = f"Could not parse model response: {raw}"

    return counts, notes
