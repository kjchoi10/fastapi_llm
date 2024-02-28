import asyncio
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from starlette.responses import JSONResponse
from llm import prompt_llm_async, OpenAIMessageType
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse
import random

app = FastAPI()

class PromptData(BaseModel):
    prompt: str

@app.post('/prompt_data')
async def create_prompt_data_view(prompt_data: PromptData):
    return prompt_data

@app.get('/', response_class=HTMLResponse)
def web_app(request: Request):
    return HTMLResponse("""
        <html>
            <head>
                <title>Chat Service</title>
            </head>
            <body>
                <h1>Welcome to the Chat Service</h1>
                <form id="chat-form">
                    <input type="text" id="message" placeholder="Enter your message" required>
                    <button type="submit">Send</button>
                </form>
                <div id="chat"></div>
                <script>
                    const chatForm = document.getElementById('chat-form');
                    const messageInput = document.getElementById('message');
                    const chatDiv = document.getElementById('chat');

                    chatForm.addEventListener('submit', async (e) => {
                        e.preventDefault();
                        const response = await fetch('/completion', {
                            method: 'POST',
                            body: new FormData(chatForm)
                        });
                        const reader = response.body.getReader();
                        while (true) {
                            const { done, value } = await reader.read();
                            if (done) break;
                            const text = new TextDecoder().decode(value);
                            const message = document.createElement('p');
                            message.textContent = text;
                            chatDiv.appendChild(message);
                        }
                    });
                </script>
            </body>
        </html>
    """)

async def streamed_ai_response(prompt: str):
    async for chunk in prompt_llm_async(prompt):
        yield f"data: {chunk}\n\n"
        await asyncio.sleep(0.5)

@app.post('/completion')
async def completion_api(prompt_form: str = Form(...)):
    return StreamingResponse(streamed_ai_response(prompt_form), media_type='text/event-stream')

@app.get("/stream-example")
async def stream_example():
    async def stream_tokens():
        for token in ['hello', ', ', 'this ', 'is ', 'a ', 'streamed ', 'response.']:
            await asyncio.sleep(random.randint(0, 3))
            yield token
    return EventSourceResponse(stream_tokens())
