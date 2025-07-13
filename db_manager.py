from fastapi import HTTPException
from sqlalchemy import select, delete, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from db import async_session
from models import RecipesModel, KitchensModel, RecipeIngredientsModel, IngredientsModel
from schemas import CreateRecipeSchema, UpdateRecipeSchema


class RecipeDBManager:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_recipe(self, recipe: CreateRecipeSchema) -> RecipesModel:
        """Create a new recipe with validation for kitchen and ingredients.

        Args:
            recipe: CreateRecipeSchema containing recipe data including:
                - title: str
                - instruction: str
                - cooking_time: int
                - cooking_difficulty: str
                - kitchen_id: int
                - recipe_ingredients: List[int] (ingredient IDs)

        Returns:
            The newly created RecipesModel instance

        Raises:
            HTTPException: 404 if kitchen or any ingredient not found
            HTTPException: 500 if database error occurs
        """
        async with self.session() as sess:
            # Проверка кухни
            kitchen = await sess.get(KitchensModel, recipe.kitchen_id)
            if not kitchen:
                raise HTTPException(status_code=404, detail="Kitchen not found")

            # Валидация ингредиентов
            ingredient_objs = []
            for ingr_id in recipe.recipe_ingredients:
                ingredient = await sess.get(IngredientsModel, ingr_id)
                if not ingredient:
                    raise HTTPException(status_code=404, detail=f"Ingredient with id={ingr_id} not found")
                ingredient_objs.append(
                    RecipeIngredientsModel(ingredient_id=ingr_id)
                )

            new_recipe = RecipesModel(
                title=recipe.title,
                instruction=recipe.instruction,
                cooking_time=recipe.cooking_time,
                recipe_ingredients=ingredient_objs,
                cooking_difficulty=recipe.cooking_difficulty,
                kitchen_id=kitchen.id,
            )

            sess.add(new_recipe)
            await sess.commit()
            await sess.refresh(new_recipe)
            return new_recipe

    async def fts_search(self, query: str) -> list[RecipesModel]:
        """Full-text search for recipes using PostgreSQL's TSVector.

        Args:
            query: Search query string (supports websearch syntax)

        Returns:
            List of RecipesModel instances matching the search query,
            with joined kitchen and ingredients data

        Note:
            Uses Russian language configuration for stemming/parsing
        """
        async with self.session() as sess:
            ts_query = func.websearch_to_tsquery('russian', query)
            stmt = (
                select(RecipesModel)
                .where(RecipesModel.search_vector.op('@@')(ts_query))
                .options(
                    joinedload(RecipesModel.recipe_ingredients).joinedload(RecipeIngredientsModel.ingredient),
                    joinedload(RecipesModel.kitchen)
                )
            )
            result = await sess.execute(stmt)
            return result.unique().scalars().all()

    async def get_recipe_by_id(self, recipe_id: int) -> RecipesModel:
        """Retrieve a single recipe by its primary key.

        Args:
            recipe_id: Integer ID of the recipe to fetch

        Returns:
            RecipesModel with joined ingredients data

        Raises:
            HTTPException: 404 if recipe not found
        """
        async with self.session() as sess:
            result = await sess.execute(
                select(RecipesModel)
                .options(joinedload(RecipesModel.recipe_ingredients))
                .where(RecipesModel.id == recipe_id)
            )
            recipe = result.unique().scalar_one_or_none()
            if not recipe:
                raise HTTPException(status_code=404, detail="Recipe not found")
            return recipe

    async def update_recipe(self, recipe_id: int, update_data: UpdateRecipeSchema) -> RecipesModel:
        """Partially update recipe attributes.

        Args:
            recipe_id: ID of recipe to update
            update_data: UpdateRecipeSchema with fields to update (None for unchanged)
                Supported fields:
                - title: Optional[str]
                - instruction: Optional[str]
                - cooking_time: Optional[int]
                - cooking_difficulty: Optional[str]
                - kitchen_name: Optional[str]
                - ingredient_names: Optional[List[str]]

        Returns:
            Updated RecipesModel instance

        Raises:
            HTTPException: 404 if recipe, kitchen or ingredients not found
            HTTPException: 400 if invalid data provided
        """
        async with self.session() as sess:
            recipe = await sess.get(RecipesModel, recipe_id)
            if not recipe:
                raise HTTPException(status_code=404, detail="Recipe not found")

            if update_data.title is not None:
                recipe.title = update_data.title
            if update_data.instruction is not None:
                recipe.instruction = update_data.instruction
            if update_data.cooking_time is not None:
                recipe.cooking_time = update_data.cooking_time
            if update_data.cooking_difficulty is not None:
                recipe.cooking_difficulty = update_data.cooking_difficulty

            if update_data.kitchen_name is not None:
                kitchen = await sess.scalar(
                    select(KitchensModel).where(KitchensModel.name == update_data.kitchen_name)
                )
                if not kitchen:
                    raise HTTPException(status_code=404, detail="Kitchen not found")
                recipe.kitchen_id = kitchen.id

            # Обработка ингредиентов
            if update_data.ingredient_names is not None:
                # 1. Удалить старые связи
                await sess.execute(
                    delete(RecipeIngredientsModel).where(
                        RecipeIngredientsModel.recipe_id == recipe.id
                    )
                )

                # 2. Добавить новые связи
                for name in update_data.ingredient_names:
                    ingredient = await sess.scalar(
                        select(IngredientsModel).where(IngredientsModel.name == name)
                    )
                    if not ingredient:
                        raise HTTPException(status_code=404, detail=f"Ingredient '{name}' not found")

                    new_relation = RecipeIngredientsModel(
                        recipe_id=recipe.id,
                        ingredient_id=ingredient.id
                    )
                    sess.add(new_relation)

            await sess.commit()
            await sess.refresh(recipe)
            return recipe

    async def delete_recipe(self, recipe_id: int) -> None:
        """Permanently delete a recipe from database.

        Args:
            recipe_id: ID of recipe to delete

        Raises:
            HTTPException: 404 if recipe not found
            HTTPException: 500 if database error occurs
        """
        async with self.session() as sess:
            recipe = await self.get_recipe_by_id(recipe_id)
            await sess.delete(recipe)
            await sess.commit()

    async def filter_recipes_by_ingredients(
            self,
            include: list[str] | None = None,
            exclude: list[str] | None = None
    ) -> list[RecipesModel]:
        """Filter recipes based on ingredient inclusion/exclusion criteria.

        Args:
            include: List of ingredient names that MUST ALL be present
            exclude: List of ingredient names that MUST NOT be present

        Returns:
            List of RecipesModel matching the criteria with joined:
            - recipe_ingredients
            - ingredients
            - kitchen data

        Note:
            When both include and exclude are provided, acts as AND condition
        """
        async with self.session() as sess:
            query = select(RecipesModel).distinct()

            if include:
                subquery = (
                    select(RecipeIngredientsModel.recipe_id)
                    .join(IngredientsModel)
                    .where(IngredientsModel.name.in_(include))
                    .group_by(RecipeIngredientsModel.recipe_id)
                    .having(func.count(RecipeIngredientsModel.ingredient_id) == len(include))
                )
                query = query.where(RecipesModel.id.in_(subquery))

            if exclude:
                excluded_recipes = (
                    select(RecipeIngredientsModel.recipe_id)
                    .join(IngredientsModel)
                    .where(IngredientsModel.name.in_(exclude))
                )
                query = query.where(~RecipesModel.id.in_(excluded_recipes))

            query = query.options(
                joinedload(RecipesModel.recipe_ingredients).joinedload(RecipeIngredientsModel.ingredient),
                joinedload(RecipesModel.kitchen)
            )

            result = await sess.execute(query)
            return result.unique().scalars().all()


recipe_manager = RecipeDBManager(async_session)
