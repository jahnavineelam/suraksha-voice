# Suraksha Voice: a multilingual scam first-responder

**Built for:** The Great Indian AI Internship Challenge by Gnani.ai

## The problem
UPI, OTP, fake-police and remote-app scams cost Indians thousands of crores every year. The first hour after a scam decides whether money can be frozen, yet victims panic, don't know the 1930 cyber-crime helpline, and many are not comfortable in English or typing long forms.

## The solution
Suraksha Voice lets a victim simply **speak** in Telugu, Hindi, English or a mix. It replies **by voice, in the same language**, with calm, ordered next steps: block the card/UPI, call 1930, file at cybercrime.gov.in. It also builds a checklist and a ready-to-edit complaint draft.

## Who will use it
Anyone who has just been scammed or is being targeted, especially Telugu and Hindi speakers, elderly users, and first-time digital-payment users. It can sit behind a helpline or inside a bank or UPI app.

## How it works (Gnani AI models)
1. **Gnani Prisma (STT, `/stt/v3`)**: transcribes the caller's Indian-language, code-mixed speech.
2. **Reasoning step:** classifies the scam type (OTP, UPI collect, remote-access, fake police/"digital arrest", KYC/SIM, lottery/job/loan) and urgency, and writes a short spoken reply. Uses Google Gemini Flash-Lite, with a built-in rule-based fallback if the LLM is slow or unavailable, so the agent never goes silent.
3. **Gnani Timbre (TTS, timbre-v2.5)**: speaks the reply in Telugu, Hindi or English.
4. **Case file:** scam type, urgency, step checklist, downloadable complaint draft, per-stage latency.

## What makes it dependable
- Replies in the language the person actually spoke.
- Remembers the conversation: asks one question about money lost, then gives next steps.
- If audio is unclear, it asks the person to repeat instead of guessing.
- Never asks for OTP, PIN, CVV or passwords.

## Honest limits
Audio limit of ~30 s per message; about 8 s end-to-end latency today; advice is general guidance, not legal advice; rule-based fallback covers six common scam types.

## Next steps
Streaming TTS for faster replies, telephony integration (calls instead of a web page), more languages, and swapping the reasoning step to Gnani Evon when an API endpoint is available.

**Contribution:** Solo project, designed, built and tested by [Your Name].
