# main.py

from fermentation import abv#, corrected_gravity, priming
from conversions import convert, UNIT_CATEGORIES, DENSITY_COMPLEX

# Helper functions
def format_formula_name(name: str) -> str:
    return name.upper() if name == "hmrc" else name.capitalize()

def get_float(prompt: str) -> float:
    while True:
        try:
            return float(input(prompt).strip())
        except ValueError:
            print("Invalid input. Please enter a numeric value.")


# Menu functions
def abv_menu() -> None:
    
    formulas = ["basic", "berry", "hall", "hmrc"]
    scales: list[str] = list(DENSITY_COMPLEX.keys())
    
    while True:
        print("\n--ABV Calculator Menu--")
        print("Select 'Back' to return to the main menu.")

        # Step 1: Formula Selection
        formula = str(input(f"Select formula ({', '.join(formulas)}): ").strip().lower())
        if formula == "back":
            break  
        if formula not in formulas:
            print("Invalid formula. Try again.")
            continue

        # Step 2: Scale Selection
        scale = str(input(f"Select scale ({', '.join(scales)}): ").strip().lower())
        if scale == "back":
            break
        if scale not in scales:
            print("Invalid scale. Try again.")
            continue

        # Step 3: Input Values
        try:
            original = float(input(f"Enter original reading ({scale}): ").strip())
            final = float(input(f"Enter final reading ({scale}): ").strip())
        except ValueError:
            print("Invalid number. Try again.")
            continue

        # Step 4: Temperature Correction (Optional)
        temp_correction = input("Apply temperature correction? (y/n): ").strip().lower()
        tr_og = tr_fg = calibration_temperature = None
        temp_scale = None

        if temp_correction.startswith("y"):
        
            while True:
                temp_scale = input("Enter temperature scale (C/F): ").strip().upper()
                if temp_scale in ("C", "F"):
                    break
                print("Invalid input. Please enter 'C' or 'F'.")


        tr_og = get_float(input("Enter the temperature of the original reading: "))
        tr_fg = get_float(input("Enter the temperature of the final reading: "))
        calibration_temperature = get_float(input(f"Enter the calibration temperature ({temp_scale}): "))

        # Step 5: Calculate ABV
        try:
            result = abv(
                original = original,
                final = final,
                scale = scale,
                formula = formula,
                tr_og = tr_og,
                tr_fg = tr_fg,
                calibration_temperature = calibration_temperature,
                temp_scale = temp_scale
            )
            print(f"ABV ({format_formula_name(formula)} formula): {result:.2f}%")
        except Exception as e:
            print(f"Calculation failed: {e}")


def gravity_adjustment_menu() -> None:
    scales: list[str] = list(DENSITY_COMPLEX.keys())

    while True:    
        print("\n--Gravity Corrector Menu--")
        print("Select 'Back' to return to the main menu.")

        # Step 1: Density and Temperature Scales Selection
        
        scale = str(input(f"Select scale ({', '.join(scales)}): ").strip().lower())
        if scale == "back":
                break
        if scale not in scales:
            print("Invalid scale. Try again.")
            continue

        temp_scale = input("Enter temperature scale (C/F): ").strip().upper()
        if temp_scale not in ("C", "F"):
            print("Invalid input. Please enter 'C' or 'F'.")
            continue

        # Step 2: Input Values
        try:
            reading: float = float(input(f"Enter gravity reading ({scale}): ").strip())
            reading_temp: float = float(input("Enter the temperature of the reading: ").strip())   
            calibration_temp: float = float(input(f"Enter the calibration temperature ({temp_scale}): ").strip())
        except ValueError:
            print("Invalid number. Try again.")
            continue

        # Step 3: Convert Values
        try:
            
        


def conversions_menu() -> None:
    while True:
        print("\n--Conversions Menu--")
        print("Select 'Back' to return to the main menu.")

        # Step 1: Category
        category = input(f"Enter category ({', '.join(UNIT_CATEGORIES.keys())}): ").strip().lower()
        if category == "back":
            break
        if category not in UNIT_CATEGORIES:
            print("Invalid category. Try again.")
            continue

        # Step 2: Value
        try:
            value = float(input("Enter value to convert: ").strip())
        except ValueError:
            print("Invalid number. Try again.")
            continue

        # Step 3: From unit
        from_unit = input(f"Enter from unit ({', '.join(UNIT_CATEGORIES[category])}): ").strip().lower()
        if from_unit not in UNIT_CATEGORIES[category]:
            print("Invalid from unit. Try again.")
            continue

        # Step 4: To unit
        to_unit = input(f"Enter to unit ({', '.join(UNIT_CATEGORIES[category])}): ").strip().lower()
        if to_unit not in UNIT_CATEGORIES[category]:
            print("Invalid to unit. Try again.")
            continue

        # Step 5: Convert 
        try: 
            result = convert(category, from_unit, to_unit, value)  # <-- corrected order
            precision = 2 if category in {"alcohol", "temperature"} else 3 
            print(f"{value} {from_unit} ({category}) = {result:.{precision}f} {to_unit}") 
        except Exception as e: 
            print(f"Conversion failed: {e}")


def main() -> None:
    print("Welcome to BrewCode!")

while True:
    print("\n--Main Menu--")
    print("1. ABV Calculator")
    print("2. Gravity Corrector")
    print("3. Priming Calculator")
    print("4. Unit Converter")
    print("5. Exit")

    choice = input("Select an option: ").strip().lower()

    if choice == '1':
        print("Coming soon")
    elif choice == '2':
        print("Coming soon")
    elif choice == '3':
        print("Coming soon")
    elif choice == '4':
        conversions_menu()
    elif choice == '5':
        print("Exiting BrewCode. Cheers!")
    else:
        print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()