import base64, json, requests

OLLAMA_CHAT_URL = "http://localhost:11434/api/chat"

def _b64png(image_bytes: bytes):
    import base64 as _b
    return "data:image/png;base64," + _b.b64encode(image_bytes).decode("utf-8")

def generate_text(system_prompt: str, user_prompt: str, model: str = "llama3.2:3b-instruct") -> str:
    try:
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "stream": False
        }
        resp = requests.post(OLLAMA_CHAT_URL, json=payload, timeout=120)
        resp.raise_for_status()
        data = resp.json()
        content = data.get("message", {}).get("content", "").strip()
        lines = [ln.strip() for ln in content.splitlines() if ln.strip()]
        if len(lines) > 2:
            lines = lines[:2]
        return "\n".join(lines) if lines else content
    except Exception as e:
        return f"⚠️ Local model error: {e}"

def vision_extract(image_bytes: bytes, model: str = "llava:7b"):
    try:
        img_b64 = _b64png(image_bytes)
        prompt = "List visible objects, colors, and the scene as strict JSON with keys: objects (list), colors (list), scene (string). Keep lists short. Do not invent unseen things."
        payload = {
            "model": model,
            "messages": [
                {"role": "user", "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": img_b64}}
                ]}
            ],
            "stream": False
        }
        resp = requests.post(OLLAMA_CHAT_URL, json=payload, timeout=180)
        resp.raise_for_status()
        content = resp.json().get("message", {}).get("content", "{}")
        try:
            data = json.loads(content)
        except Exception:
            start = content.find("{")
            end = content.rfind("}")
            data = json.loads(content[start:end+1]) if start != -1 and end != -1 else {}
        objects = data.get("objects") if isinstance(data.get("objects"), list) else None
        colors = data.get("colors") if isinstance(data.get("colors"), list) else None
        scene = data.get("scene") if isinstance(data.get("scene"), str) else None
        return objects, colors, scene
    except Exception:
        return None, None, None
