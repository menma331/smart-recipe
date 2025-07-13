import logging

import uvicorn
from fastapi import FastAPI

from api.recipes import recipes_router

# Настройка логгера
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
)
# Подключение роутеров
app.include_router(
    recipes_router,
    tags=["Recipes"]
)

def start_server(host: str = "0.0.0.0", port: int = 8000):
    """Запуск сервера Uvicorn с конфигурацией для продакшена"""
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        log_level=logging.INFO,
    )

if __name__ == "__main__":
    logger.info("Starting server in %s mode")
    start_server(host="localhost", port=8000)