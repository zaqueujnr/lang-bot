import httpx

from fastapi import APIRouter, Request
from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnableConfig
import os

WAHA_API_KEY = os.getenv("WAHA_API_KEY")
router = APIRouter()


@router.post("/webhook")
async def webhook(request: Request):

    graph = request.app.state.graph

    data = await request.json()

    payload = data["payload"]

    user_input = payload["body"]
    chat_id = payload["from"]

    print("data:", data)
    # print("Mensagem:", user_input)
    # print("Chat:", chat_id)

    config = RunnableConfig(
        configurable={
            "thread_id": chat_id
        }
    )

    result = graph.invoke(
        {
            "messages": [
                HumanMessage(content=user_input)
            ]
        },
        config=config
    )

    response = result["messages"][-1].content

    print("chat_id:", chat_id)
    print("Resposta:", response)

    # Envia a resposta para o WhatsApp através do WAHA
    async with httpx.AsyncClient() as client:

        await client.post(
            "http://waha:3000/api/sendText",
                    headers={
            "X-Api-Key": WAHA_API_KEY
        },
            json={
                "session": "default",
                "chatId": chat_id,
                "text": response
            }
        )

    return {
        "result": response
    }