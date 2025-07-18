# Smart Recipe Finder API

![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2CA5E0?style=for-the-badge&logo=docker&logoColor=white)

Backend API для приложения поиска рецептов с поддержкой полнотекстового поиска и фильтрации по ингредиентам.

## Особенности

- Полноценный CRUD для рецептов
- Фильтрация по ингредиентам (включение/исключение)
- Полнотекстовый поиск с поддержкой русского языка
- Подробная документация API (Swagger UI)
- Асинхронная работа с базой данных
- Полностью контейнеризированное решение

## Технологии

- Python 3.12
- FastAPI
- SQLAlchemy 2.0
- PostgreSQL
- Alembic (миграции)
- Docker

## Установка и запуск

### Требования

- Docker и Docker Compose
- Python 3.10+

### Запуск через Docker

1. Скопируйте `.env.example` в `.env` и при необходимости измените настройки:
   ```bash
   cp .env.example .env
   ```

2. Запустите сервисы:
   ```bash
   docker-compose up -d --build
   ```

3. Примените миграции:
   ```bash
   docker-compose exec web alembic upgrade head
   ```

4. Приложение будет доступно по адресу: [http://localhost:8000](http://localhost:8000)

### Локальная разработка

1. Установите зависимости:
   ```bash
   pip install -r requirements.txt
   ```

2. Запустите сервер:
   ```bash
   uvicorn main:app --reload
   ```

## API Endpoints

### Рецепты

| Метод | Endpoint | Описание |
|-------|----------|----------|
| POST | `/recipe/create` | Создать новый рецепт |
| GET | `/recipe/{recipe_id}` | Получить рецепт по ID |
| PATCH | `/recipe/{recipe_id}` | Обновить рецепт |
| DELETE | `/recipe/{recipe_id}` | Удалить рецепт |
| GET | `/recipe/filter-by-ingredients` | Фильтр по ингредиентам |
| GET | `/recipe/search` | Полнотекстовый поиск |

### Примеры запросов

**Создание рецепта:**
```bash
curl -X POST "http://localhost:8000/recipe/create" \
-H "Content-Type: application/json" \
-d '{
  "title": "Паста Карбонара",
  "instruction": "Приготовить пасту...",
  "recipe_ingredients": [1, 2, 3],
  "cooking_time": 30,
  "cooking_difficulty": "MEDIUM",
  "kitchen_id": 1
}'
```

**Фильтрация рецептов:**
```bash
curl "http://localhost:8000/recipe/filter-by-ingredients?include=яйца,мука&exclude=молоко"
```

**Полнотекстовый поиск:**
```bash
curl "http://localhost:8000/recipe/search?q=быстрый итальянский ужин"
```

## Тестирование

Для запуска тестов:

```bash
pytest -v
```

Тесты покрывают:
- Все CRUD операции
- Фильтрацию по ингредиентам
- Полнотекстовый поиск
- Валидацию данных

## Структура проекта

```
.
├── api/               # Роутеры FastAPI
├── db/                # Настройки базы данных
├── migrations/        # Миграции Alembic
├── models/            # SQLAlchemy модели
├── schemas/           # Pydantic схемы
├── tests/             # Тесты
├── docker-compose.yml # Конфигурация Docker
├── main.py            # Точка входа
└── README.md          # Документация
```

## Документация API

После запуска приложения документация доступна:
- Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)
- ReDoc: [http://localhost:8000/redoc](http://localhost:8000/redoc)