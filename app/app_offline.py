import os
import io
import json
import tempfile
import streamlit as st
from PIL import Image
from local_llm import generate_text, vision_extract
from prompts import SYSTEM_PROMPT, build_user_prompt
from stt import transcribe
import logs
import matplotlib.pyplot as plt
from webrtc_utils import record_audio_session

st.set_page_config(page_title="Kids Buddy — Offline", page_icon="🧒💬", layout="wide")

st.title("🧒💬 Kids Buddy — Offline (Ollama + Whisper)")
st.write("Runs **fully local** with Ollama (text/vision) and Whisper (`faster-whisper`) for speech-to-text. No API keys.")

with st.expander("Setup (one-time)"):
    st.markdown("""
1. Install **Ollama** and pull models:
```
ollama pull llama3.2:3b-instruct
ollama pull llava:7b
```
2. Whisper model downloads on first use. Choose size in the sidebar.
3. For live mic, grant your browser microphone access.
    """)

# Sidebar
st.sidebar.header("Local Models")
dialogue_model = st.sidebar.text_input("Dialogue model", value="llama3.2:3b-instruct")
vision_model = st.sidebar.text_input("Vision model", value="llava:7b")
whisper_size = st.sidebar.selectbox("Whisper STT model", ["tiny","base","small","medium","large-v3"], index=2)
session_len = st.sidebar.slider("Session stars target", 3, 10, 5)

# Auto-discover themes
st.sidebar.subheader("Theme Pack")
try:
    theme_files = [f for f in os.listdir(os.path.join(os.path.dirname(__file__), "..", "themes")) if f.endswith(".json")]
except Exception:
    theme_files = []
theme_names = ["None"] + [os.path.splitext(f)[0].capitalize() for f in theme_files]
theme_choice = st.sidebar.selectbox("Theme", theme_names, index=1 if "cars.json" in theme_files else 0)
theme = None
if theme_choice != "None":
    try:
        fname = theme_choice.lower() + ".json"
        theme = json.load(open(os.path.join(os.path.dirname(__file__), "..", "themes", fname), "r", encoding="utf-8"))
    except Exception:
        theme = None

st.sidebar.caption("Tip: smaller models (and Whisper tiny/base) run fine on CPU-only laptops.")

# Session state
if "session_id" not in st.session_state:
    st.session_state.session_id = None
if "stars" not in st.session_state:
    st.session_state.stars = 0
if "history" not in st.session_state:
    st.session_state.history = []
if "image_bytes" not in st.session_state:
    st.session_state.image_bytes = None
if "utter_lengths" not in st.session_state:
    st.session_state.utter_lengths = []

def add_star():
    st.session_state.stars += 1

def render_stars():
    return "⭐" * st.session_state.stars

tabs = st.tabs(["💬 Talk", "🎨 Draw & Tell", "📈 Progress"])

with tabs[0]:
    st.subheader("Conversation Buddy (Local)")
    if st.button("👋 Start / Reset Talk Session"):
        st.session_state.history = [("assistant", "Hi friend! I’m Lumo. Do you want to talk about cars, animals, or school? You can say: **Let’s talk about cars!**")]
        st.session_state.stars = 0
        st.session_state.utter_lengths = []
        st.session_state.session_id = logs.start_session()
        logs.append_turn(st.session_state.session_id, "assistant", st.session_state.history[0][1])

    # Theme helpers
    if theme:
        st.markdown("**Theme Stickers:** " + " ".join(theme.get("stickers", [])))
        with st.expander("Quick sentence models"):
            cols = st.columns(3)
            for i, s in enumerate(theme.get("sentence_models", [])):
                with cols[i % 3]:
                    if st.button(s, key=f"model_{i}"):
                        st.session_state.history.append(("user", s))
                        last_assistant = ""
                        for role, text_prev in reversed(st.session_state.history):
                            if role == "assistant":
                                last_assistant = text_prev
                                break
                        prompt = build_user_prompt("talk", s, last_assistant, None, None, None)
                        reply = generate_text(SYSTEM_PROMPT, prompt, model=dialogue_model)
                        st.session_state.history.append(("assistant", reply))
                        if st.session_state.session_id:
                            logs.append_turn(st.session_state.session_id, "user", s)
                            logs.append_turn(st.session_state.session_id, "assistant", reply)
                        if len(s.split()) >= 3:
                            st.session_state.utter_lengths.append(len(s.split()))
                            add_star()
        with st.expander("Scenario ideas"):
            cols = st.columns(2)
            for i, sc in enumerate(theme.get("scenarios", [])):
                with cols[i % 2]:
                    st.caption(f"• {sc['name']}: {sc['prompt']}")

    # Chat history
    for role, text in st.session_state.history:
        st.markdown(f"**{'Lumo' if role=='assistant' else 'You'}:** {text}")

    st.markdown("**Input options:** Type, upload audio, or **record live mic**.")
    c1, c2 = st.columns(2)
    with c1:
        user_text = st.text_input("Type child's speech:", key="talk_input_local")
        if st.button("Send Text"):
            last_assistant = ""
            for role, text_prev in reversed(st.session_state.history):
                if role == "assistant":
                    last_assistant = text_prev
                    break
            prompt = build_user_prompt("talk", user_text, last_assistant, None, None, None)
            reply = generate_text(SYSTEM_PROMPT, prompt, model=dialogue_model)
            st.session_state.history.append(("user", user_text))
            st.session_state.history.append(("assistant", reply))
            if st.session_state.session_id:
                logs.append_turn(st.session_state.session_id, "user", user_text)
                logs.append_turn(st.session_state.session_id, "assistant", reply)
            if len(user_text.split()) >= 3:
                add_star()
                st.session_state.utter_lengths.append(len(user_text.split()))

        audio_file = st.file_uploader("Upload audio (wav/mp3/m4a)", type=["wav","mp3","m4a"], key="audio_upload")
        if st.button("Transcribe & Send Uploaded"):
            if audio_file is not None:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
                    tmp.write(audio_file.read())
                    tmp_path = tmp.name
                text, conf = transcribe(tmp_path, model_size=whisper_size)
                os.unlink(tmp_path)
                if text:
                    st.success(f"Transcribed: {text}")
                    last_assistant = ""
                    for role, text_prev in reversed(st.session_state.history):
                        if role == "assistant":
                            last_assistant = text_prev
                            break
                    prompt = build_user_prompt("talk", text, last_assistant, None, None, None)
                    reply = generate_text(SYSTEM_PROMPT, prompt, model=dialogue_model)
                    st.session_state.history.append(("user", text))
                    st.session_state.history.append(("assistant", reply))
                    if st.session_state.session_id:
                        logs.append_turn(st.session_state.session_id, "user", text)
                        logs.append_turn(st.session_state.session_id, "assistant", reply)
                    if len(text.split()) >= 3:
                        add_star()
                        st.session_state.utter_lengths.append(len(text.split()))
                else:
                    st.warning("Could not transcribe audio.")

    with c2:
        st.markdown("**🎙️ Live Mic** — click start, speak, then stop. When it stops, save and transcribe.")
        from webrtc_utils import record_audio_session
        ctx, wav_path = record_audio_session(key="stt_webrtc")
        if wav_path and st.button("Transcribe Live Capture"):
            text, conf = transcribe(wav_path, model_size=whisper_size)
            if text:
                st.success(f"Transcribed: {text}")
                last_assistant = ""
                for role, text_prev in reversed(st.session_state.history):
                    if role == "assistant":
                        last_assistant = text_prev
                        break
                prompt = build_user_prompt("talk", text, last_assistant, None, None, None)
                reply = generate_text(SYSTEM_PROMPT, prompt, model=dialogue_model)
                st.session_state.history.append(("user", text))
                st.session_state.history.append(("assistant", reply))
                if st.session_state.session_id:
                    logs.append_turn(st.session_state.session_id, "user", text)
                    logs.append_turn(st.session_state.session_id, "assistant", reply)
                if len(text.split()) >= 3:
                    add_star()
                    st.session_state.utter_lengths.append(len(text.split()))
            else:
                st.warning("No speech detected.")

    st.markdown(f"**Stars this session:** {render_stars()} / target {session_len}")
    if st.session_state.session_id:
        logs.set_stars(st.session_state.session_id, st.session_state.stars)

with tabs[1]:
    st.subheader("Drawing & Story Buddy (Local Vision)")
    uploaded = st.file_uploader("Upload drawing/photo (PNG/JPG)", type=["png","jpg","jpeg"])
    if uploaded:
        image = Image.open(uploaded).convert("RGB")
        buf = io.BytesIO()
        image.save(buf, format="PNG")
        st.session_state.image_bytes = buf.getvalue()
        st.image(image, caption="Your drawing", use_column_width=True)

    col1, col2 = st.columns(2)
    with col1:
        child_text = st.text_input("Child says (optional):", key="draw_input_local")
    with col2:
        go = st.button("✨ Make Story (Local)")

    if go:
        if not st.session_state.image_bytes:
            st.warning("Please upload a drawing/photo.")
        else:
            objects, colors, scene = vision_extract(image_bytes=st.session_state.image_bytes, model=vision_model)
            prompt = build_user_prompt("draw", child_text, None, objects, colors, scene)
            reply = generate_text(SYSTEM_PROMPT, prompt, model=dialogue_model)
            st.markdown("**Lumo:** " + reply)
            if st.session_state.session_id:
                if child_text:
                    logs.append_turn(st.session_state.session_id, "user", child_text)
                logs.append_turn(st.session_state.session_id, "assistant", reply)
            if child_text and len(child_text.split()) >= 3:
                add_star()
                st.session_state.utter_lengths.append(len(child_text.split()))

    st.markdown(f"**Stars this session:** {render_stars()} / target {session_len}")
    if st.session_state.session_id:
        logs.set_stars(st.session_state.session_id, st.session_state.stars)

with tabs[2]:
    st.subheader("Progress")
    st.write("Charts from saved sessions (local JSON).")
    sessions = logs.list_sessions()
    if not sessions:
        st.info("No sessions yet. Start a Talk session first.")
    else:
        xs = [s["id"] for s in sessions]
        ys = [int(s.get("stars", 0)) for s in sessions]
        fig1 = plt.figure()
        plt.plot(xs, ys, marker="o")
        plt.title("Stars per session")
        plt.xlabel("Session")
        plt.ylabel("Stars")
        st.pyplot(fig1)

        avgs = []
        for s in sessions:
            lens = [t.get("len",0) for t in s.get("turns",[]) if t.get("role")=="user"]
            avgs.append(sum(lens)/len(lens) if lens else 0)
        fig2 = plt.figure()
        plt.plot(xs, avgs, marker="o")
        plt.title("Average child utterance length")
        plt.xlabel("Session")
        plt.ylabel("Words per utterance")
        st.pyplot(fig2)

with st.expander("Safety & Notes"):
    st.write("""
- 100% local inference: Ollama for LLM/VLM, `faster-whisper` for STT, and `streamlit-webrtc` for mic capture.
- Grant microphone permission to your browser for live mic.
- Review outputs; keep sessions short and joyful.
""")
