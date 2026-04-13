"""
Truss Design Module (ออกแบบชิ้นส่วนโครงถัก)
Based on วสท. 011038-22 (Engineering Institute of Thailand Standard)
Supports both Tension and Compression member design (ASD/LRFD)
"""
import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from steel_sections import SteelSection
from design_codes import (
    calc_column_capacity_lrfd, asd_allowable_compression,
    PHI_c, PHI_t
)

@dataclass
class TrussLoad:
    """Represents loads on a truss member."""
    force_D: float = 0.0    # kN (positive for tension, negative for compression)
    force_L: float = 0.0    # kN
    force_W: float = 0.0    # kN

@dataclass
class TrussDesignResult:
    """Stores truss design calculation results."""
    is_ok: bool = False
    status: str = ""
    method: str = "ASD"
    member_type: str = "Tension"
    max_force: float = 0.0          # kN (Factored if LRFD)
    allowable_force: float = 0.0    # kN (phiRn if LRFD)
    ratio: float = 0.0
    slenderness: float = 0.0
    limit_slenderness: float = 0.0
    critical_load_case: str = ""
    details: Dict = field(default_factory=dict)

class TrussDesign:
    """
    Steel truss member design per วสท. 011038-22
    """
    def __init__(self, section: SteelSection, length: float,
                 method: str = "ASD",
                 K: float = 1.0):
        self.section = section
        self.length = length  # m
        self.method = method.upper()
        self.K = K
        
        self.Fy = section.Fy
        self.A = section.A
        self.r_min = min(section.rx, section.ry)

    def check_member(self, loads: TrussLoad) -> TrussDesignResult:
        result = TrussDesignResult(method=self.method)
        
        # 1. Determine governing load
        from load_combinations import LOAD_COMBINATIONS_ASD, LOAD_COMBINATIONS_LRFD
        combinations = LOAD_COMBINATIONS_LRFD if self.method == "LRFD" else LOAD_COMBINATIONS_ASD
        
        max_f = 0.0
        crit_case = ""
        
        for lc in combinations:
            f_factored = (lc.factors["D"] * loads.force_D + 
                          lc.factors["L"] * loads.force_L + 
                          lc.factors["W"] * loads.force_W)
            if abs(f_factored) > abs(max_f):
                max_f = f_factored
                crit_case = lc.name

        result.max_force = max_f
        result.critical_load_case = crit_case
        result.member_type = "Tension" if max_f >= 0 else "Compression"
        
        # 2. Slenderness Check
        L_mm = self.length * 1000.0
        result.slenderness = (self.K * L_mm) / self.r_min if self.r_min > 0 else 999
        result.limit_slenderness = 300.0 if result.member_type == "Tension" else 200.0
        
        # 3. Capacity Check
        if result.member_type == "Tension":
            # Simplified Tension Capacity (Gross Section Yielding only)
            if self.method == "LRFD":
                # phiRn = phi_t * Fy * Ag
                result.allowable_force = PHI_t * self.Fy * self.A / 1000.0
            else:
                # ASD: Ft = 0.60 * Fy
                result.allowable_force = (0.60 * self.Fy) * self.A / 1000.0
        else:
            # Compression Capacity
            if self.method == "LRFD":
                cap = calc_column_capacity_lrfd(self.section, self.length, self.K, self.K)
                result.allowable_force = cap.phi_Pn / 1000.0
            else:
                Fa = asd_allowable_compression(self.section, self.length, self.K, self.K)
                result.allowable_force = Fa * self.A / 1000.0

        result.ratio = abs(result.max_force) / result.allowable_force if result.allowable_force > 0 else 999
        result.is_ok = (result.ratio <= 1.0 and result.slenderness <= result.limit_slenderness)
        
        if result.is_ok:
            result.status = "ผ่าน (ADEQUATE)"
        else:
            reasons = []
            if result.ratio > 1.0: reasons.append("กำลังไม่พอ")
            if result.slenderness > result.limit_slenderness: reasons.append("ความชะลูดเกินเกณฑ์")
            result.status = f"ไม่ผ่าน ({', '.join(reasons)})"
            
        return result

def format_truss_report(result: TrussDesignResult, section_name: str, length: float) -> str:
    f = lambda n, d=2: f"{n:,.{d}f}"
    lines = [
        "=" * 60,
        f"รายการคำนวณชิ้นส่วนโครงถัก: {section_name} ({result.method})",
        f"ความยาว L = {f(length)} m, ประเภท: {result.member_type}",
        "=" * 60,
        f"\n1. การตรวจสอบกำลัง",
        f"  - กรณีวิกฤต: {result.critical_load_case}",
        f"  - แรงที่เกิดขึ้นสูงสุด = {f(abs(result.max_force))} kN",
        f"  - กำลังที่ยอมให้ = {f(result.allowable_force)} kN",
        f"  - อัตราส่วนกำลัง = {f(result.ratio, 3)}",
        f"\n2. การตรวจสอบความชะลูด",
        f"  - อัตราส่วน L/r = {f(result.slenderness, 1)}",
        f"  - เกณฑ์จำกัด L/r = {f(result.limit_slenderness, 0)}",
        "\n" + "=" * 60,
        f"สรุปผล: {result.status}",
        "=" * 60,
    ]
    return "\n".join(lines)
