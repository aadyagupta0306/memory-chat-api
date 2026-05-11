import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from openai import OpenAI, OpenAIError
from pydantic import BaseModel, Field

load_dotenv()

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
MODEL_NAME = "openai/gpt-oss-120b:free"
app = FastAPI(title="Memory Project Chat API")

# --- In-memory thread storage ---
threads: dict[str, list] = {}

# --- Models ---
class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    system_prompt: str = "You are a helpful assistant."

class ChatResponse(BaseModel):
    model: str
    reply: str

# --- OpenRouter client ---
def get_openrouter_client() -> OpenAI:
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=500,
            detail="OPENROUTER_API_KEY is missing from the environment.",
        )
    return OpenAI(
        api_key=api_key,
        base_url=OPENROUTER_BASE_URL,
    )

# --- Home ---
@app.get("/")
def home() -> dict[str, str]:
    return {"message": "Chat API is running!"}

# --- 1. Create a thread ---
@app.post("/threads/{thread_id}")
def create_thread(thread_id: str):
    if thread_id in threads:
        raise HTTPException(status_code=400, detail="Thread already exists")
    threads[thread_id] = []
    return {"message": f"Thread '{thread_id}' created!"}

# --- 2. Add message → LLM replies ---
@app.post("/threads/{thread_id}/messages", response_model=ChatResponse)
def add_message(thread_id: str, request: ChatRequest):
    if thread_id not in threads:
        raise HTTPException(status_code=404, detail="Thread not found")

    client = get_openrouter_client()

    threads[thread_id].append({
        "role": "user",
        "content": request.message
    })

    try:
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": request.system_prompt},
                *threads[thread_id]
            ],
        )
    except OpenAIError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    reply = completion.choices[0].message.content or ""
    threads[thread_id].append({
        "role": "assistant",
        "content": reply
    })

    return ChatResponse(model=MODEL_NAME, reply=reply)

# --- 3. Get all messages in a thread ---
@app.get("/threads/{thread_id}")
def get_thread(thread_id: str):
    if thread_id not in threads:
        raise HTTPException(status_code=404, detail="Thread not found")
    return {
        "thread_id": thread_id,
        "messages": threads[thread_id]
    }

# codes to run the server:
# pip3 install fastapi uvicorn openai python-dotenv
# python3 -m uvicorn main:app --reload

