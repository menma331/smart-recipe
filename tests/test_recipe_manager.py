import pytest
from sqlalchemy import select

from models import KitchensModel, IngredientsModel, RecipesModel, RecipeIngredientsModel
from schemas import CreateRecipeSchema, UpdateRecipeSchema
from models import CookingDifficultEnum
from fastapi import HTTPException


@pytest.mark.asyncio
async def test_create_recipe_success(recipe_manager, db_session):
    kitchen = KitchensModel(name="Asian")
    ing1 = IngredientsModel(name="Soy Sauce")
    ing2 = IngredientsModel(name="Ginger")
    db_session.add_all([kitchen, ing1, ing2])
    await db_session.commit()
    await db_session.refresh(kitchen)
    await db_session.refresh(ing1)
    await db_session.refresh(ing2)

    instruction = 'Slice potatoes. Put slices potatoes into boiling oil and wait for 10 minutes. Get it to plate and Bon appetit !'
    data = CreateRecipeSchema(
        title="Stir Fry",
        instruction=instruction,
        recipe_ingredients=[ing1.id, ing2.id],
        cooking_time=10,
        cooking_difficulty=CookingDifficultEnum.EASY,
        kitchen_id=kitchen.id
    )

    recipe = await recipe_manager.create_recipe(data)

    assert recipe.id
    assert recipe.title == "Stir Fry"
    assert recipe.instruction == instruction

    result = await db_session.execute(
        select(RecipeIngredientsModel).where(RecipeIngredientsModel.recipe_id == recipe.id)
    )
    ingredients = result.scalars().all()
    assert len(ingredients) == 2


@pytest.mark.asyncio
async def test_create_recipe_invalid_kitchen(recipe_manager):
    data = CreateRecipeSchema(
        title="No Kitchen",
        instruction='No instruction',
        recipe_ingredients=[],
        cooking_time=5,
        cooking_difficulty=CookingDifficultEnum.EASY,
        kitchen_id=9999
    )
    with pytest.raises(HTTPException) as exc:
        await recipe_manager.create_recipe(data)
    assert exc.value.status_code == 404
    assert "Kitchen not found" in exc.value.detail


@pytest.mark.asyncio
async def test_get_recipe_by_id_success(recipe_manager, db_session):
    kitchen = KitchensModel(name="French")
    db_session.add(kitchen)
    await db_session.commit()
    await db_session.refresh(kitchen)

    recipe = RecipesModel(
        title="Quiche",
        cooking_time=30,
        cooking_difficulty=CookingDifficultEnum.MEDIUM,
        kitchen_id=kitchen.id
    )
    db_session.add(recipe)
    await db_session.commit()
    await db_session.refresh(recipe)

    result = await recipe_manager.get_recipe_by_id(recipe.id)
    assert result.title == "Quiche"
    assert result.instruction == 'Нет инструкции'


@pytest.mark.asyncio
async def test_get_recipe_not_found(recipe_manager):
    with pytest.raises(HTTPException) as exc:
        await recipe_manager.get_recipe_by_id(999)
    assert exc.value.status_code == 404
    assert "Recipe not found" in exc.value.detail


@pytest.mark.asyncio
async def test_update_recipe_success(recipe_manager, db_session):
    kitchen1 = KitchensModel(name="Mexican")
    kitchen2 = KitchensModel(name="Spanish")
    ing_old = IngredientsModel(name="Avocado")
    ing_new = IngredientsModel(name="Tomato")
    db_session.add_all([kitchen1, kitchen2, ing_old, ing_new])
    await db_session.commit()

    recipe = RecipesModel(
        title="Taco",
        cooking_time=15,
        cooking_difficulty=CookingDifficultEnum.EASY,
        kitchen_id=kitchen1.id
    )
    db_session.add(recipe)
    await db_session.commit()
    await db_session.refresh(recipe)

    # Привязываем старый ингредиент
    db_session.add(RecipeIngredientsModel(recipe_id=recipe.id, ingredient_id=ing_old.id))
    await db_session.commit()

    data = UpdateRecipeSchema(
        title="Burrito",
        cooking_time=20,
        cooking_difficulty=CookingDifficultEnum.MEDIUM,
        kitchen_name="Spanish",
        ingredient_names=["Tomato"]
    )

    updated = await recipe_manager.update_recipe(recipe.id, data)

    assert updated.title == "Burrito"
    assert updated.cooking_time == 20
    assert updated.kitchen_id == kitchen2.id

    # Проверим ингредиенты
    result = await db_session.execute(
        select(RecipeIngredientsModel).where(RecipeIngredientsModel.recipe_id == recipe.id)
    )
    ingredients = result.scalars().all()
    assert len(ingredients) == 1
    assert ingredients[0].ingredient_id == ing_new.id


@pytest.mark.asyncio
async def test_update_recipe_not_found(recipe_manager):
    data = UpdateRecipeSchema(title="Ghost")
    with pytest.raises(HTTPException) as exc:
        await recipe_manager.update_recipe(999, data)
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_update_recipe_invalid_kitchen(recipe_manager, db_session):
    kitchen = KitchensModel(name="Greek")
    db_session.add(kitchen)
    await db_session.commit()
    recipe = RecipesModel(
        title="Gyros",
        cooking_time=12,
        cooking_difficulty=CookingDifficultEnum.MEDIUM,
        kitchen_id=kitchen.id
    )
    db_session.add(recipe)
    await db_session.commit()
    await db_session.refresh(recipe)

    data = UpdateRecipeSchema(kitchen_name="NonExistent")
    with pytest.raises(HTTPException) as exc:
        await recipe_manager.update_recipe(recipe.id, data)
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_delete_recipe_success(recipe_manager, db_session):
    kitchen = KitchensModel(name="German")
    db_session.add(kitchen)
    await db_session.commit()
    recipe = RecipesModel(
        title="Schnitzel",
        cooking_time=25,
        cooking_difficulty=CookingDifficultEnum.HARD,
        kitchen_id=kitchen.id
    )
    db_session.add(recipe)
    await db_session.commit()
    await db_session.refresh(recipe)

    await recipe_manager.delete_recipe(recipe.id)

    result = await db_session.get(RecipesModel, recipe.id)
    assert result is None


@pytest.mark.asyncio
async def test_delete_recipe_not_found(recipe_manager):
    with pytest.raises(HTTPException) as exc:
        await recipe_manager.delete_recipe(999)
    assert exc.value.status_code == 404
