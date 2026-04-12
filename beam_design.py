"""
Beam Design Module (ออกแบบคานเหล็ก)
Based on วสท. 011038-22 (Engineering Institute of Thailand Standard)
Implements ASD (Allowable Stress Design) method
"""
import math
from dataclasses import dataclass
from typing import Dict, Optional
from steel_sections import SteelSection
from load_combinations import (
    LOAD_COMBINATIONS_ASD, SERVICEABILITY_COMBINATIONS, 
    DEFLECTION_LIMITS, SAFETY_FACTORS
)

# Constants
E_STEEL = 2.0e5  # MPa - Modulus of elasticity for steel
G_STEEL = 7.9e4  # MPa - Shear modulus for steel


@dataclass
class BeamLoad:
    """Represents loads on a beam."""
    dead_load: float = 0.0      # kN/m or kN
    live_load: float = 0.0      # kN/m or kN
    wind_load: float = 0.0      # kN/m or kN
    point_load_D: float = 0.0   # kN (point load at midspan)
    point_load_L: float = 0.0   # kN
    point_load_W: float = 0.0   # kN


@dataclass
class BeamDesignResult:
    """Stores beam design calculation results."""
    is_ok: bool = False
    status: str = ""
    max_moment: float = 0.0         # kN-m
    max_shear: float = 0.0          # kN
    fb: float = 0.0                 # MPa - Actual bending stress
    fv: float = 0.0                 # MPa - Actual shear stress
    Fb: float = 0.0                 # MPa - Allowable bending stress
    Fv: float = 0.0                 # MPa - Allowable shear stress
    stress_ratio: float = 0.0       # fb/Fb
    shear_ratio: float = 0.0        # fv/Fv
    delta_max: float = 0.0          # mm - Maximum deflection
    delta_allowable: float = 0.0    # mm - Allowable deflection
    deflection_ratio: float = 0.0   # delta_max/delta_allowable
    critical_load_case: str = ""
    critical_shear_case: str = ""
    critical_deflection_case: str = ""
    details: Dict = None


class BeamDesign:
    """
    Steel beam design per วสท. 011038-22
    Checks bending, shear, and deflection
    """
    
    def __init__(self, section: SteelSection, span: float, 
                 is_cantilever: bool = False,
                 lateral_bracing: str = "continuous",
                 deflection_type: str = "beam_live_load"):
        """
        Args:
            section: Steel section properties
            span: Beam span in meters
            is_cantilever: True if cantilever beam
            lateral_bracing: Lateral bracing type ("continuous", "ends_only", "intermediate")
            deflection_type: Type for deflection limit check
        """
        self.section = section
        self.span = span  # m
        self.is_cantilever = is_cantilever
        self.lateral_bracing = lateral_bracing
        self.deflection_type = deflection_type
        
        # Convert section properties to consistent units (N, mm)
        self.Fy = section.Fy  # MPa
        self.Fu = section.Fu  # MPa
        self.Sx = section.Sx  # mm³
        self.Ix = section.Ix  # mm⁴
        self.d = section.d    # mm
        self.tw = section.tw  # mm
        self.bf = section.bf  # mm
        self.tf = section.tf  # mm
        self.rx = section.rx  # mm
        self.ry = section.ry  # mm
        self.Zx = section.Zx  # mm³
        self.J = section.J    # mm⁴
        self.Cw = section.Cw  # mm⁶
        
    def calculate_moment(self, w: float, point_load: float = 0.0) -> float:
        """
        Calculate maximum bending moment
        Args:
            w: Distributed load in N/mm
            point_load: Point load at midspan in N
        Returns:
            Maximum moment in N-mm
        """
        L_mm = self.span * 1000  # Convert to mm
        
        if self.is_cantilever:
            # Cantilever: M = wL²/2 + PL
            M_dist = w * L_mm**2 / 2
            M_point = point_load * L_mm
        else:
            # Simply supported: M = wL²/8 + PL/4
            M_dist = w * L_mm**2 / 8
            M_point = point_load * L_mm / 4
            
        return M_dist + M_point
    
    def calculate_shear(self, w: float, point_load: float = 0.0) -> float:
        """
        Calculate maximum shear force
        Args:
            w: Distributed load in N/mm
            point_load: Point load at midspan in N
        Returns:
            Maximum shear in N
        """
        L_mm = self.span * 1000
        
        if self.is_cantilever:
            # Cantilever: V = wL + P
            V_dist = w * L_mm
            V_point = point_load
        else:
            # Simply supported: V = wL/2 + P/2
            V_dist = w * L_mm / 2
            V_point = point_load / 2
            
        return V_dist + V_point
    
    def calculate_deflection(self, w: float, point_load: float = 0.0) -> float:
        """
        Calculate maximum deflection
        Args:
            w: Distributed load in N/mm
            point_load: Point load at midspan in N
        Returns:
            Maximum deflection in mm
        """
        L_mm = self.span * 1000
        
        if self.is_cantilever:
            # Cantilever: δ = wL⁴/(8EI) + PL³/(3EI)
            delta_dist = w * L_mm**4 / (8 * E_STEEL * self.Ix)
            delta_point = point_load * L_mm**3 / (3 * E_STEEL * self.Ix)
        else:
            # Simply supported: δ = 5wL⁴/(384EI) + PL³/(48EI)
            delta_dist = 5 * w * L_mm**4 / (384 * E_STEEL * self.Ix)
            delta_point = point_load * L_mm**3 / (48 * E_STEEL * self.Ix)
            
        return delta_dist + delta_point
    
    def calculate_allowable_bending_stress(self) -> float:
        """
        Calculate allowable bending stress per วสท. 011038-22
        Returns:
            Allowable bending stress in MPa
        """
        # For compact sections with continuous lateral bracing
        # Fb = 0.66 * Fy (for compact sections)
        # Fb = 0.60 * Fy (for non-compact sections)
        
        # Check if section is compact
        lambda_flange = self.bf / (2 * self.tf)
        lambda_web = self.d / self.tw
        
        # Compact section limits for I-shapes
        lambda_pf = 0.38 * math.sqrt(E_STEEL / self.Fy)
        lambda_pw = 3.76 * math.sqrt(E_STEEL / self.Fy)
        
        is_compact = (lambda_flange <= lambda_pf) and (lambda_web <= lambda_pw)
        
        if is_compact and self.lateral_bracing == "continuous":
            Fb = 0.66 * self.Fy
        else:
            # Check for lateral-torsional buckling
            Fb = 0.60 * self.Fy
            
            # For unbraced length, need to check LTB
            # This is simplified - full LTB check requires unbraced length
            if self.lateral_bracing == "ends_only":
                # Conservative reduction for long unbraced length
                Fb = 0.50 * self.Fy
        
        return Fb
    
    def calculate_allowable_shear_stress(self) -> float:
        """
        Calculate allowable shear stress per วสท. 011038-22
        Returns:
            Allowable shear stress in MPa
        """
        # Fv = 0.40 * Fy (for most sections)
        # Fv = 0.50 * Fy * Cv (with Cv for web shear buckling)
        
        h = self.d - 2 * self.tf  # Clear web height
        tw = self.tw
        h_tw = h / tw if tw > 0 else float('inf')
        
        # Web shear buckling coefficient
        kv = 5.34  # For unstiffened webs
        
        # Check if web is slender
        limit = 1.10 * math.sqrt(kv * E_STEEL / self.Fy)
        
        if h_tw <= limit:
            Cv = 1.0
        else:
            Cv = limit / h_tw
            
        Fv = 0.60 * self.Fy * Cv
        
        return Fv
    
    def check_beam(self, loads: BeamLoad) -> BeamDesignResult:
        """
        Perform complete beam design check
        Args:
            loads: Beam loads
        Returns:
            Design result
        """
        result = BeamDesignResult()
        result.details = {"load_cases": [], "deflection_checks": []}
        
        # Calculate allowable stresses
        self.Fb = self.calculate_allowable_bending_stress()
        self.Fv = self.calculate_allowable_shear_stress()
        
        # Get deflection limit
        if self.deflection_type in DEFLECTION_LIMITS:
            limit_ratio = DEFLECTION_LIMITS[self.deflection_type]["limit_ratio"]
        else:
            limit_ratio = 360  # Default L/360
            
        delta_allowable = (self.span * 1000) / limit_ratio  # mm
        
        # Check all load combinations
        critical_ratio = 0.0
        critical_shear = 0.0
        critical_deflection = 0.0
        
        for lc in LOAD_COMBINATIONS_ASD:
            factors = lc.factors
            
            # Calculate factored distributed load
            w = (factors["D"] * loads.dead_load + 
                 factors["L"] * loads.live_load + 
                 factors["W"] * loads.wind_load)
            
            # Convert kN/m to N/mm
            w_N_mm = w * 1000 / 1000  # kN/m = N/mm
            
            # Calculate factored point load
            P = (factors["D"] * loads.point_load_D + 
                 factors["L"] * loads.point_load_L + 
                 factors["W"] * loads.point_load_W)
            P_N = P * 1000  # Convert kN to N
            
            # Calculate moment and shear
            M = self.calculate_moment(w_N_mm, P_N)  # N-mm
            V = self.calculate_shear(w_N_mm, P_N)    # N
            
            # Calculate stresses
            fb = M / self.Sx if self.Sx > 0 else float('inf')  # MPa
            fv = V / (self.d * self.tw) if self.tw > 0 else float('inf')  # MPa
            
            # Check ratios
            stress_ratio = fb / self.Fb if self.Fb > 0 else float('inf')
            shear_ratio = fv / self.Fv if self.Fv > 0 else float('inf')
            
            # Store load case results
            result.details["load_cases"].append({
                "name": lc.name,
                "name_th": lc.name_th,
                "w_kN_m": w,
                "M_kNm": M / 1e6,
                "V_kN": V / 1000,
                "fb_MPa": fb,
                "fv_MPa": fv,
                "stress_ratio": stress_ratio,
                "shear_ratio": shear_ratio,
            })
            
            # Track critical values
            if stress_ratio > critical_ratio:
                critical_ratio = stress_ratio
                result.max_moment = M / 1e6  # Convert to kN-m
                result.max_shear = V / 1000  # Convert to kN
                result.fb = fb
                result.fv = fv
                result.stress_ratio = stress_ratio
                result.critical_load_case = f"{lc.name} ({lc.name_th})"
                
            if V > critical_shear:
                critical_shear = V
                result.critical_shear_case = f"{lc.name} ({lc.name_th})"
        
        # Serviceability check (deflection)
        for lc in SERVICEABILITY_COMBINATIONS:
            factors = lc.factors
            
            w = (factors["D"] * loads.dead_load + 
                 factors["L"] * loads.live_load + 
                 factors["W"] * loads.wind_load)
            w_N_mm = w * 1000 / 1000
            
            P = (factors["D"] * loads.point_load_D + 
                 factors["L"] * loads.point_load_L + 
                 factors["W"] * loads.point_load_W)
            P_N = P * 1000
            
            delta = self.calculate_deflection(w_N_mm, P_N)  # mm
            
            result.details["deflection_checks"].append({
                "name": lc.name,
                "name_th": lc.name_th,
                "delta_mm": delta,
                "delta_allowable_mm": delta_allowable,
                "ratio": delta / delta_allowable if delta_allowable > 0 else float('inf'),
            })
            
            if abs(delta) > abs(critical_deflection):
                critical_deflection = delta
                result.delta_max = delta
                result.critical_deflection_case = f"{lc.name} ({lc.name_th})"
        
        # Final results
        result.Fb = self.Fb
        result.Fv = self.Fv
        result.delta_allowable = delta_allowable
        result.deflection_ratio = abs(critical_deflection) / delta_allowable if delta_allowable > 0 else float('inf')
        result.shear_ratio = result.fv / result.Fv if result.Fv > 0 else float('inf')
        
        # Determine overall status
        bending_ok = result.stress_ratio <= 1.0
        shear_ok = result.shear_ratio <= 1.0
        deflection_ok = result.deflection_ratio <= 1.0
        
        result.is_ok = bending_ok and shear_ok and deflection_ok
        
        if result.is_ok:
            result.status = "ผ่าน (ADEQUATE) - คานสามารถรับน้ำหนักได้"
        else:
            issues = []
            if not bending_ok:
                issues.append(f"หน่วยแรงดัดไม่ผ่าน (ratio={result.stress_ratio:.3f})")
            if not shear_ok:
                issues.append(f"หน่วยแรงเฉือนไม่ผ่าน (ratio={result.shear_ratio:.3f})")
            if not deflection_ok:
                issues.append(f"การแอ่นตัวไม่ผ่าน (ratio={result.deflection_ratio:.3f})")
            result.status = f"ไม่ผ่าน (INADEQUATE) - {', '.join(issues)}"
        
        return result


def format_beam_report(result: BeamDesignResult, section_name: str, span: float) -> str:
    """Format beam design report in Thai"""
    def f(n, d=2):
        return f"{n:,.{d}f}"
    
    report = []
    report.append("=" * 70)
    report.append(f"รายการคำนวณออกแบบคานเหล็ก: {section_name}")
    report.append(f"ช่วงคาน L = {f(span)} m")
    report.append("=" * 70)
    
    report.append("\n1. คุณสมบัติหน้าตัด")
    report.append(f"  - Fy = {f(result.Fb / 0.66 if result.Fb > 0 else 0, 0)} MPa")
    report.append(f"  - Sx = {f(result.Fb * 1e6 / 0.66 if result.Fb > 0 else 0, 0)} mm³")
    
    report.append("\n2. การตรวจสอบหน่วยแรงดัด (Bending Stress Check)")
    report.append(f"  - กรณีวิกฤต: {result.critical_load_case}")
    report.append(f"  - โมเมนต์สูงสุด M = {f(result.max_moment)} kN-m")
    report.append(f"  - หน่วยแรงดัดที่เกิดขึ้น fb = {f(result.fb)} MPa")
    report.append(f"  - หน่วยแรงดัดที่ยอมให้ Fb = {f(result.Fb)} MPa")
    report.append(f"  - อัตราส่วน fb/Fb = {f(result.stress_ratio, 3)}")
    
    report.append("\n3. การตรวจสอบหน่วยแรงเฉือน (Shear Stress Check)")
    report.append(f"  - กรณีวิกฤต: {result.critical_shear_case}")
    report.append(f"  - แรงเฉือนสูงสุด V = {f(result.max_shear)} kN")
    report.append(f"  - หน่วยแรงเฉือนที่เกิดขึ้น fv = {f(result.fv)} MPa")
    report.append(f"  - หน่วยแรงเฉือนที่ยอมให้ Fv = {f(result.Fv)} MPa")
    report.append(f"  - อัตราส่วน fv/Fv = {f(result.shear_ratio, 3)}")
    
    report.append("\n4. การตรวจสอบการแอ่นตัว (Deflection Check)")
    report.append(f"  - กรณีวิกฤต: {result.critical_deflection_case}")
    report.append(f"  - การแอ่นตัวสูงสุด δ = {f(result.delta_max)} mm")
    report.append(f"  - การแอ่นตัวที่ยอมให้ δ_allow = {f(result.delta_allowable)} mm")
    report.append(f"  - อัตราส่วน δ/δ_allow = {f(result.deflection_ratio, 3)}")
    
    report.append("\n" + "=" * 70)
    report.append(f"สรุปผล: {result.status}")
    report.append("=" * 70)
    
    return "\n".join(report)
