# fermentation.py
from conversions import c_to_f, DENSITY_COMPLEX, gl_to_sg

# Functions for estimating Alcohol by Volume (ABV)
def corrected_gravity(mg: float, tr: float, tc: float, scale: str = "C") -> float:
    """Return the temperature-corrected specific gravity."""

    # Convert inputs to Fahrenheit if necessary
    if scale.upper() == "C":
        tr = c_to_f(tr)
        tc = c_to_f(tc)
    elif scale.upper() != "F":
        raise ValueError("scale must be either 'C' or 'F'")

    # Factor polynomial (°F-based)
    def factor(t: float) -> float: 
        return (
            1.00130346 
            - 0.000134722124 * t 
            + 0.00000204052596 * t**2 
            - 0.00000000232820948 * t**3 
        )

    return mg * (factor(tr) / factor(tc))

def abv_basic(original_sg: float, final_sg: float, precision: int = 2) -> float:
    """
    Estimate ABV using the standard homebrew formula.

    ABV = (OG - FG) * 131.25
    """
    return round((original_sg - final_sg) * 131.25, precision)

def abv_berry(original_sg: float, final_sg: float, precision: int = 2) -> float:
    """
    Estimate ABV using C.J.J. Berry's wine method.

    ABV = (OG - FG) / 0.736
    """
    return round((original_sg - final_sg) / 0.736, precision)

def abv_hall(original_sg: float, final_sg: float, precision: int = 2) -> float:
    """
    Estimate ABV using Michael Hall's two-step ABW to ABV formula.

    ABW = 76.08 * (OG - FG) / (1.775 - OG)
    ABV = ABW / 0.794
    """
    delta_sg = original_sg - final_sg
    abw = (76.08 * delta_sg) / (1.775 - original_sg)
    abv = abw / 0.794
    return round(abv, precision)

def abv_hmrc(original_sg: float, final_sg: float, precision: int =2) -> float:
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
            return round(delta_sg * multiplier, precision)
    return round(delta_sg * 135, precision)  # fallback multiplier


# Unified ABV calculation function
def abv(
    original: float,
    final: float,
    scale: str = "sg",
    formula: str = "basic",        # "basic", "berry", "hall", or "hmrc"
    precision: int = 2,
    tr_og: float | None = None,
    tr_fg: float | None = None,
    tc: float | None = None,
    temp_scale: str = "C"
) -> float:
    """
    Calculate Alcohol By Volume (ABV) using a chosen formula.

    Parameters:
    - original: Original gravity in the given scale
    - final: Final gravity in the given scale
    - scale: one of 'sg', 'plato', 'brix', or 'oe' (default: 'sg')
    - formula: 'basic', 'berry', 'hall', or 'hmrc' (default: 'basic')
    - precision: number of decimal places
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
    if tr_og is not None and tc is not None:
        og_sg = corrected_gravity(og_sg, tr_og, tc, temp_scale)
    if tr_fg is not None and tc is not None:
        fg_sg = corrected_gravity(fg_sg, tr_fg, tc, temp_scale)

    # Compute ABV using the chosen formula
    if formula == "basic":
        abv_value = (og_sg - fg_sg) * 131.25
    elif formula == "berry":
        abv_value = (og_sg - fg_sg) / 0.736
    elif formula == "hall":
        # Hall formula: ABV = (OG - FG) * 133
        abv_value = (og_sg - fg_sg) * 133
    elif formula == "hmrc":
        # HMRC formula: ABV = (OG - FG) * 0.372 / 0.78924 * 100
        # Equivalent: (OG - FG) * 47.14
        abv_value = (og_sg - fg_sg) * 47.14
    else:
        raise ValueError("Unsupported formula. Choose 'basic', 'berry', 'hall', or 'hmrc'.")

    return round(abv_value, precision)

# Secondary Fermentation: Priming Sugar Calculations (Metric backend standard)
def priming_sugar(
    vol_co2: float,
    beverage_vol_l: float,
    temp_c: float,
    *,
    sg: float
) -> tuple[float, float, float]:
    """
    Estimate priming sugar (in grams and milliliters) needed to carbonate a beverage
    during secondary fermentation. Input should be metric and temperature in Celsius.

    Parameters:
    - vol_co2: Desired carbonation level (CO2 volumes)
    - beverage_vol_l: Volume of beverage to carbonate (liters)
    - temp_c: Bottling temperature in degrees Celsius
    - sg: Specific gravity of the sugar source (must be provided)

    Returns:
    - Tuple of estimated sugar required:
      (weight in grams, approximate volume in milliliters, estimated SG after priming)
    """
    temp_f = temp_c * 9 / 5 + 32
    priming_g = 2.0 * beverage_vol_l * (
        vol_co2 - 3.0378 + 0.050062 * temp_f - 0.00026555 * temp_f ** 2
    )

    sugar_density = 1.587  # Table sugar density in g/mL
    priming_ml = priming_g / sugar_density

    # Estimate SG increase: 4 Brix per 1000g/L → 0.004 SG per 10g/L
    delta_sg = (priming_g / beverage_vol_l) * 0.0004
    sg_after_priming = round(sg + delta_sg, 5)

    return round(priming_g, 2), round(priming_ml, 2), sg_after_priming