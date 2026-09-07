from fastapi import FastAPI
from api.routers.waha_webhook_router import router

from graph.graph import build_graph

app = FastAPI()
app.state.graph = build_graph()

app.include_router(router)