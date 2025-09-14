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

# Database connection helper
def create_db_connection(db_path: str = "brewcode.db") -> sqlite3.Connection:
    """
    Create a new SQLite database connection with foreign key support enabled.

    Args:
        db_path (str): Path to the SQLite database file. Defaults to 'brewcode.db'.

    Returns:
        sqlite3.Connection: Active database connection with foreign keys enforced.
    """
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

# Recipe management functions
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

def create_recipe(conn: sqlite3.Connection, recipe_data: RecipeData) -> int:
    """
    Insert a recipe and all its stages + ingredients into the database.

    Args:
        conn (sqlite3.Connection): Active SQLite database connection.
        recipe_data (RecipeData): Full recipe dictionary including stages and ingredients.

    Returns:
        int: The recipeID of the newly inserted recipe.
    """
    cur = conn.cursor()

    # --- Insert recipe ---
    recipe = recipe_data["recipe"]
    cur.execute(
        """
        INSERT INTO recipes (name, description, batchSizeL, notes)
        VALUES (?, ?, ?, ?)
        """,
        (recipe["name"], recipe["description"], recipe["batchSizeL"], recipe["notes"]),
    )
    recipe_id = cur.lastrowid
    if recipe_id is None:
        raise RuntimeError("Failed to retrieve recipe_id after insertion.")

    # --- Insert stages ---
    for stage in recipe_data["stages"]:
        cur.execute(
            """
            INSERT INTO recipeStages
                (recipeID, stageTypeID, stageOrder, name, instructions, durationDays, isOptional)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                recipe_id,
                stage["stageTypeID"],
                stage["stageOrder"],
                stage["name"],
                stage["instructions"],
                stage["durationDays"],
                int(stage["isOptional"]),
            ),
        )
        stage_id = cur.lastrowid

        # --- Insert ingredients for this stage ---
        for ing in stage["ingredients"]:
            cur.execute(
                """
                INSERT INTO recipeIngredients
                    (stageID, itemID, amount, unit, timing, scalingMethod, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    stage_id,
                    ing["itemID"],
                    ing["amount"],
                    ing["unit"],
                    ing["timing"],
                    ing["scalingMethod"],
                    ing["notes"],
                ),
            )

    conn.commit()
    return recipe_id


def save_recipe(conn: sqlite3.Connection, recipe_data: RecipeData) -> None:
    """Update an existing recipe, its stages, and ingredients in the database."""
    cur = conn.cursor()

    recipe = recipe_data["recipe"]
    cur.execute(
        """UPDATE recipes
           SET name = ?, description = ?, batchSizeL = ?, notes = ?
           WHERE recipeID = ?""",
        (
            recipe["name"],
            recipe["description"],
            recipe["batchSizeL"],
            recipe["notes"],
            recipe["recipeID"],
        ),
    )

    for stage in recipe_data["stages"]:
        cur.execute(
            """UPDATE recipeStages
               SET stageTypeID = ?, stageOrder = ?, name = ?,
                   instructions = ?, durationDays = ?, isOptional = ?
               WHERE stageID = ? AND recipeID = ?""",
            (
                stage["stageTypeID"],
                stage["stageOrder"],
                stage["name"],
                stage["instructions"],
                stage["durationDays"],
                int(stage["isOptional"]),
                stage["stageID"],
                recipe["recipeID"],
            ),
        )

        for ing in stage["ingredients"]:
            cur.execute(
                """UPDATE recipeIngredients
                   SET itemID = ?, amount = ?, unit = ?, timing = ?,
                       scalingMethod = ?, notes = ?
                   WHERE recipeIngredientID = ? AND stageID = ?""",
                (
                    ing["itemID"],
                    ing["amount"],
                    ing["unit"],
                    ing["timing"],
                    ing["scalingMethod"],
                    ing["notes"],
                    ing["recipeIngredientID"],
                    stage["stageID"],
                ),
            )

    conn.commit()
