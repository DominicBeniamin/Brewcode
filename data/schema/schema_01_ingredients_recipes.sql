PRAGMA foreign_keys = ON;

-- ===== INGREDIENT TAXONOMY =====
CREATE TABLE IF NOT EXISTS ingredientCategories (
  categoryID     INTEGER PRIMARY KEY,
  name           TEXT NOT NULL,
  description    TEXT
);

CREATE TABLE IF NOT EXISTS ingredientSubcategories (
  subcategoryID  INTEGER PRIMARY KEY,
  categoryID     INTEGER NOT NULL,
  name           TEXT NOT NULL,
  description    TEXT,
  FOREIGN KEY (categoryID) REFERENCES ingredientCategories(categoryID)
);

-- ===== INGREDIENTS =====
-- Store only physically storable items. Inventory tracking can be off per item.
CREATE TABLE IF NOT EXISTS ingredients (
  ingredientID        INTEGER PRIMARY KEY,
  name                TEXT NOT NULL,
  categoryID          INTEGER NOT NULL,
  subcategoryID       INTEGER,
  unit                TEXT,                    -- e.g., kg, g, L, ml (optional now)
  onDemand            INTEGER DEFAULT 0,       -- e.g., tap water
  isInventoryTracked  INTEGER DEFAULT 1,       -- 0 = reference-only, no stock tracking
  isActive            INTEGER DEFAULT 1,       -- soft delete
  notes               TEXT,
  FOREIGN KEY (categoryID)    REFERENCES ingredientCategories(categoryID),
  FOREIGN KEY (subcategoryID) REFERENCES ingredientSubcategories(subcategoryID)
);

-- ===== SUBSTITUTE GROUPS =====
CREATE TABLE IF NOT EXISTS ingredientSubstituteGroups (
  substituteGroupID INTEGER PRIMARY KEY,
  name              TEXT NOT NULL,
  notes             TEXT
);

CREATE TABLE IF NOT EXISTS ingredientSubstituteGroupMembers (
  substituteGroupID INTEGER NOT NULL,
  ingredientID      INTEGER NOT NULL,
  isPreferred       INTEGER DEFAULT 0,
  PRIMARY KEY (substituteGroupID, ingredientID),
  FOREIGN KEY (substituteGroupID) REFERENCES ingredientSubstituteGroups(substituteGroupID),
  FOREIGN KEY (ingredientID)      REFERENCES ingredients(ingredientID)
);

-- ===== RECIPES =====
CREATE TABLE IF NOT EXISTS recipes (
  recipeID     INTEGER PRIMARY KEY,
  name         TEXT NOT NULL,
  beverageType TEXT NOT NULL,                 -- Wine | Mead | Cider
  description  TEXT,
  createdAt    DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Stages are the workflow containers (instructions live in description).
CREATE TABLE IF NOT EXISTS recipeStages (
  recipeStageID INTEGER PRIMARY KEY,
  recipeID      INTEGER NOT NULL,
  stageOrder    INTEGER NOT NULL,
  name          TEXT NOT NULL,                -- e.g., "Prepare Must"
  description   TEXT,                         -- free-text instructions
  FOREIGN KEY (recipeID) REFERENCES recipes(recipeID)
);

-- Each stage can demand either a specific ingredient OR a substitutable group.
CREATE TABLE IF NOT EXISTS recipeStageIngredients (
  recipeStageIngredientID INTEGER PRIMARY KEY,
  recipeStageID           INTEGER NOT NULL,
  ingredientID            INTEGER,            -- specific ingredient
  substituteGroupID       INTEGER,            -- OR group of substitutes
  amount                  REAL,
  unit                    TEXT,
  required                INTEGER DEFAULT 1,  -- 0 = optional
  notes                   TEXT,
  FOREIGN KEY (recipeStageID)     REFERENCES recipeStages(recipeStageID),
  FOREIGN KEY (ingredientID)      REFERENCES ingredients(ingredientID),
  FOREIGN KEY (substituteGroupID) REFERENCES ingredientSubstituteGroups(substituteGroupID),
  -- Exactly one of (ingredientID, substituteGroupID) must be provided:
  CHECK ( (ingredientID IS NOT NULL) <> (substituteGroupID IS NOT NULL) )
);

-- ===== Helpful indexes =====
CREATE INDEX IF NOT EXISTS idx_ingredients_category
  ON ingredients(categoryID, subcategoryID);

CREATE INDEX IF NOT EXISTS idx_stageingredients_stage
  ON recipeStageIngredients(recipeStageID);

CREATE INDEX IF NOT EXISTS idx_groupmembers_ingredient
  ON ingredientSubstituteGroupMembers(ingredientID);
