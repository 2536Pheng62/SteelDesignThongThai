"""
Beam Design Module (ออกแบบคานเหล็ก)
Based on วสท. 011038-22 (Engineering Institute of Thailand Standard)
Implements both ASD (Allowable Stress Design) and LRFD (Load and Resistance Factor Design)
"""
import math
from dataclasses import dataclass, field
from typing import Dict, Optional, List
from steel_sections import SteelSection
from load_combinations import (
    LOAD_COMBINATIONS_ASD, LOAD_COMBINATIONS_LRFD,
    SERVICEABILITY_COMBINATIONS, DEFLECTION_LIMITS, SAFETY_FACTORS
)
from design_codes import (
    calc_beam_capacity_lrfd, asd_allowable_bending, asd_allowable_shear,
    PHI_b, PHI_v
)

# Constants
E_STEEL = 2.0e5  # MPa
G_STEEL = 7.9e4  # MPa


@dataclass
class BeamLoad:
    """Represents loads on a beam."""
    dead_load: float = 0.0      # kN/m
    live_load: float = 0.0      # kN/m
    wind_load: float = 0.0      # kN/m
    point_load_D: float = 0.0   # kN
    point_load_L: float = 0.0   # kN
    point_load_W: float = 0.0   # kN


@dataclass
class BeamDesignResult:
    """Stores beam design calculation results."""
    is_ok: bool = False
    status: str = ""
    method: str = "ASD"             # "ASD" or "LRFD"
    max_moment: float = 0.0         # kN-m (factored Mu if LRFD, else M)
    max_shear: float = 0.0          # kN (factored Vu if LRFD, else V)
    fb: float = 0.0                 # MPa - Actual bending stress (ASD only)
    fv: float = 0.0                 # MPa - Actual shear stress (ASD only)
    Fb: float = 0.0                 # MPa - Allowable bending stress (ASD only)
    Fv: float = 0.0                 # MPa - Allowable shear stress (ASD only)
    phi_Mn_kNm: float = 0.0         # kN-m (LRFD only)
    phi_Vn_kN: float = 0.0          # kN (LRFD only)
    stress_ratio: float = 0.0       # Mu/phiMn or fb/Fb
    shear_ratio: float = 0.0        # Vu/phiVn or fv/Fv
    delta_max: float = 0.0          # mm
    delta_allowable: float = 0.0    # mm
    deflection_ratio: float = 0.0
    critical_load_case: str = ""
    critical_shear_case: str = ""
    critical_deflection_case: str = ""
    details: Dict = field(default_factory=dict)


class BeamDesign:
    """
    Steel beam design per วสท. 011038-22 (AISC based)
    Supports both ASD and LRFD methods
    """
    
    def __init__(self, section: SteelSection, span: float, 
                 method: str = "ASD",
                 is_cantilever: bool = False,
                 lateral_bracing: str = "continuous",
                 deflection_type: str = "beam_live_load"):
        self.section = section
        self.span = span  # m
        self.method = method.upper()  # "ASD" or "LRFD"
        self.is_cantilever = is_cantilever
        self.lateral_bracing = lateral_bracing
        self.deflection_type = deflection_type
        
        # Section properties
        self.Fy = section.Fy
        self.Sx = section.Sx
        self.Zx = section.Zx
        self.Ix = section.Ix
        self.d = section.d
        self.tw = section.tw
        
    def calculate_moment(self, w: float, point_load: float = 0.0) -> float:
        """N-mm"""
        L_mm = self.span * 1000
        if self.is_cantilever:
            M = (w * L_mm**2 / 2) + (point_load * L_mm)
        else:
            M = (w * L_mm**2 / 8) + (point_load * L_mm / 4)
        return M
    
    def calculate_shear(self, w: float, point_load: float = 0.0) -> float:
        """N"""
        L_mm = self.span * 1000
        if self.is_cantilever:
            V = (w * L_mm) + point_load
        else:
            V = (w * L_mm / 2) + (point_load / 2)
        return V
    
    def calculate_deflection(self, w: float, point_load: float = 0.0) -> float:
        """mm"""
        L_mm = self.span * 1000
        if self.is_cantilever:
            delta = (w * L_mm**4 / (8 * E_STEEL * self.Ix)) + (point_load * L_mm**3 / (3 * E_STEEL * self.Ix))
        else:
            delta = (5 * w * L_mm**4 / (384 * E_STEEL * self.Ix)) + (point_load * L_mm**3 / (48 * E_STEEL * self.Ix))
        return delta

    def check_beam(self, loads: BeamLoad) -> BeamDesignResult:
        result = BeamDesignResult(method=self.method)
        result.details = {"load_cases": [], "deflection_checks": []}
        
        # 1. Determine Capacity
        if self.method == "LRFD":
            # Assume Lb = span if not continuous
            Lb = 0.0 if self.lateral_bracing == "continuous" else self.span * 1000.0
            cap = calc_beam_capacity_lrfd(self.section, Lb)
            phi_Mn = cap.phi_Mn  # N-mm
            phi_Vn = cap.phi_Vn  # N
            result.phi_Mn_kNm = phi_Mn / 1e6
            result.phi_Vn_kN = phi_Vn / 1000.0
        else:
            # ASD
            self.Fb = asd_allowable_bending(self.section, self.lateral_bracing)
            self.Fv = asd_allowable_shear(self.section)
            result.Fb = self.Fb
            result.Fv = self.Fv

        # 2. Deflection Limit
        limit_ratio = DEFLECTION_LIMITS.get(self.deflection_type, {}).get("limit_ratio", 360)
        delta_allowable = (self.span * 1000.0) / limit_ratio
        result.delta_allowable = delta_allowable

        # 3. Strength Check
        combinations = LOAD_COMBINATIONS_LRFD if self.method == "LRFD" else LOAD_COMBINATIONS_ASD
        
        max_ratio = 0.0
        for lc in combinations:
            factors = lc.factors
            w_kN_m = (factors["D"] * loads.dead_load + 
                      factors["L"] * loads.live_load + 
                      factors["W"] * loads.wind_load)
            P_kN = (factors["D"] * loads.point_load_D + 
                    factors["L"] * loads.point_load_L + 
                    factors["W"] * loads.point_load_W)
            
            # Internal forces (N-mm, N)
            Mu_Nmm = self.calculate_moment(w_kN_m, P_kN * 1000.0)
            Vu_N = self.calculate_shear(w_kN_m, P_kN * 1000.0)
            
            if self.method == "LRFD":
                ratio_m = Mu_Nmm / phi_Mn if phi_Mn > 0 else float("inf")
                ratio_v = Vu_N / phi_Vn if phi_Vn > 0 else float("inf")
            else:
                fb = Mu_Nmm / self.Sx if self.Sx > 0 else float("inf")
                fv = Vu_N / (self.d * self.tw) if (self.d * self.tw) > 0 else float("inf")
                ratio_m = fb / self.Fb if self.Fb > 0 else float("inf")
                ratio_v = fv / self.Fv if self.Fv > 0 else float("inf")

            case_ratio = max(ratio_m, ratio_v)
            result.details["load_cases"].append({
                "name": lc.name,
                "w": w_kN_m,
                "M": Mu_Nmm / 1e6,
                "V": Vu_N / 1000.0,
                "ratio_m": ratio_m,
                "ratio_v": ratio_v
            })

            if case_ratio > max_ratio:
                max_ratio = case_ratio
                result.max_moment = Mu_Nmm / 1e6
                result.max_shear = Vu_N / 1000.0
                result.stress_ratio = ratio_m
                result.shear_ratio = ratio_v
                result.critical_load_case = lc.name
                if self.method == "ASD":
                    result.fb, result.fv = fb, fv

        # 4. Serviceability Check
        max_delta = 0.0
        for lc in SERVICEABILITY_COMBINATIONS:
            w_kN_m = sum(lc.factors[k] * getattr(loads, f"{n}_load") for k, n in [("D","dead"), ("L","live"), ("W","wind")])
            P_kN = sum(lc.factors[k] * getattr(loads, f"point_load_{k}") for k in ["D", "L", "W"])
            delta = self.calculate_deflection(w_kN_m, P_kN * 1000.0)
            
            ratio = abs(delta) / delta_allowable if delta_allowable > 0 else float("inf")
            result.details["deflection_checks"].append({"name": lc.name, "delta": delta, "ratio": ratio})
            
            if abs(delta) > abs(max_delta):
                max_delta = delta
                result.delta_max = delta
                result.deflection_ratio = ratio
                result.critical_deflection_case = lc.name

        result.is_ok = (result.stress_ratio <= 1.0 and result.shear_ratio <= 1.0 and result.deflection_ratio <= 1.0)
        result.status = "ผ่าน (ADEQUATE)" if result.is_ok else "ไม่ผ่าน (INADEQUATE)"
        return result


def format_beam_report(result: BeamDesignResult, section_name: str, span: float) -> str:
    """Format report in Thai."""
    f = lambda n, d=2: f"{n:,.{d}f}"
    lines = [
        "=" * 60,
        f"รายการคำนวณออกแบบคานเหล็ก: {section_name} ({result.method})",
        f"ช่วงคาน L = {f(span)} m",
        "=" * 60,
        "\n1. ผลการตรวจสอบความแข็งแรง",
        f"  - กรณีวิกฤต: {result.critical_load_case}",
        f"  - โมเมนต์วิกฤต M = {f(result.max_moment)} kN-m",
    ]
    
    if result.method == "LRFD":
        lines.append(f"  - กำลังดัดที่ยอมให้ phi_Mn = {f(result.phi_Mn_kNm)} kN-m")
    else:
        lines.append(f"  - หน่วยแรงดัดที่เกิดขึ้น fb = {f(result.fb)} MPa")
        lines.append(f"  - หน่วยแรงดัดที่ยอมให้ Fb = {f(result.Fb)} MPa")
        
    lines.append(f"  - อัตราส่วนความแข็งแรง = {f(result.stress_ratio, 3)}")
    
    lines.append("\n2. การตรวจสอบการแอ่นตัว")
    lines.append(f"  - การแอ่นตัวสูงสุด delta = {f(result.delta_max)} mm")
    lines.append(f"  - การแอ่นตัวที่ยอมให้ allow = {f(result.delta_allowable)} mm")
    lines.append(f"  - อัตราส่วน = {f(result.deflection_ratio, 3)}")
    
    lines.append("\n" + "=" * 60)
    lines.append(f"สรุปผล: {result.status}")
    lines.append("=" * 60)
    return "\n".join(lines)
