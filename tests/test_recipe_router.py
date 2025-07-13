import pytest
from httpx import AsyncClient
from main import app
from models import IngredientsModel, KitchensModel, CookingDifficultEnum
from schemas import CreateRecipeSchema

@pytest.mark.asyncio
async def test_create_recipe_success(db_session):
    kitchen = KitchensModel(name="Asian")
    ing1 = IngredientsModel(name="Soy Sauce")
    ing2 = IngredientsModel(name="Ginger")
    db_session.add_all([kitchen, ing1, ing2])
    await db_session.commit()
    await db_session.refresh(kitchen)
    await db_session.refresh(ing1)
    await db_session.refresh(ing2)

    data = {
        "title": "Stir Fry",
        "instruction": "Chop and fry.",
        "recipe_ingredients": [ing1.id, ing2.id],
        "cooking_time": 15,
        "cooking_difficulty": CookingDifficultEnum.EASY,
        "kitchen_id": kitchen.id
    }

    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post("/recipe/create", json=data)

    assert response.status_code == 201
    assert response.json()["text"] == "success"
    assert isinstance(response.json()["recipe"], int)

@pytest.mark.asyncio
async def test_get_recipe_by_id_success(db_session):
    # Допустим, ты уже создал рецепт вручную или через фикстуру
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/recipe/1")

    assert response.status_code == 200
    assert "recipe" in response.json()

@pytest.mark.asyncio
async def test_update_recipe_success(db_session):
    data = {
        "title": "Updated Title",
        "cooking_time": 20
    }
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.patch("/recipe/1", json=data)

    assert response.status_code == 200
    assert response.json()["text"] == "success"
    assert response.json()["recipe"]["title"] == "Updated Title"

@pytest.mark.asyncio
async def test_delete_recipe_success(db_session):
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.delete("/recipe/1")

    assert response.status_code == 200
    assert response.json()["text"] == "Success delete"

@pytest.mark.asyncio
async def test_filter_recipes(db_session):
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/recipe/filter-by-ingredients", params={"include": "Soy Sauce"})

    assert response.status_code == 200
    assert isinstance(response.json(), list)

@pytest.mark.asyncio
async def test_search_recipes(db_session):
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/recipe/search", params={"q": "Fry"})

    assert response.status_code == 200
    assert isinstance(response.json(), list)
