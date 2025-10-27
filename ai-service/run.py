#!/usr/bin/env python
import uvicorn
from app.config import settings

if __name__ == "__main__":
    # Start the FastAPI application with the configured port
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.PORT,
        reload=True
    )