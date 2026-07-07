from fastapi import FastAPI
from routes import router
from app_init import init_app

init_app()

app = FastAPI()

app.include_router(router)