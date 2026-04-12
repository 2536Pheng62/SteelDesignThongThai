"""
Connection Design Module (ออกแบบรอยต่อโครงสร้างเหล็ก)
Based on วสท. 011038-22 (Engineering Institute of Thailand Standard)
Implements ASD (Allowable Stress Design) method for bolted and welded connections
"""
import math
from dataclasses import dataclass
from typing import Dict, List
from steel_sections import SteelSection, BOLTS, WELDS, BoltProperties, WeldProperties
from load_combinations import LOAD_COMBINATIONS_ASD, SAFETY_FACTORS


@dataclass
class ConnectionLoad:
    """Represents loads on a connection."""
    shear_load_D: float = 0.0     # kN
    shear_load_L: float = 0.0     # kN
    shear_load_W: float = 0.0     # kN
    axial_load_D: float = 0.0     # kN (tension positive)
    axial_load_L: float = 0.0     # kN
    axial_load_W: float = 0.0     # kN
    moment_load_D: float = 0.0    # kN-m
    moment_load_L: float = 0.0    # kN-m
    moment_load_W: float = 0.0    # kN-m


@dataclass
class BoltedConnectionResult:
    """Stores bolted connection design results."""
    is_ok: bool = False
    status: str = ""
    num_bolts: int = 0
    bolt_diameter: float = 0.0    # mm
    bolt_grade: str = ""
    shear_per_bolt: float = 0.0   # kN
    total_shear_capacity: float = 0.0  # kN
    bearing_per_bolt: float = 0.0  # kN
    total_bearing_capacity: float = 0.0  # kN
    applied_shear: float = 0.0    # kN
    shear_ratio: float = 0.0
    bearing_ratio: float = 0.0
    critical_load_case: str = ""
    details: Dict = None


@dataclass
class WeldedConnectionResult:
    """Stores welded connection design results."""
    is_ok: bool = False
    status: str = ""
    weld_size: float = 0.0        # mm
    weld_length: float = 0.0      # mm
    electrode: str = ""
    shear_capacity: float = 0.0   # kN
    applied_shear: float = 0.0    # kN
    shear_ratio: float = 0.0
    critical_load_case: str = ""
    details: Dict = None


class BoltedConnectionDesign:
    """
    Bolted connection design per วสท. 011038-22
    Checks bolt shear and bearing
    """
    
    def __init__(self, bolt: BoltProperties, connected_plate_thickness: float,
                 edge_distance: float = 0.0, bolt_spacing: float = 0.0,
                 plate_Fu: float = 400.0):
        """
        Args:
            bolt: Bolt properties
            connected_plate_thickness: Thickness of connected plate in mm
            edge_distance: Distance from bolt center to edge in mm
            bolt_spacing: Bolt spacing in mm
            plate_Fu: Ultimate strength of connected plate in MPa
        """
        self.bolt = bolt
        self.plate_thickness = connected_plate_thickness  # mm
        self.edge_distance = edge_distance  # mm
        self.bolt_spacing = bolt_spacing  # mm
        self.plate_Fu = plate_Fu  # MPa
        
    def calculate_shear_capacity_per_bolt(self, num_shear_planes: int = 1) -> float:
        """
        Calculate shear capacity per bolt
        Args:
            num_shear_planes: Number of shear planes (1 for single shear, 2 for double)
        Returns:
            Shear capacity per bolt in kN
        """
        # Allowable shear stress per วสท. 011038-22
        # Fv = 0.40 * Fub for ASD (omega = 2.5)
        Fv = self.bolt.shear_strength  # MPa (already calculated)
        
        # Shear capacity = Fv * Ab * num_shear_planes
        Ab = self.bolt.area  # mm²
        Vn = Fv * Ab * num_shear_planes / 1000  # Convert to kN
        
        return Vn
    
    def calculate_bearing_capacity_per_bolt(self) -> float:
        """
        Calculate bearing capacity per bolt
        Returns:
            Bearing capacity per bolt in kN
        """
        # Bearing capacity per วสท. 011038-22
        # Rn = 1.2 * Lc * t * Fu <= 2.4 * d * t * Fu
        # For ASD: Rn / omega, where omega = 2.0
        
        d = self.bolt.diameter  # mm
        t = self.plate_thickness  # mm
        Fu = self.plate_Fu  # MPa
        
        # Check edge distance
        if self.edge_distance > 0:
            Lc = self.edge_distance - d / 2  # Clear distance to edge
            Rn_edge = 1.2 * Lc * t * Fu / 1000  # kN
            Rn_max = 2.4 * d * t * Fu / 1000  # kN
            Rn = min(Rn_edge, Rn_max)
        else:
            # Use conservative value
            Rn = 2.4 * d * t * Fu / 1000  # kN
        
        # ASD capacity
        omega = 2.0
        Rn_asd = Rn / omega
        
        return Rn_asd
    
    def check_connection(self, loads: ConnectionLoad, num_bolts: int, 
                        num_shear_planes: int = 1) -> BoltedConnectionResult:
        """
        Perform complete bolted connection design check
        Args:
            loads: Connection loads
            num_bolts: Number of bolts
            num_shear_planes: Number of shear planes
        Returns:
            Design result
        """
        result = BoltedConnectionResult()
        result.details = {"load_cases": []}
        result.num_bolts = num_bolts
        result.bolt_diameter = self.bolt.diameter
        result.bolt_grade = self.bolt.grade
        
        # Calculate capacities per bolt
        shear_per_bolt = self.calculate_shear_capacity_per_bolt(num_shear_planes)
        bearing_per_bolt = self.calculate_bearing_capacity_per_bolt()
        
        result.shear_per_bolt = shear_per_bolt
        result.bearing_per_bolt = bearing_per_bolt
        result.total_shear_capacity = shear_per_bolt * num_bolts
        result.total_bearing_capacity = bearing_per_bolt * num_bolts
        
        # Check all load combinations
        critical_shear = 0.0
        critical_shear_ratio = 0.0
        critical_bearing_ratio = 0.0
        
        for lc in LOAD_COMBINATIONS_ASD:
            factors = lc.factors
            
            # Calculate factored shear load
            V = (factors["D"] * loads.shear_load_D + 
                 factors["L"] * loads.shear_load_L + 
                 factors["W"] * loads.shear_load_W)
            
            # Calculate ratios
            shear_ratio = V / result.total_shear_capacity if result.total_shear_capacity > 0 else float('inf')
            bearing_ratio = V / result.total_bearing_capacity if result.total_bearing_capacity > 0 else float('inf')
            
            # Store load case results
            result.details["load_cases"].append({
                "name": lc.name,
                "name_th": lc.name_th,
                "V_kN": V,
                "shear_ratio": shear_ratio,
                "bearing_ratio": bearing_ratio,
            })
            
            # Track critical values
            if V > critical_shear:
                critical_shear = V
                result.applied_shear = V
                critical_shear_ratio = shear_ratio
                critical_bearing_ratio = bearing_ratio
                result.critical_load_case = f"{lc.name} ({lc.name_th})"
        
        result.shear_ratio = critical_shear_ratio
        result.bearing_ratio = critical_bearing_ratio
        
        # Determine overall status
        shear_ok = result.shear_ratio <= 1.0
        bearing_ok = result.bearing_ratio <= 1.0
        
        result.is_ok = shear_ok and bearing_ok
        
        if result.is_ok:
            result.status = "ผ่าน (ADEQUATE) - รอยต่อสลักเกลียวสามารถรับน้ำหนักได้"
        else:
            issues = []
            if not shear_ok:
                issues.append(f"แรงเฉือนสลักเกลียวไม่ผ่าน (ratio={result.shear_ratio:.3f})")
            if not bearing_ok:
                issues.append(f"แรงตปะไม่ผ่าน (ratio={result.bearing_ratio:.3f})")
            result.status = f"ไม่ผ่าน (INADEQUATE) - {', '.join(issues)}"
        
        return result


class WeldedConnectionDesign:
    """
    Welded connection design per วสท. 011038-22
    Checks weld shear capacity
    """
    
    def __init__(self, weld: WeldProperties, base_metal_Fy: float = 245.0):
        """
        Args:
            weld: Weld electrode properties
            base_metal_Fy: Yield strength of base metal in MPa
        """
        self.weld = weld
        self.base_metal_Fy = base_metal_Fy
        
    def calculate_weld_capacity_per_mm(self, weld_size: float) -> float:
        """
        Calculate weld capacity per mm length
        Args:
            weld_size: Weld size (throat thickness) in mm
        Returns:
            Capacity per mm length in kN/mm
        """
        # For fillet weld, throat = 0.707 * leg size
        throat = 0.707 * weld_size
        
        # Allowable shear stress per วสท. 011038-22
        # Fv = 0.30 * Fu for ASD (omega = 3.33)
        Fv = self.weld.shear_strength  # MPa
        
        # Capacity per mm = Fv * throat
        capacity = Fv * throat / 1000  # Convert to kN/mm
        
        return capacity
    
    def check_connection(self, loads: ConnectionLoad, weld_size: float, 
                        weld_length: float) -> WeldedConnectionResult:
        """
        Perform complete welded connection design check
        Args:
            loads: Connection loads
            weld_size: Weld size (leg size) in mm
            weld_length: Total weld length in mm
        Returns:
            Design result
        """
        result = WeldedConnectionResult()
        result.details = {"load_cases": []}
        result.weld_size = weld_size
        result.weld_length = weld_length
        result.electrode = self.weld.electrode
        
        # Calculate capacity
        capacity_per_mm = self.calculate_weld_capacity_per_mm(weld_size)
        total_capacity = capacity_per_mm * weld_length  # kN
        
        result.shear_capacity = total_capacity
        
        # Check all load combinations
        critical_shear = 0.0
        critical_ratio = 0.0
        
        for lc in LOAD_COMBINATIONS_ASD:
            factors = lc.factors
            
            # Calculate factored shear load
            V = (factors["D"] * loads.shear_load_D + 
                 factors["L"] * loads.shear_load_L + 
                 factors["W"] * loads.shear_load_W)
            
            # Calculate ratio
            ratio = V / total_capacity if total_capacity > 0 else float('inf')
            
            # Store load case results
            result.details["load_cases"].append({
                "name": lc.name,
                "name_th": lc.name_th,
                "V_kN": V,
                "ratio": ratio,
            })
            
            # Track critical values
            if V > critical_shear:
                critical_shear = V
                result.applied_shear = V
                critical_ratio = ratio
                result.critical_load_case = f"{lc.name} ({lc.name_th})"
        
        result.shear_ratio = critical_ratio
        
        # Determine overall status
        shear_ok = result.shear_ratio <= 1.0
        
        result.is_ok = shear_ok
        
        if result.is_ok:
            result.status = "ผ่าน (ADEQUATE) - รอยเชื่อมสามารถรับน้ำหนักได้"
        else:
            result.status = f"ไม่ผ่าน (INADEQUATE) - แรงเฉือนรอยเชื่อมไม่ผ่าน (ratio={result.shear_ratio:.3f})"
        
        return result


def format_bolted_report(result: BoltedConnectionResult) -> str:
    """Format bolted connection design report in Thai"""
    def f(n, d=2):
        return f"{n:,.{d}f}"
    
    report = []
    report.append("=" * 70)
    report.append(f"รายการคำนวณออกแบบรอยต่อสลักเกลียว")
    report.append(f"สลักเกลียว: {result.bolt_grade} M{f(result.bolt_diameter, 0)}")
    report.append(f"จำนวน: {result.num_bolts} ตัว")
    report.append("=" * 70)
    
    report.append("\n1. คุณสมบัติสลักเกลียว")
    report.append(f"  - เส้นผ่านศูนย์กลาง d = {f(result.bolt_diameter, 0)} mm")
    report.append(f"  - เกรด = {result.bolt_grade}")
    
    report.append("\n2. การตรวจสอบแรงเฉือนสลักเกลียว (Bolt Shear Check)")
    report.append(f"  - กรณีวิกฤต: {result.critical_load_case}")
    report.append(f"  - แรงเฉือนที่กระทำ V = {f(result.applied_shear)} kN")
    report.append(f"  - ความสามารถรับแรงเฉือนต่อตัว = {f(result.shear_per_bolt)} kN")
    report.append(f"  - ความสามารถรับแรงเฉือนรวม = {f(result.total_shear_capacity)} kN")
    report.append(f"  - อัตราส่วน V/V_allow = {f(result.shear_ratio, 3)}")
    
    report.append("\n3. การตรวจสอบแรงตปะ (Bearing Check)")
    report.append(f"  - ความสามารถรับแรงตปะต่อตัว = {f(result.bearing_per_bolt)} kN")
    report.append(f"  - ความสามารถรับแรงตปะรวม = {f(result.total_bearing_capacity)} kN")
    report.append(f"  - อัตราส่วน V/V_bearing = {f(result.bearing_ratio, 3)}")
    
    report.append("\n" + "=" * 70)
    report.append(f"สรุปผล: {result.status}")
    report.append("=" * 70)
    
    return "\n".join(report)


def format_welded_report(result: WeldedConnectionResult) -> str:
    """Format welded connection design report in Thai"""
    def f(n, d=2):
        return f"{n:,.{d}f}"
    
    report = []
    report.append("=" * 70)
    report.append(f"รายการคำนวณออกแบบรอยเชื่อม")
    report.append(f"ลวดเชื่อม: {result.electrode}")
    report.append("=" * 70)
    
    report.append("\n1. คุณสมบัติรอยเชื่อม")
    report.append(f"  - ขนาดรอยเชื่อม (leg size) = {f(result.weld_size)} mm")
    report.append(f"  - ความยาวรอยเชื่อม = {f(result.weld_length)} mm")
    report.append(f"  - เกรดลวดเชื่อม = {result.electrode}")
    
    report.append("\n2. การตรวจสอบแรงเฉือนรอยเชื่อม (Weld Shear Check)")
    report.append(f"  - กรณีวิกฤต: {result.critical_load_case}")
    report.append(f"  - แรงเฉือนที่กระทำ V = {f(result.applied_shear)} kN")
    report.append(f"  - ความสามารถรับแรงเฉือน = {f(result.shear_capacity)} kN")
    report.append(f"  - อัตราส่วน V/V_allow = {f(result.shear_ratio, 3)}")
    
    report.append("\n" + "=" * 70)
    report.append(f"สรุปผล: {result.status}")
    report.append("=" * 70)
    
    return "\n".join(report)
