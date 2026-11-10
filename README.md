# Suraksha Voice: a multilingual scam first-responder

Built for **The Great Indian AI Internship Challenge by Gnani.ai**.

After a UPI / OTP / fake-police scam, the victim speaks in **Telugu, Hindi or English** (or a mix). The agent replies **by voice, in the same language**, with calm, ordered next steps (block card/UPI, call **1930**, file at cybercrime.gov.in), shows a checklist, and drafts a complaint.

See [PITCH.md](PITCH.md) for the one-page solution pitch.

## How it works

`mic -> Gnani Prisma (STT) -> reasoning step -> Gnani Timbre (TTS)`

| Step | What is used |
|---|---|
| Speech to text | **Gnani Prisma** (`/stt/v3`, prisma-v3.0) |
| Reasoning (scam type, urgency, short spoken reply) | **Google Gemini Flash-Lite** through an OpenAI-compatible endpoint. If it is slow or fails, a **built-in rule-based fallback** answers, so the agent never goes silent. Any OpenAI-compatible model can be plugged in (for example Gnani Evon once an endpoint is available). |
| Text to speech | **Gnani Timbre** (`/api/v1/tts/inference`, timbre-v2.5) |

Other features: replies in the language the person actually spoke, remembers the conversation, asks to repeat when audio is unclear, never asks for OTP/PIN/CVV, downloadable complaint draft, per-stage latency shown on screen.

## Run it

1. Get a Gnani API key at https://app.gnani.ai/voice (API Keys -> Add API Key).
2. Optional, for the Gemini brain: get a Google AI Studio key at https://aistudio.google.com.
3. Install and start:
   ```
   pip install -r requirements.txt
   python -m streamlit run app.py
   ```
4. Paste the key(s) in the sidebar. For the brain use Base URL `https://generativelanguage.googleapis.com/v1beta/openai` and Model `gemini-flash-lite-latest`. Leave the Brain boxes empty to use the built-in rules only.

You can also set keys as environment variables instead of typing them: `GNANI_API_KEY`, `LLM_BASE_URL`, `LLM_API_KEY`, `LLM_MODEL`.

**Never commit API keys.** No keys are stored in this repository.

`test_llm.py` is a small script that checks which Gemini model answers fastest on your connection:
`python test_llm.py YOUR_GOOGLE_KEY`

## Honest limits

- About 30 seconds of audio per message and about 8 seconds end-to-end latency today.
- Advice is general guidance, not legal advice.
- The rule-based fallback covers six common scam types; the LLM handles everything else.
- Next steps: streaming TTS for faster replies, phone-call integration, more languages.

## Team and contributions

**Jahnavi Neelam** (jahnavineelam2006@gmail.com): voice pipeline and integration with Gnani Prisma (STT) and Timbre (TTS), Streamlit app, language handling for Telugu, Hindi and English, GitHub repository and deployment steps.

**Bandela Chandana** (chandanabandela23@gmail.com): scam classification logic and knowledge base (six scam types, response steps, 1930 and cybercrime.gov.in guidance), prompt design and fallback logic, testing across languages and unclear-audio cases, demo video and project write-up.
