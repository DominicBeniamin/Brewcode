# conversions.py
"""
Module for unit conversions related to brewing (alcohol content, density, mass, temperature, volume).
"""

from typing import Callable, Dict, NamedTuple


# Helper functions
def normalise_unit(unit: str, category: str) -> str:
    """
    Normalise a user-facing unit label or key into its canonical internal unit key.

    Parameters
    ----------
    unit : str
        The unit string provided by the user (can be a key like "sg" or a label like "Specific Gravity (SG)").
    category : str
        The category of the unit ("alcohol", "density", "mass", "temperature", "volume").

    Returns
    -------
    str
        The normalised unit key (e.g., "sg", "c", "abv").

    Raises
    ------
    ValueError
        If the unit cannot be resolved within the given category.
    """
    category = category.lower()

    if category not in CONVERSIONS:
        raise ValueError(f"Unsupported category: {category}")

    units = CONVERSIONS[category].units

    unit_lower = unit.lower()

    # Direct match (internal key)
    if unit_lower in units:
        return unit_lower

    # Reverse lookup by label
    for key, label in units.items():
        if unit_lower == label.lower():
            return key

    raise ValueError(f"Unsupported unit '{unit}' for category '{category}'")


# ALCOHOL CONTENT (base unit: ABV)

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
    """
    # Step 1: Normalise units
    from_unit = normalise_unit(from_unit, "alcohol")
    to_unit = normalise_unit(to_unit, "alcohol")

    # Step 3: Convert
    value_in_abv = value * ALCOHOL_TO_ABV[from_unit]
    return value_in_abv / ALCOHOL_TO_ABV[to_unit]


# DENSITY (base unit: g/L)

# Factor-based units (simple scaling)
# These are direct multipliers to/from g/L.
DENSITY_TO_G_L: dict[str, float] = {
    "g/ml": 1000,       # grams per millilitre
    "g/l": 1,           # grams per litre (base unit)
    "kg/m3": 1,         # kilograms per cubic metre (same as g/L)
    "lb/gal(us)": 119.826,   # pounds per US gallon
    "lb/gal(uk)": 99.7764,   # pounds per Imperial gallon
    "lb/ft3": 16.0185,       # pounds per cubic foot
}


# Complex brewing scales (empirical formulas)

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

    Raises
    ------
    ValueError
        If either `from_unit` or `to_unit` is not recognised.
    """
    # Step 1: Normalise units
    from_unit = normalise_unit(from_unit, "density")
    to_unit = normalise_unit(to_unit, "density")

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
    
def density_correction(
    density_scale: str = "SG",
    temp_scale: str = "C",
    density_measured: float = 1.000,
    reading_temp: float = 20.0,
    calibration_temp: float = 20.0,
) -> float:
    """
    Apply temperature correction to a density measurement.

    Parameters
    ----------
    density_scale : str
        Density unit for both input and output (e.g. "SG", "Plato", "Brix").
        Defaults to "SG".
    temp_scale : str
        Temperature scale for reading_temp and calibration_temp ("C" or "F").
        Defaults to "C".
    density_measured : float
        The density value obtained with a hydrometer.
    reading_temp : float
        The temperature at which the hydrometer reading was taken.
    calibration_temp : float
        The hydrometer's calibration temperature.

    Returns
    -------
    float
        The corrected density value in the same scale as the input.

    Notes
    -----
    - Hydrometers are typically calibrated at 20 °C (68 °F).
    - Corrections are approximate and based on a standard ASBC polynomial.
    - Works with any supported density scale via convert_density() and with
      Celsius/Fahrenheit via convert_temperature().
    """

    # Step 1: Validate and normalise density and temperature scales
    density_scale = normalise_unit(density_scale, "density")
    temp_scale = normalise_unit(temp_scale, "temperature")


    # Step 2: Convert input density to SG for internal correction
    sg_value: float = convert_density(density_measured, density_scale, "sg")

    # Step 3: Convert temperatures to Fahrenheit (polynomial is °F-based)
    reading_temp_f: float = convert_temperature(reading_temp, temp_scale, "f")
    calibration_temp_f: float = convert_temperature(calibration_temp, temp_scale, "f")

    # Step 4: Apply ASBC polynomial correction to get corrected SG
    corrected_sg: float = (
        sg_value
        * (
            1.00130346
            - 0.000134722124 * reading_temp_f
            + 0.00000204052596 * (reading_temp_f ** 2)
            - 0.00000000232820948 * (reading_temp_f ** 3)
        )
        / (
            1.00130346
            - 0.000134722124 * calibration_temp_f
            + 0.00000204052596 * (calibration_temp_f ** 2)
            - 0.00000000232820948 * (calibration_temp_f ** 3)
        )
    )

    # Step 5: Convert corrected SG back to user's density scale
    corrected_density: float = convert_density(corrected_sg, "sg", density_scale)

    # Step 6: Return corrected density
    return corrected_density


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
    """
    # Step 1: Normalise units
    from_unit = normalise_unit(from_unit, "mass")
    to_unit = normalise_unit(to_unit, "mass")

    # Step 2: Convert
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
    """
    # Step 1: Normalise units
    from_unit = normalise_unit(from_unit, "temperature")
    to_unit = normalise_unit(to_unit, "temperature")

    # Step 2: Convert
    value_in_c = OTHER_TO_C[from_unit](value)
    return C_TO_OTHER[to_unit](value_in_c)


# VOLUME (base unit: litres)

# Conversion factors to litres
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
    """
    # Step 1: Normalise units
    from_unit = normalise_unit(from_unit, "volume")
    to_unit = normalise_unit(to_unit, "volume")

    # Step 2: Convert
    value_in_l = value * VOLUME_TO_L[from_unit]
    return value_in_l / VOLUME_TO_L[to_unit]

#  
class ConversionCategory(NamedTuple):
    """
    Represents a unit conversion category (e.g., volume, mass, temperature).
    
    Each category groups together:
      - A canonical (base) unit for backend storage/processing
      - A dictionary of units belonging to this category
      - Conversion functions for each unit relative to the canonical unit
    
    This allows:
      - Consistent unit handling across the application
      - Easy addition of new units by extending the dictionary
      - Decoupling backend logic (always using canonical units) from frontend
        display (user-preferred units)
    
    Example:
        The 'volume' category might have 'l' as canonical, with 'ml' and 'gal'
        as supported units. Conversions are defined relative to 'l'.
    """
    label: str  # Category label (for UI, e.g. "Alcohol")
    function: Callable[[float, str, str], float]
    units: dict[str, str]  # unit -> user-facing label


# Global registry of all conversion categories, used for consistent unit handling across the app
CONVERSIONS: dict[str, ConversionCategory] = {
    "alcohol": ConversionCategory(
        label = "Alcohol Content",
        function = convert_alcohol,
        units = {
            "abv": "ABV",
            "abw": "ABW",
            "proof(us)": "Proof (US)",
            "proof(uk)": "Proof (UK)",
        },
    ),
    "density": ConversionCategory(
        label = "Density",
        function = convert_density,
        units = {
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
        },
    ),
    "mass": ConversionCategory(
        label = "Mass",
        function = convert_mass,
        units = {
            "mg": "mg",
            "g": "g",
            "kg": "kg",
            "tonne": "t",
            "gr": "gr",
            "dr": "dr",
            "oz": "oz",
            "lb": "lb",
            "ton": "ton",
        },
    ),
    "volume": ConversionCategory(
        label = "Volume",
        function = convert_volume,
        units = {
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
        },
    ),
    "temperature": ConversionCategory(
        label = "Temperature",
        function = convert_temperature,
        units = {
            "c": "°C",
            "f": "°F",
            "k": "K",
        },
    ),
}


def convert(category: str, from_unit: str, to_unit: str, value: float) -> float:
    """
    Unified conversion function for alcohol, density, mass, temperature, and volume.

    Parameters:
    category : str
        The category of the unit ("alcohol", "density", "mass", "temperature", "volume").
    from_unit : str
        Unit of the input value.
    to_unit : str
        Unit to convert to.
    value : float
        The numeric value to convert.

    Returns:
    float
        The converted value in the requested unit.

    Raises:
    ValueError
        If the category is unsupported.
    """
    category = category.lower()

    if category not in CONVERSIONS:
        raise ValueError(f"Unsupported category: {category}")

    conv_category = CONVERSIONS[category]

    return conv_category.function(value, from_unit, to_unit)