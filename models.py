from enum import Enum

from sqlalchemy import VARCHAR, Integer, ForeignKey, TEXT
from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy.orm import mapped_column, relationship, Mapped
from sqlalchemy import Enum as SqlEnum

from db import BaseDBModel


class CookingDifficultEnum(str, Enum):
    """Enumeration representing recipe difficulty levels.

        Attributes:
            EASY: Simple recipes with minimal steps
            MEDIUM: Recipes requiring some cooking experience
            HARD: Complex recipes for experienced cooks
        """

    EASY = "EASY"
    MEDIUM = "MEDIUM"
    HARD = "HARD"


class IngredientsModel(BaseDBModel):
    """Ingredient entity for recipe management system.

    Attributes:
        id: Primary key
        name: Ingredient name (max 30 chars)
        ingredient_recipes: Relationship to RecipeIngredientsModel (join table)

    Relationships:
        recipes: Many-to-many relationship to RecipesModel through RecipeIngredientsModel
    """
    __tablename__ = 'ingredients'

    id: Mapped[int] = mapped_column(type_=Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(type_=VARCHAR(30))

    ingredient_recipes: Mapped[list["RecipeIngredientsModel"]] = relationship(
        back_populates="ingredient",
        cascade="all, delete-orphan",
    )


class KitchensModel(BaseDBModel):
    """Cuisine type/cooking style entity.

        Attributes:
            id: Primary key
            name: Kitchen/cuisine name (max 30 chars)
            recipes: One-to-many relationship to recipes

        Indexes:
            name: Should have index for frequent lookups
        """
    __tablename__ = "kitchens"

    id: Mapped[int] = mapped_column(type_=Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(type_=VARCHAR(30))  # навесить индекс

    recipes: Mapped[list["RecipesModel"]] = relationship(back_populates="kitchen")

class RecipeIngredientsModel(BaseDBModel):
    """Join table for many-to-many relationship between Recipes and Ingredients.

        Attributes:
            id: Primary key
            recipe_id: ForeignKey to RecipesModel
            ingredient_id: ForeignKey to IngredientsModel

        Relationships:
            recipe: Parent RecipesModel
            ingredient: Related IngredientsModel
        """
    """Связующая таблица между рецептами и ингредиентами для связи мэни ту мэни."""
    __tablename__ = "recipe_ingredients"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    recipe_id: Mapped[int] = mapped_column(ForeignKey("recipes.id", ondelete="CASCADE"), nullable=False)
    ingredient_id: Mapped[int] = mapped_column(ForeignKey("ingredients.id", ondelete="CASCADE"), nullable=False)

    recipe: Mapped["RecipesModel"] = relationship(back_populates="recipe_ingredients")
    ingredient: Mapped["IngredientsModel"] = relationship(back_populates="ingredient_recipes", lazy='subquery')


class RecipesModel(BaseDBModel):
    """Main recipe entity containing cooking instructions and metadata.

        Attributes:
            id: Primary key
            title: Recipe name (max 70 chars)
            instruction: Cooking instructions (text)
            cooking_time: Preparation time in minutes
            cooking_difficulty: Enum (EASY/MEDIUM/HARD)
            kitchen_id: ForeignKey to KitchensModel
            search_vector: TSVECTOR for full-text search

        Relationships:
            recipe_ingredients: Join table relationship to IngredientsModel
            kitchen: Parent KitchensModel

        Indexes:
            search_vector: GIN index for full-text search
        """
    __tablename__ = "recipes"

    id: Mapped[int] = mapped_column(type_=Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(type_=VARCHAR(70), nullable=False)
    instruction: Mapped[str] = mapped_column(type_=TEXT, default='Нет инструкции', nullable=True, doc="Инструкция по приготовлению блюда. Тип TEXT")
    recipe_ingredients: Mapped[list["RecipeIngredientsModel"]] = relationship(
        back_populates="recipe", cascade="all, delete-orphan", lazy='subquery'
    )
    cooking_time: Mapped[int] = mapped_column(type_=Integer, doc="Время приготовления(в минутах)")
    cooking_difficulty: Mapped[CookingDifficultEnum] = mapped_column(
        SqlEnum(CookingDifficultEnum, name="cooking_difficulty_enum", create_constraint=True),
        nullable=False,
        doc="Сложность приготовления"
    )
    kitchen_id: Mapped[int] = mapped_column(ForeignKey("kitchens.id"), nullable=False)
    kitchen: Mapped[KitchensModel] = relationship(back_populates="recipes", lazy='subquery')

    search_vector: Mapped[str] = mapped_column(TSVECTOR)
