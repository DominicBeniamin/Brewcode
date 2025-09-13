# fermentation.py
"""
Module for fermentation-related calculations, including Alcohol By Volume (ABV)
estimation and priming sugar calculations.
"""

from conversions import ( 
    normalise_unit,
    convert_alcohol, 
    convert_density,
    density_correction,
    convert_temperature,
    convert_volume,
)
from dataclasses import dataclass
from typing import Callable

# Functions for estimating Alcohol by Volume (ABV)


def abv_basic(original_sg: float, final_sg: float) -> float:
    """
    Estimate ABV using the standard homebrew formula.

    ABV = (OG - FG) * 131.25
    """
    return (original_sg - final_sg) * 131.25

def abv_berry(original_sg: float, final_sg: float) -> float:
    """
    Estimate ABV using C.J.J. Berry's wine method.

    ABV = (OG - FG) / 0.736
    """
    return (original_sg - final_sg) / 0.736

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

    Returns the estimated ABV as a float.
    """
    thresholds: list[tuple[float, int]] = [
        (0.0069, 125), (0.0104, 126), (0.0172, 127), (0.0261, 128),
        (0.0360, 129), (0.0465, 130), (0.0571, 131), (0.0679, 132),
        (0.0788, 133), (0.0897, 134), (0.1007, 135),
    ]
    delta_sg = original_sg - final_sg
    for threshold, multiplier in thresholds:
        if delta_sg <= threshold:
            return delta_sg * multiplier
    return delta_sg * 135  # fallback multiplier


@dataclass(frozen=True)
class Formula:
    """Encapsulates a user-facing label and the function used for ABV calculation."""
    label: str
    function: Callable[[float, float], float]

# Registry of available ABV formulas with internal keys and user-facing labels
FORMULAS: dict[str, Formula] = {
    "abv_basic": Formula("Basic", abv_basic),
    "abv_berry": Formula("Berry", abv_berry),
    "abv_hall": Formula("Hall", abv_hall),
    "abv_hmrc": Formula("HMRC", abv_hmrc),
}

# Unified ABV calculation function
def abv(
    alcohol_unit: str = "abv",
    density_scale: str = "sg",
    temp_scale: str = "c",
    calibration_temp: float = 20.0,
    formula: str = "abv_basic",
    original_reading: float = 1.000,
    original_temp: float | None = None,
    final_reading: float = 1.000,
    final_temp: float | None = None,
) -> float:
    """
    Calculate Alcohol By Volume (ABV) using a chosen formula.

    Parameters:
        density_scale : str
            Density scale of readings, e.g., "SG", "Plato", "Brix".
        temp_scale : str
            Temperature scale, either "C" or "F".
        calibration_temp : float
            Hydrometer calibration temperature in temp_scale.
        formula : str
            Key of the formula to use. Must be one of:
                - "abv_basic" → Basic
                - "abv_berry" → Berry
                - "abv_hall" → Hall
                - "abv_hmrc" → HMRC
        original_reading (float): 
            Original gravity reading in density_scale.
        original_temp : float | None 
            Temperature of original reading (optional).
        final_reading : float 
            Final gravity reading in density_scale.
        final_temp : float | None
            Temperature of final reading (optional).

    Returns:
        float: Calculated ABV converted to the user's chosen alcohol content unit.

    Raises:
    ValueError
        If the specified formula is not recognised.
    """
    # Step 1: Apply temperature correction
    original_corrected: float = density_correction(
        density_scale = density_scale,
        temp_scale = temp_scale,
        density_measured = original_reading,
        reading_temp = original_temp if original_temp is not None else calibration_temp,
        calibration_temp = calibration_temp,
    )
    final_corrected: float = density_correction(
        density_scale = density_scale,
        temp_scale = temp_scale,
        density_measured = final_reading,
        reading_temp = final_temp if final_temp is not None else calibration_temp,
        calibration_temp = calibration_temp,
    )

    # Step 2: Convert corrected densities to SG for internal ABV calculation
    original_sg: float = convert_density(original_corrected, density_scale, "SG")
    final_sg: float = convert_density(final_corrected, density_scale, "SG")

    # Step 3: Compute ABV using the chosen formula
    if formula not in FORMULAS:
        raise ValueError(f"Invalid formula '{formula}'. Must be one of: {list(FORMULAS.keys())}")

    abv_value: float = FORMULAS[formula].function(original_sg, final_sg)

    # Step 4: Return ABV converted to user's preferred unit
    return abv_value

def priming( 
    beverage_volume: float, 
    volume_unit: str = "l", 
    beverage_temp: float = 20.0, 
    temp_scale: str = "c", 
    desired_vol_co2: float = 2.0, 
    sugar_type: str | None = None, 
    sugar_density: float | None = None, 
    fermentable_fraction: float | None = None, 
    custom_factor: float | None = None, 
) -> dict[str, float]:
    """
    Calculate the amount of priming sugar needed to achieve a desired carbonation level.

    Parameters:
        beverage_volume : float
            Volume of the beverage to be carbonated.
        volume_unit : str
            Unit of the beverage volume (e.g., "l", "ml", "gal", "qt").
        beverage_temp : float
            Temperature of the beverage at bottling time.
        temp_scale : str
            Temperature scale, either "C" or "F".
        desired_vol_co2 : float
            Desired carbonation level in volumes of CO₂.
        sugar_type : str | None
            Type of sugar used for priming. Supported types:
                - "dextrose" (corn sugar)
                - "sucrose" (table sugar)
                - "honey"
                - "maltose"
            If None, defaults to dextrose.
        sugar_density : float | None
            Density of the sugar in g/L. If None, defaults based on sugar_type.
        fermentable_fraction : float | None
            Fraction of the sugar that is fermentable (0.0 to 1.0). If None, defaults based on sugar_type.
        custom_factor : float | None
            Custom factor for sugar to CO₂ conversion. If provided, overrides sugar_type and fermentable_fraction.

    Returns:
        dict[str, float]: A dictionary containing:
            - "mass_g": Mass of sugar needed in grams.
            - "volume_ml": Volume of sugar needed in millilitres (requires sugar_density).
            - "delta_sg": Estimated increase in specific gravity due to added sugar.
            - "new_volume_l": New total volume after adding sugar (requires sugar_density).

    Raises:
        ValueError
            If sugar_density is not provided and cannot be resolved from defaults.
    """

    # Step 1: Normalise units
    volume_unit = normalise_unit(volume_unit, "volume")
    temp_scale = normalise_unit(temp_scale, "temperature")

    # Step 2: Convert input values
    beverage_volume_l: float = convert_volume(beverage_volume, volume_unit, "l")
    beverage_temp_c: float = convert_temperature(beverage_temp, temp_scale, "c")

    # Step 3: Residual CO₂ at given temperature
    residual_co2 = 3.0378 - (0.050062 * beverage_temp_c) + (0.00026555 * beverage_temp_c**2)
    residual_co2 = max(residual_co2, 0.0)
    additional_co2 = max(desired_vol_co2 - residual_co2, 0.0)

    # Step 4: Prepare sugar properties
    sugar_density_val: float | None = sugar_density  # always exists, may be overwritten

    if custom_factor is not None:
        factor = custom_factor
    else:
        defaults = {
            "dextrose": (1.0, 1587),  # (fermentable fraction, g/L density ≈ 1.587 g/mL)
            "sucrose": (1.0, 1587),
            "honey": (0.75, 1420),
            "maltose": (1.0, 1540),
        }
        if sugar_type in defaults:
            default_fraction, default_density = defaults[sugar_type]
        else:
            default_fraction, default_density = (1.0, 1587)

        fermentable_fraction = fermentable_fraction or default_fraction
        sugar_density_val = sugar_density_val or default_density

        factor = 4.01 * fermentable_fraction

    # Step 5: Calculate sugar needed
    sugar_needed_g = beverage_volume_l * additional_co2 * factor

    # Step 6: Volume of sugar (mL) — must have a density
    if sugar_density_val is None:
        raise ValueError("Sugar density must be provided or resolved from defaults.")
    sugar_volume_ml = sugar_needed_g / (sugar_density_val / 1000.0)

    # Step 7: Estimate change in SG & final volume
    delta_sg = (sugar_needed_g / beverage_volume_l) * 0.0004
    new_volume_l: float = beverage_volume_l + (sugar_volume_ml / 1000.0)

    return {
        "mass_g": sugar_needed_g,
        "volume_ml": sugar_volume_ml,
        "delta_sg": delta_sg,
        "new_volume_l": new_volume_l,
    }
