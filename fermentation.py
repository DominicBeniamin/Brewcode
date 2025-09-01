# fermentation.py
from conversions import convert_alcohol, convert_temperature, DENSITY_COMPLEX, gl_to_sg

# Functions for estimating Alcohol by Volume (ABV)
def corrected_gravity(mg: float, tr: float, tc: float, scale: str = "C") -> float:
    """
    Return the temperature-corrected specific gravity.

    Parameters
    ----------
    mg : float
        Measured specific gravity (unitless, e.g., 1.050)
    tr : float
        Temperature at which the measurement was taken
    tc : float
        Target temperature for correction
    scale : str, optional
        Temperature scale of tr and tc ("C" for Celsius or "F" for Fahrenheit, default "C")

    Returns
    -------
    float
        Temperature-corrected specific gravity
    """
    # Normalize scale and convert to Fahrenheit for the formula
    scale = scale.upper()
    if scale not in {"C", "F"}:
        raise ValueError("scale must be either 'C' or 'F'")

    tr_f: float = convert_temperature(tr, scale.lower(), "f")
    tc_f: float = convert_temperature(tc, scale.lower(), "f")

    # Factor polynomial (°F-based)
    def factor(t: float) -> float:
        return (
            1.00130346
            - 0.000134722124 * t
            + 0.00000204052596 * t**2
            - 0.00000000232820948 * t**3
        )

    return mg * (factor(tr_f) / factor(tc_f))


def abv_basic(original_sg: float, final_sg: float) -> float:
    """
    Estimate ABV using the standard homebrew formula.

    ABV = (OG - FG) * 131.25
    """
    return round((original_sg - final_sg) * 131.25)

def abv_berry(original_sg: float, final_sg: float) -> float:
    """
    Estimate ABV using C.J.J. Berry's wine method.

    ABV = (OG - FG) / 0.736
    """
    return round((original_sg - final_sg) / 0.736)

def abv_hall(original_sg: float, final_sg: float) -> float:
    """
    Estimate ABV using Michael Hall's two-step ABW to ABV formula.

    ABW = 76.08 * (OG - FG) / (1.775 - OG)
    ABV = ABW / 0.794
    """
    delta_sg = original_sg - final_sg
    abw = (76.08 * delta_sg) / (1.775 - original_sg)
    abv = convert_alcohol(abw, from_unit="abw", to_unit="abv")
    return abv

def abv_hmrc(original_sg: float, final_sg: float) -> float:
    """
    Estimate ABV using the UK HMRC table-based method for taxation.

    This method uses a series of thresholds to determine the appropriate multiplier
    based on the difference between original and final specific gravity.

    Returns the estimated ABV as a float rounded to two decimal places.
    """
    thresholds: list[tuple[float, int]] = [
        (0.0069, 125), (0.0104, 126), (0.0172, 127), (0.0261, 128),
        (0.0360, 129), (0.0465, 130), (0.0571, 131), (0.0679, 132),
        (0.0788, 133), (0.0897, 134), (0.1007, 135),
    ]
    delta_sg = round(original_sg - final_sg, 4)
    for threshold, multiplier in thresholds:
        if delta_sg <= threshold:
            return delta_sg * multiplier
    return delta_sg * 135  # fallback multiplier


# Unified ABV calculation function
def abv(
    original: float,
    final: float,
    scale: str = "sg",
    formula: str = "basic", # "basic", "berry", "hall", or "hmrc"
    tr_og: float | None = None,
    tr_fg: float | None = None,
    tc: float | None = None,
    temp_scale: str | None = "C"
) -> float:
    """
    Calculate Alcohol By Volume (ABV) using a chosen formula.

    Parameters:
    - original: Original gravity in the given scale
    - final: Final gravity in the given scale
    - scale: one of 'sg', 'plato', 'brix', or 'oe' (default: 'sg')
    - formula: 'basic', 'berry', 'hall', or 'hmrc' (default: 'basic')
    - tr_og: optional reading temperature for OG
    - tr_fg: optional reading temperature for FG
    - tc: optional hydrometer calibration temperature
    - temp_scale: "C" or "F" (default "C")
    """

    scale = scale.lower()
    formula = formula.lower()

    if scale not in DENSITY_COMPLEX:
        raise ValueError(f"Unsupported scale '{scale}'. Must be one of {list(DENSITY_COMPLEX.keys())}")

    # Convert input values to g/L
    to_gl, _ = DENSITY_COMPLEX[scale]
    og_gl = to_gl(original)
    fg_gl = to_gl(final)

    # Convert g/L to SG
    og_sg = gl_to_sg(og_gl)
    fg_sg = gl_to_sg(fg_gl)

    # Apply temperature correction if provided
    if tr_og is not None and tc is not None and temp_scale is not None:
        og_sg = corrected_gravity(og_sg, tr_og, tc, temp_scale)
    if tr_fg is not None and tc is not None and temp_scale is not None:
        fg_sg = corrected_gravity(fg_sg, tr_fg, tc, temp_scale)

    # Compute ABV using the chosen formula
    if formula == "basic":
        return abv_basic(og_sg, fg_sg)
    elif formula == "berry":
        return abv_berry(og_sg, fg_sg)
    elif formula == "hall":
        return abv_hall(og_sg, fg_sg)
    elif formula == "hmrc":
        return abv_hmrc(og_sg, fg_sg)
    else:
        raise ValueError("Unsupported formula. Choose 'basic', 'berry', 'hall', or 'hmrc'.")


# Secondary Fermentation: Priming Sugar Calculations (Metric backend standard)
def priming(
    vol_co2: float,
    beverage_vol_l: float,
    temp: float,
    temp_unit: str = "c",
    *,
    sg: float
) -> tuple[float, float, float]:
    """
    Estimate priming sugar (in grams and milliliters) needed to carbonate a beverage
    during secondary fermentation. Accepts temperature in Celsius or Fahrenheit.

    Parameters
    ----------
    vol_co2 : float
        Desired carbonation level (CO2 volumes)
    beverage_vol_l : float
        Volume of beverage to carbonate (liters)
    temp : float
        Bottling temperature (numeric value)
    temp_unit : str, optional
        Unit of `temp`, either "c" for Celsius or "f" for Fahrenheit (default "c")
    sg : float
        Specific gravity of the sugar source (must be provided)

    Returns
    -------
    tuple[float, float, float]
        Estimated sugar required:
        (weight in grams, approximate volume in milliliters, estimated SG after priming)

    Notes
    -----
    - The calculation converts the input temperature to Fahrenheit internally for the
      priming formula.
    - Rounding is not applied; frontend or user preferences should handle formatting.
    """
    # Normalize temperature unit
    temp_unit = temp_unit.lower()
    if temp_unit not in {"c", "f"}:
        raise ValueError(f"Unsupported temperature unit: {temp_unit}")

    # Convert temperature to Fahrenheit for priming formula
    temp_f: float = convert_temperature(temp, temp_unit, "f")

    # Calculate priming sugar in grams using empirical formula
    priming_g: float = 2.0 * beverage_vol_l * (
        vol_co2 - 3.0378 + 0.050062 * temp_f - 0.00026555 * temp_f ** 2
    )

    sugar_density: float = 1.587  # Table sugar density in g/mL
    priming_ml: float = priming_g / sugar_density  # Approximate volume in mL

    # Estimate increase in specific gravity due to added sugar
    delta_sg: float = (priming_g / beverage_vol_l) * 0.0004
    sg_after_priming: float = sg + delta_sg

    return priming_g, priming_ml, sg_after_priming

