"""
Base Plate Design Module (ออกแบบแผ่นฐานเสาเหล็ก)
Based on วสท. 011038-22 (Engineering Institute of Thailand Standard)
Implements ASD (Allowable Stress Design) method
"""
import math
from dataclasses import dataclass
from typing import Dict
from steel_sections import SteelSection
from load_combinations import LOAD_COMBINATIONS_ASD


@dataclass
class BasePlateLoad:
    """Represents loads on a base plate."""
    axial_load_D: float = 0.0    # kN (compression positive)
    axial_load_L: float = 0.0    # kN
    axial_load_W: float = 0.0    # kN
    moment_x_D: float = 0.0      # kN-m
    moment_x_L: float = 0.0      # kN-m
    moment_x_W: float = 0.0      # kN-m
    shear_x_D: float = 0.0       # kN
    shear_x_L: float = 0.0       # kN
    shear_x_W: float = 0.0       # kN


@dataclass
class BasePlateResult:
    """Stores base plate design results."""
    is_ok: bool = False
    status: str = ""
    plate_width_B: float = 0.0       # mm
    plate_length_N: float = 0.0      # mm
    plate_thickness: float = 0.0     # mm
    concrete_Fc: float = 0.0         # MPa
    max_bearing_pressure: float = 0.0  # MPa
    allowable_bearing_pressure: float = 0.0  # MPa
    bearing_ratio: float = 0.0
    required_thickness: float = 0.0  # mm
    actual_thickness: float = 0.0    # mm
    thickness_ratio: float = 0.0
    critical_load_case: str = ""
    details: Dict = None


class BasePlateDesign:
    """
    Base plate design per วสท. 011038-22
    Checks concrete bearing and plate bending
    """
    
    def __init__(self, section: SteelSection, plate_width: float, plate_length: float,
                 plate_thickness: float, concrete_Fc: float = 24.0):
        """
        Args:
            section: Column steel section properties
            plate_width: Base plate width B in mm
            plate_length: Base plate length N in mm
            plate_thickness: Base plate thickness in mm
            concrete_Fc: Concrete compressive strength in MPa
        """
        self.section = section
        self.B = plate_width  # mm
        self.N = plate_length  # mm
        self.tp = plate_thickness  # mm
        self.concrete_Fc = concrete_Fc  # MPa
        
        # Column dimensions
        self.d = section.d      # mm
        self.bf = section.bf    # mm
        self.tf = section.tf    # mm
        self.tw = section.tw    # mm
        
    def calculate_bearing_pressure(self, P: float, Mx: float = 0.0) -> float:
        """
        Calculate bearing pressure on concrete
        Args:
            P: Axial load in kN
            Mx: Moment about x-axis in kN-m
        Returns:
            Maximum bearing pressure in MPa
        """
        A_plate = self.B * self.N  # mm²
        I_plate = self.B * self.N**3 / 12  # mm⁴
        
        # Convert P to N
        P_N = P * 1000
        
        # Average pressure
        f_avg = P_N / A_plate  # MPa
        
        # If moment exists, calculate eccentricity and check if within middle third
        if Mx > 0:
            e = Mx * 1000 / P  # mm (eccentricity)
            
            # Check if e <= N/6 (within middle third)
            if e <= self.N / 6:
                # Full compression, linear distribution
                f_max = f_avg * (1 + 6 * e / self.N)
            else:
                # Partial compression (triangular distribution)
                # Length of compression zone = 3 * (N/2 - e)
                comp_length = 3 * (self.N / 2 - e)
                if comp_length > 0:
                    f_max = 2 * P_N / (self.B * comp_length)
                else:
                    f_max = float('inf')
        else:
            f_max = f_avg
        
        return f_max / 1000  # Convert to MPa
    
    def calculate_allowable_bearing_pressure(self) -> float:
        """
        Calculate allowable bearing pressure on concrete per วสท. 011038-22
        Returns:
            Allowable bearing pressure in MPa
        """
        # For concrete bearing: Fp = 0.35 * f'c * sqrt(A2/A1) <= 0.70 * f'c
        # For ASD with full area support: Fp = 0.35 * f'c
        
        A1 = self.B * self.N  # Area of base plate
        A2 = A1  # Assuming full area support (conservative)
        
        sqrt_ratio = math.sqrt(A2 / A1) if A1 > 0 else 1.0
        
        Fp = 0.35 * self.concrete_Fc * sqrt_ratio
        Fp_max = 0.70 * self.concrete_Fc
        
        return min(Fp, Fp_max)
    
    def calculate_required_thickness(self, P: float) -> float:
        """
        Calculate required base plate thickness
        Args:
            P: Axial load in kN
        Returns:
            Required thickness in mm
        """
        # Calculate bearing pressure
        fp = self.calculate_bearing_pressure(P)
        
        # Calculate cantilever dimensions
        # m = (N - 0.95d) / 2
        # n = (B - 0.80bf) / 2
        m = (self.N - 0.95 * self.d) / 2
        n = (self.B - 0.80 * self.bf) / 2
        
        # Use larger value
        l = max(m, n)
        
        # Also check n' = sqrt(d * bf) / 4
        n_prime = math.sqrt(self.d * self.bf) / 4
        l = max(l, n_prime)
        
        # Required thickness: tp = l * sqrt(3.33 * fp / Fy)
        # For ASD: tp = l * sqrt(2 * fp / (0.75 * Fy))
        Fy_plate = 245  # MPa (base plate yield strength)
        
        if fp > 0:
            tp_req = l * math.sqrt(2 * fp / (0.75 * Fy_plate))
        else:
            tp_req = 0
        
        return tp_req
    
    def check_base_plate(self, loads: BasePlateLoad) -> BasePlateResult:
        """
        Perform complete base plate design check
        Args:
            loads: Base plate loads
        Returns:
            Design result
        """
        result = BasePlateResult()
        result.details = {"load_cases": []}
        result.plate_width_B = self.B
        result.plate_length_N = self.N
        result.plate_thickness = self.tp
        result.concrete_Fc = self.concrete_Fc
        
        # Calculate allowable bearing pressure
        Fp = self.calculate_allowable_bearing_pressure()
        result.allowable_bearing_pressure = Fp
        
        # Check all load combinations
        critical_pressure = 0.0
        critical_thickness_ratio = 0.0
        
        for lc in LOAD_COMBINATIONS_ASD:
            factors = lc.factors
            
            # Calculate factored axial load
            P = (factors["D"] * loads.axial_load_D + 
                 factors["L"] * loads.axial_load_L + 
                 factors["W"] * loads.axial_load_W)
            
            # Calculate factored moment
            Mx = (factors["D"] * loads.moment_x_D + 
                  factors["L"] * loads.moment_x_L + 
                  factors["W"] * loads.moment_x_W)
            
            # Calculate bearing pressure
            fp = self.calculate_bearing_pressure(P, Mx)
            
            # Calculate required thickness
            tp_req = self.calculate_required_thickness(P)
            
            # Calculate ratios
            bearing_ratio = fp / Fp if Fp > 0 else float('inf')
            thickness_ratio = tp_req / self.tp if self.tp > 0 else float('inf')
            
            # Store load case results
            result.details["load_cases"].append({
                "name": lc.name,
                "name_th": lc.name_th,
                "P_kN": P,
                "Mx_kNm": Mx,
                "fp_MPa": fp,
                "Fp_MPa": Fp,
                "tp_req_mm": tp_req,
                "bearing_ratio": bearing_ratio,
                "thickness_ratio": thickness_ratio,
            })
            
            # Track critical values
            if fp > critical_pressure:
                critical_pressure = fp
                result.max_bearing_pressure = fp
                critical_thickness_ratio = thickness_ratio
                result.required_thickness = tp_req
                result.critical_load_case = f"{lc.name} ({lc.name_th})"
        
        result.actual_thickness = self.tp
        result.bearing_ratio = critical_pressure / Fp if Fp > 0 else float('inf')
        result.thickness_ratio = critical_thickness_ratio
        
        # Determine overall status
        bearing_ok = result.bearing_ratio <= 1.0
        thickness_ok = result.thickness_ratio <= 1.0
        
        result.is_ok = bearing_ok and thickness_ok
        
        if result.is_ok:
            result.status = "ผ่าน (ADEQUATE) - แผ่นฐานสามารถรับน้ำหนักได้"
        else:
            issues = []
            if not bearing_ok:
                issues.append(f"แรงตปะคอนกรีตไม่ผ่าน (ratio={result.bearing_ratio:.3f})")
            if not thickness_ok:
                issues.append(f"ความหนาแผ่นฐานไม่เพียงพอ (required={result.required_thickness:.1f} mm)")
            result.status = f"ไม่ผ่าน (INADEQUATE) - {', '.join(issues)}"
        
        return result


def format_baseplate_report(result: BasePlateResult, section_name: str) -> str:
    """Format base plate design report in Thai"""
    def f(n, d=2):
        return f"{n:,.{d}f}"
    
    report = []
    report.append("=" * 70)
    report.append(f"รายการคำนวณออกแบบแผ่นฐานเสาเหล็ก: {section_name}")
    report.append("=" * 70)
    
    report.append("\n1. ขนาดแผ่นฐาน")
    report.append(f"  - ขนาดแผ่น B x N = {f(result.plate_width_B, 0)} x {f(result.plate_length_N, 0)} mm")
    report.append(f"  - ความหนาแผ่น tp = {f(result.plate_thickness, 0)} mm")
    report.append(f"  - กำลังคอนกรีต f'c = {f(result.concrete_Fc)} MPa")
    
    report.append("\n2. การตรวจสอบแรงตปะคอนกรีต (Concrete Bearing Check)")
    report.append(f"  - กรณีวิกฤต: {result.critical_load_case}")
    report.append(f"  - แรงตปะที่เกิดขึ้น fp = {f(result.max_bearing_pressure)} MPa")
    report.append(f"  - แรงตปะที่ยอมให้ Fp = {f(result.allowable_bearing_pressure)} MPa")
    report.append(f"  - อัตราส่วน fp/Fp = {f(result.bearing_ratio, 3)}")
    
    report.append("\n3. การตรวจสอบความหนาแผ่นฐาน (Plate Thickness Check)")
    report.append(f"  - ความหนาที่ต้องการ tp_req = {f(result.required_thickness)} mm")
    report.append(f"  - ความหนาจริง tp = {f(result.actual_thickness, 0)} mm")
    report.append(f"  - อัตราส่วน tp_req/tp = {f(result.thickness_ratio, 3)}")
    
    report.append("\n" + "=" * 70)
    report.append(f"สรุปผล: {result.status}")
    report.append("=" * 70)
    
    return "\n".join(report)
