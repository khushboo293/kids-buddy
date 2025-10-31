# Kids Buddy — Parent Guide 💛

A gentle, offline **AI talking friend** that helps your child grow — through play, drawing, and simple conversations.

- 100% **local**: no API keys, no cloud calls while running  
- **Ollama** for language + vision models (on your device)  
- **Whisper (faster-whisper)** for speech-to-text (offline)  
- **Live mic** recording via `streamlit-webrtc`  
- **Theme packs** included: Cars, Animals, School  
- **Progress charts** + local JSON session logs  


## 🛠️ Local setup (one-time)

### 1) Install prerequisites
- **Python 3.10 or 3.11**
- **Ollama** app (open it once)

### 2) Pull local models (first run only)
```bash
ollama pull llama3.2:3b-instruct
ollama pull llava:7b
```
> On slower machines, try `llama3.2:1b` and `moondream` for vision.

### 3) Create virtual environment & install
```bash
python -m venv venv
# mac/linux:
source venv/bin/activate
# windows:
# venv\Scripts\activate

pip install -r requirements.txt
```

### 4) Run
```bash
streamlit run app/app_offline.py
```
Allow the browser to use your **microphone** when prompted.

---

## 🎛️ App overview
- **Talk** tab — type, upload audio, or use **live mic** → Buddy replies with praise + a modeled sentence + one question.  
- **Draw & Tell** — upload a drawing/toy photo → local vision extracts objects/colors/scene → Buddy builds a tiny story prompt.  
- **Progress** — charts for stars/session and average child utterance length.  
- **Themes** — pick Cars / Animals / School for ready-made sentence models, stickers, and scenarios.

All logs save locally in `/sessions/` (ignored by git).

---

## 🎨 Themes
Drop JSON files into `/themes/`. The app auto-discovers any `*.json`.
Included:
- `cars.json`
- `animals.json`
- `school.json`

Each theme supports:
```json
{
  "name": "Cars",
  "stickers": ["🚗","🏎️","🚓"],
  "sentence_models": ["The red car is fast."],
  "two_choice_questions": ["Park or home?"],
  "scenarios": [{"name":"Car Wash","prompt":"We are at the car wash. What will we do?"}]
}
```

---

## 🔒 Safety
- Home practice buddy; **no medical advice/diagnosis**.  
- Short, concrete language; literal to what’s said/seen.  
- Parent supervision recommended.

---

## 🤝 Contributing
- Share ideas via issues/PRs.  
- Keep language child-safe and positive.  
- Don’t include model weights in the repo (Ollama pulls them).

---

## 📜 License
MIT — see `LICENSE`.
