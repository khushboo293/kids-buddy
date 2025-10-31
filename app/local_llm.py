import json, requests, base64

import os
OLLAMA_GENERATE_URL = os.getenv("KIDS_BUDDY_OLLAMA", "http://127.0.0.1:11434") + "/api/generate"


def generate_text(system_prompt: str, user_prompt: str, model: str = "llama3.2:3b-instruct") -> str:
    try:
        payload = {"model": model, "system": system_prompt, "prompt": user_prompt, "stream": False}
        r = requests.post(OLLAMA_GENERATE_URL, json=payload, timeout=120); r.raise_for_status()
        text = (r.json().get("response") or "").strip()
        lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
        if len(lines) > 2: lines = lines[:2]
        return "\n".join(lines) if lines else text
    except Exception as e:
        return f"⚠️ Local model error: {e}"

def _b64png(b: bytes) -> str:
    return base64.b64encode(b).decode("utf-8")

def vision_extract(image_bytes: bytes, model: str = "llava:7b"):
    try:
        prompt = ("List visible objects, colors, and the scene as strict JSON with keys: "
                  "objects (list), colors (list), scene (string). Keep lists short. Do not invent unseen things.")
        payload = {"model": model, "prompt": prompt, "images": [_b64png(image_bytes)], "stream": False}
        r = requests.post(OLLAMA_GENERATE_URL, json=payload, timeout=180); r.raise_for_status()
        content = (r.json().get("response") or "").strip()
        try:
            data = json.loads(content)
        except Exception:
            s, e = content.find("{"), content.rfind("}")
            data = json.loads(content[s:e+1]) if s != -1 and e != -1 else {}
        objs = data.get("objects") if isinstance(data.get("objects"), list) else None
        cols = data.get("colors") if isinstance(data.get("colors"), list) else None
        scene = data.get("scene") if isinstance(data.get("scene"), str) else None
        return objs, cols, scene
    except Exception:
        return None, None, None
