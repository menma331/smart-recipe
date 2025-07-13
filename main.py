import uvicorn
from fastapi import FastAPI

from api.recipes import recipes_router

app = FastAPI()

app.include_router(recipes_router)

uvicorn.run(app=app, host='127.0.0.1', port=8000)
