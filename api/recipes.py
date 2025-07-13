from typing import Optional, List
from fastapi import APIRouter
from fastapi.params import Query, Path
from schemas import RecipeReadSchema, UpdateRecipeSchema
from schemas import CreateRecipeSchema
from db_manager import recipe_manager
from fastapi.responses import JSONResponse

recipes_router = APIRouter(
    prefix='/recipe',
    tags=['Recipes'],
    responses={
        404: {"description": "Recipe not found"},
        400: {"description": "Invalid input data"}
    }
)


@recipes_router.post(
    '/create',
    response_model=RecipeReadSchema,
    status_code=201,
    summary="Create new recipe",
    responses={
        201: {"description": "Recipe created successfully"},
        404: {"description": "Kitchen or ingredient not found"}
    }
)
async def create_recipe(recipe: CreateRecipeSchema):
    """Create a new recipe with full validation.

    Args:
        recipe: CreateRecipeSchema with all required recipe data

    Returns:
        JSONResponse with:
        - status: 201 on success
        - body: {
            "text": "success",
            "recipe": <new_recipe_id>
        }

    Raises:
        HTTPException: 404 if referenced kitchen/ingredients don't exist
        HTTPException: 422 if validation fails
    """
    new_recipe = await recipe_manager.create_recipe(recipe)
    return JSONResponse(
        status_code=201,
        content={"text": "success", 'recipe': new_recipe.id}
    )


@recipes_router.get(
    '/filter-by-ingredients',
    response_model=List[RecipeReadSchema],
    summary="Filter recipes by ingredients",
    description="""Filter recipes using inclusion/exclusion criteria.
    - include: ALL listed ingredients must be present
    - exclude: NONE of listed ingredients may be present""",
    responses={
        200: {"description": "List of matching recipes"}
    }
)
async def filter_recipes(
        include: Optional[List[str]] = Query(
            default=None,
            description="Ingredients that MUST be present"
        ),
        exclude: Optional[List[str]] = Query(
            default=None,
            description="Ingredients that MUST NOT be present"
        ),
):
    """Filter recipes based on ingredient presence/absence.

    Args:
        include: Optional list of ingredient names to include
        exclude: Optional list of ingredient names to exclude

    Returns:
        List of RecipeReadSchema objects matching criteria

    Note:
        When both parameters provided, acts as AND condition
    """
    recipes = await recipe_manager.filter_recipes_by_ingredients(
        include=include,
        exclude=exclude
    )
    return [RecipeReadSchema.model_validate(r) for r in recipes]


@recipes_router.get(
    "/search",
    response_model=List[RecipeReadSchema],
    summary="Full-text recipe search",
    description="Search recipes using PostgreSQL full-text search",
    responses={
        200: {"description": "List of matching recipes"}
    }
)
async def search_recipes(q: str = Query(..., description="Search query")):
    """Search recipes by text query.

    Args:
        q: Search string (supports advanced search syntax)

    Returns:
        List of RecipeReadSchema objects matching search

    Note:
        Uses Russian language stemming for search
    """
    recipes = await recipe_manager.fts_search(q)
    return [RecipeReadSchema.model_validate(r) for r in recipes]


@recipes_router.get(
    '/{recipe_id}',
    response_model=RecipeReadSchema,
    summary="Get recipe by ID",
    responses={
        200: {"description": "Recipe data"},
        404: {"description": "Recipe not found"}
    }
)
async def get_recipe_by_id(recipe_id: int = Path(..., description="Recipe ID")):
    """Retrieve complete recipe data by its ID.

    Args:
        recipe_id: Integer ID of the recipe

    Returns:
        JSONResponse with:
        - status: 200 on success
        - body: {
            "recipe": <full_recipe_data>
        }

    Raises:
        HTTPException: 404 if recipe not found
    """
    recipe = await recipe_manager.get_recipe_by_id(recipe_id)
    recipe_schema = RecipeReadSchema.model_validate(recipe)
    return JSONResponse(
        status_code=200,
        content={"recipe": recipe_schema.model_dump()}
    )


@recipes_router.patch(
    '/{recipe_id}',
    response_model=RecipeReadSchema,
    summary="Update recipe",
    description="Partially update recipe fields",
    responses={
        200: {"description": "Recipe updated successfully"},
        404: {"description": "Recipe/kitchen/ingredient not found"}
    }
)
async def update_recipe_by_id(
        update_recipe: UpdateRecipeSchema,
        recipe_id: int = Path(..., description="Recipe ID to update"),

):
    """Update recipe fields with partial data.

    Args:
        recipe_id: ID of recipe to update
        update_recipe: UpdateRecipeSchema with fields to update

    Returns:
        JSONResponse with:
        - status: 200 on success
        - body: {
            "text": "success",
            "recipe": <updated_recipe_data>
        }

    Note:
        - Null values are ignored
        - Supports updating ingredients by name
        - Supports updating kitchen by name
    """
    updated_recipe = await recipe_manager.update_recipe(
        recipe_id=recipe_id,
        update_data=update_recipe
    )
    updated_recipe_schema = RecipeReadSchema.model_validate(updated_recipe)
    return JSONResponse(
        status_code=200,
        content={
            "text": "success",
            "recipe": updated_recipe_schema.model_dump()
        }
    )


@recipes_router.delete(
    '/{recipe_id}',
    status_code=200,
    summary="Delete recipe",
    responses={
        200: {"description": "Recipe deleted successfully"},
        404: {"description": "Recipe not found"}
    }
)
async def delete_recipe_by_id(
        recipe_id: int = Path(..., description="Recipe ID to delete")
):
    """Permanently delete a recipe.

    Args:
        recipe_id: ID of recipe to delete

    Returns:
        JSONResponse with:
        - status: 200 on success
        - body: {"text": "Success delete"}
    """
    await recipe_manager.delete_recipe(recipe_id)
    return JSONResponse(
        status_code=200,
        content={"text": "Success delete"}
    )
