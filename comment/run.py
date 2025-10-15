# run.py
import uvicorn
from .config import settings

uvicorn.run("comment.main:app", host="127.0.0.1", port=settings.PORT, reload=True)
