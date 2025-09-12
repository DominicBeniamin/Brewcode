PRAGMA foreign_keys = ON;

-- ===== ITEM CATEGORIES =====
CREATE TABLE IF NOT EXISTS itemCategories (
  categoryID   INTEGER PRIMARY KEY,
  name         TEXT NOT NULL UNIQUE,
  description  TEXT
);

-- ===== ITEMS =====
CREATE TABLE IF NOT EXISTS items (
  itemID       INTEGER PRIMARY KEY,
  categoryID   INTEGER NOT NULL,
  name         TEXT NOT NULL,
  isActive     INTEGER DEFAULT 1,
  notes        TEXT,
  FOREIGN KEY (categoryID) REFERENCES itemCategories(categoryID)
);

-- ===== USAGE CONTEXTS =====
CREATE TABLE IF NOT EXISTS usageContexts (
  contextID    INTEGER PRIMARY KEY,
  name         TEXT NOT NULL UNIQUE,
  description  TEXT
);

-- Many-to-many: items ↔ usageContexts
CREATE TABLE IF NOT EXISTS itemUsageContexts (
  itemID     INTEGER NOT NULL,
  contextID  INTEGER NOT NULL,
  PRIMARY KEY (itemID, contextID),
  FOREIGN KEY (itemID) REFERENCES items(itemID),
  FOREIGN KEY (contextID) REFERENCES usageContexts(contextID)
);

-- Which contexts apply to which categories
CREATE TABLE IF NOT EXISTS categoryAllowedContexts (
  categoryID  INTEGER NOT NULL,
  contextID   INTEGER NOT NULL,
  PRIMARY KEY (categoryID, contextID),
  FOREIGN KEY (categoryID) REFERENCES itemCategories(categoryID),
  FOREIGN KEY (contextID) REFERENCES usageContexts(contextID)
);

-- ===== CATEGORY-SPECIFIC DETAIL TABLES ===== 

-- Fruits 
CREATE TABLE IF NOT EXISTS fruits ( 
  itemID        INTEGER PRIMARY KEY, 
  sugarContent  REAL,         -- g/100ml or similar 
  acidity       REAL,         -- pH or titratable acidity 
  FOREIGN KEY (itemID) REFERENCES items(itemID) 
); 
 
-- Grains & Malts 
CREATE TABLE IF NOT EXISTS grainsMalts ( 
  itemID        INTEGER PRIMARY KEY, 
  potentialSG   REAL,         -- e.g., PPG or °P contribution 
  colorSRM      REAL,         -- color contribution 
  FOREIGN KEY (itemID) REFERENCES items(itemID) 
); 
 
-- Honeys, Syrups, Sugars 
CREATE TABLE IF NOT EXISTS honeysSyrupsSugars ( 
  itemID        INTEGER PRIMARY KEY, 
  type          TEXT NOT NULL,   -- "Honey", "Syrup", or "Sugar" 
  fermentability REAL,           -- percentage fermentable 
  FOREIGN KEY (itemID) REFERENCES items(itemID) 
); 
 
-- Flavorants (spices, herbs, woods, extracts, acids, etc.) 
CREATE TABLE IF NOT EXISTS flavorants ( 
  itemID        INTEGER PRIMARY KEY, 
  type          TEXT,         -- e.g., spice, herb, wood, extract, acid 
  FOREIGN KEY (itemID) REFERENCES items(itemID) 
); 

-- Hops (specialized flavorant) 
CREATE TABLE IF NOT EXISTS hops ( 
  itemID        INTEGER PRIMARY KEY, 
  alphaAcid     REAL,         -- bitterness potential (%) 
  betaAcid      REAL,         -- optional, for flavor balance 
  form          TEXT,         -- pellet, whole leaf, cryo, extract 
  FOREIGN KEY (itemID) REFERENCES items(itemID) 
); 

-- Bottles (packaging) 
CREATE TABLE IF NOT EXISTS bottles ( 
  itemID        INTEGER PRIMARY KEY, 
  capacityML    REAL,         -- volume capacity 
  color         TEXT,         -- e.g., brown, green, clear 
  FOREIGN KEY (itemID) REFERENCES items(itemID) 
); 

-- Closures (corks, caps, screw caps) 
CREATE TABLE IF NOT EXISTS closures ( 
  itemID        INTEGER PRIMARY KEY, 
  type          TEXT,         -- cork, crown cap, screw cap 
  size          TEXT,         -- e.g., 26mm, #9 cork 
  FOREIGN KEY (itemID) REFERENCES items(itemID) 
); 

-- Other Packaging (labels, boxes, etc.) 
CREATE TABLE IF NOT EXISTS otherPackaging ( 
  itemID        INTEGER PRIMARY KEY, 
  type          TEXT,         -- label, shrink wrap, carrier, box 
  material      TEXT,         -- paper, plastic, cardboard 
  FOREIGN KEY (itemID) REFERENCES items(itemID) 
); 
 
-- Additives (nutrients, salts, stabilisers)) 
CREATE TABLE IF NOT EXISTS additives ( 
  itemID        INTEGER PRIMARY KEY, 
  purpose       TEXT,         -- e.g., "nutrient", "salt", "stabiliser" 
  dosage        TEXT,         -- recommended dosage or usage 
  FOREIGN KEY (itemID) REFERENCES items(itemID) 
); 
 
-- Cleaners & Sanitisers 
CREATE TABLE IF NOT EXISTS cleanersSanitisers ( 
  itemID        INTEGER PRIMARY KEY, 
  type          TEXT,         -- cleaner or sanitiser 
  dosage        TEXT,         -- recommended dosage or usage 
  FOREIGN KEY (itemID) REFERENCES items(itemID) 
); 
 
-- Yeasts & Microbes 
CREATE TABLE IF NOT EXISTS yeastsMicrobes ( 
  itemID        INTEGER PRIMARY KEY, 
  strain        TEXT,         -- yeast strain or microbial species 
  form          TEXT,         -- liquid, dry, slurry 
  attenuation   REAL,         -- expected attenuation percentage 
  alcoholTolerance REAL,      -- max alcohol tolerance percentage 
  malolactic    INTEGER,      -- 1 if capable of malolactic fermentation, else 0 
  FOREIGN KEY (itemID) REFERENCES items(itemID) 
); 


-- ===== RECIPES =====
-- Stage Types (system-defined, not user editable)
CREATE TABLE IF NOT EXISTS stageTypes (
  stageTypeID   INTEGER PRIMARY KEY,
  name          TEXT NOT NULL,        -- e.g., "Primary", "Stabilise", "Bottling"
  description   TEXT,
  isRequired    INTEGER NOT NULL,     -- 1 = always required
  requiresStage INTEGER,              -- dependency (FK to another stageTypeID)
  excludesStage INTEGER               -- stage that becomes invalid if this is chosen
);

-- Recipes (the templates)
CREATE TABLE IF NOT EXISTS recipes (
  recipeID      INTEGER PRIMARY KEY,
  name          TEXT NOT NULL,
  description   TEXT,
  batchSizeL    REAL,         -- typical target size in liters
  notes         TEXT
);

-- Recipe Stages (ordered steps)
CREATE TABLE IF NOT EXISTS recipeStages (
  stageID       INTEGER PRIMARY KEY,
  recipeID      INTEGER NOT NULL,
  stageTypeID   INTEGER NOT NULL,  -- link to stageTypes
  stageOrder    INTEGER NOT NULL,  -- sequence within recipe
  name          TEXT NOT NULL,     -- e.g., "Primary", "Stabilise", "Clearing"
  instructions  TEXT,              -- guidance for this stage
  durationDays  INTEGER,          -- typical duration in days
  isOptional    INTEGER DEFAULT 0, -- 1 = optional stage
  FOREIGN KEY (recipeID) REFERENCES recipes(recipeID)
  FOREIGN KEY (stageTypeID) REFERENCES stageTypes(stageTypeID
);

-- Recipe Ingredients (per stage)
CREATE TABLE IF NOT EXISTS recipeIngredients (
  recipeIngredientID INTEGER PRIMARY KEY,
  stageID       INTEGER NOT NULL,
  itemID        INTEGER NOT NULL,     -- link to items (fruit, honey, yeast, etc.)
  amount        REAL,                 -- base amount for recipe batch size
  unit          TEXT,                 -- g, kg, L, tsp, etc.
  timing        TEXT,                 -- optional e.g. "at start", "after 3 days"
  scalingMethod TEXT NOT NULL DEFAULT 'linear',  
  -- how to scale when batch size changes
  -- e.g. 'linear' (factor = newVol/originalVol),
  --      'fixed' (always same amount, e.g. yeast packet),
  --      'step' (scale in steps, e.g. 1 packet per 20 L)
  notes         TEXT,
  FOREIGN KEY (stageID) REFERENCES recipeStages(stageID),
  FOREIGN KEY (itemID) REFERENCES items(itemID)
);


-- ===== SEED DATA ===== 
-- Categories 
INSERT OR IGNORE INTO itemCategories (name, description) VALUES 
  ('Fruits', 'Fresh or processed fruits used in fermentation or flavoring'), 
  ('Grains & Malts', 'Base malts, specialty malts, and adjunct grains'), 
  ('Honeys, Syrups & Sugars', 'Sweeteners of various types'), 
  ('Flavorants', 'Spices, herbs, woods, and extracts (excluding hops)'), 
  ('Hops', 'Hop varieties used for bitterness, flavor, and aroma'), 
  ('Bottles', 'Glass or plastic bottles used for packaging'), 
  ('Closures', 'Corks, caps, screw caps used to seal bottles'), 
  ('Other Packaging', 'Labels, carriers, boxes, and other packaging materials'), 
  ('Additives', 'Nutrients, salts, stabilisers'), 
  ('Cleaners & Sanitisers', 'Cleaning and sanitising agents'), 
  ('Yeasts & Microbes', 'Yeast strains and microbial cultures'); 
 
-- Usage Contexts 
INSERT OR IGNORE INTO usageContexts (name, description) VALUES
  ('fermentable', 'Provides fermentable sugars'),
  ('primer', 'Used for priming carbonation'),
  ('nonfermentable', 'Adds flavor or body without fermenting'),
  ('nutrient', 'Provides nutrients for yeast or microbes'),
  ('salt', 'Used to adjust ionic strength or water chemistry'),
  ('cleaner', 'Used to clean equipment'),
  ('sanitiser', 'Used to sanitise equipment'),
  ('stabiliser', 'Inhibits microbial activity or stabilises product'),
  ('fining', 'Used to clarify and remove particulates'),
  ('packaging', 'Used to package the final product'),
  ('fermenter', 'Yeast or microbes that perform fermentation');

-- ===== CATEGORY ALLOWED CONTEXTS =====
INSERT OR IGNORE INTO categoryAllowedContexts (categoryID, contextID)
SELECT c.categoryID, u.contextID
FROM itemCategories c, usageContexts u
WHERE 
  -- Fruits
  (c.name = 'Fruits' AND u.name IN ('fermentable', 'primer')) OR

  -- Grains & Malts
  (c.name = 'Grains & Malts' AND u.name IN ('fermentable', 'primer')) OR

  -- Honeys, Syrups & Sugars
  (c.name = 'Honeys, Syrups & Sugars' AND u.name IN ('fermentable', 'primer')) OR

  -- Flavorants
  (c.name = 'Flavorants' AND u.name = 'nonfermentable') OR

  -- Hops
  (c.name = 'Hops' AND u.name = 'nonfermentable') OR

  -- Yeasts & Microbes
  (c.name = 'Yeasts & Microbes' AND u.name = 'fermenter') OR

  -- Additives
  (c.name = 'Additives' AND u.name IN ('nutrient', 'salt', 'stabiliser', 'fining')) OR

  -- Cleaners & Sanitisers
  (c.name = 'Cleaners & Sanitisers' AND u.name IN ('cleaner', 'sanitiser')) OR

  -- Bottles
  (c.name = 'Bottles' AND u.name = 'packaging') OR

  -- Closures
  (c.name = 'Closures' AND u.name = 'packaging') OR

  -- Other Packaging
  (c.name = 'Other Packaging' AND u.name = 'packaging');

-- ===== STAGE TYPES =====
INSERT OR IGNORE INTO stageTypes 
(stageTypeID, name, description, isRequired, requiresStage, excludesStage) VALUES
(1, 'Must Preparation', 'Prepare the must (mix ingredients, measure SG/pH)', 1, NULL, NULL),
(2, 'Fermentation', 'Active fermentation with yeast/microbes', 1, 1, NULL),
(3, 'Malolactic Fermentation', 'Secondary microbial fermentation to reduce acidity', 0, 2, NULL),
(4, 'Stabilisation', 'Prevent further fermentation (chemical, pasteurisation, etc.)', 0, 2, 7),
(5, 'Back Sweeten', 'Add sugars/sweeteners after stabilisation', 0, 4, NULL),
(6, 'Clarification & Aging', 'Fining, clearing, or bulk aging for stability and clarity', 0, 2, NULL),
(7, 'Priming', 'Add fermentables before bottling for carbonation', 0, 2, 4),
(8, 'Bottling', 'Final packaging of the beverage into bottles', 1, 2, NULL);
