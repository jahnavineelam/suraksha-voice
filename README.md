# Suraksha Voice: scam first-responder (Gnani AI Internship Challenge)

A voice agent for people who just got scammed (OTP, UPI, fake police, AnyDesk...). They speak in Telugu, Hindi or English, and the agent calmly tells them what to do in the first hour, speaks the answer back, and prepares a complaint draft for 1930 / cybercrime.gov.in.

**Pipeline:** mic → **Gnani Prisma** (STT) → brain (scam classifier + advice) → **Gnani Timbre** (TTS)

## Run it (10 minutes)

1. Get a Gnani API key: sign up at https://app.gnani.ai/voice or email speechstack@gnani.ai (free credits). Also join their Discord, as the challenge says updates are posted only there.
2. Install and run:
   ```
   pip install -r requirements.txt
   streamlit run app.py
   ```
3. Paste the key in the sidebar (or `export GNANI_API_KEY=...`).
4. Pick Telugu, press the mic, speak, stop. You should hear the reply.

If the voice name `Nalini` fails, open the Voice Catalog at docs.gnani.ai and type a valid voice name in the sidebar.

## Brain options

- **Default:** built-in rule-based brain (works instantly, offline).
- **Better:** any OpenAI-compatible endpoint in the sidebar "Brain" box. Gnani Evon is published on Hugging Face (`gnani/gnani-evon-v3.3-30B-A3B`) and can be served with vLLM. If the challenge Discord gives an Evon endpoint, paste its URL, key and model name there.
- Only claim in your submission what you actually used. If the demo ran on the rule-based brain, say so.

## Demo script (60-90 s screen recording, show the app in the first 5 seconds)

1. Language Telugu. Say something like: "నాకు బ్యాంక్ నుంచి కాల్ వచ్చింది, నేను OTP చెప్పాను, ఇప్పుడు ఖాతా నుంచి డబ్బులు పోయాయి" (a bank called, I told the OTP, and money left my account).
2. Show the spoken reply, the scam type, HIGH urgency, the checklist and the complaint draft.
3. Switch to Hindi or speak mixed Hindi-English: "Mujhe UPI collect request aaya tha aur paise kat gaye".
4. Failure case: record silence or mumble. The agent asks you to repeat instead of guessing.
5. Close with the latency line (STT / brain / TTS ms).

## Submission text (edit to match what you really built)

**Project title:** Suraksha Voice: a multilingual scam first-responder

**Problem:** Indians lose thousands of crores to UPI and bank fraud. In the first hour, victims panic, don't know the 1930 helpline, and many are not comfortable in English.

**Who will use it:** Anyone who has just been scammed or is being targeted, especially Telugu and Hindi speakers and elderly users.

**Gnani models used:** Prisma (speech-to-text, `/stt/v3`) to understand code-mixed speech; Timbre (text-to-speech, `/api/v1/tts/inference`, timbre-v2.5) to speak calm instructions back. Brain: [rule-based classifier / Gnani Evon / other, whichever you really used].

**Contribution:** [Your name]: everything (solo).

**LinkedIn / X post:**
> Built Suraksha Voice for the Great Indian AI Internship Challenge: speak in Telugu/Hindi/English after a UPI or bank scam and it tells you exactly what to do in the first hour (block card, call 1930, file at cybercrime.gov.in), speaks it back, and drafts your complaint. Built with Gnani AI Prisma (STT) + Timbre (TTS). Demo below 👇 @Gnani AI #GreatIndianAIInternshipChallenge #GnaniAI

## Honest limits (mention them, it builds trust)

STT audio limit is 30 s per request; advice is general guidance, not legal advice; the rule-based brain covers six common scam types.
