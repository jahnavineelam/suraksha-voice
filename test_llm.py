"""Usage:  python test_llm.py YOUR_GOOGLE_KEY
Tries several Gemini models and prints how long each takes."""
import sys, time, requests

key = sys.argv[1]
url = "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"
for model in ["gemini-flash-lite-latest", "gemini-flash-latest", "gemini-3.8-flash"]:
    t = time.time()
    try:
        r = requests.post(url, headers={"Authorization": f"Bearer {key}"}, timeout=25, json={
            "model": model, "max_tokens": 200,
            "messages": [{"role": "user", "content": "Reply with the single word: ready"}]})
        ms = (time.time() - t) * 1000
        if r.ok:
            print(f"OK    {model:28s} {ms:6.0f} ms  -> {r.json()['choices'][0]['message']['content'][:40]!r}")
        else:
            print(f"FAIL  {model:28s} {ms:6.0f} ms  HTTP {r.status_code}: {r.text[:150]}")
    except Exception as e:
        print(f"ERROR {model:28s} {(time.time()-t)*1000:6.0f} ms  {type(e).__name__}")