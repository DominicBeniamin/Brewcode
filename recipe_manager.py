# recipe_manager.py
"""
Module for managing recipes, including retrieval and scaling.
"""

import sqlite3
from typing import TypedDict, List, Optional
import copy


class IngredientDict(TypedDict):
    recipeIngredientID: int
    stageID: int
    itemID: int
    amount: float
    unit: str
    timing: Optional[str]
    scalingMethod: str
    notes: Optional[str]


class StageDict(TypedDict):
    stageID: int
    recipeID: int
    stageTypeID: int
    stageOrder: int
    name: str
    instructions: Optional[str]
    durationDays: Optional[int]
    isOptional: bool
    ingredients: List[IngredientDict]


class RecipeDict(TypedDict):
    recipeID: int
    name: str
    description: Optional[str]
    batchSizeL: float
    notes: Optional[str]


class RecipeData(TypedDict):
    recipe: RecipeDict
    stages: List[StageDict]
    ingredients: List[IngredientDict]


def get_recipe(conn: sqlite3.Connection, recipe_id: int) -> RecipeData:
    """
    Retrieve a recipe and its related stages and ingredients from the database.
    """
    cur = conn.cursor()

    # Get the recipe itself
    cur.execute(
        """
        SELECT recipeID, name, description, batchSizeL, notes
        FROM recipes
        WHERE recipeID = ?
        """,
        (recipe_id,),
    )
    recipe_row = cur.fetchone()
    if not recipe_row:
        raise ValueError(f"Recipe with ID {recipe_id} does not exist.")

    recipe: RecipeDict = {
        "recipeID": recipe_row[0],
        "name": recipe_row[1],
        "description": recipe_row[2],
        "batchSizeL": recipe_row[3],
        "notes": recipe_row[4],
    }

    # Get stages
    cur.execute(
        """
        SELECT stageID, recipeID, stageTypeID, stageOrder, name, instructions, durationDays, isOptional
        FROM recipeStages
        WHERE recipeID = ?
        ORDER BY stageOrder
        """,
        (recipe_id,),
    )
    stage_rows = cur.fetchall()

    stages: List[StageDict] = []
    ingredients: List[IngredientDict] = []

    for s in stage_rows:
        stage: StageDict = {
            "stageID": s[0],
            "recipeID": s[1],
            "stageTypeID": s[2],
            "stageOrder": s[3],
            "name": s[4],
            "instructions": s[5],
            "durationDays": s[6],
            "isOptional": bool(s[7]),
            "ingredients": [],
        }

        # Get ingredients for this stage
        cur.execute(
            """
            SELECT recipeIngredientID, itemID, amount, unit, timing, scalingMethod, notes
            FROM recipeIngredients
            WHERE stageID = ?
            """,
            (s[0],),
        )
        ing_rows = cur.fetchall()
        for ing in ing_rows:
            ing_dict: IngredientDict = {
                "recipeIngredientID": ing[0],
                "itemID": ing[1],
                "amount": ing[2],
                "unit": ing[3],
                "timing": ing[4],
                "scalingMethod": ing[5],
                "notes": ing[6],
                "stageID": s[0],
            }
            stage["ingredients"].append(ing_dict)
            ingredients.append(ing_dict)

        stages.append(stage)

    return {
        "recipe": recipe,
        "stages": stages,
        "ingredients": ingredients,
    }


def scale_recipe(recipe: RecipeData, desired_volume: float) -> RecipeData:
    """
    Return a new recipe dictionary with ingredient amounts scaled
    to match the desired batch size.
    """
    scale_factor = desired_volume / recipe["recipe"]["batchSizeL"]

    # Deep copy so we don’t mutate original
    scaled_recipe = copy.deepcopy(recipe)
    scaled_recipe["recipe"]["batchSizeL"] = desired_volume

    for stage in scaled_recipe["stages"]:
        for ing in stage["ingredients"]:
            if ing["scalingMethod"] == "linear":
                ing["amount"] *= scale_factor
            elif ing["scalingMethod"] == "fixed":
                pass  # leave unchanged
            elif ing["scalingMethod"] == "step":
                # example: 1 packet per 20 L
                packets = int((desired_volume - 1e-9) // 20) + 1
                ing["amount"] = packets
            else:
                raise ValueError(f"Unknown scaling method: {ing['scalingMethod']}")

    return scaled_recipe
