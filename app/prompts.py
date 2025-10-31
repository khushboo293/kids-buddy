SYSTEM_PROMPT = """
You are **Lumo**, a gentle speech practice buddy for a 4–7 year old child.
Goals:
- Expand 1–2 word utterances into 3–5 word sentences.
- Use praise + model a sentence + ask one simple question.
- Keep it literal to provided inputs (text/vision).

Rules:
- Max 2 short lines per reply.
- Offer choices if the child is silent.
- No medical or diagnostic advice.
"""

def build_user_prompt(mode, child_input=None, last_assistant=None, image_objects=None, image_colors=None, scene_guess=None):
    parts = []
    parts.append(f"Mode: {mode}")
    if last_assistant:
        parts.append(f"Last assistant line: {last_assistant}")
    if child_input:
        parts.append(f"Child said: {child_input}")
    if image_objects:
        parts.append(f"Image objects: {image_objects}")
    if image_colors:
        parts.append(f"Image colors: {image_colors}")
    if scene_guess:
        parts.append(f"Image scene guess: {scene_guess}")
    parts.append("""Respond with at most 2 short lines:
1) Praise + model a 3–5 word sentence (wrap model in ** **).
2) Ask exactly one simple question or give a two-choice prompt.
Keep it warm, playful, and literal to inputs.
""")
    return "\\n".join(str(p) for p in parts if p)
