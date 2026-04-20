"""
Footing Design Module (ออกแบบฐานรากแผ่)
Simplified design for Isolated Footing
Supports Soil Bearing and Concrete Shear checks (ASD/LRFD)
"""
import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional

@dataclass
class FootingLoad:
    """Represents loads on a footing."""
    axial_load_D: float = 0.0    # kN
    axial_load_L: float = 0.0    # kN
    moment_x: float = 0.0        # kN-m (for future expansion)
    moment_y: float = 0.0        # kN-m

@dataclass
class FootingDesignResult:
    """Stores footing design calculation results."""
    is_ok: bool = False
    status: str = ""
    bearing_ratio: float = 0.0
    shear_1way_ratio: float = 0.0
    shear_2way_ratio: float = 0.0
    required_area: float = 0.0   # m²
    actual_area: float = 0.0     # m²
    soil_pressure: float = 0.0   # kPa
    details: Dict = field(default_factory=dict)

class FootingDesign:
    """
    Isolated Footing design logic
    """
    def __init__(self, width: float, length: float, thickness: float,
                 allowable_bearing_kPa: float,
                 fc_MPa: float = 21.0, fy_MPa: float = 390.0,
                 concrete_cover_mm: float = 75.0):
        self.B = width       # m
        self.L = length      # m
        self.H = thickness   # m
        self.qa = allowable_bearing_kPa
        self.fc = fc_MPa
        self.fy = fy_MPa
        self.cover = concrete_cover_mm
        
        self.d = (self.H * 1000.0) - self.cover - 12.0 # Effective depth approx (assume DB12)

    def check_footing(self, loads: FootingLoad) -> FootingDesignResult:
        result = FootingDesignResult()
        
        # 1. Soil Bearing Check (ASD - Service Loads)
        total_p = loads.axial_load_D + loads.axial_load_L
        # Add self-weight of footing
        self_weight = (self.B * self.L * self.H) * 24.0 # 24 kN/m³ for reinforced concrete
        p_service = total_p + self_weight
        
        result.actual_area = self.B * self.L
        result.soil_pressure = p_service / result.actual_area if result.actual_area > 0 else 999
        result.bearing_ratio = result.soil_pressure / self.qa if self.qa > 0 else 999
        
        # 2. Concrete Shear Check (Simplified LRFD logic for shear)
        # Pu = 1.2D + 1.6L
        Pu = (1.2 * loads.axial_load_D + 1.6 * loads.axial_load_L)
        qu = Pu / result.actual_area # Factored soil pressure (net)
        phi_v = 0.75
        
        # One-way Shear
        # Assume column size 0.3x0.3m for simplicity if not provided
        col_s = 0.3
        critical_dist = (self.L - col_s) / 2.0 - (self.d / 1000.0)
        if critical_dist > 0:
            Vu1 = qu * self.B * critical_dist
            # phiVc = 0.75 * (1/6) * sqrt(fc) * B * d
            phiVc1 = phi_v * (1.0/6.0) * math.sqrt(self.fc) * (self.B * 1000.0) * self.d / 1000.0
            result.shear_1way_ratio = Vu1 / phiVc1 if phiVc1 > 0 else 999
        else:
            result.shear_1way_ratio = 0.0
            
        # Two-way Shear (Punching)
        bo = 4 * (col_s * 1000.0 + self.d) # Perimeter
        Vu2 = qu * (result.actual_area - (col_s + self.d/1000.0)**2)
        phiVc2 = phi_v * (1.0/3.0) * math.sqrt(self.fc) * bo * self.d / 1000.0
        result.shear_2way_ratio = Vu2 / phiVc2 if phiVc2 > 0 else 999
        
        result.is_ok = (result.bearing_ratio <= 1.0 and 
                        result.shear_1way_ratio <= 1.0 and 
                        result.shear_2way_ratio <= 1.0)
        
        if result.is_ok:
            result.status = "ผ่าน (ADEQUATE)"
        else:
            reasons = []
            if result.bearing_ratio > 1.0: reasons.append("แรงดันดินเกิน")
            if result.shear_1way_ratio > 1.0 or result.shear_2way_ratio > 1.0: reasons.append("แรงเฉือนคอนกรีตเกิน")
            result.status = f"ไม่ผ่าน ({', '.join(reasons)})"
            
        return result

def format_footing_report(result: FootingDesignResult, B: float, L: float, H: float) -> str:
    f = lambda n, d=2: f"{n:,.{d}f}"
    lines = [
        "=" * 60,
        f"รายการคำนวณฐานรากแผ่: {f(B)} x {f(L)} x {f(H)} m",
        "=" * 60,
        f"\n1. การตรวจสอบแรงดันดิน (Soil Bearing)",
        f"  - แรงดันดินที่เกิดขึ้น = {f(result.soil_pressure)} kPa",
        f"  - แรงดันดินที่ยอมให้ = {f(result.soil_pressure / result.bearing_ratio if result.bearing_ratio > 0 else 0)} kPa",
        f"  - อัตราส่วน = {f(result.bearing_ratio, 3)}",
        f"\n2. การตรวจสอบแรงเฉือนคอนกรีต",
        f"  - One-way Shear Ratio = {f(result.shear_1way_ratio, 3)}",
        f"  - Punching Shear Ratio = {f(result.shear_2way_ratio, 3)}",
        "\n" + "=" * 60,
        f"สรุปผล: {result.status}",
        "=" * 60,
    ]
    return "\n".join(lines)
