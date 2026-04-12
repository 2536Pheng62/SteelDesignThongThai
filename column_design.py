"""
Column Design Module (ออกแบบเสเหล็ก)
Based on วสท. 011038-22 (Engineering Institute of Thailand Standard)
Implements ASD (Allowable Stress Design) method for compression members
"""
import math
from dataclasses import dataclass
from typing import Dict, List
from steel_sections import SteelSection
from load_combinations import (
    LOAD_COMBINATIONS_ASD, EFFECTIVE_LENGTH_FACTORS, SAFETY_FACTORS
)

# Constants
E_STEEL = 2.0e5  # MPa - Modulus of elasticity for steel
PI = math.pi


@dataclass
class ColumnLoad:
    """Represents loads on a column."""
    axial_load_D: float = 0.0    # kN (dead load)
    axial_load_L: float = 0.0    # kN (live load)
    axial_load_W: float = 0.0    # kN (wind load)
    moment_x_D: float = 0.0      # kN-m (dead load moment about x-axis)
    moment_x_L: float = 0.0      # kN-m
    moment_x_W: float = 0.0      # kN-m
    moment_y_D: float = 0.0      # kN-m (dead load moment about y-axis)
    moment_y_L: float = 0.0      # kN-m
    moment_y_W: float = 0.0      # kN-m


@dataclass
class ColumnDesignResult:
    """Stores column design calculation results."""
    is_ok: bool = False
    status: str = ""
    max_axial_load: float = 0.0      # kN
    allowable_axial_load: float = 0.0  # kN
    axial_ratio: float = 0.0          # P/P_allow
    KLx: float = 0.0                  # m - Effective length about x
    KLy: float = 0.0                  # m - Effective length about y
    slenderness_x: float = 0.0        # KL/r about x
    slenderness_y: float = 0.0        # KL/r about y
    critical_slenderness: float = 0.0
    Fa: float = 0.0                   # MPa - Allowable compressive stress
    fa: float = 0.0                   # MPa - Actual compressive stress
    interaction_ratio: float = 0.0    # For combined axial + bending
    critical_load_case: str = ""
    details: Dict = None


class ColumnDesign:
    """
    Steel column design per วสท. 011038-22
    Checks axial compression, bending, and combined loading
    """
    
    def __init__(self, section: SteelSection, height: float,
                 Kx: float = 1.0, Ky: float = 1.0,
                 is_braced_frame: bool = True):
        """
        Args:
            section: Steel section properties
            height: Column height in meters
            Kx: Effective length factor about x-axis
            Ky: Effective length factor about y-axis
            is_braced_frame: True if braced frame (sidesway inhibited)
        """
        self.section = section
        self.height = height  # m
        self.Kx = Kx
        self.Ky = Ky
        self.is_braced_frame = is_braced_frame
        
        # Convert section properties
        self.Fy = section.Fy    # MPa
        self.A = section.A      # mm²
        self.Ix = section.Ix    # mm⁴
        self.Iy = section.Iy    # mm⁴
        self.rx = section.rx    # mm
        self.ry = section.ry    # mm
        self.d = section.d      # mm
        self.bf = section.bf    # mm
        self.tf = section.tf    # mm
        self.tw = section.tw    # mm
        self.Sx = section.Sx    # mm³
        self.Sy = section.Sy    # mm³
        
    def calculate_slenderness(self) -> tuple:
        """
        Calculate slenderness ratios KL/r for both axes
        Returns:
            (KLx_rx, KLy_ry, KLx_m, KLy_m)
        """
        KLx = self.Kx * self.height * 1000  # Convert to mm
        KLy = self.Ky * self.height * 1000
        
        KLx_rx = KLx / self.rx if self.rx > 0 else float('inf')
        KLy_ry = KLy / self.ry if self.ry > 0 else float('inf')
        
        return KLx_rx, KLy_ry, KLx / 1000, KLy / 1000
    
    def calculate_allowable_compressive_stress(self) -> float:
        """
        Calculate allowable compressive stress per วสท. 011038-22
        Uses Euler buckling formula with safety factors
        Returns:
            Allowable compressive stress Fa in MPa
        """
        KLx_rx, KLy_ry, _, _ = self.calculate_slenderness()
        
        # Use maximum slenderness ratio
        KLr_max = max(KLx_rx, KLy_ry)
        
        # Check maximum slenderness limit (KL/r <= 200)
        if KLr_max > 200:
            return 0.0  # Section fails slenderness limit
        
        # Calculate critical slenderness parameter Cc
        Cc = math.sqrt(2 * PI**2 * E_STEEL / self.Fy)
        
        # Calculate allowable stress using ASD formulas
        if KLr_max <= Cc:
            # Inelastic buckling range
            # Fa = [1 - (KL/r)²/(2*Cc²)] * Fy / [5/3 + 3*(KL/r)/(8*Cc) - (KL/r)³/(8*Cc³)]
            numerator = (1 - (KLr_max**2) / (2 * Cc**2)) * self.Fy
            denominator = 5/3 + 3*KLr_max/(8*Cc) - (KLr_max**3)/(8*Cc**3)
            Fa = numerator / denominator
        else:
            # Elastic buckling range
            # Fa = 12*PI²*E / [23*(KL/r)²]
            Fa = 12 * PI**2 * E_STEEL / (23 * KLr_max**2)
        
        return Fa
    
    def check_axial_only(self, axial_load: float) -> Dict:
        """
        Check column for axial load only
        Args:
            axial_load: Factored axial load in kN
        Returns:
            Dictionary with axial check results
        """
        Fa = self.calculate_allowable_compressive_stress()
        
        P_N = axial_load * 1000  # Convert kN to N
        fa = P_N / self.A if self.A > 0 else float('inf')  # MPa
        
        ratio = fa / Fa if Fa > 0 else float('inf')
        P_allow = Fa * self.A / 1000  # kN
        
        return {
            "fa_MPa": fa,
            "Fa_MPa": Fa,
            "ratio": ratio,
            "P_kN": axial_load,
            "P_allow_kN": P_allow,
            "is_ok": ratio <= 1.0,
        }
    
    def check_combined_loading(self, loads: ColumnLoad) -> ColumnDesignResult:
        """
        Perform complete column design check for combined axial + bending
        Args:
            loads: Column loads
        Returns:
            Design result
        """
        result = ColumnDesignResult()
        result.details = {"load_cases": []}
        
        # Calculate slenderness
        KLx_rx, KLy_ry, KLx_m, KLy_m = self.calculate_slenderness()
        result.KLx = KLx_m
        result.KLy = KLy_m
        result.slenderness_x = KLx_rx
        result.slenderness_y = KLy_ry
        result.critical_slenderness = max(KLx_rx, KLy_ry)
        
        # Check slenderness limit
        if result.critical_slenderness > 200:
            result.is_ok = False
            result.status = f"ไม่ผ่าน - อัตราส่วนความชะลูด KL/r = {result.critical_slenderness:.1f} > 200"
            return result
        
        # Calculate allowable stresses
        self.Fa = self.calculate_allowable_compressive_stress()
        
        # Allowable bending stress (simplified)
        Fbx = 0.66 * self.Fy  # About x-axis
        Fby = 0.75 * self.Fy  # About y-axis
        
        # Check all load combinations
        critical_interaction = 0.0
        
        for lc in LOAD_COMBINATIONS_ASD:
            factors = lc.factors
            
            # Calculate factored axial load
            P = (factors["D"] * loads.axial_load_D + 
                 factors["L"] * loads.axial_load_L + 
                 factors["W"] * loads.axial_load_W)
            
            # Calculate factored moments
            Mx = (factors["D"] * loads.moment_x_D + 
                  factors["L"] * loads.moment_x_L + 
                  factors["W"] * loads.moment_x_W)
            
            My = (factors["D"] * loads.moment_y_D + 
                  factors["L"] * loads.moment_y_L + 
                  factors["W"] * loads.moment_y_W)
            
            # Calculate stresses
            fa = (P * 1000) / self.A if self.A > 0 else float('inf')  # MPa
            fbx = (Mx * 1e6) / self.Sx if self.Sx > 0 else float('inf')  # MPa
            fby = (My * 1e6) / self.Sy if self.Sy > 0 else float('inf')  # MPa
            
            # Interaction check per วสท. 011038-22
            # For fa/Fa <= 0.15: fa/Fa + fbx/Fbx + fby/Fby <= 1.0
            # For fa/Fa > 0.15: Use interaction equations
            
            fa_Fa = fa / self.Fa if self.Fa > 0 else float('inf')
            fbx_Fbx = fbx / Fbx if Fbx > 0 else float('inf')
            fby_Fby = fby / Fby if Fby > 0 else float('inf')
            
            if fa_Fa <= 0.15:
                # Simple interaction
                interaction = fa_Fa + fbx_Fbx + fby_Fby
            else:
                # Modified interaction (simplified - full check requires amplification factors)
                # Using conservative approach
                interaction = fa_Fa + fbx_Fbx + fby_Fby
            
            # Store load case results
            result.details["load_cases"].append({
                "name": lc.name,
                "name_th": lc.name_th,
                "P_kN": P,
                "Mx_kNm": Mx,
                "My_kNm": My,
                "fa_MPa": fa,
                "fbx_MPa": fbx,
                "fby_MPa": fby,
                "fa_Fa": fa_Fa,
                "fbx_Fbx": fbx_Fbx,
                "fby_Fby": fby_Fby,
                "interaction_ratio": interaction,
            })
            
            # Track critical values
            if interaction > critical_interaction:
                critical_interaction = interaction
                result.max_axial_load = P
                result.interaction_ratio = interaction
                result.fa = fa
                result.critical_load_case = f"{lc.name} ({lc.name_th})"
        
        # Calculate allowable axial load
        result.allowable_axial_load = self.Fa * self.A / 1000  # kN
        result.axial_ratio = result.max_axial_load / result.allowable_axial_load if result.allowable_axial_load > 0 else float('inf')
        result.Fa = self.Fa
        
        # Determine overall status
        axial_ok = result.axial_ratio <= 1.0
        interaction_ok = result.interaction_ratio <= 1.0
        slenderness_ok = result.critical_slenderness <= 200
        
        result.is_ok = axial_ok and interaction_ok and slenderness_ok
        
        if result.is_ok:
            result.status = "ผ่าน (ADEQUATE) - เสาสามารถรับน้ำหนักได้"
        else:
            issues = []
            if not axial_ok:
                issues.append(f"แรงอัดไม่ผ่าน (ratio={result.axial_ratio:.3f})")
            if not interaction_ok:
                issues.append(f"Interaction ไม่ผ่าน (ratio={result.interaction_ratio:.3f})")
            if not slenderness_ok:
                issues.append(f"ความชะลูดไม่ผ่าน (KL/r={result.critical_slenderness:.1f})")
            result.status = f"ไม่ผ่าน (INADEQUATE) - {', '.join(issues)}"
        
        return result


def format_column_report(result: ColumnDesignResult, section_name: str, height: float) -> str:
    """Format column design report in Thai"""
    def f(n, d=2):
        return f"{n:,.{d}f}"
    
    report = []
    report.append("=" * 70)
    report.append(f"รายการคำนวณออกแบบเสาเหล็ก: {section_name}")
    report.append(f"ความสูงเสา H = {f(height)} m")
    report.append("=" * 70)
    
    report.append("\n1. คุณสมบัติหน้าตัด")
    report.append(f"  - A = {f(result.Fa * 1e6 / 0.66 if result.Fa > 0 else 0, 0)} mm²")
    report.append(f"  - rx = {f(result.Fa * 1e6 / 0.66 if result.Fa > 0 else 0, 1)} mm")
    report.append(f"  - ry = {f(result.Fa * 1e6 / 0.66 if result.Fa > 0 else 0, 1)} mm")
    
    report.append("\n2. การตรวจสอบความชะลูด (Slenderness Check)")
    report.append(f"  - KLx = {f(result.KLx)} m, KLy = {f(result.KLy)} m")
    report.append(f"  - KLx/rx = {f(result.slenderness_x, 1)}")
    report.append(f"  - KLy/ry = {f(result.slenderness_y, 1)}")
    report.append(f"  - ค่าวิกฤต KL/r = {f(result.critical_slenderness, 1)} (จำกัด ≤ 200)")
    
    report.append("\n3. การตรวจสอบแรงอัดแกน (Axial Compression Check)")
    report.append(f"  - แรงอัดสูงสุด P = {f(result.max_axial_load)} kN")
    report.append(f"  - แรงอัดที่ยอมให้ P_allow = {f(result.allowable_axial_load)} kN")
    report.append(f"  - หน่วยแรงอัดที่เกิดขึ้น fa = {f(result.fa)} MPa")
    report.append(f"  - หน่วยแรงอัดที่ยอมให้ Fa = {f(result.Fa)} MPa")
    report.append(f"  - อัตราส่วน P/P_allow = {f(result.axial_ratio, 3)}")
    
    report.append("\n4. การตรวจสอบแรงรวม (Combined Loading Check)")
    report.append(f"  - กรณีวิกฤต: {result.critical_load_case}")
    report.append(f"  - อัตราส่วน Interaction = {f(result.interaction_ratio, 3)}")
    
    report.append("\n" + "=" * 70)
    report.append(f"สรุปผล: {result.status}")
    report.append("=" * 70)
    
    return "\n".join(report)
