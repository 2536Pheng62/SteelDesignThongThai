"""
Column Design Module (ออกแบบเสาเหล็ก)
Based on วสท. 011038-22 (Engineering Institute of Thailand Standard)
Implements both ASD (Allowable Stress Design) and LRFD (Load and Resistance Factor Design)
"""
import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from steel_sections import SteelSection
from load_combinations import (
    LOAD_COMBINATIONS_ASD, LOAD_COMBINATIONS_LRFD,
    EFFECTIVE_LENGTH_FACTORS, SAFETY_FACTORS
)
from design_codes import (
    calc_column_capacity_lrfd, check_combined_lrfd, 
    asd_allowable_compression, PHI_c
)

# Constants
E_STEEL = 2.0e5  # MPa
PI = math.pi


@dataclass
class ColumnLoad:
    """Represents loads on a column."""
    axial_load_D: float = 0.0    # kN
    axial_load_L: float = 0.0    # kN
    axial_load_W: float = 0.0    # kN
    moment_x_D: float = 0.0      # kN-m
    moment_x_L: float = 0.0      # kN-m
    moment_x_W: float = 0.0      # kN-m
    moment_y_D: float = 0.0      # kN-m
    moment_y_L: float = 0.0      # kN-m
    moment_y_W: float = 0.0      # kN-m


@dataclass
class ColumnDesignResult:
    """Stores column design calculation results."""
    is_ok: bool = False
    status: str = ""
    method: str = "ASD"
    max_axial_load: float = 0.0      # kN (factored Pu if LRFD, else P)
    allowable_axial_load: float = 0.0  # kN (phiPn if LRFD, else P_allow)
    axial_ratio: float = 0.0          # Pu/phiPn or P/P_allow
    KLx: float = 0.0                  # m
    KLy: float = 0.0                  # m
    slenderness_x: float = 0.0
    slenderness_y: float = 0.0
    critical_slenderness: float = 0.0
    Fa: float = 0.0                   # MPa (ASD only)
    fa: float = 0.0                   # MPa (ASD only)
    interaction_ratio: float = 0.0    # Combined axial + bending
    critical_load_case: str = ""
    details: Dict = field(default_factory=dict)


class ColumnDesign:
    """
    Steel column design per วสท. 011038-22
    Supports both ASD and LRFD methods
    """
    
    def __init__(self, section: SteelSection, height: float,
                 method: str = "ASD",
                 Kx: float = 1.0, Ky: float = 1.0,
                 is_braced_frame: bool = True):
        self.section = section
        self.height = height  # m
        self.method = method.upper()
        self.Kx = Kx
        self.Ky = Ky
        self.is_braced_frame = is_braced_frame
        
        # Section properties
        self.Fy = section.Fy
        self.A = section.A
        self.rx = section.rx
        self.ry = section.ry
        self.Sx = section.Sx
        self.Sy = section.Sy
        self.Zx = section.Zx
        self.Zy = section.Zy or (1.5 * section.Sy) # Approx if not in DB
        
    def check_combined_loading(self, loads: ColumnLoad) -> ColumnDesignResult:
        result = ColumnDesignResult(method=self.method)
        result.details = {"load_cases": []}
        
        # 1. Capacity
        if self.method == "LRFD":
            cap = calc_column_capacity_lrfd(self.section, self.height, self.Kx, self.Ky)
            phi_Pn = cap.phi_Pn # N
            result.phi_Pn_kN = phi_Pn / 1000.0
            result.allowable_axial_load = result.phi_Pn_kN
            
            # Simple beam capacity for interaction (Chapter F)
            # For simplicity in columns, use Mp if fully braced
            phi_Mnx = PHI_c * self.Fy * self.Zx
            phi_Mny = PHI_c * self.Fy * self.Zy
        else:
            # ASD
            self.Fa = asd_allowable_compression(self.section, self.height, self.Kx, self.Ky)
            result.Fa = self.Fa
            result.allowable_axial_load = self.Fa * self.A / 1000.0
            
            # ASD Allowable Bending (simplified)
            Fbx = 0.60 * self.Fy
            Fby = 0.75 * self.Fy

        # 2. Slenderness
        KLx = self.Kx * self.height * 1000.0
        KLy = self.Ky * self.height * 1000.0
        rx_ry = (self.rx, self.ry)
        result.KLx, result.KLy = KLx / 1000.0, KLy / 1000.0
        result.slenderness_x = KLx / rx_ry[0] if rx_ry[0] > 0 else 999
        result.slenderness_y = KLy / rx_ry[1] if rx_ry[1] > 0 else 999
        result.critical_slenderness = max(result.slenderness_x, result.slenderness_y)

        # 3. Check combinations
        combinations = LOAD_COMBINATIONS_LRFD if self.method == "LRFD" else LOAD_COMBINATIONS_ASD
        max_interaction = 0.0
        
        for lc in combinations:
            factors = lc.factors
            Pu_kN = (factors["D"] * loads.axial_load_D + factors["L"] * loads.axial_load_L + factors["W"] * loads.axial_load_W)
            Mux_kNm = (factors["D"] * loads.moment_x_D + factors["L"] * loads.moment_x_L + factors["W"] * loads.moment_x_W)
            Muy_kNm = (factors["D"] * loads.moment_y_D + factors["L"] * loads.moment_y_L + factors["W"] * loads.moment_y_W)

            if self.method == "LRFD":
                # AISC H1-1
                Pu_N = Pu_kN * 1000.0
                Mux_Nmm = Mux_kNm * 1e6
                Muy_Nmm = Muy_kNm * 1e6
                
                check = check_combined_lrfd(self.section, Pu_N, Mux_Nmm, Muy_Nmm, phi_Pn, phi_Mnx, phi_Mny)
                interaction = check.ratio
            else:
                # ASD Simplified
                fa = (Pu_kN * 1000.0) / self.A if self.A > 0 else 999
                fbx = (Mux_kNm * 1e6) / self.Sx if self.Sx > 0 else 0
                fby = (Muy_kNm * 1e6) / self.Sy if self.Sy > 0 else 0
                
                ratio_p = fa / self.Fa if self.Fa > 0 else 999
                interaction = ratio_p + (fbx / Fbx) + (fby / Fby)
            
            result.details["load_cases"].append({
                "name": lc.name, "P": Pu_kN, "Mx": Mux_kNm, "My": Muy_kNm, "ratio": interaction
            })
            
            if interaction > max_interaction:
                max_interaction = interaction
                result.max_axial_load = Pu_kN
                result.interaction_ratio = interaction
                result.critical_load_case = lc.name
                if self.method == "ASD": result.fa = fa

        result.axial_ratio = result.max_axial_load / result.allowable_axial_load if result.allowable_axial_load > 0 else 999
        result.is_ok = (result.interaction_ratio <= 1.0 and result.critical_slenderness <= 200)
        result.status = "ผ่าน (ADEQUATE)" if result.is_ok else "ไม่ผ่าน (INADEQUATE)"
        return result


def format_column_report(result: ColumnDesignResult, section_name: str, height: float) -> str:
    """Format report in Thai."""
    f = lambda n, d=2: f"{n:,.{d}f}"
    lines = [
        "=" * 60,
        f"รายการคำนวณออกแบบเสาเหล็ก: {section_name} ({result.method})",
        f"ความสูงเสา H = {f(height)} m",
        "=" * 60,
        "\n1. การตรวจสอบความชะลูด",
        f"  - KL/r วิฤต = {f(result.critical_slenderness, 1)} (จำกัด <= 200)",
        "\n2. การตรวจสอบแรงอัดและแรงดัดรวม",
        f"  - กรณีวิกฤต: {result.critical_load_case}",
        f"  - แรงอัดวิกฤต P = {f(result.max_axial_load)} kN",
        f"  - กำลังอัดที่ยอมให้ = {f(result.allowable_axial_load)} kN",
        f"  - อัตราส่วน Interaction = {f(result.interaction_ratio, 3)}",
        "\n" + "=" * 60,
        f"สรุปผล: {result.status}",
        "=" * 60,
    ]
    return "\n".join(lines)
