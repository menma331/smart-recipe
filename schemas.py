from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, computed_field
from pydantic.alias_generators import to_snake


class CookingDifficultEnum(str, Enum):
    """Enum representing recipe difficulty levels.

    Values:
        EASY: Simple recipes with minimal steps
        MEDIUM: Recipes requiring basic cooking skills
        HARD: Complex recipes for experienced cooks
    """
    EASY = "EASY"
    MEDIUM = "MEDIUM"
    HARD = "HARD"


class IngredientSchema(BaseModel):
    """Response schema for ingredient representation.

    Fields:
        id: Unique ingredient identifier
        name: Ingredient name (max 30 characters)
    """
    id: int
    name: str

    class Config:
        from_attributes = True  # Enable ORM mode


class RecipeIngredientReadSchema(BaseModel):
    """Join table schema for recipe-ingredient relationship.

    Fields:
        ingredient_id: Reference to ingredient ID
        ingredient: Full IngredientSchema object

    Note:
        Can be extended with quantity/measurement fields
    """
    ingredient_id: int
    ingredient: IngredientSchema

    class Config:
        from_attributes = True


class RecipeReadSchema(BaseModel):
    """Complete recipe response schema with nested relationships.

    Fields:
        id: Recipe unique identifier
        title: Recipe name (max 70 chars)
        instruction: Cooking instructions
        cooking_time: Preparation time in minutes
        cooking_difficulty: Difficulty level enum
        kitchen_id: Associated cuisine type ID
        recipe_ingredients: List of ingredient associations

    Computed Fields:
        ingredients: List of ingredient IDs (convenience accessor)
    """
    id: int = 1
    title: str = "Название рецепта"
    instruction: str = 'Нет инструкции'
    cooking_time: int = 5
    cooking_difficulty: str = "MEDIUM"
    kitchen_id: int = 1
    recipe_ingredients: list[RecipeIngredientReadSchema] = [1, 2, 3]

    class Config:
        from_attributes = True  # ORM mode
        alias_generator = to_snake  # Auto-convert field names
        populate_by_name = True  # Allow alias population

    @computed_field
    @property
    def ingredients(self) -> List[int]:
        """Extract ingredient IDs from recipe_ingredients relationships."""
        return [ri.ingredient_id for ri in self.recipe_ingredients]


class CreateRecipeSchema(BaseModel):
    """Schema for recipe creation endpoint.

    Fields:
        title: Dish name (required)
        instruction: Cooking process description
        recipe_ingredients: List of ingredient IDs
        cooking_time: Preparation time in minutes (must be > 0)
        cooking_difficulty: Default MEDIUM
        kitchen_id: Associated cuisine ID

    Validation:
        - cooking_time must be greater than 0
        - All ingredient IDs must exist in DB
        - kitchen_id must reference existing kitchen
    """
    title: str = Field(..., description='Dish name')
    instruction: str = Field(..., description="Cooking instructions")
    recipe_ingredients: List[int] = Field(
        ...,
        description='List of ingredient IDs'
        )
    cooking_time: int = Field(
        default=0, gt=0,
        description='Preparation time in minutes (must be > 0)'
        )
    cooking_difficulty: CookingDifficultEnum = Field(
        default=CookingDifficultEnum.MEDIUM,
        description="Difficulty level (EASY/MEDIUM/HARD)"
    )
    kitchen_id: int = Field(..., description="Associated cuisine ID")


class UpdateRecipeSchema(BaseModel):
    """Schema for partial recipe updates (PATCH operations).

    Fields:
        title: Optional new title
        instruction: Optional new instructions
        cooking_time: Optional new preparation time
        cooking_difficulty: Optional new difficulty
        kitchen_name: Optional new cuisine by name
        ingredient_names: Optional new ingredients by name

    Note:
        - kitchen_name and ingredient_names provide alternative identifiers
        - Null values indicate fields shouldn't be updated
    """
    title: Optional[str] = None
    instruction: Optional[str] = None
    cooking_time: Optional[int] = None
    cooking_difficulty: Optional[CookingDifficultEnum] = None
    kitchen_name: Optional[str] = None
    ingredient_names: Optional[List[str]] = None


class DeleteRecipeSchema(BaseModel):
    """Schema for recipe deletion requests.

    Fields:
        id: Recipe ID to delete

    Validation:
        - ID must reference existing recipe
    """
    id: int = Field(..., description="Recipe ID to delete")