
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from interfaces import chat_router
from interfaces import document_router
from interfaces import knowledge_base_router
from interfaces import users_router




app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users_router)
app.include_router(knowledge_base_router)
app.include_router(document_router)
app.include_router(chat_router)




@app.get("/")
def read_root():
    return {"Hello": "World"}
