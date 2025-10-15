from fastapi import FastAPI
from .config import settings
from .database import init_db
from .routers import comment


def lifespan(app: FastAPI):
    print(f"🚀 Starting {settings.APP_NAME}...")
    init_db()
    yield
    print("🛑 Shutting down...")



app = FastAPI(lifespan=lifespan)

app.include_router(comment.router, prefix="/api/v1")


@app.get("/")
def health_check():
    return "Ok"