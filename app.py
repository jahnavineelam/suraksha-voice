"""Suraksha Voice: a multilingual UPI / bank-fraud first-responder voice agent.

Pipeline:  mic -> Gnani Prisma (STT) -> brain (classify + advise) -> Gnani Timbre (TTS)
The brain is any OpenAI-compatible chat endpoint (set LLM_* in the sidebar or env, e.g. Gnani
Evon served via vLLM). If none is set, or the call fails, a built-in rule-based brain answers,
so the demo never dies.
"""
import hashlib
import json
import os
import re
import time
from datetime import datetime

import requests
import streamlit as st

BASE = "https://api.vachana.ai"
LANGS = {
    "Telugu": "te-IN",
    "Hindi": "hi-IN",
    "English (India)": "en-IN",
    "Auto-detect (mixed languages)": "indic-auto",
}

# ---------------------------------------------------------------- scam knowledge
KEYFILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "saved_keys.json")


def load_saved() -> dict:
    try:
        with open(KEYFILE, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


SAVED = load_saved()

SCAMS = {
    "otp_fraud": {
        "label": "OTP / bank-impersonation fraud",
        "keys": ["otp", "pin", "cvv", "bank officer", "bank manager", "account blocked", "card blocked",
                 "ओटीपी", "ओ टी पी", "ఓటీపీ", "ఒటిపి", "బ్యాంక్ నుంచి", "बैंक से"],
        "steps": ["Call your bank's official helpline and block the card / UPI / net banking now",
                  "Never share OTP, PIN or CVV with anyone again",
                  "Call 1930 (National Cyber Crime Helpline) immediately, the first hour matters most",
                  "File a complaint at cybercrime.gov.in with transaction IDs and screenshots",
                  "Change your banking passwords and check for linked devices"],
    },
    "upi_collect": {
        "label": "UPI collect-request / QR scam",
        "keys": ["upi", "collect request", "qr", "scan", "phonepe", "gpay", "google pay", "paytm",
                 "यूपीआई", "यू पी आई", "रिक्वेस्ट", "कलेक्ट", "फोन पे", "గూగుల్ పే", "ఫోన్ పే", "క్యూఆర్", "యూపీఐ", "రిక్వెస్ట్"],
        "steps": ["Decline any pending collect request and never enter your UPI PIN to RECEIVE money",
                  "Report the transaction inside your UPI app and block the sender",
                  "Call 1930 and give the transaction reference number",
                  "File at cybercrime.gov.in and inform your bank in writing"],
    },
    "remote_access": {
        "label": "Remote-access app scam (AnyDesk / TeamViewer)",
        "keys": ["anydesk", "teamviewer", "quicksupport", "screen share", "remote", "एनीडेस्क", "ఎనీడెస్క్"],
        "steps": ["Uninstall the remote-access app and switch off internet / airplane mode now",
                  "Call your bank to freeze accounts, then call 1930",
                  "Change all banking and email passwords from a different, clean device",
                  "File at cybercrime.gov.in"],
    },
    "digital_arrest": {
        "label": "Fake police / courier / 'digital arrest' scam",
        "keys": ["courier", "customs", "cbi", "police", "arrest", "narcotics", "fedex", "video call",
                 "पुलिस", "गिरफ्तार", "కొరియర్", "పోలీస్", "అరెస్ట్"],
        "steps": ["Hang up. No agency arrests or investigates people over video call or demands money",
                  "Do NOT transfer any money or share Aadhaar / PAN details",
                  "Call 1930 and report the number that called you",
                  "Tell a family member, scammers rely on isolation"],
    },
    "kyc_sim": {
        "label": "KYC update / SIM-swap scam",
        "keys": ["kyc", "sim", "update your", "link expired", "aadhaar", "pan card", "केवाईसी", "కేవైసీ"],
        "steps": ["Do not click the link or install any app they sent",
                  "Contact your bank only through the number printed on your card",
                  "If your SIM stopped working suddenly, call your telecom operator right away",
                  "Report on 1930 and the Sanchar Saathi portal"],
    },
    "lottery_job_loan": {
        "label": "Lottery / job / loan-app scam",
        "keys": ["lottery", "prize", "job offer", "work from home", "task", "loan app", "processing fee",
                 "लॉटरी", "लोन", "లాటరీ", "లోన్", "జాబ్"],
        "steps": ["Stop paying any 'fee', genuine prizes and jobs never ask for money upfront",
                  "Do not share contacts / gallery permissions with loan apps; uninstall them",
                  "Call 1930 and report the payments made so far",
                  "File at cybercrime.gov.in with chat screenshots"],
    },
    "unknown": {
        "label": "Suspected online fraud (type unclear)",
        "keys": [],
        "steps": ["If money has left your account, call 1930 right now",
                  "Call your bank's official helpline to block cards / UPI",
                  "Save screenshots, numbers and transaction IDs",
                  "File at cybercrime.gov.in"],
    },
}
URGENT_WORDS = ["lost", "debited", "deducted", "transferred", "gone", "paid", "shared otp", "cut", "withdrawn",
                "कट", "निकाल", "गया", "పోయాయి", "కట్", "డెబిట్", "ట్రాన్స్ఫర్"]

SAFE_LINES = {  # spoken fallback replies (short, calm, actionable)
    "te": "భయపడకండి, నేను సహాయం చేస్తాను. వెంటనే మీ బ్యాంక్ కార్డ్ మరియు UPI ని బ్లాక్ చేయండి. తర్వాత 1930 కి కాల్ చేసి ఫిర్యాదు చేయండి. ఇంకెవరికీ OTP చెప్పకండి.",
    "hi": "घबराइए नहीं, मैं आपकी मदद करूँगा। तुरंत अपना बैंक कार्ड और UPI ब्लॉक करवाइए। फिर 1930 पर कॉल करके शिकायत दर्ज कीजिए। किसी को भी OTP न बताएं।",
    "en": "Please stay calm, I will help you. First, block your bank card and UPI right now. Then call 1930 to report it. And do not share any OTP with anyone.",
}
REPEAT_LINES = {
    "te": "క్షమించండి, నాకు సరిగా వినిపించలేదు. దయచేసి మళ్లీ చెప్పండి.",
    "hi": "माफ़ कीजिए, मुझे ठीक से सुनाई नहीं दिया। कृपया दोबारा बताइए।",
    "en": "Sorry, I could not hear that clearly. Could you please say it again?",
}

SCAM_REPLIES = {  # per-scam spoken replies (te / hi / en)
    "otp_fraud": {
        "te": "ఇది బ్యాంక్ పేరుతో జరిగే OTP మోసం. వెంటనే మీ బ్యాంక్ హెల్ప్‌లైన్‌కు కాల్ చేసి కార్డ్ మరియు UPI బ్లాక్ చేయండి. తర్వాత 1930 కి కాల్ చేయండి. ఇంకెవరికీ OTP చెప్పకండి.",
        "hi": "यह बैंक के नाम पर OTP धोखाधड़ी है। तुरंत बैंक की हेल्पलाइन पर कॉल करके कार्ड और UPI ब्लॉक करवाइए। फिर 1930 पर कॉल कीजिए। OTP किसी को न बताएं।",
        "en": "This is a bank-impersonation OTP scam. Call your bank's helpline now and block your card and UPI. Then call 1930. Never share an OTP again."},
    "upi_collect": {
        "te": "ఇది UPI కలెక్ట్ రిక్వెస్ట్ మోసం లాగా ఉంది. డబ్బులు తీసుకోవడానికి UPI పిన్ ఎప్పుడూ ఎంటర్ చేయకండి. రిక్వెస్ట్‌ను రిజెక్ట్ చేసి, వెంటనే 1930 కి కాల్ చేయండి.",
        "hi": "यह UPI कलेक्ट रिक्वेस्ट फ्रॉड लगता है। पैसे पाने के लिए UPI पिन कभी न डालें। रिक्वेस्ट रिजेक्ट कीजिए और तुरंत 1930 पर कॉल कीजिए।",
        "en": "This looks like a UPI collect-request scam. You never enter your UPI PIN to receive money. Decline the request and call 1930 right away."},
    "remote_access": {
        "te": "ముందుగా ఆ రిమోట్ యాప్‌ను తొలగించి, ఇంటర్నెట్ ఆఫ్ చేయండి. తర్వాత బ్యాంక్‌కు కాల్ చేసి ఖాతాను ఫ్రీజ్ చేయించండి, ఆపై 1930 కి కాల్ చేయండి.",
        "hi": "पहले वह रिमोट ऐप हटाइए और इंटरनेट बंद कीजिए। फिर बैंक को कॉल करके अकाउंट फ्रीज करवाइए, और 1930 पर कॉल कीजिए।",
        "en": "First uninstall that remote-access app and turn off your internet. Then call your bank to freeze your accounts, and call 1930."},
    "digital_arrest": {
        "te": "కాల్ కట్ చేయండి. ఏ పోలీస్ లేదా కొరియర్ సంస్థ వీడియో కాల్‌లో అరెస్ట్ చేయదు, డబ్బులు అడగదు. డబ్బులు పంపకండి, 1930 కి కాల్ చేసి ఇంట్లో వాళ్లకు చెప్పండి.",
        "hi": "फोन काट दीजिए। कोई पुलिस या कूरियर एजेंसी वीडियो कॉल पर गिरफ्तार नहीं करती और पैसे नहीं मांगती। पैसे न भेजें, 1930 पर कॉल करें और घर पर बताइए।",
        "en": "Hang up. No police or courier agency arrests anyone over a video call or asks for money. Send nothing, call 1930, and tell someone at home."},
    "kyc_sim": {
        "te": "ఆ లింక్ క్లిక్ చేయకండి, యాప్ ఇన్‌స్టాల్ చేయకండి. మీ బ్యాంక్ కార్డ్ మీద ఉన్న నంబర్‌కే కాల్ చేయండి. అనుమానం ఉంటే 1930 కి రిపోర్ట్ చేయండి.",
        "hi": "उस लिंक पर क्लिक न करें और कोई ऐप इंस्टॉल न करें। बैंक को केवल कार्ड पर छपे नंबर पर कॉल करें। शक हो तो 1930 पर रिपोर्ट करें।",
        "en": "Do not click that link or install any app. Call your bank only on the number printed on your card. If in doubt, report to 1930."},
    "lottery_job_loan": {
        "te": "నిజమైన బహుమతి లేదా ఉద్యోగానికి ముందుగా డబ్బులు అడగరు. ఇక ఎలాంటి ఫీజు చెల్లించకండి. ఇప్పటివరకు చెల్లించిన వివరాలతో 1930 కి కాల్ చేయండి.",
        "hi": "असली इनाम या नौकरी के लिए पहले पैसे नहीं मांगे जाते। अब कोई फीस न दें। अब तक दिए गए पैसों की जानकारी के साथ 1930 पर कॉल करें।",
        "en": "Real prizes and jobs never ask for money upfront. Stop paying any fee. Call 1930 with the details of what you have paid so far."},
}


def lang2(code: str) -> str:
    return code[:2] if code[:2] in ("te", "hi", "en") else "hi"


# ---------------------------------------------------------------- Gnani calls
def gnani_stt(audio: bytes, lang_code: str, key: str) -> dict:
    r = requests.post(
        f"{BASE}/stt/v3",
        headers={"X-API-Key-ID": key},
        files={"audio_file": ("audio.wav", audio, "audio/wav")},
        data={"model": "prisma-v3.0", "language_code": lang_code},
        timeout=60,
    )
    r.raise_for_status()
    return r.json()


def gnani_tts(text: str, voice: str, lang_code: str, key: str) -> bytes:
    r = requests.post(
        f"{BASE}/api/v1/tts/inference",
        headers={"X-API-Key-ID": key, "Content-Type": "application/json"},
        json={
            "text": text, "voice": voice, "model": "timbre-v2.5", "language": lang_code, "speed": 1.0,
            "audio_config": {"sample_rate": 24000, "num_channels": 1, "sample_width": 2,
                             "encoding": "linear_pcm", "container": "wav"},
        },
        timeout=60,
    )
    r.raise_for_status()
    return r.content


# ---------------------------------------------------------------- brain
def rule_brain(text: str, lang_code: str) -> dict:
    t = text.lower()
    best, hits = "unknown", 0
    for k, v in SCAMS.items():
        n = sum(1 for w in v["keys"] if w.lower() in t)
        if n > hits:
            best, hits = k, n
    money_lost = any(w in t for w in URGENT_WORDS)
    return {
        "scam_type": best,
        "urgency": "HIGH" if (money_lost or best in ("otp_fraud", "remote_access")) else "MEDIUM",
        "money_lost": money_lost,
        "reply": SCAM_REPLIES.get(best, SAFE_LINES)[lang2(lang_code)] if best in SCAM_REPLIES else SAFE_LINES[lang2(lang_code)],
        "engine": "rule-based fallback",
    }


SYSTEM_PROMPT = """You are Suraksha, a calm voice assistant helping Indians who just fell for, or are being targeted by, a bank/UPI/online scam. The user's words come from speech recognition and may mix languages.
Reply ONLY with JSON: {"scam_type": one of [otp_fraud, upi_collect, remote_access, digital_arrest, kyc_sim, lottery_job_loan, unknown],
"urgency": "HIGH"|"MEDIUM"|"LOW", "money_lost": true|false,
"reply": "max 3 short spoken sentences, in the SAME language as the user (use native script), calm, tell them the single most important next actions in order: block card/UPI, call 1930, file at cybercrime.gov.in. Never ask for OTP, PIN, CVV or passwords. If the person has NOT yet said whether any money was lost or any OTP/details were shared, END your reply with exactly one short question asking that. Once they have said it, do not ask again; give the next steps. Write only in the user's language and script, never mix in other scripts."}"""


def llm_brain(history: list, text: str, lang_code: str, cfg: dict) -> dict:
    msgs = [{"role": "system", "content": SYSTEM_PROMPT}] + history[-6:] + [{"role": "user", "content": text}]
    payload = {"model": cfg["model"], "messages": msgs, "temperature": 0.2, "max_tokens": 1500,
               "reasoning_effort": "low"}  # keep "thinking" short so replies come back fast
    url = cfg["url"].rstrip("/") + "/chat/completions"
    hdr = {"Authorization": f"Bearer {cfg['key']}"}
    r = requests.post(url, headers=hdr, json=payload, timeout=15)
    if r.status_code == 400:  # model may not accept reasoning_effort -> retry plain
        payload.pop("reasoning_effort")
        r = requests.post(url, headers=hdr, json=payload, timeout=15)
    r.raise_for_status()
    choices = r.json().get("choices") or [{}]
    raw = (choices[0].get("message") or {}).get("content") or ""
    if not raw.strip():
        raise ValueError("empty LLM reply")
    data = json.loads(re.search(r"\{.*\}", raw, re.S).group(0))
    if data.get("scam_type") not in SCAMS:
        data["scam_type"] = "unknown"
    data.setdefault("urgency", "HIGH")
    data.setdefault("money_lost", False)
    data["engine"] = cfg["model"]
    if not data.get("reply"):
        raise ValueError("empty reply")
    return data


def think(history, text, lang_code, cfg):
    if cfg["url"] and cfg["key"]:
        err = None
        for _ in range(2):  # one quick retry for odd/empty responses
            try:
                return llm_brain(history, text, lang_code, cfg)
            except requests.exceptions.Timeout as e:
                err = e
                break  # don't wait another 15 s
            except Exception as e:
                err = e
        out = rule_brain(text, lang_code)
        out["engine"] = f"rule-based fallback (LLM error: {type(err).__name__}: {str(err)[:60]})"
        return out
    return rule_brain(text, lang_code)


def script_lang(text: str, default: str) -> str:
    """Reply in the language/script the person actually spoke."""
    if re.search(r"[\u0C00-\u0C7F]", text):
        return "te-IN"
    if re.search(r"[\u0900-\u097F]", text):
        return "hi-IN"
    return default


def complaint_draft(turns: list) -> str:
    if not turns:
        return ""
    last = turns[-1]["analysis"]
    said = "\n".join(f"- {t['user']}" for t in turns)
    steps = "\n".join(f"{i}. {s}" for i, s in enumerate(SCAMS[last["scam_type"]]["steps"], 1))
    return (
        f"CYBER FRAUD COMPLAINT DRAFT (for cybercrime.gov.in / 1930)\n"
        f"Generated: {datetime.now():%d %b %Y, %I:%M %p}\n"
        f"Category: {SCAMS[last['scam_type']]['label']}\n"
        f"Urgency: {last['urgency']}    Money lost: {'Yes' if last.get('money_lost') else 'Not confirmed'}\n\n"
        f"Victim's statement (transcribed from voice):\n{said}\n\n"
        f"Details to fill before submitting: amount, date/time, transaction IDs / UTR, scammer phone number or UPI ID, bank name.\n\n"
        f"Actions to take:\n{steps}\n"
    )


# ---------------------------------------------------------------- UI
st.set_page_config(page_title="Suraksha Voice", page_icon="🛡️", layout="wide",
                   initial_sidebar_state="collapsed")
st.title("🛡️ Suraksha Voice: scam first-responder")
st.caption("Speak in Telugu, Hindi or English (or mix). Powered by Gnani Prisma (speech-to-text) and Gnani Timbre (text-to-speech).")

with st.sidebar:
    st.header("Settings")
    api_key = st.text_input("Gnani API key", value=os.getenv("GNANI_API_KEY") or SAVED.get("gnani_key", ""), type="password")
    lang_name = st.selectbox("Language", list(LANGS), index=0)
    lang_code = LANGS[lang_name]
    voice = st.text_input("TTS voice", value=os.getenv("GNANI_VOICE") or SAVED.get("voice", "Nalini"),
                          help="Pick a voice name from the Gnani Voice Catalog (docs.gnani.ai).")
    with st.expander("Brain (LLM), optional"):
        st.caption("Any OpenAI-compatible endpoint, e.g. Gnani Evon served with vLLM. Empty = built-in rules.")
        llm_url = st.text_input("Base URL", value=os.getenv("LLM_BASE_URL") or SAVED.get("llm_url", "https://generativelanguage.googleapis.com/v1beta/openai"))
        llm_key = st.text_input("LLM key", value=os.getenv("LLM_API_KEY") or SAVED.get("llm_key", ""), type="password")
        llm_model = st.text_input("Model", value=os.getenv("LLM_MODEL") or SAVED.get("llm_model", "gemini-flash-lite-latest"))
    if st.button("Reset conversation"):
        st.session_state.clear()
        st.rerun()

# auto-save keys locally so they never need re-typing
_now = {"gnani_key": api_key, "voice": voice, "llm_url": llm_url, "llm_key": llm_key, "llm_model": llm_model}
if api_key and _now != {k: SAVED.get(k) for k in _now}:
    try:
        with open(KEYFILE, "w", encoding="utf-8") as f:
            json.dump(_now, f)
    except Exception:
        pass

cfg = {"url": llm_url, "key": llm_key, "model": llm_model}
ss = st.session_state
ss.setdefault("turns", [])
ss.setdefault("history", [])
ss.setdefault("last_audio", "")
ss.setdefault("autoplay", None)


def handle(user_text: str, detected: str, stt_ms: float):
    code = detected if lang_code == "indic-auto" else lang_code
    code = code if code and code != "indic-auto" else "hi-IN"
    if user_text.strip():
        code = script_lang(user_text, code)
    t0 = time.time()
    if not user_text.strip():  # failure case: nothing heard -> ask to repeat, don't guess
        analysis = {"scam_type": "unknown", "urgency": "LOW", "money_lost": False,
                    "reply": REPEAT_LINES[lang2(code)], "engine": "repeat-request"}
        user_text = "(unclear audio)"
    else:
        analysis = think(ss.history, user_text, code, cfg)
    brain_ms = (time.time() - t0) * 1000
    t1 = time.time()
    audio, tts_err = None, None
    try:
        audio = gnani_tts(analysis["reply"], voice, code, api_key)
    except Exception as e:
        tts_err = str(e)
    tts_ms = (time.time() - t1) * 1000
    ss.history += [{"role": "user", "content": user_text}, {"role": "assistant", "content": analysis["reply"]}]
    ss.turns.append({"user": user_text, "analysis": analysis, "audio": audio, "tts_err": tts_err,
                     "ms": (stt_ms, brain_ms, tts_ms)})
    ss.autoplay = len(ss.turns) - 1


left, right = st.columns([3, 2], gap="large")

with left:
    if not api_key:
        st.info("Add your Gnani API key in the sidebar to begin.")
    st.subheader("1. Tell me what happened")
    wav = st.audio_input("🎙️ Record (up to ~30 seconds)", disabled=not api_key)
    typed = st.chat_input("...or type it here (backup if the mic fails)", disabled=not api_key)

    if wav is not None and api_key:
        data = wav.getvalue()
        h = hashlib.md5(data).hexdigest()
        if h != ss.last_audio:
            ss.last_audio = h
            with st.spinner("Listening → thinking → speaking..."):
                t0 = time.time()
                try:
                    res = gnani_stt(data, lang_code, api_key)
                    handle(res.get("transcript", ""), res.get("detected_language_code", lang_code),
                           (time.time() - t0) * 1000)
                except Exception as e:
                    st.error(f"Speech recognition failed: {e}")
    if typed and api_key:
        with st.spinner("Thinking → speaking..."):
            handle(typed, lang_code, 0.0)

    st.subheader("2. Conversation")
    for i, t in enumerate(ss.turns):
        with st.chat_message("user"):
            st.write(t["user"])
        with st.chat_message("assistant"):
            st.write(t["analysis"]["reply"])
            if t["audio"]:
                st.audio(t["audio"], format="audio/wav", autoplay=(i == ss.autoplay))
            elif t["tts_err"]:
                st.warning(f"Voice reply failed ({t['tts_err'][:120]}). Text reply shown above.")
    ss.autoplay = None

with right:
    st.subheader("3. Case file")
    if not ss.turns:
        st.write("Waiting for your first message...")
    else:
        last = ss.turns[-1]
        a = last["analysis"]
        sc = SCAMS[a["scam_type"]]
        c1, c2 = st.columns(2)
        c1.metric("Scam type", sc["label"])
        c2.metric("Urgency", a["urgency"])
        if a["urgency"] == "HIGH":
            st.error("📞 Call **1930** now. Reporting within the first hour gives the best chance of freezing the money.")
        st.markdown("**Do these in order**")
        for i, s in enumerate(sc["steps"]):
            st.checkbox(s, key=f"step_{len(ss.turns)}_{i}")
        st.markdown("**Complaint draft**")
        draft = complaint_draft(ss.turns)
        st.text_area("draft", draft, height=260, label_visibility="collapsed")
        st.download_button("⬇️ Download complaint draft", draft, file_name="fraud_complaint_draft.txt")
        s_ms, b_ms, t_ms = last["ms"]
        st.caption(f"⏱ STT {s_ms:.0f} ms · brain {b_ms:.0f} ms · TTS {t_ms:.0f} ms · brain engine: {a['engine']}")
        st.caption("Helplines: 1930 (cyber crime) · cybercrime.gov.in · your bank's official number")