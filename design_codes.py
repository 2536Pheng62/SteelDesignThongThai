"""
Design Codes Module (ชุดกฎการออกแบบ)
Implements LRFD per AISC 360-16 and วสท. 011038-22
Covers: Section classification, LTB, beam/column LRFD capacity
"""
import math
from dataclasses import dataclass, field
from typing import Optional
from steel_sections import SteelSection

PI = math.pi
E_STEEL = 2.0e5   # MPa
G_STEEL = 7.9e4   # MPa

# LRFD resistance factors
PHI_b = 0.90   # Bending
PHI_v = 1.00   # Shear  (AISC 360-16 §G2.1, Cv1=1 most rolled I-shapes)
PHI_c = 0.90   # Compression


# ============================================================================
# Section Classification (AISC 360-16 Table B4.1b - For flexure)
# ============================================================================

@dataclass
class SectionClass:
    """Result of section compactness classification."""
    flange_class: str    # "compact", "noncompact", "slender"
    web_class: str
    overall_class: str   # worst of flange and web
    lambda_f: float      # flange slenderness bf/(2tf)
    lambda_pf: float     # compact flange limit
    lambda_rf: float     # noncompact flange limit
    lambda_w: float      # web slenderness h/tw
    lambda_pw: float     # compact web limit
    lambda_rw: float     # noncompact web limit


def classify_section(sec: SteelSection, Fy: Optional[float] = None) -> SectionClass:
    """
    Classify I-shape/H-shape section for flexure per AISC 360-16 Table B4.1b.
    For RHS/SHS and pipes, uses appropriate limits.

    Args:
        sec: SteelSection
        Fy: Override yield strength (MPa). Defaults to sec.Fy.
    Returns:
        SectionClass
    """
    Fy = Fy or sec.Fy

    # Flange: bf/(2*tf) for I/H-shapes
    if sec.tf > 0 and sec.bf > 0:
        lambda_f = sec.bf / (2.0 * sec.tf)
    else:
        lambda_f = 0.0

    # Compact flange limit  λpf = 0.38√(E/Fy)
    lambda_pf = 0.38 * math.sqrt(E_STEEL / Fy)
    # Noncompact flange limit  λrf = 1.0√(E/Fy)
    lambda_rf = 1.0 * math.sqrt(E_STEEL / Fy)

    if lambda_f <= lambda_pf:
        flange_class = "compact"
    elif lambda_f <= lambda_rf:
        flange_class = "noncompact"
    else:
        flange_class = "slender"

    # Web: h/tw  (h = clear distance between flanges = d - 2*tf)
    h = sec.d - 2.0 * sec.tf
    lambda_w = h / sec.tw if sec.tw > 0 else 0.0

    # Compact web limit  λpw = 3.76√(E/Fy)
    lambda_pw = 3.76 * math.sqrt(E_STEEL / Fy)
    # Noncompact web limit  λrw = 5.70√(E/Fy)
    lambda_rw = 5.70 * math.sqrt(E_STEEL / Fy)

    if lambda_w <= lambda_pw:
        web_class = "compact"
    elif lambda_w <= lambda_rw:
        web_class = "noncompact"
    else:
        web_class = "slender"

    # Overall: worst case
    rank = {"compact": 0, "noncompact": 1, "slender": 2}
    overall = flange_class if rank[flange_class] >= rank[web_class] else web_class

    return SectionClass(
        flange_class=flange_class,
        web_class=web_class,
        overall_class=overall,
        lambda_f=lambda_f,
        lambda_pf=lambda_pf,
        lambda_rf=lambda_rf,
        lambda_w=lambda_w,
        lambda_pw=lambda_pw,
        lambda_rw=lambda_rw,
    )


# ============================================================================
# Lateral-Torsional Buckling — AISC 360-16 Chapter F (F2 for doubly-symmetric I)
# ============================================================================

@dataclass
class LTBResult:
    """Full LTB calculation result."""
    Mn: float          # Nominal moment capacity (N-mm)
    phi_Mn: float      # Design moment capacity (N-mm)
    zone: str          # "plastic", "inelastic_LTB", "elastic_LTB"
    Lp: float          # mm — plastic limit unbraced length
    Lr: float          # mm — elastic LTB limit unbraced length
    Lb: float          # mm — actual unbraced length
    Cb: float          # Moment gradient factor
    Mp: float          # Plastic moment (N-mm)


def calc_rts(sec: SteelSection) -> float:
    """
    Effective radius of gyration rts (AISC 360-16 Eq. F2-7).
    rts² = √(Iy * Cw) / Sx
    """
    if sec.Sx > 0 and sec.Iy > 0 and sec.Cw > 0:
        return math.sqrt(math.sqrt(sec.Iy * sec.Cw) / sec.Sx)
    # Fallback: approximate as ry
    return sec.ry


def calc_ho(sec: SteelSection) -> float:
    """Distance between flange centroids (mm): ho = d - tf"""
    return sec.d - sec.tf


def calc_ltb(
    sec: SteelSection,
    Lb: float,
    Cb: float = 1.0,
    Fy: Optional[float] = None,
) -> LTBResult:
    """
    Lateral-Torsional Buckling check for doubly-symmetric I/H-shapes.
    Per AISC 360-16 Section F2.

    Args:
        sec:  SteelSection
        Lb:   Unbraced length (mm)
        Cb:   Moment gradient factor (default 1.0 = conservative)
        Fy:   Override yield strength (MPa)
    Returns:
        LTBResult with Mn and φMn in N-mm
    """
    Fy = Fy or sec.Fy

    Sx = sec.Sx      # mm³
    Zx = sec.Zx      # mm³
    J  = sec.J       # mm⁴
    Iy = sec.Iy      # mm⁴
    Cw = sec.Cw      # mm⁶

    Mp = Fy * Zx     # N-mm (plastic moment, Fy in MPa = N/mm²)

    rts = calc_rts(sec)
    ho = calc_ho(sec)

    c = 1.0  # doubly-symmetric I-shape (AISC F2-8b)

    # Lp — limiting unbraced length for plastic hinge (F2-5)
    Lp = 1.76 * sec.ry * math.sqrt(E_STEEL / Fy)

    # Lr — limiting unbraced length for elastic LTB (F2-6)
    term1 = 1.95 * rts * (E_STEEL / (0.7 * Fy))
    if Sx > 0 and ho > 0:
        sqrt_term = math.sqrt(
            (J * c) / (Sx * ho)
            + math.sqrt(((J * c) / (Sx * ho))**2 + 6.76 * (0.7 * Fy / E_STEEL)**2)
        )
    else:
        sqrt_term = 1.0
    Lr = term1 * sqrt_term

    # Determine zone and Mn
    if Lb <= Lp:
        zone = "plastic"
        Mn = Mp

    elif Lb <= Lr:
        zone = "inelastic_LTB"
        # F2-2: Mn = Cb[Mp - (Mp - 0.7*Fy*Sx)*(Lb-Lp)/(Lr-Lp)] <= Mp
        Mn = Cb * (Mp - (Mp - 0.7 * Fy * Sx) * (Lb - Lp) / (Lr - Lp))
        Mn = min(Mn, Mp)

    else:
        zone = "elastic_LTB"
        # F2-3: Mn = Fcr * Sx   where Fcr per F2-4
        Fcr = (Cb * PI**2 * E_STEEL / (Lb / rts)**2) * math.sqrt(
            1.0 + 0.078 * (J * c / (Sx * ho)) * (Lb / rts)**2
        ) if rts > 0 else 0.0
        Mn = min(Fcr * Sx, Mp)

    phi_Mn = PHI_b * Mn

    return LTBResult(
        Mn=Mn, phi_Mn=phi_Mn,
        zone=zone, Lp=Lp, Lr=Lr, Lb=Lb,
        Cb=Cb, Mp=Mp,
    )


def calc_Cb(M1: float, M2: float, M3: float, Mmax: float) -> float:
    """
    Moment gradient factor Cb per AISC 360-16 Eq. F1-1.
    M1, M2, M3 = moments at quarter points of unbraced segment (N-mm)
    Mmax = maximum moment in unbraced segment (N-mm)
    Uses absolute values internally.
    """
    M1, M2, M3, Mmax = abs(M1), abs(M2), abs(M3), abs(Mmax)
    if Mmax == 0:
        return 1.0
    Cb = 12.5 * Mmax / (2.5 * Mmax + 3.0 * M1 + 4.0 * M2 + 3.0 * M3)
    return min(Cb, 3.0)


# ============================================================================
# LRFD Beam Capacity — Chapter F/G (bending + shear)
# ============================================================================

@dataclass
class BeamCapacityLRFD:
    """LRFD beam capacity result."""
    phi_Mn: float        # N-mm — design flexural strength
    phi_Vn: float        # N   — design shear strength
    ltb: LTBResult
    section_class: SectionClass
    # Reduced capacity for noncompact/slender flanges (Mn governs)
    Mn_FLB: float        # N-mm — flange local buckling capacity
    Mn_WLB: float        # N-mm — web local buckling capacity
    Mn_final: float      # N-mm — governing Mn


def calc_beam_capacity_lrfd(
    sec: SteelSection,
    Lb: float,
    Cb: float = 1.0,
    Fy: Optional[float] = None,
) -> BeamCapacityLRFD:
    """
    Full LRFD beam capacity for doubly-symmetric compact/noncompact I/H-shapes.
    Checks LTB (F2), Flange Local Buckling (F3), Web Local Buckling.

    Args:
        sec: SteelSection
        Lb:  Unbraced length (mm)
        Cb:  Moment gradient factor
        Fy:  Override yield strength
    Returns:
        BeamCapacityLRFD
    """
    Fy = Fy or sec.Fy
    sc = classify_section(sec, Fy)
    ltb = calc_ltb(sec, Lb, Cb, Fy)

    Mp = Fy * sec.Zx  # N-mm

    # --- Flange Local Buckling (F3) ---
    if sc.flange_class == "compact":
        Mn_FLB = Mp
    elif sc.flange_class == "noncompact":
        # F3-1: Mn = Mp - (Mp - 0.7*Fy*Sx)*( (λf-λpf)/(λrf-λpf) )
        Mn_FLB = Mp - (Mp - 0.7 * Fy * sec.Sx) * (
            (sc.lambda_f - sc.lambda_pf) / (sc.lambda_rf - sc.lambda_pf)
        )
    else:
        # Slender flange: elastic FLB (simplified Fel approach)
        kc = max(0.35, min(0.76, 4.0 / math.sqrt(sec.d / sec.tw))) if sec.tw > 0 else 0.35
        Fcr_FLB = 0.9 * E_STEEL * kc / sc.lambda_f**2
        Mn_FLB = min(Fcr_FLB * sec.Sx, Mp)

    # --- Web Local Buckling — noncompact webs (F4/F5) ---
    # Simplified for doubly-symmetric sections (full check requires rpc/rpg)
    if sc.web_class == "compact":
        Mn_WLB = Mp
    elif sc.web_class == "noncompact":
        # Linear interpolation: Mn = Mp - 0.1*Mp*( (λw-λpw)/(λrw-λpw) )  [approximate]
        Mn_WLB = Mp - 0.1 * Mp * (
            (sc.lambda_w - sc.lambda_pw) / (sc.lambda_rw - sc.lambda_pw)
        )
    else:
        # Slender web: use Rpg factor approach (F5-2)
        aw = sec.tw * (sec.d - 2 * sec.tf) / (sec.tf * sec.bf) if sec.tf * sec.bf > 0 else 0
        aw = min(aw, 10.0)
        Rpg = 1.0 - aw / (1200.0 + 300.0 * aw) * (sc.lambda_w - 5.7 * math.sqrt(E_STEEL / Fy))
        Rpg = min(Rpg, 1.0)
        Mn_WLB = Rpg * Fy * sec.Sx

    # Governing Mn = min of LTB, FLB, WLB
    Mn_final = min(ltb.Mn, Mn_FLB, Mn_WLB)
    phi_Mn = PHI_b * Mn_final

    # --- Shear capacity (G2.1) ---
    h = sec.d - 2.0 * sec.tf
    h_tw = h / sec.tw if sec.tw > 0 else float("inf")
    kv = 5.34  # unstiffened web
    limit1 = 2.24 * math.sqrt(E_STEEL / Fy)

    if h_tw <= limit1:
        Cv1 = 1.0
        phi_v_used = 1.00
    else:
        kv_full = 5.34
        Cv1 = min(1.0, 1.10 * math.sqrt(kv_full * E_STEEL / Fy) / h_tw)
        phi_v_used = PHI_v

    Vn = 0.6 * Fy * (sec.d * sec.tw) * Cv1  # N
    phi_Vn = phi_v_used * Vn

    return BeamCapacityLRFD(
        phi_Mn=phi_Mn,
        phi_Vn=phi_Vn,
        ltb=ltb,
        section_class=sc,
        Mn_FLB=Mn_FLB,
        Mn_WLB=Mn_WLB,
        Mn_final=Mn_final,
    )


# ============================================================================
# LRFD Column Capacity — Chapter E (axial compression)
# ============================================================================

@dataclass
class ColumnCapacityLRFD:
    """LRFD column axial capacity result."""
    phi_Pn: float      # N — design compressive strength
    Pn: float          # N — nominal compressive strength
    Fcr: float         # MPa — critical stress
    Fe: float          # MPa — elastic buckling stress
    KL_r: float        # governing slenderness ratio
    KLx_m: float       # mm — effective length x
    KLy_m: float       # mm — effective length y
    failure_mode: str  # "inelastic_buckling" or "elastic_buckling"


def calc_column_capacity_lrfd(
    sec: SteelSection,
    height: float,
    Kx: float = 1.0,
    Ky: float = 1.0,
    Fy: Optional[float] = None,
) -> ColumnCapacityLRFD:
    """
    LRFD axial compression capacity per AISC 360-16 Chapter E.

    Args:
        sec:    SteelSection
        height: Column height (m)
        Kx:     Effective length factor about x-axis
        Ky:     Effective length factor about y-axis
        Fy:     Override yield strength (MPa)
    Returns:
        ColumnCapacityLRFD
    """
    Fy = Fy or sec.Fy
    A = sec.A   # mm²

    KLx = Kx * height * 1000.0   # mm
    KLy = Ky * height * 1000.0   # mm

    KLx_rx = KLx / sec.rx if sec.rx > 0 else float("inf")
    KLy_ry = KLy / sec.ry if sec.ry > 0 else float("inf")
    KL_r = max(KLx_rx, KLy_ry)

    # Elastic buckling stress (E3-4)
    Fe = PI**2 * E_STEEL / KL_r**2

    # Critical stress (E3-2/E3-3)
    if KL_r <= 4.71 * math.sqrt(E_STEEL / Fy):  # inelastic
        Fcr = (0.658 ** (Fy / Fe)) * Fy
        mode = "inelastic_buckling"
    else:  # elastic
        Fcr = 0.877 * Fe
        mode = "elastic_buckling"

    Pn = Fcr * A          # N
    phi_Pn = PHI_c * Pn   # N

    return ColumnCapacityLRFD(
        phi_Pn=phi_Pn,
        Pn=Pn,
        Fcr=Fcr,
        Fe=Fe,
        KL_r=KL_r,
        KLx_m=KLx,
        KLy_m=KLy,
        failure_mode=mode,
    )


# ============================================================================
# LRFD Combined Loading — Chapter H (H1-1 interaction)
# ============================================================================

@dataclass
class CombinedCheckLRFD:
    """LRFD combined axial + bending interaction result."""
    ratio: float       # interaction ratio (<=1.0 = OK)
    is_ok: bool
    Pu: float          # N — factored axial demand
    Mux: float         # N-mm — factored x-moment demand
    Muy: float         # N-mm — factored y-moment demand
    phi_Pn: float      # N — axial capacity
    phi_Mnx: float     # N-mm — x-bending capacity
    phi_Mny: float     # N-mm — y-bending capacity (simplified)
    equation: str      # "H1-1a" or "H1-1b"


def check_combined_lrfd(
    sec: SteelSection,
    Pu: float,
    Mux: float,
    Muy: float,
    phi_Pn: float,
    phi_Mnx: float,
    phi_Mny: float,
) -> CombinedCheckLRFD:
    """
    LRFD combined axial-flexure interaction per AISC 360-16 H1-1.

    Args:
        Pu:      Factored axial load (N, compression positive)
        Mux/Muy: Factored moments (N-mm)
        phi_Pn:  Design compressive strength (N)
        phi_Mnx/Mny: Design flexural strengths (N-mm)
    """
    pr_pc = Pu / phi_Pn if phi_Pn > 0 else float("inf")

    if pr_pc >= 0.2:
        # H1-1a
        ratio = pr_pc + (8.0 / 9.0) * (
            (Mux / phi_Mnx if phi_Mnx > 0 else 0)
            + (Muy / phi_Mny if phi_Mny > 0 else 0)
        )
        eq = "H1-1a"
    else:
        # H1-1b
        ratio = pr_pc / 2.0 + (
            (Mux / phi_Mnx if phi_Mnx > 0 else 0)
            + (Muy / phi_Mny if phi_Mny > 0 else 0)
        )
        eq = "H1-1b"

    return CombinedCheckLRFD(
        ratio=ratio,
        is_ok=ratio <= 1.0,
        Pu=Pu,
        Mux=Mux,
        Muy=Muy,
        phi_Pn=phi_Pn,
        phi_Mnx=phi_Mnx,
        phi_Mny=phi_Mny,
        equation=eq,
    )


# ============================================================================
# Utility: Tension capacity per AISC 360-16 Chapter D
# ============================================================================

def calc_tension_lrfd(sec: SteelSection, Ae: Optional[float] = None) -> dict:
    """
    LRFD tensile capacity (D2-1/D2-2).
    Ae: Effective net area (mm²). If None, uses Ag (gross area).
    Returns dict with phi_Pn_yield and phi_Pn_fracture.
    """
    Ag = sec.A
    Ae = Ae or Ag
    phi_Pn_yield = 0.90 * Ag * sec.Fy       # D2-1
    phi_Pn_fracture = 0.75 * Ae * sec.Fu    # D2-2
    return {
        "phi_Pn_yield_N": phi_Pn_yield,
        "phi_Pn_fracture_N": phi_Pn_fracture,
        "phi_Pn_N": min(phi_Pn_yield, phi_Pn_fracture),
        "governs": "yield" if phi_Pn_yield <= phi_Pn_fracture else "fracture",
    }


# ============================================================================
# ASD allowable stress helpers (consolidates scattered logic)
# ============================================================================

def asd_allowable_bending(sec: SteelSection, lateral_bracing: str = "continuous") -> float:
    """
    ASD allowable bending stress per วสท. 011038-22.
    Returns Fb in MPa.
    """
    sc = classify_section(sec)
    if sc.overall_class == "compact" and lateral_bracing == "continuous":
        return 0.66 * sec.Fy
    elif lateral_bracing == "ends_only":
        return 0.50 * sec.Fy
    else:
        return 0.60 * sec.Fy


def asd_allowable_shear(sec: SteelSection) -> float:
    """ASD allowable shear stress Fv (MPa) per วสท. 011038-22."""
    h = sec.d - 2.0 * sec.tf
    h_tw = h / sec.tw if sec.tw > 0 else float("inf")
    kv = 5.34
    limit = 1.10 * math.sqrt(kv * E_STEEL / sec.Fy)
    Cv = 1.0 if h_tw <= limit else limit / h_tw
    return 0.60 * sec.Fy * Cv


def asd_allowable_compression(sec: SteelSection, height: float, Kx: float = 1.0, Ky: float = 1.0) -> float:
    """
    ASD allowable compressive stress Fa (MPa) per วสท. 011038-22.
    """
    KLx = Kx * height * 1000.0
    KLy = Ky * height * 1000.0
    KLx_rx = KLx / sec.rx if sec.rx > 0 else float("inf")
    KLy_ry = KLy / sec.ry if sec.ry > 0 else float("inf")
    KLr = max(KLx_rx, KLy_ry)
    if KLr > 200:
        return 0.0
    Cc = math.sqrt(2.0 * PI**2 * E_STEEL / sec.Fy)
    if KLr <= Cc:
        num = (1.0 - KLr**2 / (2.0 * Cc**2)) * sec.Fy
        den = 5.0/3.0 + 3.0*KLr/(8.0*Cc) - KLr**3/(8.0*Cc**3)
        return num / den
    else:
        return 12.0 * PI**2 * E_STEEL / (23.0 * KLr**2)
