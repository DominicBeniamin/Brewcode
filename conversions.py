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

# User-facing labels for dropdowns / UI
ALCOHOL_LABELS: Dict[str, str] = {
    "abv": "ABV",
    "abw": "ABW",
    "proof(us)": "Proof (US)",
    "proof(uk)": "Proof (UK)",
}

DENSITY_LABELS: dict[str, str] = {
    "sg": "Specific Gravity (SG)",
    "brix": "°Bx (Brix)",
    "plato": "°P (Plato)",
    "oe": "°Oe (Oechsle)",
    "tw": "°Tw (Twaddell)",
    "g/ml": "g/mL",
    "g/l": "g/L",
    "kg/m3": "kg/m³",
    "lb/gal(us)": "lb/gal (US)",
    "lb/gal(uk)": "lb/gal (UK)",
    "lb/ft3": "lb/ft³",
}

MASS_LABELS: Dict[str, str] = {
    "mg": "mg",
    "g": "g",
    "kg": "kg",
    "tonne": "t",
    "gr": "gr",
    "dr": "dr",
    "oz": "oz",
    "lb": "lb",
    "ton": "ton",
}

VOLUME_LABELS: Dict[str, str] = {
    "ml": "mL",
    "l": "L",
    "cl": "cL",
    "dl": "dL",
    "m3": "m³",
    "tsp": "tsp",
    "tbsp": "tbsp",
    "fl_oz": "fl oz",
    "cup": "cup",
    "pt": "pt",
    "qt": "qt",
    "gal": "gal",
    "imp_fl_oz": "imp fl oz",
    "imp_pt": "imp pt",
    "imp_qt": "imp qt",
    "imp_gal": "imp gal",
}

TEMP_LABELS = {
    "c": "°C",
    "f": "°F",
    "k": "K",
}

# Helper functions
def build_label_to_key(labels: dict[str, str]) -> dict[str, str]:
    """
    Build a reverse lookup dictionary (label → key) from a label mapping (key → label).
    """
    return {label: key for key, label in labels.items()}

def normalise_unit(unit: str, labels: dict[str, str]) -> str:
    """
    Normalise a unit string to its internal key.
    
    Accepts either:
      - the internal key (e.g. "g/l")
      - the user-facing label (e.g. "g/L")
    
    Parameters
    ----------
    unit : str
        The unit to normalize.
    labels : dict[str, str]
        Mapping of internal keys to user-facing labels.

    Returns
    -------
    str
        The normalized internal key.
    """
    if unit in labels:  # already a key
        return unit
    label_to_key = build_label_to_key(labels)
    if unit in label_to_key:
        return label_to_key[unit]
    raise ValueError(f"Unsupported unit: {unit}")


# ALCOHOL (base unit: ABV)
# ----------------------------
# ALCOHOL CONTENT (base unit: ABV)
# ----------------------------

# Conversion factors to ABV
ALCOHOL_TO_ABV: Dict[str, float] = {
    "abv": 1,
    "abw": 0.794,             # ABW → ABV: multiply by 0.794
    "proof(us)": 0.5,         # US proof → ABV: multiply by 0.5
    "proof(uk)": 0.5714285714 # UK proof → ABV: multiply by 1/1.75
}


def convert_alcohol(value: float, from_unit: str, to_unit: str) -> float:
    """
    Convert an alcohol content value between ABV, ABW, and proof scales.

    Parameters
    ----------
    value : float
        The numeric alcohol content to convert.
    from_unit : str
        Unit of the input value. Can be a key (e.g., "abv") or user-facing label (e.g., "ABV").
    to_unit : str
        Unit to convert to. Same options as `from_unit`.

    Returns
    -------
    float
        Converted alcohol content in the requested unit.

    Raises
    ------
    ValueError
        If either `from_unit` or `to_unit` is not recognised.
    """
    # Step 1: Normalise units
    from_unit = normalise_unit(from_unit, ALCOHOL_LABELS)
    to_unit = normalise_unit(to_unit, ALCOHOL_LABELS)

    # Step 2: Check validity
    if from_unit not in ALCOHOL_TO_ABV or to_unit not in ALCOHOL_TO_ABV:
        raise ValueError(f"Unsupported alcohol unit: {from_unit} or {to_unit}")

    # Step 3: Convert
    value_in_abv = value * ALCOHOL_TO_ABV[from_unit]
    return value_in_abv / ALCOHOL_TO_ABV[to_unit]


# DENSITY (base unit: g/L)

# --- Factor-based units (simple scaling) ---
# These are direct multipliers to/from g/L.
DENSITY_TO_G_L: dict[str, float] = {
    "g/ml": 1000,       # grams per millilitre
    "g/l": 1,           # grams per litre (base unit)
    "kg/m3": 1,         # kilograms per cubic metre (same as g/L)
    "lb/gal(us)": 119.826,   # pounds per US gallon
    "lb/gal(uk)": 99.7764,   # pounds per Imperial gallon
    "lb/ft3": 16.0185,       # pounds per cubic foot
}


# --- Complex brewing scales (empirical formulas) ---

def sg_to_gl(sg: float) -> float:
    """Convert Specific Gravity (SG, dimensionless) to density in g/L."""
    return sg * 1000


def gl_to_sg(gl: float) -> float:
    """Convert density in g/L to Specific Gravity (SG, dimensionless)."""
    return gl / 1000


def brix_to_gl(brix: float) -> float:
    """Convert degrees Brix (°Bx) to density in g/L using an empirical SG relation."""
    sg = 1 + (brix / (258.6 - ((brix / 258.2) * 227.1)))
    return sg_to_gl(sg)


def gl_to_brix(gl: float) -> float:
    """Convert density in g/L to degrees Brix (°Bx) using a cubic polynomial."""
    sg = gl_to_sg(gl)
    return (182.4601 * sg**3) - (775.6821 * sg**2) + (1262.7794 * sg) - 669.5622


def plato_to_gl(plato: float) -> float:
    """Convert degrees Plato (°P) to density in g/L. (Equivalent to °Bx.)"""
    return brix_to_gl(plato)


def gl_to_plato(gl: float) -> float:
    """Convert density in g/L to degrees Plato (°P). (Equivalent to °Bx.)"""
    return gl_to_brix(gl)


def oe_to_gl(oe: float) -> float:
    """Convert degrees Oechsle (°Oe) to density in g/L.
    
    Definition: °Oe = (SG - 1) * 1000
    Example: SG 1.075 → 75 °Oe
    """
    sg = (oe / 1000) + 1
    return sg_to_gl(sg)


def gl_to_oe(gl: float) -> float:
    """Convert density in g/L to degrees Oechsle (°Oe)."""
    sg = gl_to_sg(gl)
    return (sg - 1) * 1000


def tw_to_gl(tw: float) -> float:
    """Convert degrees Twaddell (°Tw) to density in g/L.
    
    Definition: SG = 1 + (°Tw / 200)
    """
    sg = 1 + (tw / 200)
    return sg_to_gl(sg)


def gl_to_tw(gl: float) -> float:
    """Convert density in g/L to degrees Twaddell (°Tw)."""
    sg = gl_to_sg(gl)
    return (sg - 1) * 200


# Registry of complex conversions
DENSITY_COMPLEX: dict[str, tuple[Callable[[float], float], Callable[[float], float]]] = {
    "sg": (sg_to_gl, gl_to_sg),
    "brix": (brix_to_gl, gl_to_brix),
    "plato": (plato_to_gl, gl_to_plato),
    "oe": (oe_to_gl, gl_to_oe),
    "tw": (tw_to_gl, gl_to_tw),
}


def convert_density(value: float, from_unit: str, to_unit: str) -> float:
    """
    Convert a density value between different units.

    Parameters
    ----------
    value : float
        The numeric value to convert.
    from_unit : str
        The unit of the input value (must be a key in DENSITY_TO_G_L or DENSITY_COMPLEX).
    to_unit : str
        The unit to convert to (same requirement as from_unit).

    Returns
    -------
    float
        Converted value in the requested unit.
    """
    # Step 1: Normalise units
    from_unit = normalise_unit(from_unit, DENSITY_LABELS)
    to_unit = normalise_unit(to_unit, DENSITY_LABELS)

    # Step 2: Convert to g/L
    if from_unit in DENSITY_TO_G_L:
        value_in_gl = value * DENSITY_TO_G_L[from_unit]
    elif from_unit in DENSITY_COMPLEX:
        to_gl, _ = DENSITY_COMPLEX[from_unit]
        value_in_gl = to_gl(value)
    else:
        raise ValueError(f"Unsupported density unit: {from_unit}")

    # Step 3: Convert from g/L
    if to_unit in DENSITY_TO_G_L:
        return value_in_gl / DENSITY_TO_G_L[to_unit]
    elif to_unit in DENSITY_COMPLEX:
        _, from_gl = DENSITY_COMPLEX[to_unit]
        return from_gl(value_in_gl)
    else:
        raise ValueError(f"Unsupported density unit: {to_unit}")

# MASS (base unit: grams)

# Conversion factors to grams
MASS_TO_G: Dict[str, float] = {
    "mg": 0.001,
    "g": 1,
    "kg": 1000,
    "tonne": 1_000_000,      # metric tonne
    "gr": 0.06479891,         # grain
    "dr": 1.7718451953125,    # dram
    "oz": 28.349523125,       # ounce
    "lb": 453.59237,          # pound
    "ton": 907_184.74,        # US short ton
}

def convert_mass(value: float, from_unit: str, to_unit: str) -> float:
    """
    Convert a mass value between different units.

    Parameters
    ----------
    value : float
        The numeric mass to convert.
    from_unit : str
        Unit of the input value. Can be a key (e.g., "g") or user-facing label (e.g., "kg").
    to_unit : str
        Unit to convert to. Same options as `from_unit`.

    Returns
    -------
    float
        The converted mass in the requested unit.

    Raises
    ------
    ValueError
        If either `from_unit` or `to_unit` is not recognised.
    """
    # Step 1: Normalise units
    from_unit = normalise_unit(from_unit, MASS_LABELS)
    to_unit = normalise_unit(to_unit, MASS_LABELS)

    # Step 2: Check validity
    if from_unit not in MASS_TO_G or to_unit not in MASS_TO_G:
        raise ValueError(f"Unsupported mass unit: {from_unit} or {to_unit}")

    # Step 3: Convert
    value_in_g = value * MASS_TO_G[from_unit]
    return value_in_g / MASS_TO_G[to_unit]



# TEMPERATURE (base unit: °C)

# Functions for each conversion
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

# Centralised dictionaries
OTHER_TO_C: dict[str, Callable[[float], float]] = {
    "c": c_identity,
    "k": k_to_c,
    "f": f_to_c,
}

C_TO_OTHER: dict[str, Callable[[float], float]] = {
    "c": c_identity,
    "k": c_to_k,
    "f": c_to_f,
}

# Step 3: conversion function
def convert_temperature(value: float, from_unit: str, to_unit: str) -> float:
    """
    Convert a temperature value between Celsius, Kelvin, and Fahrenheit.

    Parameters
    ----------
    value : float
        The numeric temperature value to convert.
    from_unit : str
        The unit of the input value. Accepted units: "c", "k", "f" or labels that normalise to them.
    to_unit : str
        The unit to convert to. Accepted units: "c", "k", "f" or labels that normalise to them.

    Returns
    -------
    float
        The converted temperature in the requested unit.

    Raises
    ------
    ValueError
        If either `from_unit` or `to_unit` is not recognised after normalisation.
    """
    # Step 1: Normalise units
    from_unit = normalise_unit(from_unit, TEMP_LABELS)
    to_unit = normalise_unit(to_unit, TEMP_LABELS)

    # Step 2: Check validity
    if from_unit not in OTHER_TO_C or to_unit not in C_TO_OTHER:
        raise ValueError(f"Unsupported temperature unit: {from_unit} or {to_unit}")

    # Step 3: Convert
    value_in_c = OTHER_TO_C[from_unit](value)
    return C_TO_OTHER[to_unit](value_in_c)


# VOLUME (base unit: liters)

# Conversion factors to liters
VOLUME_TO_L: Dict[str, float] = {
    "ml": 0.001,
    "l": 1,
    "cl": 0.01,
    "dl": 0.1,
    "m3": 1000,
    "tsp": 0.00492892,      # US teaspoon
    "tbsp": 0.0147868,      # US tablespoon
    "fl_oz": 0.0295735,     # US fluid ounce
    "cup": 0.24,            # Metric cup
    "pt": 0.473176,         # US pint
    "qt": 0.946353,         # US quart
    "gal": 3.78541,         # US gallon
    "imp_fl_oz": 0.0284131, # Imperial fluid ounce
    "imp_pt": 0.568261,     # Imperial pint
    "imp_qt": 1.13652,      # Imperial quart
    "imp_gal": 4.54609,     # Imperial gallon
}

def convert_volume(value: float, from_unit: str, to_unit: str) -> float:
    """
    Convert a volume value between different units.

    Parameters
    ----------
    value : float
        The numeric volume to convert.
    from_unit : str
        Unit of the input value. Can be a key (e.g., "ml") or user-facing label (e.g., "mL").
    to_unit : str
        Unit to convert to. Same options as `from_unit`.

    Returns
    -------
    float
        The converted volume in the requested unit.

    Raises
    ------
    ValueError
        If either `from_unit` or `to_unit` is not recognised.
    """
    # Step 1: Normalise units
    from_unit = normalise_unit(from_unit, VOLUME_LABELS)
    to_unit = normalise_unit(to_unit, VOLUME_LABELS)

    # Step 2: Check validity
    if from_unit not in VOLUME_TO_L or to_unit not in VOLUME_TO_L:
        raise ValueError(f"Unsupported volume unit: {from_unit} or {to_unit}")

    # Step 3: Convert
    value_in_l = value * VOLUME_TO_L[from_unit]
    return value_in_l / VOLUME_TO_L[to_unit]


# Mapping of categories to conversion functions
CONVERSION_FUNCTIONS: dict[str, Callable[[float, str, str], float]] = {
    "alcohol": convert_alcohol,
    "density": convert_density,
    "mass": convert_mass,
    "temperature": convert_temperature,
    "volume": convert_volume,
}

def convert(category: str, from_unit: str, to_unit: str, value: float) -> float:
    """
    Unified conversion function for alcohol, density, mass, temperature, and volume.

    Parameters
    ----------
    category : str
        The category of the unit ("alcohol", "density", "mass", "temperature", "volume").
    from_unit : str
        Unit of the input value.
    to_unit : str
        Unit to convert to.
    value : float
        The numeric value to convert.

    Returns
    -------
    float
        The converted value in the requested unit.

    Raises
    ------
    ValueError
        If the category is unsupported.
    """
    category = category.lower()  # normalise category input
    if category not in CONVERSION_FUNCTIONS:
        raise ValueError(f"Unsupported category: {category}")

    return CONVERSION_FUNCTIONS[category](value, from_unit, to_unit)
