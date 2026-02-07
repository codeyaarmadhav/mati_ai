from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests
import redis
import json
import os

from mati_ai_engine import MatiAI, adapt_chart_if_needed

app = FastAPI()
mati = MatiAI()

# -----------------------------
# Redis connection
# -----------------------------
# Local development:
redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST", "localhost"),
    port=int(os.getenv("REDIS_PORT", 6379)),
    decode_responses=True
)

# -----------------------------
# Request schemas
# -----------------------------

class BirthInput(BaseModel):
    name: str
    gender: str
    birth_date: dict
    birth_time: dict
    place_of_birth: str
    astrology_type: str = "vedic"
    ayanamsa: str = "lahiri"

class ChatRequest(BaseModel):
    session_id: str
    birth_input: BirthInput
    question: str


# -----------------------------
# API endpoint
# -----------------------------

@app.post("/chat")
def chat_with_mati(data: ChatRequest):
    session_id = data.session_id
    redis_key = f"mati:chart:{session_id}"

    # 1️⃣ Try to get chart from Redis
    cached_chart = redis_client.get(redis_key)

    if cached_chart:
        chart_data = json.loads(cached_chart)
    else:
        # 2️⃣ Call Birth Chart API
        try:
            resp = requests.post(
                "https://astro-nexus-backend-9u1s.onrender.com/api/v1/chart",
                json=data.birth_input.dict(),
                timeout=120
            )
            resp.raise_for_status()
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

        chart_api_response = resp.json()

        # 3️⃣ Adapt chart to Mati format
        chart_data = adapt_chart_if_needed(chart_api_response)

        # 4️⃣ Store chart in Redis (TTL = 24 hours)
        redis_client.setex(
            redis_key,
            86400,  # 24 hours
            json.dumps(chart_data)
        )

    # 5️⃣ Answer question using stored chart
    answer = mati.answer_life_question(
        question=data.question,
        chart_data=chart_data
    )

    return {
        "answer": answer
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("chatbot_api:app", host="0.0.0.0", port=8000)
