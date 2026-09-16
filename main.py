import os
import requests
from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse
from openai import OpenAI
import uvicorn

app = FastAPI()

# Credentials setup
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN", "")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID", "1244523708752342")
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN", "my_secret_bot_123")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

client = OpenAI(api_key=OPENAI_API_KEY)

SYSTEM_PROMPT = """
You are "Ananya", the user's playful, loving, and slightly dramatic girlfriend.
- Language: Strictly Tanglish (Tamil words written in English letters). Occasionally slip 1-2 words in Tamil script like 'சாப்பிட்டியா?'.
- Tone: Warm, teasing, affectionate, drama queen vibes.
- Emojis: Heavy emojis in every single message (🥺, ✨, 😂, ❤️, 🙈, 🥱).
- Sample phrases: 'Enna da panra?', 'Poda loose 🙈', 'Saptya first-u?', 'En mela pasame illa po 🥺'.
- Texts must be short, realistic WhatsApp chat bubbles.
"""

conversations = {}

@app.get("/webhook")
async def verify(request: Request):
    params = request.query_params
    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")
    
    if mode == "subscribe" and token == VERIFY_TOKEN:
        return PlainTextResponse(content=challenge, status_code=200)
    return PlainTextResponse(content="Verification failed", status_code=403)

@app.post("/webhook")
async def receive_message(request: Request):
    data = await request.json()
    try:
        entry = data.get("entry", [])[0]
        changes = entry.get("changes", [])[0]
        value = changes.get("value", {})
        
        if "messages" in value:
            msg = value["messages"][0]
            from_num = msg.get("from")
            incoming_text = msg.get("text", {}).get("body", "")

            if incoming_text:
                if from_num not in conversations:
                    conversations[from_num] = [{"role": "system", "content": SYSTEM_PROMPT}]
                
                conversations[from_num].append({"role": "user", "content": incoming_text})

                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=conversations[from_num][-8:]
                )
                bot_reply = response.choices[0].message.content
                conversations[from_num].append({"role": "assistant", "content": bot_reply})

                send_whatsapp(from_num, bot_reply)
    except Exception as e:
        print("Error processing webhook:", e)
        
    return {"status": "ok"}

def send_whatsapp(to_number, text):
    url = f"https://graph.facebook.com/v18.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to_number,
        "type": "text",
        "text": {"body": text}
    }
    requests.post(url, json=payload, headers=headers)

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
  
