# conversions.py

from typing import Callable, Dict


# Categories of units
UNIT_CATEGORIES: Dict[str, list[str]] = {
    "alcohol": ["abv", "abw", "proof(us)", "proof(uk)"],
    "density": ["g/ml", "g/l", "kg/m3", "lb/gal(us)", "lb/gal(uk)", "lb/ft3", "sg", "brix", "plato", "oe", "tw"],
    "mass": ["mg", "g", "kg", "tonne", "gr", "dr", "oz", "lb", "ton"],
    "volume": ["ml", "l", "cl", "dl", "m3", "tsp", "tbsp", "fl_oz", "cup", "pt", "qt", "gal", "imp_fl_oz", "imp_pt", "imp_qt", "imp_gal"],
    "temperature": ["c", "k", "f"],
}

# ALCOHOL (base unit: ABV)
ALCOHOL_TO_ABV: Dict[str,float] = { 
    "abv": 1,
    "abw": 0.794,
    "proof(us)": 0.5,
    "proof(uk)": 0.5714285714,  # 1/1.75
}

def convert_alcohol(value: float, from_unit: str, to_unit: str) -> float:
    if from_unit not in ALCOHOL_TO_ABV or to_unit not in ALCOHOL_TO_ABV:
        raise ValueError(f"Unsupported alcohol unit: {from_unit} or {to_unit}")
    value_in_abv = value * ALCOHOL_TO_ABV[from_unit]
    return value_in_abv / ALCOHOL_TO_ABV[to_unit]

# DENSITY (base unit: g/L)
# Factor-based units
DENSITY_TO_G_L: Dict[str,float] = {
    "g/ml": 1000,
    "g/l": 1,
    "kg/m3": 1,              # same as g/L
    "lb/gal(us)": 119.826,   # US gallon
    "lb/gal(uk)": 99.7764,   # Imperial gallon
    "lb/ft3": 16.0185,       # pounds per cubic foot
}

# --- Complex brewing scales ---
def sg_to_gl(sg: float) -> float:
    return sg * 1000

def gl_to_sg(gl: float) -> float:
    return gl / 1000

def brix_to_gl(brix: float) -> float:
    sg = 1 + (brix / (258.6 - ((brix / 258.2) * 227.1)))
    return sg_to_gl(sg)

def gl_to_brix(gl: float) -> float:
    sg = gl_to_sg(gl)
    return (182.4601 * sg**3) - (775.6821 * sg**2) + (1262.7794 * sg) - 669.5622

def plato_to_gl(plato: float) -> float:
    return brix_to_gl(plato)

def gl_to_plato(gl: float) -> float:
    return gl_to_brix(gl)

def oe_to_gl(oe: float) -> float:
    sg = (oe / 1000) + 1
    return sg_to_gl(sg)

def gl_to_oe(gl: float) -> float:
    sg = gl_to_sg(gl)
    return (sg - 1) * 1000

def tw_to_gl(tw: float) -> float:
    return tw / 4

def gl_to_tw(gl: float) -> float:
    return gl * 4

DENSITY_COMPLEX: dict[str, tuple[Callable[[float], float], Callable[[float], float]]] = {
    "sg": (sg_to_gl, gl_to_sg),
    "brix": (brix_to_gl, gl_to_brix),
    "plato": (plato_to_gl, gl_to_plato),
    "oe": (oe_to_gl, gl_to_oe),
    "tw": (tw_to_gl, gl_to_tw),
}

def convert_density(value: float, from_unit: str, to_unit: str) -> float:
    # Step 1: to g/L
    if from_unit in DENSITY_TO_G_L:
        value_in_gl = value * DENSITY_TO_G_L[from_unit]
    elif from_unit in DENSITY_COMPLEX:
        to_gl, _ = DENSITY_COMPLEX[from_unit]
        value_in_gl = to_gl(value)
    elif from_unit == "tw" in DENSITY_COMPLEX:
        to_gl, _ = DENSITY_COMPLEX["tw"]
        value_in_gl = to_gl(value)
    else:
        raise ValueError(f"Unsupported density unit: {from_unit}")

    # Step 2: from g/L
    if to_unit in DENSITY_TO_G_L:
        return value_in_gl / DENSITY_TO_G_L[to_unit]
    elif to_unit in DENSITY_COMPLEX:
        _, from_gl = DENSITY_COMPLEX[to_unit]
        return from_gl(value_in_gl)
    else:
        raise ValueError(f"Unsupported density unit: {to_unit}")

# MASS (base unit: grams)
MASS_TO_G: Dict[str,float] = {
    "mg": 0.001,
    "g": 1,
    "kg": 1000,
    "tonne": 1_000_000,  # metric tonne
    "gr": 0.06479891,
    "dr": 1.7718451953125,
    "oz": 28.349523125,
    "lb": 453.59237,
    "ton": 907_184.74,    # US short ton
}

def convert_mass(value: float, from_unit: str, to_unit: str) -> float:
    if from_unit not in MASS_TO_G or to_unit not in MASS_TO_G:
        raise ValueError(f"Unsupported mass unit: {from_unit} or {to_unit}")
    value_in_g = value * MASS_TO_G[from_unit]
    return value_in_g / MASS_TO_G[to_unit]

# TEMPERATURE (base unit: °C)
def c_identity(x: float) -> float:
    return x

def c_to_k(x: float) -> float:
    return x + 273.15

def c_to_f(x: float) -> float:
    return x * 9 / 5 + 32

def f_to_c(x: float) -> float:
    return (x - 32) * 5 / 9

def k_to_c(x: float) -> float:
    return x - 273.15

def c_to_other(unit: str) -> Callable[[float], float]:
    return {
        "c": c_identity,
        "k": c_to_k,
        "f": c_to_f,
    }[unit]

def other_to_c(unit: str) -> Callable[[float], float]:
    return {
        "c": c_identity,
        "k": k_to_c,
        "f": f_to_c,
    }[unit]

def convert_temperature(value: float, from_unit: str, to_unit: str) -> float:
    if from_unit not in {"c", "k", "f"} or to_unit not in {"c", "k", "f"}:
        raise ValueError(f"Unsupported temperature unit: {from_unit} or {to_unit}")
    value_in_c = other_to_c(from_unit)(value)
    return c_to_other(to_unit)(value_in_c)

# VOLUME (base unit: liters)
VOLUME_TO_L: Dict[str,float] = {
    "ml": 0.001,
    "l": 1,
    "cl": 0.01,
    "dl": 0.1,
    "m3": 1000,
    "tsp": 0.00492892,    # US teaspoon
    "tbsp": 0.0147868,    # US tablespoon
    "fl_oz": 0.0295735,   # US fluid ounce
    "cup": 0.24,          # Metric cup
    "pt": 0.473176,       # US pint
    "qt": 0.946353,       # US quart
    "gal": 3.78541,       # US gallon
    "imp_fl_oz": 0.0284131, # Imperial fluid ounce
    "imp_pt": 0.568261,   # Imperial pint
    "imp_qt": 1.13652,    # Imperial quart
    "imp_gal": 4.54609,   # Imperial gallon
}

def convert_volume(value: float, from_unit: str, to_unit: str) -> float:
    if from_unit not in VOLUME_TO_L or to_unit not in VOLUME_TO_L:
        raise ValueError(f"Unsupported volume unit: {from_unit} or {to_unit}")
    value_in_ml = value * VOLUME_TO_L[from_unit]
    return value_in_ml / VOLUME_TO_L[to_unit]

# Unified conversion function
def convert(value: float, category: str, from_unit: str, to_unit: str) -> float:
    if category == "alcohol":
        return convert_alcohol(value, from_unit, to_unit)
    elif category == "density":
        return convert_density(value, from_unit, to_unit)
    elif category == "mass":
        return convert_mass(value, from_unit, to_unit)
    elif category == "temperature":
        return convert_temperature(value, from_unit, to_unit)
    elif category == "volume":
        return convert_volume(value, from_unit, to_unit)
    else:
        raise ValueError(f"Unsupported category: {category}")
    