"""
Seismic Design Module (ออกแบบต้านทานแรงแผ่นดินไหว)
Based on มยผ. 1302-61 (Thai Standard for Seismic Design of Buildings)
Implements the Equivalent Lateral Force (ELF) procedure (วิธีแรงสถิตเทียบเท่า).

References:
- มยผ. 1301/1302-61 กรมโยธาธิการและผังเมือง
- ASCE 7-16 Chapter 12 (Equivalent Lateral Force Procedure - parallel reference)
"""
import math
from dataclasses import dataclass, field
from typing import Dict, List, Tuple


# ============================================================================
# Site Coefficients (Fa, Fv) per มยผ. 1302-61 Table
# Interpolated between site classes A, B, C, D, E for given Ss and S1
# ============================================================================

# Site coefficients Fa (short period) as function of site class and Ss
FA_TABLE = {
    "A": {0.25: 0.8, 0.50: 0.8, 0.75: 0.8, 1.00: 0.8, 1.25: 0.8},
    "B": {0.25: 1.0, 0.50: 1.0, 0.75: 1.0, 1.00: 1.0, 1.25: 1.0},
    "C": {0.25: 1.2, 0.50: 1.2, 0.75: 1.1, 1.00: 1.0, 1.25: 1.0},
    "D": {0.25: 1.6, 0.50: 1.4, 0.75: 1.2, 1.00: 1.1, 1.25: 1.0},
    "E": {0.25: 2.5, 0.50: 1.7, 0.75: 1.2, 1.00: 0.9, 1.25: 0.9},
}

# Site coefficients Fv (long period) as function of site class and S1
FV_TABLE = {
    "A": {0.10: 0.8, 0.20: 0.8, 0.30: 0.8, 0.40: 0.8, 0.50: 0.8},
    "B": {0.10: 1.0, 0.20: 1.0, 0.30: 1.0, 0.40: 1.0, 0.50: 1.0},
    "C": {0.10: 1.7, 0.20: 1.6, 0.30: 1.5, 0.40: 1.4, 0.50: 1.3},
    "D": {0.10: 2.4, 0.20: 2.0, 0.30: 1.8, 0.40: 1.6, 0.50: 1.5},
    "E": {0.10: 3.5, 0.20: 3.2, 0.30: 2.8, 0.40: 2.4, 0.50: 2.4},
}


def _interpolate(table: Dict[float, float], x: float) -> float:
    """Linear interpolation across the keys of a 1-D table."""
    keys = sorted(table.keys())
    if x <= keys[0]:
        return table[keys[0]]
    if x >= keys[-1]:
        return table[keys[-1]]
    for i in range(len(keys) - 1):
        x0, x1 = keys[i], keys[i + 1]
        if x0 <= x <= x1:
            y0, y1 = table[x0], table[x1]
            return y0 + (y1 - y0) * (x - x0) / (x1 - x0)
    return table[keys[-1]]


def get_Fa(site_class: str, Ss: float) -> float:
    """Site coefficient Fa per มยผ. 1302-61 (short period)."""
    sc = site_class.upper()
    if sc not in FA_TABLE:
        sc = "D"  # default
    return _interpolate(FA_TABLE[sc], Ss)


def get_Fv(site_class: str, S1: float) -> float:
    """Site coefficient Fv per มยผ. 1302-61 (1-second period)."""
    sc = site_class.upper()
    if sc not in FV_TABLE:
        sc = "D"
    return _interpolate(FV_TABLE[sc], S1)


# ============================================================================
# Approximate Period (Ta) — มยผ. 1302-61 / ASCE 7-16 Eq. 12.8-7
# Ta = Ct * hn^x
# ============================================================================

PERIOD_COEFFICIENTS = {
    "steel_mrf":          {"Ct": 0.0724, "x": 0.80, "name_th": "โครงต้านโมเมนต์เหล็ก"},
    "steel_eccentric":    {"Ct": 0.0731, "x": 0.75, "name_th": "โครงเหล็กค้ำยันเยื้องศูนย์"},
    "steel_braced":       {"Ct": 0.0488, "x": 0.75, "name_th": "โครงเหล็กค้ำยันรวมศูนย์"},
    "concrete_mrf":       {"Ct": 0.0466, "x": 0.90, "name_th": "โครงต้านโมเมนต์คอนกรีต"},
    "other":              {"Ct": 0.0488, "x": 0.75, "name_th": "ระบบโครงสร้างอื่น ๆ"},
}


def calc_period_approximate(structure_type: str, height_m: float) -> float:
    """
    Approximate fundamental period Ta (seconds) per มยผ. 1302-61.
    Ta = Ct * hn^x, where hn is building height (m).
    """
    key = structure_type if structure_type in PERIOD_COEFFICIENTS else "other"
    Ct = PERIOD_COEFFICIENTS[key]["Ct"]
    x = PERIOD_COEFFICIENTS[key]["x"]
    return Ct * (height_m ** x)


# ============================================================================
# Response Modification Factor (R), Overstrength (Ω0), Deflection Amp. (Cd)
# Table 12.2-1 style per มยผ. 1302-61
# ============================================================================

SEISMIC_SYSTEM_FACTORS = {
    "steel_smf":           {"R": 8.0, "Omega": 3.0, "Cd": 5.5, "name_th": "โครงต้านโมเมนต์เหล็กพิเศษ (SMF)"},
    "steel_imf":           {"R": 4.5, "Omega": 3.0, "Cd": 4.0, "name_th": "โครงต้านโมเมนต์เหล็กระดับกลาง (IMF)"},
    "steel_omf":           {"R": 3.5, "Omega": 3.0, "Cd": 3.0, "name_th": "โครงต้านโมเมนต์เหล็กธรรมดา (OMF)"},
    "steel_scbf":          {"R": 6.0, "Omega": 2.0, "Cd": 5.0, "name_th": "โครงเหล็กค้ำยันรวมศูนย์พิเศษ (SCBF)"},
    "steel_ocbf":          {"R": 3.25, "Omega": 2.0, "Cd": 3.25, "name_th": "โครงเหล็กค้ำยันรวมศูนย์ธรรมดา (OCBF)"},
    "steel_ebf":           {"R": 8.0, "Omega": 2.0, "Cd": 4.0, "name_th": "โครงเหล็กค้ำยันเยื้องศูนย์ (EBF)"},
    "steel_dual_smf":      {"R": 7.0, "Omega": 2.5, "Cd": 5.5, "name_th": "ระบบสองประเภท SMF + ค้ำยัน"},
}


# ============================================================================
# Importance Factor Ie per Risk Category (มยผ. 1302-61)
# ============================================================================

IMPORTANCE_FACTORS = {
    "I":   {"Ie": 1.00, "name_th": "ประเภทความสำคัญปกติ I"},
    "II":  {"Ie": 1.00, "name_th": "ประเภทความสำคัญปกติ II (อาคารทั่วไป)"},
    "III": {"Ie": 1.25, "name_th": "ประเภทความสำคัญมาก III (อาคารรวมคนจำนวนมาก)"},
    "IV":  {"Ie": 1.50, "name_th": "ประเภทความสำคัญที่สุด IV (โรงพยาบาล/สถานีดับเพลิง)"},
}


# ============================================================================
# Equivalent Lateral Force (ELF) — the core calculation
# ============================================================================

@dataclass
class SeismicDesignResult:
    """Holds the output of an ELF seismic analysis."""
    # Inputs (echoed)
    Ss: float
    S1: float
    site_class: str
    R: float
    Ie: float
    W: float                         # Total seismic weight (kN)

    # Site-modified spectral accelerations
    Fa: float
    Fv: float
    SMS: float                       # Fa * Ss
    SM1: float                       # Fv * S1
    SDS: float                       # (2/3) * SMS
    SD1: float                       # (2/3) * SM1

    # Period
    Ta: float                        # Approximate period (s)

    # Seismic response coefficient
    Cs: float                        # Governing Cs
    Cs_max: float                    # SD1/(T*(R/Ie))
    Cs_controlled_by_period: bool    # True if SD1 formula controls

    # Base shear
    V: float                         # Base shear (kN)

    # Story force distribution (if multi-story)
    story_forces: List[Dict] = field(default_factory=list)

    # Diagnostics / intermediate values
    details: Dict = field(default_factory=dict)


def calc_base_shear_elf(
    Ss: float,
    S1: float,
    site_class: str,
    risk_category: str,
    structure_type: str,
    seismic_system: str,
    height_m: float,
    total_weight_kN: float,
) -> SeismicDesignResult:
    """
    Compute design base shear by the Equivalent Lateral Force procedure
    per มยผ. 1302-61 / ASCE 7-16 §12.8.

    Args:
        Ss: Mapped short-period spectral acceleration (g)
        S1: Mapped 1-second spectral acceleration (g)
        site_class: "A"-"E" (use "D" if unknown)
        risk_category: "I", "II", "III", "IV"
        structure_type: Key of PERIOD_COEFFICIENTS (for Ta)
        seismic_system: Key of SEISMIC_SYSTEM_FACTORS (for R)
        height_m: Building height above base (m)
        total_weight_kN: Effective seismic weight W (kN)

    Returns:
        SeismicDesignResult
    """
    # 1. Site coefficients
    Fa = get_Fa(site_class, Ss)
    Fv = get_Fv(site_class, S1)

    # 2. MCE spectral accelerations
    SMS = Fa * Ss
    SM1 = Fv * S1

    # 3. Design spectral accelerations (2/3 of MCE)
    SDS = (2.0 / 3.0) * SMS
    SD1 = (2.0 / 3.0) * SM1

    # 4. Importance factor
    ie_info = IMPORTANCE_FACTORS.get(risk_category.upper(), IMPORTANCE_FACTORS["II"])
    Ie = ie_info["Ie"]

    # 5. Response modification factor
    sys_info = SEISMIC_SYSTEM_FACTORS.get(seismic_system, SEISMIC_SYSTEM_FACTORS["steel_omf"])
    R = sys_info["R"]

    # 6. Approximate fundamental period
    Ta = calc_period_approximate(structure_type, height_m)

    # 7. Seismic response coefficient Cs
    # Upper bound (ASCE 12.8-2): Cs = SDS / (R/Ie)
    Cs_upper = SDS / (R / Ie)

    # Long-period limit (ASCE 12.8-3): Cs = SD1 / (T * (R/Ie))  for T <= TL (assume TL=4s)
    if Ta > 0:
        Cs_T = SD1 / (Ta * (R / Ie))
    else:
        Cs_T = Cs_upper

    # Minimum (ASCE 12.8-5): Cs >= 0.044*SDS*Ie >= 0.01
    Cs_min = max(0.044 * SDS * Ie, 0.01)

    # Additional minimum for sites with S1 >= 0.6g (ASCE 12.8-6)
    if S1 >= 0.6:
        Cs_min_high = 0.5 * S1 / (R / Ie)
        Cs_min = max(Cs_min, Cs_min_high)

    # Governing Cs: min(upper, period-dependent) but not less than Cs_min
    if Cs_T < Cs_upper:
        Cs = max(Cs_T, Cs_min)
        controlled_by_period = True
    else:
        Cs = max(Cs_upper, Cs_min)
        controlled_by_period = False

    # 8. Base shear
    V = Cs * total_weight_kN  # kN

    return SeismicDesignResult(
        Ss=Ss, S1=S1, site_class=site_class,
        R=R, Ie=Ie, W=total_weight_kN,
        Fa=Fa, Fv=Fv,
        SMS=SMS, SM1=SM1, SDS=SDS, SD1=SD1,
        Ta=Ta, Cs=Cs, Cs_max=Cs_upper,
        Cs_controlled_by_period=controlled_by_period,
        V=V,
        details={
            "Cs_upper": Cs_upper,
            "Cs_period": Cs_T,
            "Cs_min": Cs_min,
            "system_name_th": sys_info["name_th"],
            "importance_name_th": ie_info["name_th"],
        },
    )


# ============================================================================
# Vertical Distribution of Base Shear — ASCE 7-16 §12.8.3 / มยผ. 1302-61
# Fx = Cvx * V,   Cvx = wx*hx^k / Σ wi*hi^k
# ============================================================================

def distribute_story_forces(
    V: float,
    story_weights: List[float],
    story_heights: List[float],
    T: float,
) -> List[Dict]:
    """
    Distribute base shear V to each story per ASCE 7-16 Eq. 12.8-11/12.
    story_weights[i] is weight at level i (kN), story_heights[i] is height
    above base (m). Levels ordered from bottom (1) to top (N).

    Args:
        V: Base shear (kN)
        story_weights: List of story weights wi (kN), from bottom to top
        story_heights: List of story heights hi above base (m)
        T: Fundamental period (s), used to determine k exponent

    Returns:
        List of dicts per story: {level, wi, hi, k_term, Cvx, Fx, Vx_accum}
    """
    # Distribution exponent k
    if T <= 0.5:
        k = 1.0
    elif T >= 2.5:
        k = 2.0
    else:
        k = 1.0 + (T - 0.5) / 2.0  # linear interpolation

    k_terms = [w * (h ** k) for w, h in zip(story_weights, story_heights)]
    total = sum(k_terms)
    if total <= 0:
        return []

    # Forces from bottom to top
    Cvx_list = [kt / total for kt in k_terms]
    Fx_list = [cv * V for cv in Cvx_list]

    # Story shear Vx accumulated from top downward
    Vx_list = [0.0] * len(Fx_list)
    running = 0.0
    for i in range(len(Fx_list) - 1, -1, -1):
        running += Fx_list[i]
        Vx_list[i] = running

    rows = []
    for i, (w, h, kt, cv, fx, vx) in enumerate(
        zip(story_weights, story_heights, k_terms, Cvx_list, Fx_list, Vx_list), start=1
    ):
        rows.append({
            "level": i,
            "wi_kN": w,
            "hi_m": h,
            "wi_hi_k": kt,
            "Cvx": cv,
            "Fx_kN": fx,
            "Vx_kN": vx,
            "k": k,
        })
    return rows


# ============================================================================
# Report formatter
# ============================================================================

def format_seismic_report(result: SeismicDesignResult) -> str:
    """Plain-text Thai report suitable for monospace display."""
    f = lambda n, d=3: f"{n:,.{d}f}"
    lines = [
        "=" * 70,
        "รายการคำนวณแรงแผ่นดินไหว วิธีแรงสถิตเทียบเท่า (ELF)",
        "ตามมาตรฐาน มยผ. 1302-61",
        "=" * 70,
        "",
        "1. พารามิเตอร์พื้นฐาน",
        f"  - Ss (spectral accel. ที่คาบสั้น) = {f(result.Ss, 3)} g",
        f"  - S1 (spectral accel. ที่คาบ 1 วินาที) = {f(result.S1, 3)} g",
        f"  - ชั้นดิน (Site Class) = {result.site_class}",
        f"  - ประเภทความสำคัญ: {result.details.get('importance_name_th','')}  (Ie = {f(result.Ie,2)})",
        f"  - ระบบต้านแรงแผ่นดินไหว: {result.details.get('system_name_th','')}  (R = {f(result.R,2)})",
        "",
        "2. ค่าสัมประสิทธิ์ชั้นดิน",
        f"  - Fa = {f(result.Fa, 3)}",
        f"  - Fv = {f(result.Fv, 3)}",
        f"  - SMS = Fa * Ss = {f(result.SMS, 3)} g",
        f"  - SM1 = Fv * S1 = {f(result.SM1, 3)} g",
        f"  - SDS = (2/3)·SMS = {f(result.SDS, 3)} g",
        f"  - SD1 = (2/3)·SM1 = {f(result.SD1, 3)} g",
        "",
        "3. คาบการสั่นพื้นฐานโดยประมาณ",
        f"  - Ta = {f(result.Ta, 3)} วินาที",
        "",
        "4. สัมประสิทธิ์การตอบสนองแผ่นดินไหว (Cs)",
        f"  - Cs (บน) = SDS/(R/Ie) = {f(result.details.get('Cs_upper',0), 4)}",
        f"  - Cs (คาบ) = SD1/(T·R/Ie) = {f(result.details.get('Cs_period',0), 4)}",
        f"  - Cs_min = {f(result.details.get('Cs_min',0), 4)}",
        f"  - Cs ควบคุม = {f(result.Cs, 4)}   "
        f"({'คาบยาว' if result.Cs_controlled_by_period else 'คาบสั้น'})",
        "",
        "5. แรงเฉือนที่ฐาน (Base Shear)",
        f"  - น้ำหนักอาคารประสิทธิผล W = {f(result.W, 2)} kN",
        f"  - V = Cs · W = {f(result.V, 2)} kN",
    ]
    if result.story_forces:
        lines.append("")
        lines.append("6. การกระจายแรงตามชั้น (Fx = Cvx · V)")
        lines.append(f"  {'Level':>6} {'wi(kN)':>10} {'hi(m)':>8} {'Cvx':>8} {'Fx(kN)':>10} {'Vx(kN)':>10}")
        for row in result.story_forces:
            lines.append(
                f"  {row['level']:>6} {row['wi_kN']:>10.2f} {row['hi_m']:>8.2f} "
                f"{row['Cvx']:>8.4f} {row['Fx_kN']:>10.2f} {row['Vx_kN']:>10.2f}"
            )
    lines.append("")
    lines.append("=" * 70)
    return "\n".join(lines)
