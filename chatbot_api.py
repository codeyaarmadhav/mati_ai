from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests, json, os
import redis

from mati_ai_engine import MatiAI, adapt_chart_if_needed

app = FastAPI()
mati = MatiAI()

# Redis
redis_client = redis.from_url(
    os.getenv("REDIS_URL"),
    decode_responses=True
)

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


@app.post("/chat")
def chat_with_mati(data: ChatRequest):
    session_key = f"chart:{data.session_id}"

    # 1️⃣ Try Redis first
    cached_chart = redis_client.get(session_key)

    if cached_chart:
        chart_data = json.loads(cached_chart)
    else:
        # 2️⃣ Generate chart ONCE
        try:
            resp = requests.post(
                "https://astro-nexus-backend-9u1s.onrender.com/api/v1/chart",
                json=data.birth_input.dict(),
                timeout=120
            )

            if resp.status_code == 429:
                raise HTTPException(
                    status_code=429,
                    detail="Birth chart service rate-limited. Please retry after a minute."
                )

            resp.raise_for_status()

        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

        adapted_chart = adapt_chart_if_needed(resp.json())

        # 3️⃣ Cache permanently (or long TTL)
        redis_client.set(session_key, json.dumps(adapted_chart), ex=86400)

        chart_data = adapted_chart

    # 4️⃣ Answer question
    answer = mati.answer_life_question(
        question=data.question,
        chart_data=chart_data
    )

    return {"answer": answer}
