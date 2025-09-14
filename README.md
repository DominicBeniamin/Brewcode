# Brewcode

Brewcode is a personal project to manage fruit wine, mead, and cider production.
It includes:

- Recipe creation and management
- Ingredients tracking
- Database schema for storing recipes, ingredients, and production stages
- Scripts for initializing and managing the database

## Files

- conversions.py – Unit and measurement conversion functions
- fermentation.py – Fermentation calculations and helpers
- recipe_manager.py – Recipe creation, editing, scaling, and saving functions
- init_db.py – Script to create the database tables
- data/schema/schema_01_ingredients_recipes.sql – SQL schema for ingredients and recipes

## Getting Started

1. Clone this repository:
git clone https://github.com/DominicBeniamin/Brewcode.git

2. Run init_db.py to create the database:
python init_db.py

3. Use the provided scripts for calculations and recipe management.

## Roadmap

- Add inventory management with FIFO costing
- Expand fermentation calculators
- Interactive frontend for recipe planning and batch tracking

## License

This project is licensed under the MIT License. See the LICENSE file for details.
