import math
from dataclasses import dataclass
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import re

# --- Third-party imports for plotting ---
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# --- Third-party imports for PDF Export ---
try:
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.lib.units import inch
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

# --- Constants ---
G = 9.81  # Gravitational acceleration (m/s^2)
E_STEEL = 2.0e11  # Modulus of Elasticity for steel (Pa)

# --- AISC ASD (ว.ส.ท.) Allowable Stress Factors ---
ALLOWABLE_BENDING_STRESS_FACTOR_X = 0.60
ALLOWABLE_BENDING_STRESS_FACTOR_Y = 0.75
ALLOWABLE_SHEAR_STRESS_FACTOR = 0.40

# --- Deflection Limits ---
LIVE_LOAD_DEFLECTION_LIMIT_RATIO = 240  # L / 240
TOTAL_LOAD_DEFLECTION_LIMIT_RATIO = 180 # L / 180

# --- Unit Conversion Factors ---
KPA_TO_PA = 1000
MPA_TO_PA = 1e6
MM3_TO_M3 = 1e-9
MM4_TO_M4 = 1e-12


@dataclass
class SteelSection:
    """Represents the properties of a C-Channel steel section."""
    weight: float  # kg/m
    Fy: float      # MPa
    A: float       # mm^2
    d: float       # mm
    tw: float      # mm
    bf: float      # mm
    tf: float      # mm
    Ix: float      # mm^4
    Sx: float      # mm^3
    Iy: float      # mm^4
    Sy: float      # mm^3


# --- DATA SECTION: คุณสมบัติของหน้าตัดเหล็กรูปตัวซี (C-Channel) ---
STEEL_SECTIONS = {
    "C100x50x20x2.3": SteelSection(weight=3.67, Fy=245, A=467.2, d=100, tw=2.3, bf=50, tf=2.3, Ix=1.08e6, Sx=2.15e4, Iy=0.147e6, Sy=4.4e3),
    "C100x50x20x3.2": SteelSection(weight=4.99, Fy=245, A=635.8, d=100, tw=3.2, bf=50, tf=3.2, Ix=1.45e6, Sx=2.90e4, Iy=0.194e6, Sy=6.0e3),
    "C125x50x20x3.2": SteelSection(weight=5.62, Fy=245, A=715.8, d=125, tw=3.2, bf=50, tf=3.2, Ix=2.54e6, Sx=4.06e4, Iy=0.213e6, Sy=6.4e3),
    "C150x50x20x3.2": SteelSection(weight=6.42, Fy=245, A=817.8, d=150, tw=3.2, bf=50, tf=3.2, Ix=4.25e6, Sx=5.67e4, Iy=0.232e6, Sy=6.8e3),
    "C150x65x20x4.0": SteelSection(weight=8.78, Fy=245, A=1118.0, d=150, tw=4.0, bf=65, tf=4.0, Ix=5.68e6, Sx=7.58e4, Iy=0.477e6, Sy=10.7e3),
    "C150x75x25x4.5": SteelSection(weight=11.0, Fy=345, A=1401.0, d=150, tw=4.5, bf=75, tf=4.5, Ix=6.91e6, Sx=9.22e4, Iy=0.822e6, Sy=15.9e3),
    "C200x75x25x4.5": SteelSection(weight=12.9, Fy=345, A=1641.0, d=200, tw=4.5, bf=75, tf=4.5, Ix=1.45e7, Sx=1.45e5, Iy=0.908e6, Sy=17.0e3),
}

class PurlinDesign:
    """
    Encapsulates the design calculations for a hot-rolled steel purlin
    based on AISC ASD (ว.ส.ท.) standards.
    """
    def __init__(self, section_name: str, purlin_span: float, purlin_spacing: float,
                 roof_slope_degree: float, dead_load_kPa: float, live_load_kPa: float,
                 basic_wind_speed_mps: float, building_height_m: float,
                 exposure_category: str, internal_pressure_coeff_pos: float,
                 internal_pressure_coeff_neg: float, gust_effect_factor: float = 0.85,
                 topographic_factor: float = 1.0, wind_directionality_factor: float = 0.85):
        """
        Args:
            section_name (str): Name of the steel section from STEEL_SECTIONS.
            purlin_span (float): Purlin span (distance between trusses), in meters (m).
            purlin_spacing (float): Distance between purlins, in meters (m).
            roof_slope_degree (float): Roof slope angle, in degrees.
            dead_load_kPa (float): Dead load (excluding purlin self-weight), in kPa.
            live_load_kPa (float): Live load, in kPa.
            basic_wind_speed_mps (float): Basic wind speed in m/s.
            building_height_m (float): Mean roof height of the building in meters.
            exposure_category (str): Exposure category (e.g., 'B', 'C', 'D').
            internal_pressure_coeff_pos (float): Positive internal pressure coefficient (Cpi).
            internal_pressure_coeff_neg (float): Negative internal pressure coefficient (Cpi).
            gust_effect_factor (float): Gust effect factor (G).
            topographic_factor (float): Topographic factor (Kzt).
            wind_directionality_factor (float): Wind directionality factor (Kd).
        """
        # Validate exposure category
        valid_exposure_categories = ['B', 'C', 'D'] # Common ASCE 7 categories
        if exposure_category.upper() not in valid_exposure_categories:
            raise ValueError(f"Exposure category '{exposure_category}' ไม่ถูกต้อง. ต้องเป็นหนึ่งใน {valid_exposure_categories}")

        if section_name not in STEEL_SECTIONS:
            raise ValueError(f"ไม่พบหน้าตัดเหล็ก '{section_name}' ในฐานข้อมูล")

        # --- Store Inputs ---
        self.section_name = section_name
        self.L = purlin_span
        self.spacing = purlin_spacing
        self.slope_deg = roof_slope_degree
        self.theta_rad = math.radians(roof_slope_degree)
        self.dl_kPa = dead_load_kPa
        self.ll_kPa = live_load_kPa
        
        # Wind Load Inputs
        self.basic_wind_speed_mps = basic_wind_speed_mps
        self.building_height_m = building_height_m
        self.exposure_category = exposure_category.upper()
        self.internal_pressure_coeff_pos = internal_pressure_coeff_pos
        self.internal_pressure_coeff_neg = internal_pressure_coeff_neg
        self.gust_effect_factor = gust_effect_factor
        self.topographic_factor = topographic_factor
        self.wind_directionality_factor = wind_directionality_factor

        # --- Get Section Properties (converted to base SI units) ---
        props = STEEL_SECTIONS[section_name]
        self.purlin_weight_per_m = props.weight * G  # N/m
        self.Fy = props.Fy * MPA_TO_PA              # Pa
        self.Sx = props.Sx * MM3_TO_M3              # m^3
        self.Sy = props.Sy * MM3_TO_M3              # m^3
        self.Ix = props.Ix * MM4_TO_M4              # m^4
        self.Iy = props.Iy * MM4_TO_M4              # m^4
        self.d = props.d / 1000                     # m
        self.tw = props.tw / 1000                   # m

    def _get_kz(self, height_m: float) -> float:
        """
        Simplified Kz (Velocity Pressure Exposure Coefficient) based on height and exposure.
        THIS IS A SIMPLIFICATION. REFER TO THAI STANDARD (ว.ส.ท.) FOR ACTUAL VALUES.
        Values are illustrative for ASCE 7-05 Exposure C.
        """
        # For z < 4.5m, Kz = 0.85 (Exposure C)
        if self.exposure_category == 'C':
            if height_m <= 4.5:
                return 0.85
            elif height_m <= 6.0:
                return 0.90
            elif height_m <= 7.5:
                return 0.94
            elif height_m <= 9.0:
                return 0.98
            elif height_m <= 12.0:
                return 1.04
            else: # Linear interpolation for heights > 12m, or use formula from standard
                # For simplicity, let's cap it for typical purlin heights
                return 1.04 
        # Add other exposure categories (B, D) if needed, or raise error
        raise ValueError(f"Exposure category '{self.exposure_category}' ไม่รองรับสำหรับการคำนวณ Kz")

    def _calculate_wind_pressure_kPa(self) -> tuple[float, float]:
        """
        Calculates design wind pressures (uplift and downward) in kPa.
        THIS IS A SIMPLIFICATION. REFER TO THAI STANDARD (ว.ส.ท.) FOR ACTUAL Cp VALUES AND METHODOLOGY.
        """
        # 1. Calculate Velocity Pressure (qz)
        # qz = 0.613 * Kz * Kzt * Kd * V^2 (Pa)
        # Kz is evaluated at the mean roof height, for purlins, we can use building_height_m
        Kz = self._get_kz(self.building_height_m)
        
        qz = 0.613 * Kz * self.topographic_factor * self.wind_directionality_factor * (self.basic_wind_speed_mps**2) # Pa

        # 2. Determine External Pressure Coefficients (Cp) for roof
        # These are highly simplified and should come from the Thai standard.
        # Assuming wind perpendicular to ridge for simplicity.
        # For low-slope roofs (common for purlins), suction (uplift) is usually critical.
        # Let's define two cases: critical uplift and critical downward.

        # Case 1: Critical Uplift (Suction)
        # This typically occurs on the windward edge or corners, or overall leeward roof.
        # For simplicity, let's assume a general suction coefficient for the roof.
        # A common value for roof suction (Cp) can be around -0.7 to -1.0 for low slopes.
        # IMPORTANT: Replace with values from Thai standard based on roof slope and zone.
        Cp_uplift_external = -0.8 
        
        # Case 2: Critical Downward Pressure
        # This occurs on the windward side of steeper roofs. For low slopes, it might be negligible or even suction.
        # IMPORTANT: Replace with values from Thai standard based on roof slope and zone.
        Cp_downward_external = 0.2 

        # 3. Calculate Design Pressures (p)
        # p = qz * G * (Cp - Cpi)
        # For uplift, we combine external suction (negative Cp) with internal suction (negative Cpi)
        # For downward, we combine external pressure (positive Cp) with internal pressure (positive Cpi)

        # Design Uplift Pressure (outward, negative pressure)
        # p_uplift = qz * G * (Cp_external_negative - Cpi_negative)
        p_uplift_Pa = qz * self.gust_effect_factor * (Cp_uplift_external - self.internal_pressure_coeff_pos) # Changed Cpi to positive for uplift

        # Design Downward Pressure (inward, positive pressure).
        # Worst case combines external pressure (positive Cp) with internal suction (negative Cpi).
        p_downward_Pa = qz * self.gust_effect_factor * (Cp_downward_external - self.internal_pressure_coeff_neg)

        return p_uplift_Pa / KPA_TO_PA, p_downward_Pa / KPA_TO_PA # Return in kPa

    def run_check(self) -> dict:
        """Runs all design checks and returns a dictionary of results."""
        # 1. Calculate distributed loads (N/m)
        w_dl_applied = self.dl_kPa * KPA_TO_PA * self.spacing
        w_dl_total = w_dl_applied + self.purlin_weight_per_m
        w_ll = self.ll_kPa * KPA_TO_PA * self.spacing
        
        # Calculate wind loads (kPa) and convert to N/m
        wind_uplift_kPa, wind_downward_kPa = self._calculate_wind_pressure_kPa()
        w_wind_uplift = wind_uplift_kPa * KPA_TO_PA * self.spacing # N/m (outward)
        w_wind_downward = wind_downward_kPa * KPA_TO_PA * self.spacing # N/m (inward)

        # Define Load Combinations for STRESS (factored loads for strength design)
        # These are simplified. Refer to Thai standard (ว.ส.ท.) for full load combinations.
        # Wind load is assumed perpendicular to roof surface, so it affects w_x.
        # Uplift wind load will be negative w_x. Downward wind load will be positive w_x.
        stress_load_combinations = [
            {"name": "D + L", "factors": {"DL": 1.0, "LL": 1.0, "WL_down": 0.0, "WL_up": 0.0}},
            {"name": "D + W (down)", "factors": {"DL": 1.0, "LL": 0.0, "WL_down": 1.0, "WL_up": 0.0}},
            {"name": "D + W (uplift)", "factors": {"DL": 1.0, "LL": 0.0, "WL_down": 0.0, "WL_up": 1.0}},
            {"name": "D + 0.75L + 0.75W (down)", "factors": {"DL": 1.0, "LL": 0.75, "WL_down": 0.75, "WL_up": 0.0}},
            {"name": "D + 0.75L + 0.75W (uplift)", "factors": {"DL": 1.0, "LL": 0.75, "WL_down": 0.0, "WL_up": 0.75}},
        ]

        critical_stress_ratio = 0.0
        critical_load_case_stress = ""
        overall_stress_ok = True
        stress_check_all_cases = [] # To store results for all load cases for plotting
        critical_w_x_for_shear = 0.0
        critical_load_case_shear = ""


        # --- Added for detailed report ---
        # Initialize with a default structure in case no load case is processed
        stress_results_lc = {
            "fbx_MPa": 0, "fby_MPa": 0,
            "Fbx_MPa": 0, "Fby_MPa": 0,
            "interaction_ratio": 0, "is_ok": True
        }
        critical_stress_details = {
            "w_x": 0, "w_y": 0, "Mx": 0, "My": 0,
            "fbx_MPa": 0, "fby_MPa": 0
        }

        for lc in stress_load_combinations:
            # Resolve loads into components perpendicular (x) and parallel (y) to the roof
            w_x_dl_lc = lc["factors"]["DL"] * w_dl_total * math.cos(self.theta_rad)
            w_y_dl_lc = lc["factors"]["DL"] * w_dl_total * math.sin(self.theta_rad)
            w_x_ll_lc = lc["factors"]["LL"] * w_ll * math.cos(self.theta_rad)
            w_y_ll_lc = lc["factors"]["LL"] * w_ll * math.sin(self.theta_rad)

            w_x_wind_lc = 0.0
            w_y_wind_lc = 0.0 # Wind load is assumed to be perpendicular to roof, so no y-component from wind
            if lc["factors"]["WL_down"] > 0:
                w_x_wind_lc = lc["factors"]["WL_down"] * w_wind_downward # Downward is positive w_x
            elif lc["factors"]["WL_up"] > 0:
                w_x_wind_lc = -lc["factors"]["WL_up"] * w_wind_uplift # Uplift is negative w_x

            w_x_total_lc = w_x_dl_lc + w_x_ll_lc + w_x_wind_lc
            w_y_total_lc = w_y_dl_lc + w_y_ll_lc + w_y_wind_lc

            # Check for critical shear (based on w_x which is perpendicular to purlin, resisted by web)
            if abs(w_x_total_lc) > abs(critical_w_x_for_shear):
                critical_w_x_for_shear = w_x_total_lc
                critical_load_case_shear = lc["name"]

            stress_results_lc = self._check_bending_stress(w_x_total_lc, w_y_total_lc)
            stress_check_all_cases.append({"name": lc["name"], "ratio": stress_results_lc["interaction_ratio"]})

            if stress_results_lc["interaction_ratio"] > critical_stress_ratio:
                critical_stress_ratio = stress_results_lc["interaction_ratio"]
                critical_load_case_stress = lc["name"]
                # --- Added for detailed report ---
                critical_stress_details = {
                    "w_x": w_x_total_lc, "w_y": w_y_total_lc,
                    "Mx": w_x_total_lc * (self.L**2) / 8, "My": w_y_total_lc * (self.L**2) / 8,
                    "fbx_MPa": stress_results_lc["fbx_MPa"], "fby_MPa": stress_results_lc["fby_MPa"]
                }
            if not stress_results_lc["is_ok"]:
                overall_stress_ok = False

        # Load Combinations for DEFLECTION (unfactored serviceability loads)
        # These are typically D+L, D+W, D+0.75L+0.75W
        serviceability_load_combinations = [
            {"name": "D + L", "components": {"DL": w_dl_total, "LL": w_ll, "WL_down": 0.0, "WL_up": 0.0}},
            {"name": "D + W (down)", "components": {"DL": w_dl_total, "LL": 0.0, "WL_down": w_wind_downward, "WL_up": 0.0}},
            {"name": "D + W (uplift)", "components": {"DL": w_dl_total, "LL": 0.0, "WL_down": 0.0, "WL_up": w_wind_uplift}},
            {"name": "D + 0.75L + 0.75W (down)", "components": {"DL": w_dl_total, "LL": 0.75 * w_ll, "WL_down": 0.75 * w_wind_downward, "WL_up": 0.0}},
            {"name": "D + 0.75L + 0.75W (uplift)", "components": {"DL": w_dl_total, "LL": 0.75 * w_ll, "WL_down": 0.0, "WL_up": 0.75 * w_wind_uplift}},
        ]

        # Live Load Deflection (special case: only LL)
        w_x_ll_only = w_ll * math.cos(self.theta_rad)
        w_y_ll_only = w_ll * math.sin(self.theta_rad)
        ll_deflection_check_results = self._check_deflection(w_x_ll_only, w_y_ll_only, is_live_load_only=True)
        overall_deflection_ll_ok = ll_deflection_check_results["is_ll_ok"]
        # --- Added for detailed report ---
        ll_deflection_details = {
            "w_x": w_x_ll_only, "w_y": w_y_ll_only,
            "delta_v_mm": ll_deflection_check_results["delta_vertical_mm"]
        }

        # --- Added for detailed report ---
        critical_deflection_details = {
            "w_x": 0, "w_y": 0, "delta_v_mm": 0
        }
        
        # Total Load Deflection (iterate through serviceability combinations)
        critical_total_deflection_mm = 0.0
        critical_load_case_deflection_total = ""
        overall_deflection_total_ok = True

        for lc in serviceability_load_combinations:
            w_x_dl_unfactored = lc["components"]["DL"] * math.cos(self.theta_rad)
            w_y_dl_unfactored = lc["components"]["DL"] * math.sin(self.theta_rad)
            w_x_ll_unfactored = lc["components"]["LL"] * math.cos(self.theta_rad)
            w_y_ll_unfactored = lc["components"]["LL"] * math.sin(self.theta_rad)

            w_x_wind_unfactored = 0.0
            w_y_wind_unfactored = 0.0 # Wind load is assumed to be perpendicular to roof, so no y-component from wind
            if lc["components"]["WL_down"] > 0:
                w_x_wind_unfactored = lc["components"]["WL_down"]
            elif lc["components"]["WL_up"] > 0:
                w_x_wind_unfactored = -lc["components"]["WL_up"] # Uplift is negative

            w_x_total_unfactored_lc = w_x_dl_unfactored + w_x_ll_unfactored + w_x_wind_unfactored
            w_y_total_unfactored_lc = w_y_dl_unfactored + w_y_ll_unfactored + w_y_wind_unfactored # Wind doesn't affect w_y directly in this component

            total_deflection_results_lc = self._check_deflection(w_x_total_unfactored_lc, w_y_total_unfactored_lc, is_live_load_only=False)

            # Deflection can be positive or negative (uplift/downward). We care about magnitude for deflection check.
            current_deflection_magnitude = abs(total_deflection_results_lc["delta_vertical_mm"])

            if current_deflection_magnitude > critical_total_deflection_mm:
                critical_total_deflection_mm = current_deflection_magnitude
                critical_load_case_deflection_total = lc["name"]
                # --- Added for detailed report ---
                critical_deflection_details = {
                    "w_x": w_x_total_unfactored_lc, "w_y": w_y_total_unfactored_lc,
                    "delta_v_mm": total_deflection_results_lc["delta_vertical_mm"]
                }
            if not total_deflection_results_lc["is_total_ok"]:
                overall_deflection_total_ok = False

        # Perform Shear Check
        V_max = critical_w_x_for_shear * self.L / 2
        shear_check_results = self._check_shear_stress(V_max)
        overall_shear_ok = shear_check_results["is_ok"]
        # Final overall status
        overall_ok = overall_stress_ok and overall_shear_ok and overall_deflection_ll_ok and overall_deflection_total_ok

        # Compile and return results
        return {
            "Inputs": {
                "Section": self.section_name, "Span (m)": self.L, "Spacing (m)": self.spacing,
                "Slope (deg)": self.slope_deg, "Dead Load (kPa)": self.dl_kPa, "Live Load (kPa)": self.ll_kPa,
                "Basic Wind Speed (m/s)": self.basic_wind_speed_mps,
                "Building Height (m)": self.building_height_m,
                "Exposure Category": self.exposure_category,
                "Internal Pressure Coeff (+/-)": f"{self.internal_pressure_coeff_pos}/{self.internal_pressure_coeff_neg}",
                "Gust Effect Factor": self.gust_effect_factor,
                "Topographic Factor": self.topographic_factor,
                "Wind Directionality Factor": self.wind_directionality_factor,
                "Calculated Wind Uplift (kPa)": wind_uplift_kPa,
                "Calculated Wind Downward (kPa)": wind_downward_kPa,
            },
            "Calculated Stresses (MPa)": {"fbx": critical_stress_details["fbx_MPa"], "fby": critical_stress_details["fby_MPa"]},
            "Allowable Stresses (MPa)": {"Fbx": (ALLOWABLE_BENDING_STRESS_FACTOR_X * self.Fy) / MPA_TO_PA, "Fby": (ALLOWABLE_BENDING_STRESS_FACTOR_Y * self.Fy) / MPA_TO_PA},
            "Stress Check": {
                "Interaction Ratio": critical_stress_ratio,
                "Critical Load Case": critical_load_case_stress,
                "Status": "ผ่าน (ADEQUATE)" if overall_stress_ok else "ไม่ผ่าน (INADEQUATE)",
                "Details": critical_stress_details,
                "All Cases": stress_check_all_cases # Add data for plotting
            },
            "Shear Check": {
                "V_max (kN)": V_max / 1000,
                "fv (MPa)": shear_check_results["fv_MPa"],
                "Fv (MPa)": shear_check_results["Fv_MPa"],
                "Ratio": shear_check_results["ratio"],
                "Status": shear_check_results["status"],
                "Critical Load Case": critical_load_case_shear,
                "is_ok": overall_shear_ok
            },
            "Calculated Deflection (mm)": {
                "Live Load Vertical": ll_deflection_details["delta_v_mm"],
                "Total Vertical": critical_deflection_details.get("delta_v_mm", 0)
            },
            "Allowable Deflection (mm)": {
                "Live Load (L/240)": ll_deflection_check_results["allowable_ll_mm"],
                "Total (L/180)": ll_deflection_check_results["allowable_total_mm"]
            },
            "Deflection Check": {
                "Live Load": "ผ่าน (OK)" if overall_deflection_ll_ok else "ไม่ผ่าน (NG)",
                "Total Load": "ผ่าน (OK)" if overall_deflection_total_ok else "ไม่ผ่าน (NG)",
                "Critical Total Load Case": critical_load_case_deflection_total,
                "LL_Details": ll_deflection_details,
                "Total_Details": critical_deflection_details
            },
            "Final Result": "หน้าตัดสามารถรับน้ำหนักได้" if overall_ok else "หน้าตัดไม่สามารถรับน้ำหนักได้",
            "is_ok": overall_ok
        }

    def _check_bending_stress(self, w_x: float, w_y: float) -> dict:
        """Calculates and checks bending stresses."""
        # Assuming simply supported beam, M = wL^2 / 8
        Mx = w_x * (self.L**2) / 8
        My = w_y * (self.L**2) / 8

        fbx = Mx / self.Sx if self.Sx > 0 else 0
        fby = My / self.Sy if self.Sy > 0 else 0

        Fbx = ALLOWABLE_BENDING_STRESS_FACTOR_X * self.Fy
        Fby = ALLOWABLE_BENDING_STRESS_FACTOR_Y * self.Fy

        # Handle division by zero if Fbx or Fby are zero (e.g., Fy=0, though unlikely)
        ratio_x = fbx / Fbx if Fbx > 0 else float('inf')
        ratio_y = fby / Fby if Fby > 0 else float('inf')

        interaction_ratio = ratio_x + ratio_y
        
        return {
            "fbx_MPa": fbx / MPA_TO_PA, "fby_MPa": fby / MPA_TO_PA,
            "Fbx_MPa": Fbx / MPA_TO_PA, "Fby_MPa": Fby / MPA_TO_PA,
            "interaction_ratio": interaction_ratio, "is_ok": interaction_ratio <= 1.0
        }

    def _check_shear_stress(self, V_max: float) -> dict:
        """Calculates and checks shear stress on the web."""
        area_web = self.d * self.tw
        if area_web <= 0: # Handle zero or negative area
            fv = float('inf')
        else:
            fv = abs(V_max) / area_web
        
        Fv = ALLOWABLE_SHEAR_STRESS_FACTOR * self.Fy
        
        ratio = fv / Fv if Fv > 0 else float('inf')
        is_ok = ratio <= 1.0
        
        return {
            "V_max_N": V_max,
            "fv_MPa": fv / MPA_TO_PA if fv != float('inf') else float('inf'), # Convert to MPa, handle inf
            "Fv_MPa": Fv / MPA_TO_PA,
            "ratio": ratio,
            "is_ok": is_ok,
            "status": "ผ่าน (OK)" if is_ok else "ไม่ผ่าน (NG)"
        }
    def _check_deflection(self, w_x_total_unfactored: float, w_y_total_unfactored: float, is_live_load_only: bool = False) -> dict:
        """Calculates and checks vertical deflection for given unfactored loads."""
        # Deflection formula: delta = 5*w*L^4 / (384*E*I)
        # Calculate deflection components along section axes
        # Handle potential division by zero for Ix or Iy if they are zero (e.g., malformed section data)
        delta_x = (5 * w_x_total_unfactored * (self.L**4)) / (384 * E_STEEL * self.Ix) if self.Ix > 0 else float('inf')
        delta_y = (5 * w_y_total_unfactored * (self.L**4)) / (384 * E_STEEL * self.Iy) if self.Iy > 0 else float('inf')
        # Resolve components to get vertical deflection
        delta_vertical = (delta_x * math.cos(self.theta_rad)) + (delta_y * math.sin(self.theta_rad))
        
        # Allowable deflections
        allowable_delta_ll = self.L / LIVE_LOAD_DEFLECTION_LIMIT_RATIO
        allowable_delta_total = self.L / TOTAL_LOAD_DEFLECTION_LIMIT_RATIO

        # For deflection, we usually care about the absolute magnitude
        delta_vertical_abs = abs(delta_vertical)

        is_ll_ok = True # Default to true if not checking LL only
        is_total_ok = True

        if is_live_load_only:
            is_ll_ok = delta_vertical_abs <= allowable_delta_ll
            is_total_ok = True # Not applicable for LL only check
        else:
            is_total_ok = delta_vertical_abs <= allowable_delta_total
            is_ll_ok = True # Not applicable for total load check

        return {
            "delta_vertical_mm": delta_vertical * 1000, # Keep original sign for debugging
            "delta_vertical_abs_mm": delta_vertical_abs * 1000, # Magnitude for comparison
            "allowable_ll_mm": allowable_delta_ll * 1000,
            "allowable_total_mm": allowable_delta_total * 1000,
            "is_ll_ok": is_ll_ok,
            "is_total_ok": is_total_ok,
        }


def format_detailed_report(design: PurlinDesign, results: dict) -> str:
    """Formats a detailed calculation report into a string."""
    # Helper for formatting numbers
    def f(n, d=2): return f"{n:,.{d}f}"

    # Get data from objects
    inputs = results['Inputs']
    section_name = results["Inputs"]["Section"]
    props = STEEL_SECTIONS[section_name]
    theta_rad = design.theta_rad

    # Start building the report string
    report = []
    report.append(f"--- รายการคำนวณออกแบบแปเหล็ก: {section_name} ---")
    report.append("=" * 60)

    # 1. ข้อมูลนำเข้าและคุณสมบัติหน้าตัด
    report.append("1. ข้อมูลนำเข้าและคุณสมบัติหน้าตัด")
    report.append(f"  - ความยาวช่วงแป (L)      = {f(design.L)} m")
    report.append(f"  - ระยะห่างแป (Spacing)   = {f(design.spacing)} m")
    report.append(f"  - มุมหลังคา (θ)           = {f(design.slope_deg)} °")
    report.append(f"  - Fy                    = {f(props.Fy, 0)} MPa")
    report.append(f"  - Sx                    = {f(design.Sx * 1e9, 0)} mm³")
    report.append(f"  - Sy                    = {f(design.Sy * 1e9, 0)} mm³")
    report.append(f"  - Ix                    = {f(design.Ix * 1e12, 0)} mm⁴")
    report.append(f"  - Iy                    = {f(design.Iy * 1e12, 0)} mm⁴")
    report.append(f"  - E                     = {f(E_STEEL / 1e9, 0)} GPa")
    report.append("-" * 60)

    # 2. การคำนวณน้ำหนักบรรทุก (Loads)
    w_dl_applied = design.dl_kPa * KPA_TO_PA * design.spacing
    w_ll = design.ll_kPa * KPA_TO_PA * design.spacing
    w_dl_total = w_dl_applied + design.purlin_weight_per_m
    report.append("2. การคำนวณน้ำหนักบรรทุก (Load Calculation)")
    report.append(f"  - น้ำหนักบรรทุกคงที่ (DL)    = {f(design.dl_kPa)} kPa * {f(design.spacing)} m = {f(w_dl_applied)} N/m")
    report.append(f"  - น้ำหนักแป (Self-weight)  = {f(props.weight)} kg/m * {f(G)} m/s² = {f(design.purlin_weight_per_m)} N/m")
    report.append(f"  - w_DL_total              = {f(w_dl_applied)} + {f(design.purlin_weight_per_m)} = {f(w_dl_total)} N/m")
    report.append(f"  - น้ำหนักบรรทุกจร (LL)      = {f(design.ll_kPa)} kPa * {f(design.spacing)} m = {f(w_ll)} N/m")
    report.append(f"  - แรงลม (คำนวณ) Uplift={f(inputs['Calculated Wind Uplift (kPa)'], 3)} kPa, Downward={f(inputs['Calculated Wind Downward (kPa)'], 3)} kPa")
    report.append("-" * 60)

    # 3. การตรวจสอบหน่วยแรงดัด (Bending Stress Check)
    stress_check = results['Stress Check']
    stress_details = stress_check.get('Details', {})
    report.append("3. การตรวจสอบหน่วยแรงดัด (Bending Stress Check)")
    report.append(f"  - กรณีวิกฤตที่สุด: {stress_check['Critical Load Case']}")
    if stress_details:
        w_x, w_y = stress_details['w_x'], stress_details['w_y']
        Mx, My = stress_details['Mx'], stress_details['My']
        fbx, fby = stress_details['fbx_MPa'], stress_details['fby_MPa']
        Fbx = (ALLOWABLE_BENDING_STRESS_FACTOR_X * design.Fy) / MPA_TO_PA
        Fby = (ALLOWABLE_BENDING_STRESS_FACTOR_Y * design.Fy) / MPA_TO_PA

        report.append(f"  - แรงกระทำตามแนวแกน (Factored Loads):")
        report.append(f"    - w_x = {f(w_x)} N/m (ตั้งฉากหลังคา)")
        report.append(f"    - w_y = {f(w_y)} N/m (ขนานหลังคา)")
        report.append(f"  - โมเมนต์ดัดสูงสุด (M = wL²/8):")
        report.append(f"    - Mx = {f(w_x)} * ({f(design.L)}²) / 8 = {f(Mx)} Nm")
        report.append(f"    - My = {f(w_y)} * ({f(design.L)}²) / 8 = {f(My)} Nm")
        report.append(f"  - หน่วยแรงดัดที่เกิดขึ้นจริง (fb = M/S):")
        report.append(f"    - fbx = {f(Mx)} / ({design.Sx:.4e}) = {f(fbx)} MPa")
        report.append(f"    - fby = {f(My)} / ({design.Sy:.4e}) = {f(fby)} MPa")
        report.append(f"  - หน่วยแรงดัดที่ยอมให้:")
        report.append(f"    - Fbx = {ALLOWABLE_BENDING_STRESS_FACTOR_X:.2f} * Fy = {f(Fbx)} MPa")
        report.append(f"    - Fby = {ALLOWABLE_BENDING_STRESS_FACTOR_Y:.2f} * Fy = {f(Fby)} MPa")
        report.append(f"  - ตรวจสอบ (Interaction): fbx/Fbx + fby/Fby <= 1.0")
        report.append(f"    - {f(fbx)}/{f(Fbx)} + {f(fby)}/{f(Fby)} = {f(stress_check['Interaction Ratio'], 3)}")
        report.append(f"  - ผลลัพธ์: {stress_check['Status']}")
    else:
        report.append("  - ไม่สามารถคำนวณรายละเอียดได้ (อาจไม่มีแรงกระทำ)")
    
    # 3.5 Shear Stress Check
    shear_check = results['Shear Check']
    report.append("\n  3.5) การตรวจสอบหน่วยแรงเฉือน (Shear Stress Check)")
    report.append(f"    - กรณีวิกฤตที่สุด: {shear_check['Critical Load Case']}")
    V_max_N = shear_check['V_max (kN)'] * 1000
    report.append(f"    - แรงเฉือนสูงสุด (V_max = w_x*L/2) = {f(V_max_N)} N = {f(V_max_N/1000)} kN")
    report.append(f"    - หน่วยแรงเฉือนที่เกิดขึ้น (fv = V_max / (d*tw)) = {f(shear_check['fv (MPa)'])} MPa")
    report.append(f"    - หน่วยแรงเฉือนที่ยอมให้ (Fv = {ALLOWABLE_SHEAR_STRESS_FACTOR:.2f}*Fy) = {f(shear_check['Fv (MPa)'])} MPa")
    report.append(f"    - ตรวจสอบ (fv/Fv <= 1.0): {f(shear_check['Ratio'], 3)}")
    report.append(f"    - ผลลัพธ์: {shear_check['Status']}")

    report.append("-" * 60)

    # 4. การตรวจสอบการแอ่นตัว (Deflection Check)
    deflection_check = results['Deflection Check']
    ll_details = deflection_check['LL_Details']
    total_details = deflection_check.get('Total_Details', {})
    allowable_ll_mm = results['Allowable Deflection (mm)']['Live Load (L/240)']
    allowable_total_mm = results['Allowable Deflection (mm)']['Total (L/180)']

    report.append("4. การตรวจสอบการแอ่นตัว (Deflection Check)")
    # Live Load Deflection
    report.append(f"  4.1) กรณีน้ำหนักบรรทุกจร (Live Load Only)")
    w_x_ll, w_y_ll = ll_details.get('w_x', 0), ll_details.get('w_y', 0)
    delta_x_ll = (5 * w_x_ll * (design.L**4)) / (384 * E_STEEL * design.Ix) if design.Ix > 0 else float('inf')
    delta_y_ll = (5 * w_y_ll * (design.L**4)) / (384 * E_STEEL * design.Iy) if design.Iy > 0 else float('inf')
    delta_v_ll_mm = ll_details.get('delta_v_mm', 0)
    report.append(f"    - Δx = 5*w_x*L⁴/(384EIx) = 5*({f(w_x_ll)})*({f(design.L)}⁴)/(384*E*{f(design.Ix):.4e}) = {f(delta_x_ll*1000)} mm")
    report.append(f"    - Δy = 5*w_y*L⁴/(384EIy) = 5*({f(w_y_ll)})*({f(design.L)}⁴)/(384*E*{f(design.Iy):.4e}) = {f(delta_y_ll*1000)} mm")
    report.append(f"    - Δ_vertical = Δx*cos(θ) + Δy*sin(θ) = {f(delta_v_ll_mm)} mm")
    report.append(f"    - Δ_allowable = L/240 = {f(design.L*1000)}/240 = {f(allowable_ll_mm)} mm")
    report.append(f"    - ผลลัพธ์: {deflection_check['Live Load']}")
    
    # Total Load Deflection
    report.append(f"\n  4.2) กรณีน้ำหนักรวม (Total Load)")
    report.append(f"    - กรณีวิกฤตที่สุด: {deflection_check.get('Critical Total Load Case', 'N/A')}")
    if total_details: # Check if total_details is not empty
        w_x_total, w_y_total = total_details.get('w_x', 0), total_details.get('w_y', 0)
        delta_x_total = (5 * w_x_total * (design.L**4)) / (384 * E_STEEL * design.Ix) if design.Ix > 0 else float('inf')
        delta_y_total = (5 * w_y_total * (design.L**4)) / (384 * E_STEEL * design.Iy) if design.Iy > 0 else float('inf')
        delta_v_total_mm = total_details.get('delta_v_mm', 0)
        report.append(f"    - Δx = 5*w_x*L⁴/(384EIx) = 5*({f(w_x_total)})*({f(design.L)}⁴)/(384*E*{f(design.Ix):.4e}) = {f(delta_x_total*1000)} mm")
        report.append(f"    - Δy = 5*w_y*L⁴/(384EIy) = 5*({f(w_y_total)})*({f(design.L)}⁴)/(384*E*{f(design.Iy):.4e}) = {f(delta_y_total*1000)} mm")
        report.append(f"    - Δ_vertical = Δx*cos(θ) + Δy*sin(θ) = {f(delta_v_total_mm)} mm")
        report.append(f"    - Δ_allowable = L/180 = {f(design.L*1000)}/180 = {f(allowable_total_mm)} mm")
        report.append(f"    - ผลลัพธ์: {deflection_check['Total Load']}")
    else:
        report.append("    - ไม่สามารถคำนวณรายละเอียดได้ (อาจไม่มีแรงกระทำ)")
    report.append("-" * 60)

    # 5. สรุปผล
    report.append("5. สรุปผลการออกแบบ")
    report.append(f"  >>> {results.get('Final Result', 'N/A')} <<<")
    report.append("=" * 60)

    return "\n".join(report)

# --- GUI Application ---
class PurlinDesignApp:
    def __init__(self, master):
        self.master = master
        master.title("โปรแกรมออกแบบแปเหล็ก")
        master.geometry("850x800") # Increased size for larger font

        # Configure grid for better layout
        master.grid_rowconfigure(0, weight=0)
        master.grid_rowconfigure(1, weight=1)
        master.grid_columnconfigure(0, weight=1)

        # --- Input Frame ---
        self.input_frame = ttk.LabelFrame(master, text="ข้อมูลนำเข้า")
        self.input_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        self.input_frame.grid_columnconfigure(1, weight=1) # Make entry fields expand

        # Set font style for all ttk widgets
        style = ttk.Style(master)
        try:
            # Use a theme that respects font settings well
            style.theme_use('clam')
        except tk.TclError:
            pass # Use default theme if 'clam' is not available
        style.configure('.', font=('Tahoma', 14))
        style.configure('TLabelframe.Label', font=('Tahoma', 14, 'bold'))

        # Register validation command
        vcmd = (master.register(self._validate_float_input), '%P')

        # General Inputs
        row = 0
        ttk.Label(self.input_frame, text="หน้าตัดเหล็ก:").grid(row=row, column=0, padx=5, pady=2, sticky="w")
        self.section_var = tk.StringVar(master)
        self.section_combobox = ttk.Combobox(self.input_frame, textvariable=self.section_var,
                                             values=list(STEEL_SECTIONS.keys()), state="readonly")
        self.section_combobox.grid(row=row, column=1, padx=5, pady=2, sticky="ew")
        self.section_combobox.set("C150x65x20x4.0") # Default selection
        row += 1

        ttk.Label(self.input_frame, text="ความยาวช่วงแป (m):").grid(row=row, column=0, padx=5, pady=2, sticky="w")
        self.span_entry = ttk.Entry(self.input_frame, validate="key", validatecommand=vcmd)
        self.span_entry.grid(row=row, column=1, padx=5, pady=2, sticky="ew")
        self.span_entry.insert(0, "6.0")
        row += 1

        ttk.Label(self.input_frame, text="ระยะห่างแป (m):").grid(row=row, column=0, padx=5, pady=2, sticky="w")
        self.spacing_entry = ttk.Entry(self.input_frame, validate="key", validatecommand=vcmd)
        self.spacing_entry.grid(row=row, column=1, padx=5, pady=2, sticky="ew")
        self.spacing_entry.insert(0, "1.2")
        row += 1

        ttk.Label(self.input_frame, text="มุมลาดชันหลังคา (องศา):").grid(row=row, column=0, padx=5, pady=2, sticky="w")
        self.slope_entry = ttk.Entry(self.input_frame, validate="key", validatecommand=vcmd)
        self.slope_entry.grid(row=row, column=1, padx=5, pady=2, sticky="ew")
        self.slope_entry.insert(0, "15.0")
        row += 1

        # Load Inputs
        ttk.Label(self.input_frame, text="น้ำหนักบรรทุกคงที่ (kPa):").grid(row=row, column=0, padx=5, pady=2, sticky="w")
        self.dl_entry = ttk.Entry(self.input_frame, validate="key", validatecommand=vcmd)
        self.dl_entry.grid(row=row, column=1, padx=5, pady=2, sticky="ew")
        self.dl_entry.insert(0, f"{15 * 0.00981:.3f}") # Default value
        row += 1

        ttk.Label(self.input_frame, text="น้ำหนักบรรทุกจร (kPa):").grid(row=row, column=0, padx=5, pady=2, sticky="w")
        self.ll_entry = ttk.Entry(self.input_frame, validate="key", validatecommand=vcmd)
        self.ll_entry.grid(row=row, column=1, padx=5, pady=2, sticky="ew")
        self.ll_entry.insert(0, "0.50") # Default value
        row += 1

        # Wind Load Inputs (grouped in a sub-frame for clarity)
        self.wind_frame = ttk.LabelFrame(self.input_frame, text="ข้อมูลน้ำหนักลม (อ้างอิง ว.ส.ท.)")
        self.wind_frame.grid(row=row, column=0, columnspan=2, padx=5, pady=5, sticky="nsew")
        self.wind_frame.grid_columnconfigure(1, weight=1)
        wind_row = 0

        ttk.Label(self.wind_frame, text="ความเร็วลมพื้นฐาน (m/s):").grid(row=wind_row, column=0, padx=5, pady=2, sticky="w")
        self.wind_speed_entry = ttk.Entry(self.wind_frame, validate="key", validatecommand=vcmd)
        self.wind_speed_entry.grid(row=wind_row, column=1, padx=5, pady=2, sticky="ew")
        self.wind_speed_entry.insert(0, "30.0")
        wind_row += 1

        ttk.Label(self.wind_frame, text="ความสูงอาคารเฉลี่ย (m):").grid(row=wind_row, column=0, padx=5, pady=2, sticky="w")
        self.building_height_entry = ttk.Entry(self.wind_frame, validate="key", validatecommand=vcmd)
        self.building_height_entry.grid(row=wind_row, column=1, padx=5, pady=2, sticky="ew")
        self.building_height_entry.insert(0, "6.0")
        wind_row += 1

        ttk.Label(self.wind_frame, text="ประเภทสภาพภูมิประเทศ:").grid(row=wind_row, column=0, padx=5, pady=2, sticky="w")
        self.exposure_var = tk.StringVar(master)
        self.exposure_combobox = ttk.Combobox(self.wind_frame, textvariable=self.exposure_var,
                                              values=['B', 'C', 'D'], state="readonly")
        self.exposure_combobox.grid(row=wind_row, column=1, padx=5, pady=2, sticky="ew")
        self.exposure_combobox.set("C") # Default selection
        wind_row += 1

        ttk.Label(self.wind_frame, text="Cpi (บวก):").grid(row=wind_row, column=0, padx=5, pady=2, sticky="w")
        self.cpi_pos_entry = ttk.Entry(self.wind_frame, validate="key", validatecommand=vcmd)
        self.cpi_pos_entry.grid(row=wind_row, column=1, padx=5, pady=2, sticky="ew")
        self.cpi_pos_entry.insert(0, "0.18")
        wind_row += 1

        ttk.Label(self.wind_frame, text="Cpi (ลบ):").grid(row=wind_row, column=0, padx=5, pady=2, sticky="w")
        self.cpi_neg_entry = ttk.Entry(self.wind_frame, validate="key", validatecommand=vcmd)
        self.cpi_neg_entry.grid(row=wind_row, column=1, padx=5, pady=2, sticky="ew")
        self.cpi_neg_entry.insert(0, "-0.18")
        wind_row += 1

        # --- Button Frame ---
        button_frame = ttk.Frame(self.input_frame)
        button_frame.grid(row=row + 1, column=0, columnspan=2, pady=10)

        self.calculate_button = ttk.Button(button_frame, text="คำนวณ", command=self.calculate_design)
        self.calculate_button.pack(side=tk.LEFT, padx=5, ipady=2)

        self.find_button = ttk.Button(button_frame, text="ค้นหาหน้าตัดที่ประหยัดที่สุด", command=self.find_economical_section)
        self.find_button.pack(side=tk.LEFT, padx=5, ipady=2)

        self.export_pdf_button = ttk.Button(button_frame, text="Export PDF", command=self.export_pdf)
        self.export_pdf_button.pack(side=tk.LEFT, padx=5, ipady=2)
        if not REPORTLAB_AVAILABLE:
            self.export_pdf_button.config(state="disabled")

        # --- Output Frame ---
        # Use a Notebook to create tabs for report and graph
        self.notebook = ttk.Notebook(master)
        self.notebook.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")

        # --- Report Tab ---
        self.report_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.report_tab, text='รายงาน chi tiết')
        self.report_tab.grid_rowconfigure(0, weight=1)
        self.report_tab.grid_columnconfigure(0, weight=1)
        
        # Use a monospaced font for the report to align text properly
        report_font = ("Consolas", 14)
        self.results_text = tk.Text(self.report_tab, wrap="word", height=15, font=report_font)
        self.results_text.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")

        # Add a scrollbar to the text widget
        self.text_scrollbar = ttk.Scrollbar(self.report_tab, orient="vertical", command=self.results_text.yview)
        self.text_scrollbar.grid(row=0, column=1, sticky="ns")
        self.results_text.config(yscrollcommand=self.text_scrollbar.set)

        # --- Graph Tab ---
        self.graph_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.graph_tab, text='กราฟผลลัพธ์')

        self.fig = Figure(figsize=(8, 6), dpi=100, tight_layout=True)
        self.ax = self.fig.add_subplot(111)

        self.canvas = FigureCanvasTkAgg(self.fig, master=self.graph_tab)
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        self._clear_plot() # Initialize with a clean plot

    def _validate_float_input(self, P):
        """Validates that the input is a valid floating-point number string."""
        if P == "" or P == "-":
            return True
        try:
            float(P)
            return True
        except ValueError:
            # Beep to provide feedback on invalid key press
            self.master.bell()
            return False

    def get_float_from_entry(self, entry_widget, name):
        try:
            return float(entry_widget.get())
        except ValueError:
            raise ValueError(f"กรุณาป้อนตัวเลขที่ถูกต้องสำหรับ '{name}'")

    def _get_inputs(self) -> dict:
        """Gathers and validates all inputs from the GUI."""
        try:
            inputs = {
                "section_name": self.section_var.get(),
                "purlin_span": self.get_float_from_entry(self.span_entry, "ความยาวช่วงแป"),
                "purlin_spacing": self.get_float_from_entry(self.spacing_entry, "ระยะห่างแป"),
                "roof_slope_degree": self.get_float_from_entry(self.slope_entry, "มุมลาดชันหลังคา"),
                "dead_load_kPa": self.get_float_from_entry(self.dl_entry, "น้ำหนักบรรทุกคงที่"),
                "live_load_kPa": self.get_float_from_entry(self.ll_entry, "น้ำหนักบรรทุกจร"),
                "basic_wind_speed_mps": self.get_float_from_entry(self.wind_speed_entry, "ความเร็วลมพื้นฐาน"),
                "building_height_m": self.get_float_from_entry(self.building_height_entry, "ความสูงอาคารเฉลี่ย"),
                "exposure_category": self.exposure_var.get(),
                "internal_pressure_coeff_pos": self.get_float_from_entry(self.cpi_pos_entry, "Cpi (บวก)"),
                "internal_pressure_coeff_neg": self.get_float_from_entry(self.cpi_neg_entry, "Cpi (ลบ)"),
            }
            return inputs
        except ValueError as e:
            messagebox.showerror("ข้อผิดพลาดในการป้อนข้อมูล", str(e))
            return None

    def calculate_design(self):
        inputs = self._get_inputs()
        if not inputs:
            return

        try:
            design = PurlinDesign(
                section_name=inputs['section_name'],
                purlin_span=inputs['purlin_span'],
                purlin_spacing=inputs['purlin_spacing'],
                roof_slope_degree=inputs['roof_slope_degree'],
                dead_load_kPa=inputs['dead_load_kPa'],
                live_load_kPa=inputs['live_load_kPa'],
                basic_wind_speed_mps=inputs['basic_wind_speed_mps'],
                building_height_m=inputs['building_height_m'],
                exposure_category=inputs['exposure_category'],
                internal_pressure_coeff_pos=inputs['internal_pressure_coeff_pos'],
                internal_pressure_coeff_neg=inputs['internal_pressure_coeff_neg'],
                gust_effect_factor=0.85,
                topographic_factor=1.0,
                wind_directionality_factor=0.85
            )
            results = design.run_check()
            summary_str = format_detailed_report(design, results) # Call the new detailed report function
            
            # Update text report
            self.results_text.delete(1.0, tk.END) # Clear previous results
            self.results_text.insert(tk.END, summary_str)

            # Update graph
            self._plot_stress_interaction(results['Stress Check'].get("All Cases", []))

        except Exception as e:
            messagebox.showerror("ข้อผิดพลาด", f"เกิดข้อผิดพลาดที่ไม่คาดคิด: {e}")

    def export_pdf(self):
        """Exports the current report in the text widget to a PDF file."""
        if not REPORTLAB_AVAILABLE:
            messagebox.showerror(
                "ไลบรารีไม่พร้อมใช้งาน",
                "กรุณาติดตั้งไลบรารี 'reportlab' เพื่อใช้งานฟังก์ชันนี้:\n\n"
                "pip install reportlab"
            )
            return

        report_text = self.results_text.get(1.0, tk.END).strip()
        if not report_text:
            messagebox.showinfo("ไม่มีข้อมูล", "กรุณาคำนวณผลลัพธ์ก่อนทำการ Export PDF")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF Documents", "*.pdf"), ("All Files", "*.*")],
            title="บันทึกรายงานเป็น PDF"
        )

        if not file_path:
            return # User cancelled

        try:
            # --- Font Setup ---
            # This function requires a TrueType font that supports Thai.
            # It will first look for 'THSarabunNew.ttf' in the script's directory.
            # If not found, it will try to use 'tahoma.ttf' from the Windows font directory.
            font_name = "THSarabunNew"
            font_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "THSarabunNew.ttf")
            
            if not os.path.exists(font_path):
                win_font_dir = os.path.join(os.environ.get("WINDIR", "C:/Windows"), "Fonts")
                font_path_win = os.path.join(win_font_dir, "tahoma.ttf")
                if os.path.exists(font_path_win):
                    font_name = "Tahoma"
                    font_path = font_path_win
                else:
                    messagebox.showerror("ไม่พบฟอนต์", "ไม่พบฟอนต์ 'THSarabunNew.ttf' ในโฟลเดอร์โปรแกรม\nและไม่พบฟอนต์สำรอง (tahoma.ttf) ในระบบ\n\nกรุณาดาวน์โหลดฟอนต์ที่รองรับภาษาไทยและวางไว้ในโฟลเดอร์เดียวกับโปรแกรม")
                    return
            
            pdfmetrics.registerFont(TTFont(font_name, font_path))

            # --- PDF Document Creation ---
            doc = SimpleDocTemplate(file_path, pagesize=letter, rightMargin=0.75*inch, leftMargin=0.75*inch, topMargin=0.75*inch, bottomMargin=0.75*inch)
            styles = getSampleStyleSheet()
            styles.add(ParagraphStyle(name='ReportStyle', fontName=font_name, fontSize=10, leading=14))
            
            story = []
            for line in report_text.split('\n'):
                # Replace multiple spaces with non-breaking spaces to preserve layout from monospaced font
                processed_line = re.sub(r' {2,}', lambda m: '\u00A0' * len(m.group(0)), line)
                p = Paragraph(processed_line, styles['ReportStyle'])
                story.append(p)

            doc.build(story)
            messagebox.showinfo("สำเร็จ", f"รายงานถูกบันทึกเป็น PDF เรียบร้อยแล้วที่:\n{file_path}")

        except Exception as e:
            messagebox.showerror("เกิดข้อผิดพลาด", f"ไม่สามารถสร้างไฟล์ PDF ได้:\n{e}")

    def _clear_plot(self):
        """Clears the plot and shows an empty state."""
        self.ax.clear()
        self.ax.set_title("กราฟแสดงผล Interaction Ratio")
        self.ax.set_xlabel("Load Combination")
        self.ax.set_ylabel("Interaction Ratio (fbx/Fbx + fby/Fby)")
        self.ax.text(0.5, 0.5, "กด 'คำนวณ' เพื่อแสดงกราฟ",
                     horizontalalignment='center', verticalalignment='center',
                     transform=self.ax.transAxes, fontsize=12, color='gray')
        self.canvas.draw()

    def _plot_stress_interaction(self, plot_data: list):
        """Creates a bar chart for stress interaction ratios."""
        self.ax.clear()

        if not plot_data:
            self._clear_plot()
            return

        names = [item['name'] for item in plot_data]
        ratios = [item['ratio'] for item in plot_data]
        
        bars = self.ax.bar(names, ratios, color='skyblue')
        self.ax.set_title("กราฟเปรียบเทียบ Interaction Ratio ของหน่วยแรงดัด")
        self.ax.set_xlabel("กรณีการรวมน้ำหนัก (Load Combination)")
        self.ax.set_ylabel("Interaction Ratio")
        self.ax.axhline(y=1.0, color='r', linestyle='--', label='Limit (1.0)')
        self.ax.legend()
        self.ax.tick_params(axis='x', rotation=45, labelsize='small')
        self.fig.tight_layout() # Adjust layout to prevent labels overlapping

        # Add value labels on top of each bar
        self.ax.bar_label(bars, fmt='%.3f', padding=3)
        self.canvas.draw()

    def find_economical_section(self):
        inputs = self._get_inputs()
        if not inputs:
            return

        try:
            sorted_sections = sorted(STEEL_SECTIONS.keys(), key=lambda k: STEEL_SECTIONS[k].weight)
            
            found_section = None
            final_results = None
            final_design_instance = None

            self.results_text.delete(1.0, tk.END)
            self._clear_plot()
            self.results_text.insert(tk.END, "กำลังค้นหาหน้าตัดที่ประหยัดที่สุด...\n\n")
            self.master.update_idletasks()

            for section in sorted_sections:
                self.results_text.insert(tk.END, f"กำลังตรวจสอบ: {section}...")
                self.master.update_idletasks()

                design_trial = PurlinDesign(
                    section_name=section,
                    purlin_span=inputs['purlin_span'],
                    purlin_spacing=inputs['purlin_spacing'],
                    roof_slope_degree=inputs['roof_slope_degree'],
                    dead_load_kPa=inputs['dead_load_kPa'],
                    live_load_kPa=inputs['live_load_kPa'],
                    basic_wind_speed_mps=inputs['basic_wind_speed_mps'],
                    building_height_m=inputs['building_height_m'],
                    exposure_category=inputs['exposure_category'],
                    internal_pressure_coeff_pos=inputs['internal_pressure_coeff_pos'],
                    internal_pressure_coeff_neg=inputs['internal_pressure_coeff_neg'],
                    gust_effect_factor=0.85,
                    topographic_factor=1.0,
                    wind_directionality_factor=0.85
                )
                results = design_trial.run_check()
                
                if results['is_ok']:
                    self.results_text.insert(tk.END, " ผ่าน (OK)\n")
                    found_section = section
                    final_results = results
                    final_design_instance = design_trial
                    break
                else:
                    self.results_text.insert(tk.END, " ไม่ผ่าน (NG)\n")

            if found_section:
                self.section_var.set(found_section)
                report_str = format_detailed_report(final_design_instance, final_results)
                self.results_text.delete(1.0, tk.END)
                self.results_text.insert(tk.END, report_str)
                self._plot_stress_interaction(final_results['Stress Check'].get("All Cases", []))
                messagebox.showinfo("สำเร็จ", f"พบหน้าตัดที่ประหยัดที่สุดคือ: {found_section}")
            else:
                self.results_text.insert(tk.END, "\nไม่พบหน้าตัดที่เหมาะสมในฐานข้อมูลสำหรับเงื่อนไขที่กำหนด")
                messagebox.showwarning("ไม่พบ", "ไม่พบหน้าตัดที่เหมาะสมในฐานข้อมูลสำหรับเงื่อนไขที่กำหนด")

        except Exception as e:
            messagebox.showerror("ข้อผิดพลาด", f"เกิดข้อผิดพลาดที่ไม่คาดคิดระหว่างการค้นหา: {e}")

# --- MAIN EXECUTION ---
if __name__ == "__main__":
    root = tk.Tk()
    app = PurlinDesignApp(root)
    root.mainloop()