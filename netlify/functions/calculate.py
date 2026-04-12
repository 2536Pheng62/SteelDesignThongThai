"""
Netlify Serverless Function — Steel Structure Design Calculator
Returns structured calculation steps for formula display + JSON results.
"""
import json
import sys
import os
import math
from unittest.mock import MagicMock

# --------------------------------------------------------------------------
# Mock GUI/plotting libraries before importing project modules
# --------------------------------------------------------------------------
_GUI_MOCKS = [
    'tkinter', 'tkinter.ttk', 'tkinter.messagebox', 'tkinter.filedialog',
    'matplotlib', 'matplotlib.figure', 'matplotlib.backends',
    'matplotlib.backends.backend_tkagg',
    'reportlab', 'reportlab.lib', 'reportlab.lib.pagesizes',
    'reportlab.platypus', 'reportlab.lib.styles', 'reportlab.lib.units',
    'reportlab.pdfbase', 'reportlab.pdfbase.pdfmetrics',
    'reportlab.pdfbase.ttfonts',
]
for _m in _GUI_MOCKS:
    sys.modules[_m] = MagicMock()

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from purlin import (PurlinDesign, STEEL_SECTIONS as PURLIN_SECTIONS,
                    format_detailed_report,
                    ALLOWABLE_BENDING_STRESS_FACTOR_X,
                    ALLOWABLE_BENDING_STRESS_FACTOR_Y,
                    ALLOWABLE_SHEAR_STRESS_FACTOR,
                    LIVE_LOAD_DEFLECTION_LIMIT_RATIO,
                    TOTAL_LOAD_DEFLECTION_LIMIT_RATIO,
                    E_STEEL as PURLIN_E, KPA_TO_PA, MPA_TO_PA, G)
from beam_design import BeamDesign, BeamLoad, E_STEEL as BEAM_E
from column_design import ColumnDesign, ColumnLoad, E_STEEL as COL_E, PI
from connection_design import BoltedConnectionDesign, WeldedConnectionDesign, ConnectionLoad
from baseplate_design import BasePlateDesign, BasePlateLoad
from steel_sections import C_CHANNELS, H_BEAMS, I_BEAMS, EQUAL_ANGLES, BOLTS, WELDS

_CORS = {
    "Content-Type": "application/json",
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
}


def _serial(obj):
    if isinstance(obj, float):
        if math.isnan(obj): return "NaN"
        if math.isinf(obj): return "Inf" if obj > 0 else "-Inf"
    raise TypeError(f"Not serializable: {type(obj)}")


def _ok(data):
    return {"statusCode": 200, "headers": _CORS,
            "body": json.dumps(data, default=_serial)}


def _err(msg, code=400):
    return {"statusCode": code, "headers": _CORS,
            "body": json.dumps({"error": msg})}


# --------------------------------------------------------------------------
# Handler
# --------------------------------------------------------------------------
def handler(event, context):
    if event.get("httpMethod") == "OPTIONS":
        return {"statusCode": 200, "headers": _CORS, "body": ""}
    try:
        body = json.loads(event.get("body") or "{}")
    except json.JSONDecodeError as e:
        return _err(f"Invalid JSON: {e}")

    module = body.get("module", "")
    inputs = body.get("inputs", {})

    try:
        if module == "sections":   return _ok(_get_sections())
        elif module == "purlin":   return _ok(_calc_purlin(inputs))
        elif module == "beam":     return _ok(_calc_beam(inputs))
        elif module == "column":   return _ok(_calc_column(inputs))
        elif module == "connection": return _ok(_calc_connection(inputs))
        elif module == "baseplate":  return _ok(_calc_baseplate(inputs))
        else: return _err(f"ไม่รู้จัก module: '{module}'")
    except (ValueError, KeyError) as e:
        return _err(str(e))
    except Exception as e:
        return _err(f"ข้อผิดพลาดในการคำนวณ: {e}", 500)


# --------------------------------------------------------------------------
# Sections catalogue
# --------------------------------------------------------------------------
def _get_sections():
    return {
        "purlin_sections": list(PURLIN_SECTIONS.keys()),
        "c_channels": list(C_CHANNELS.keys()),
        "h_beams": list(H_BEAMS.keys()),
        "i_beams": list(I_BEAMS.keys()),
        "angles": list(EQUAL_ANGLES.keys()),
        "bolts": list(BOLTS.keys()),
        "welds": list(WELDS.keys()),
    }


# ==========================================================================
#  PURLIN
# ==========================================================================
def _calc_purlin(inp):
    design = PurlinDesign(
        section_name=inp["section_name"],
        purlin_span=float(inp["purlin_span"]),
        purlin_spacing=float(inp["purlin_spacing"]),
        roof_slope_degree=float(inp["roof_slope_degree"]),
        dead_load_kPa=float(inp["dead_load_kPa"]),
        live_load_kPa=float(inp["live_load_kPa"]),
        basic_wind_speed_mps=float(inp["basic_wind_speed_mps"]),
        building_height_m=float(inp["building_height_m"]),
        exposure_category=str(inp["exposure_category"]),
        internal_pressure_coeff_pos=float(inp["internal_pressure_coeff_pos"]),
        internal_pressure_coeff_neg=float(inp.get("internal_pressure_coeff_neg", -0.18)),
        gust_effect_factor=float(inp.get("gust_effect_factor", 0.85)),
        topographic_factor=float(inp.get("topographic_factor", 1.0)),
        wind_directionality_factor=float(inp.get("wind_directionality_factor", 0.85)),
    )
    results = design.run_check()
    try:
        results["report"] = format_detailed_report(design, results)
    except Exception:
        results["report"] = ""
    results["calc_steps"] = _purlin_calc_steps(design, results)
    return results


def _purlin_calc_steps(design, results):
    """Build structured step-by-step calculation for formula display."""
    props   = PURLIN_SECTIONS[design.section_name]
    inp     = results["Inputs"]
    sc      = results["Stress Check"]
    sh      = results["Shear Check"]
    dc      = results["Deflection Check"]
    det     = sc.get("Details", {})
    Fbx     = results["Allowable Stresses (MPa)"]["Fbx"]
    Fby     = results["Allowable Stresses (MPa)"]["Fby"]
    fbx     = results["Calculated Stresses (MPa)"]["fbx"]
    fby     = results["Calculated Stresses (MPa)"]["fby"]

    # Loads
    w_dl_app   = design.dl_kPa * KPA_TO_PA * design.spacing
    w_self     = design.purlin_weight_per_m
    w_dl_tot   = w_dl_app + w_self
    w_ll       = design.ll_kPa * KPA_TO_PA * design.spacing
    wind_up    = inp.get("Calculated Wind Uplift (kPa)", 0)
    wind_dn    = inp.get("Calculated Wind Downward (kPa)", 0)
    w_wind_up  = wind_up  * KPA_TO_PA * design.spacing
    w_wind_dn  = wind_dn  * KPA_TO_PA * design.spacing

    # Critical stress details
    wx = det.get("w_x", 0)
    wy = det.get("w_y", 0)
    Mx = det.get("Mx", 0)
    My = det.get("My", 0)

    # Deflection (LL only, recompute for step display)
    w_ll_cos = w_ll * math.cos(design.theta_rad)
    w_ll_sin = w_ll * math.sin(design.theta_rad)
    dx_ll = (5 * w_ll_cos * design.L**4 / (384 * PURLIN_E * design.Ix)
             if design.Ix > 0 else 0)
    dy_ll = (5 * w_ll_sin * design.L**4 / (384 * PURLIN_E * design.Iy)
             if design.Iy > 0 else 0)
    dv_ll    = dx_ll * math.cos(design.theta_rad) + dy_ll * math.sin(design.theta_rad)
    allow_ll = design.L / LIVE_LOAD_DEFLECTION_LIMIT_RATIO   # m

    # Shear
    V_max_N  = sh.get("V_max (kN)", 0) * 1000
    A_web    = props.d * props.tw   # mm²
    fv_MPa   = sh.get("fv (MPa)", 0)
    Fv_MPa   = sh.get("Fv (MPa)", 0)

    def f(v, d=2):
        try: return f"{float(v):,.{d}f}"
        except: return str(v)

    steps = [
        # ── STEP 1 : Section Properties ──────────────────────────────────
        {
            "title": "1. คุณสมบัติหน้าตัด (Section Properties)",
            "rows": [
                _row("หน้าตัด",  "Section name",          "",                                  design.section_name,                ""),
                _row("น้ำหนัก",  "Unit weight",            "ตารางผู้ผลิต",                       f(props.weight),                    "kg/m"),
                _row("Fy",      "กำลังคราก",               "ตารางมาตรฐาน",                       f(props.Fy, 0),                     "MPa"),
                _row("E",       "Modulus of Elasticity",  "ค่าคงที่เหล็ก",                      f(PURLIN_E/1e9, 0),                 "GPa"),
                _row("d",       "ความสูงหน้าตัด",           "ตารางผู้ผลิต",                       f(props.d, 1),                      "mm"),
                _row("tw",      "ความหนาเอว",              "ตารางผู้ผลิต",                       f(props.tw, 1),                     "mm"),
                _row("Sx",      "Section modulus แกน x",  "ตารางผู้ผลิต",                       f(props.Sx, 0),                     "mm³"),
                _row("Sy",      "Section modulus แกน y",  "ตารางผู้ผลิต",                       f(props.Sy, 0),                     "mm³"),
                _row("Ix",      "Moment of inertia แกน x","ตารางผู้ผลิต",                       f"{props.Ix:.3e}",                  "mm⁴"),
                _row("Iy",      "Moment of inertia แกน y","ตารางผู้ผลิต",                       f"{props.Iy:.3e}",                  "mm⁴"),
            ]
        },
        # ── STEP 2 : Loads ────────────────────────────────────────────────
        {
            "title": "2. การคำนวณน้ำหนักบรรทุก (Load Calculation)",
            "rows": [
                _row("w_DL",       "น้ำหนักคงที่ (applied)",
                     "DL × spacing × 1,000",
                     f"{f(design.dl_kPa)} × {f(design.spacing)} × 1,000",
                     f(w_dl_app, 1), "N/m"),
                _row("w_self",     "น้ำหนักตัวเอง",
                     "w × g",
                     f"{f(props.weight)} × {G}",
                     f(w_self, 1), "N/m"),
                _row("w_DL_total", "น้ำหนักคงที่รวม",
                     "w_DL + w_self",
                     f"{f(w_dl_app, 1)} + {f(w_self, 1)}",
                     f(w_dl_tot, 1), "N/m"),
                _row("w_LL",       "น้ำหนักจร",
                     "LL × spacing × 1,000",
                     f"{f(design.ll_kPa)} × {f(design.spacing)} × 1,000",
                     f(w_ll, 1), "N/m"),
                _row("q_wind_up",  "แรงลมยก (uplift)",
                     "qz·G·(Cp − Cpi) [วสท./ASCE7]",
                     "จากการคำนวณ",
                     f(wind_up, 3), "kPa"),
                _row("w_wind_up",  "แรงลมยกต่อเมตร",
                     "q_wind_up × spacing × 1,000",
                     f"{f(wind_up, 3)} × {f(design.spacing)} × 1,000",
                     f(w_wind_up, 1), "N/m"),
                _row("q_wind_dn",  "แรงลมกด (downward)",
                     "qz·G·(Cp − Cpi) [วสท./ASCE7]",
                     "จากการคำนวณ",
                     f(wind_dn, 3), "kPa"),
                _row("w_wind_dn",  "แรงลมกดต่อเมตร",
                     "q_wind_dn × spacing × 1,000",
                     f"{f(wind_dn, 3)} × {f(design.spacing)} × 1,000",
                     f(w_wind_dn, 1), "N/m"),
            ]
        },
        # ── STEP 3 : Bending ─────────────────────────────────────────────
        {
            "title": "3. ตรวจสอบหน่วยแรงดัด (Bending Stress Check)",
            "subtitle": f"กรณีน้ำหนักวิกฤต: {sc.get('Critical Load Case', '')}",
            "rows": [
                _row("θ",     "มุมลาดชัน",
                     "ค่าที่ป้อน",
                     f"{f(design.slope_deg)}°",
                     f(math.degrees(design.theta_rad), 1), "°"),
                _row("wx",    "แรงกระทำตั้งฉากหลังคา",
                     "Σ(w·cos θ) ตามชุดน้ำหนักวิกฤต",
                     "ดูตารางชุดน้ำหนัก",
                     f(wx, 1), "N/m"),
                _row("wy",    "แรงกระทำขนานหลังคา",
                     "Σ(w·sin θ) ตามชุดน้ำหนักวิกฤต",
                     "ดูตารางชุดน้ำหนัก",
                     f(wy, 1), "N/m"),
                _row("Mx",    "โมเมนต์ดัดสูงสุด แกน x",
                     "wx × L² / 8",
                     f"{f(wx, 1)} × {f(design.L)}² / 8",
                     f(Mx, 1), "N·m"),
                _row("My",    "โมเมนต์ดัดสูงสุด แกน y",
                     "wy × L² / 8",
                     f"{f(wy, 1)} × {f(design.L)}² / 8",
                     f(My, 1), "N·m"),
                _row("fbx",   "หน่วยแรงดัดจริง (แกน x)",
                     "Mx / Sx",
                     f"{f(Mx, 1)} N·m / ({f(props.Sx, 0)} mm³ × 10⁻⁶)",
                     f(fbx, 2), "MPa"),
                _row("fby",   "หน่วยแรงดัดจริง (แกน y)",
                     "My / Sy",
                     f"{f(My, 1)} N·m / ({f(props.Sy, 0)} mm³ × 10⁻⁶)",
                     f(fby, 2), "MPa"),
                _row("Fbx",   "หน่วยแรงดัดที่ยอมให้ (แกน x)",
                     "0.60 × Fy",
                     f"0.60 × {f(props.Fy, 0)}",
                     f(Fbx, 1), "MPa"),
                _row("Fby",   "หน่วยแรงดัดที่ยอมให้ (แกน y)",
                     "0.75 × Fy",
                     f"0.75 × {f(props.Fy, 0)}",
                     f(Fby, 1), "MPa"),
                _check_row("U.C.", "Unity Check (Biaxial Bending)",
                           "fbx/Fbx + fby/Fby ≤ 1.0",
                           f"{f(fbx, 2)}/{f(Fbx, 1)} + {f(fby, 2)}/{f(Fby, 1)}",
                           sc["Interaction Ratio"],
                           sc["Interaction Ratio"] <= 1.0),
            ]
        },
        # ── STEP 4 : Shear ────────────────────────────────────────────────
        {
            "title": "4. ตรวจสอบหน่วยแรงเฉือน (Shear Stress Check)",
            "subtitle": f"กรณีน้ำหนักวิกฤต: {sh.get('Critical Load Case', '')}",
            "rows": [
                _row("V_max",  "แรงเฉือนสูงสุด",
                     "wx_critical × L / 2",
                     f"wx × {f(design.L)} / 2",
                     f(V_max_N, 1), "N"),
                _row("A_web",  "พื้นที่หน้าตัดเอว",
                     "d × tw",
                     f"{f(props.d, 1)} × {f(props.tw, 1)}",
                     f(A_web, 1), "mm²"),
                _row("fv",     "หน่วยแรงเฉือนจริง",
                     "V_max / A_web",
                     f"{f(V_max_N, 1)} / {f(A_web, 1)}",
                     f(fv_MPa, 2), "MPa"),
                _row("Fv",     "หน่วยแรงเฉือนที่ยอมให้",
                     "0.40 × Fy",
                     f"0.40 × {f(props.Fy, 0)}",
                     f(Fv_MPa, 1), "MPa"),
                _check_row("fv/Fv", "อัตราส่วน ≤ 1.0",
                           "fv / Fv",
                           f"{f(fv_MPa, 2)} / {f(Fv_MPa, 1)}",
                           sh.get("ratio", 0),
                           sh.get("ratio", 0) <= 1.0),
            ]
        },
        # ── STEP 5 : Deflection ───────────────────────────────────────────
        {
            "title": "5. ตรวจสอบการโก่งตัว (Deflection Check) — LL Only",
            "rows": [
                _row("E",          "Modulus of Elasticity",
                     "ค่าคงที่เหล็ก",
                     "",
                     f"{PURLIN_E:.2e}", "Pa"),
                _row("wx_LL",      "แรงลมจร ตั้งฉากหลังคา",
                     "w_LL × cos θ",
                     f"{f(w_ll, 1)} × cos({f(design.slope_deg)}°)",
                     f(w_ll_cos, 1), "N/m"),
                _row("wy_LL",      "แรงจรขนานหลังคา",
                     "w_LL × sin θ",
                     f"{f(w_ll, 1)} × sin({f(design.slope_deg)}°)",
                     f(w_ll_sin, 1), "N/m"),
                _row("δx_LL",      "การโก่งตัวแนว x",
                     "5wx_LL·L⁴ / (384·E·Ix)",
                     f"5×{f(w_ll_cos,1)}×{design.L}⁴ / (384×{PURLIN_E:.2e}×{design.Ix:.3e})",
                     f(abs(dx_ll)*1000, 3), "mm"),
                _row("δy_LL",      "การโก่งตัวแนว y",
                     "5wy_LL·L⁴ / (384·E·Iy)",
                     f"5×{f(w_ll_sin,1)}×{design.L}⁴ / (384×{PURLIN_E:.2e}×{design.Iy:.3e})",
                     f(abs(dy_ll)*1000, 3), "mm"),
                _row("δv_LL",      "การโก่งตัวแนวดิ่ง (LL)",
                     "δx·cos θ + δy·sin θ",
                     f"{f(abs(dx_ll)*1000,3)}·cos θ + {f(abs(dy_ll)*1000,3)}·sin θ",
                     f(abs(dv_ll)*1000, 3), "mm"),
                _row("δ_allow",    "การโก่งตัวที่ยอมให้ (L/240)",
                     f"L / {LIVE_LOAD_DEFLECTION_LIMIT_RATIO}",
                     f"{design.L*1000:.0f} mm / {LIVE_LOAD_DEFLECTION_LIMIT_RATIO}",
                     f(allow_ll*1000, 2), "mm"),
                _check_row("δ/δ_allow", "อัตราส่วน ≤ 1.0",
                           "δv_LL / δ_allow",
                           f"{f(abs(dv_ll)*1000,3)} / {f(allow_ll*1000,2)}",
                           abs(dv_ll) / allow_ll if allow_ll > 0 else float('inf'),
                           abs(dv_ll) <= allow_ll),
            ]
        },
    ]
    return steps


# ==========================================================================
#  BEAM
# ==========================================================================
def _calc_beam(inp):
    sname   = inp["section_name"]
    section = H_BEAMS.get(sname) or I_BEAMS.get(sname) or C_CHANNELS.get(sname)
    if not section:
        raise ValueError(f"ไม่พบหน้าตัด '{sname}' ในฐานข้อมูล")

    design = BeamDesign(
        section=section,
        span=float(inp["span"]),
        is_cantilever=bool(inp.get("is_cantilever", False)),
        lateral_bracing=str(inp.get("lateral_bracing", "continuous")),
        deflection_type=str(inp.get("deflection_type", "beam_live_load")),
    )
    load = BeamLoad(
        dead_load=float(inp.get("dead_load", 0)),
        live_load=float(inp.get("live_load", 0)),
        wind_load=float(inp.get("wind_load", 0)),
        point_load_D=float(inp.get("point_load_D", 0)),
        point_load_L=float(inp.get("point_load_L", 0)),
        point_load_W=float(inp.get("point_load_W", 0)),
    )
    result = design.check_beam(load)
    out = _dataclass_to_dict(result)
    out["calc_steps"] = _beam_calc_steps(design, section, load, result)
    return out


def _beam_calc_steps(design, section, load, result):
    def f(v, d=2):
        try: return f"{float(v):,.{d}f}"
        except: return str(v)

    L_mm   = design.span * 1000
    Fb     = result.Fb
    Fv     = result.Fv
    Fy     = section.Fy
    # Compact check
    lam_f  = section.bf / (2 * section.tf) if section.tf > 0 else 99
    lam_pf = 0.38 * math.sqrt(BEAM_E / Fy) if Fy > 0 else 99
    compact = lam_f <= lam_pf
    # Shear Cv
    h      = section.d - 2 * section.tf
    h_tw   = h / section.tw if section.tw > 0 else 99
    Cv_lim = 1.10 * math.sqrt(5.34 * BEAM_E / Fy) if Fy > 0 else 99
    Cv     = 1.0 if h_tw <= Cv_lim else Cv_lim / h_tw
    # w for critical case (simplified — show D+L combo)
    w_DL   = load.dead_load * 1000 / 1000   # N/mm
    w_LL   = load.live_load * 1000 / 1000
    w_crit = w_DL + w_LL
    P_crit = (load.point_load_D + load.point_load_L) * 1000  # N

    steps = [
        {
            "title": "1. คุณสมบัติหน้าตัด (Section Properties)",
            "rows": [
                _row("หน้าตัด", "Section",   "", section.name, ""),
                _row("Fy",  "กำลังคราก",        "ตารางมาตรฐาน",  f(Fy, 0),       "MPa"),
                _row("E",   "Modulus",          "ค่าคงที่",       f(BEAM_E, 0),   "MPa"),
                _row("d",   "ความสูงหน้าตัด",   "ตารางผู้ผลิต",   f(section.d, 1), "mm"),
                _row("bf",  "ความกว้างปีก",     "ตารางผู้ผลิต",   f(section.bf, 1), "mm"),
                _row("tw",  "ความหนาเอว",       "ตารางผู้ผลิต",   f(section.tw, 1), "mm"),
                _row("tf",  "ความหนาปีก",       "ตารางผู้ผลิต",   f(section.tf, 1), "mm"),
                _row("Sx",  "Section modulus",  "ตารางผู้ผลิต",   f(section.Sx, 0), "mm³"),
                _row("Ix",  "Moment of inertia","ตารางผู้ผลิต",   f"{section.Ix:.3e}", "mm⁴"),
            ]
        },
        {
            "title": "2. หน่วยแรงดัดที่ยอมให้ (Allowable Bending Stress)",
            "rows": [
                _row("λ_f",  "อัตราส่วนปีก",
                     "bf / (2·tf)",
                     f"{f(section.bf,1)} / (2×{f(section.tf,1)})",
                     f(lam_f, 2), ""),
                _row("λ_pf", "ขีดจำกัด compact",
                     "0.38√(E/Fy)",
                     f"0.38×√({f(BEAM_E,0)}/{f(Fy,0)})",
                     f(lam_pf, 2), ""),
                _row("Compact?", "หน้าตัด compact หรือไม่",
                     "λ_f ≤ λ_pf",
                     f"{f(lam_f,2)} {'≤' if compact else '>'} {f(lam_pf,2)}",
                     "ใช่ (compact)" if compact else "ไม่ใช่ (non-compact)", ""),
                _row("Fb",   "หน่วยแรงดัดที่ยอมให้",
                     "0.66·Fy (compact) หรือ 0.60·Fy" if compact else "0.60·Fy",
                     f"{'0.66' if compact else '0.60'}×{f(Fy,0)}",
                     f(Fb, 1), "MPa"),
            ]
        },
        {
            "title": "3. หน่วยแรงเฉือนที่ยอมให้ (Allowable Shear Stress)",
            "rows": [
                _row("h",    "ความสูงเอว",
                     "d − 2·tf",
                     f"{f(section.d,1)} − 2×{f(section.tf,1)}",
                     f(h, 1), "mm"),
                _row("h/tw", "อัตราส่วนเอว",
                     "h / tw",
                     f"{f(h,1)} / {f(section.tw,1)}",
                     f(h_tw, 1), ""),
                _row("Cv",   "Shear coefficient",
                     "1.0 (ถ้า h/tw ≤ 1.10√(5.34E/Fy))",
                     "ตรวจสอบเงื่อนไข",
                     f(Cv, 3), ""),
                _row("Fv",   "หน่วยแรงเฉือนที่ยอมให้",
                     "0.40·Fy (ถ้า Cv=1)",
                     f"0.40×{f(Fy,0)}×{f(Cv,3)}",
                     f(Fv, 1), "MPa"),
            ]
        },
        {
            "title": f"4. ตรวจสอบหน่วยแรงดัด — กรณีวิกฤต: {result.critical_load_case or 'D+L'}",
            "rows": [
                _row("w",    "น้ำหนักแผ่วิกฤต",
                     "ΣγiWi (ชุดน้ำหนักวิกฤต)",
                     f"DL+LL = {f(load.dead_load)}+{f(load.live_load)} kN/m",
                     f(w_crit * 1000, 2), "N/m"),
                _row("M_max","โมเมนต์ดัดสูงสุด",
                     "wL²/8  [+ PL/4]",
                     f"{f(w_crit,4)}×{f(L_mm,0)}²/8",
                     f(result.max_moment, 2), "kN·m"),
                _row("fb",   "หน่วยแรงดัดจริง",
                     "M / Sx",
                     f"{f(result.max_moment,2)} kN·m / {f(section.Sx,0)} mm³",
                     f(result.fb, 2), "MPa"),
                _row("Fb",   "หน่วยแรงดัดที่ยอมให้",
                     "คำนวณจาก Step 2",
                     "",
                     f(Fb, 1), "MPa"),
                _check_row("fb/Fb", "ตรวจสอบ ≤ 1.0",
                           "fb / Fb",
                           f"{f(result.fb,2)} / {f(Fb,1)}",
                           result.stress_ratio, result.stress_ratio <= 1.0),
            ]
        },
        {
            "title": "5. ตรวจสอบหน่วยแรงเฉือน (Shear Check)",
            "rows": [
                _row("V_max", "แรงเฉือนสูงสุด",
                     "wL/2  [+ P/2]",
                     f"{f(w_crit,4)}×{f(L_mm,0)}/2",
                     f(result.max_shear, 2), "kN"),
                _row("fv",   "หน่วยแรงเฉือนจริง",
                     "V / (d·tw)",
                     f"{f(result.max_shear,2)}kN / ({f(section.d,1)}×{f(section.tw,1)} mm²)",
                     f(result.fv, 2), "MPa"),
                _check_row("fv/Fv", "ตรวจสอบ ≤ 1.0",
                           "fv / Fv",
                           f"{f(result.fv,2)} / {f(Fv,1)}",
                           result.shear_ratio, result.shear_ratio <= 1.0),
            ]
        },
        {
            "title": "6. ตรวจสอบการแอ่นตัว (Deflection Check)",
            "rows": [
                _row("δ_max",    "การแอ่นตัวสูงสุด (กรณีวิกฤต)",
                     "5wL⁴/(384EI)  [+ PL³/(48EI)]",
                     f"5×{f(w_LL,4)}×{f(L_mm,0)}⁴/(384×{BEAM_E}×{f(section.Ix,.0f)})",
                     f(result.delta_max, 2), "mm"),
                _row("δ_allow",  "การแอ่นตัวที่ยอมให้",
                     "L / 360",
                     f"{f(L_mm,0)} / 360",
                     f(result.delta_allowable, 2), "mm"),
                _check_row("δ/δ_allow", "ตรวจสอบ ≤ 1.0",
                           "δ_max / δ_allow",
                           f"{f(result.delta_max,2)} / {f(result.delta_allowable,2)}",
                           result.deflection_ratio, result.deflection_ratio <= 1.0),
            ]
        },
    ]
    return steps


# ==========================================================================
#  COLUMN
# ==========================================================================
def _calc_column(inp):
    sname   = inp["section_name"]
    section = H_BEAMS.get(sname) or I_BEAMS.get(sname)
    if not section:
        raise ValueError(f"ไม่พบหน้าตัด '{sname}' ในฐานข้อมูล")

    design = ColumnDesign(
        section=section,
        height=float(inp["height"]),
        Kx=float(inp.get("Kx", 1.0)),
        Ky=float(inp.get("Ky", 1.0)),
        is_braced_frame=bool(inp.get("is_braced_frame", True)),
    )
    load = ColumnLoad(
        axial_load_D=float(inp.get("axial_load_D", 0)),
        axial_load_L=float(inp.get("axial_load_L", 0)),
        axial_load_W=float(inp.get("axial_load_W", 0)),
        moment_x_D=float(inp.get("moment_x_D", 0)),
        moment_x_L=float(inp.get("moment_x_L", 0)),
        moment_x_W=float(inp.get("moment_x_W", 0)),
        moment_y_D=float(inp.get("moment_y_D", 0)),
        moment_y_L=float(inp.get("moment_y_L", 0)),
        moment_y_W=float(inp.get("moment_y_W", 0)),
    )
    result = design.check_combined_loading(load)
    out = _dataclass_to_dict(result)
    out["calc_steps"] = _column_calc_steps(design, section, load, result)
    return out


def _column_calc_steps(design, section, load, result):
    def f(v, d=2):
        try: return f"{float(v):,.{d}f}"
        except: return str(v)

    Fy   = section.Fy
    KLx  = design.Kx * design.height * 1000  # mm
    KLy  = design.Ky * design.height * 1000
    KLx_rx = KLx / section.rx if section.rx > 0 else 9999
    KLy_ry = KLy / section.ry if section.ry > 0 else 9999
    KLr  = max(KLx_rx, KLy_ry)
    Cc   = math.sqrt(2 * PI**2 * COL_E / Fy) if Fy > 0 else 9999
    Fa   = result.Fa if hasattr(result, 'Fa') else 0
    P_crit = (load.axial_load_D + load.axial_load_L) * 1000  # N
    fa   = P_crit / section.A if section.A > 0 else 0

    steps = [
        {
            "title": "1. คุณสมบัติหน้าตัด (Section Properties)",
            "rows": [
                _row("หน้าตัด", "Section",         "", section.name,        ""),
                _row("Fy",  "กำลังคราก",            "ตารางมาตรฐาน", f(Fy, 0), "MPa"),
                _row("A",   "พื้นที่หน้าตัด",        "ตารางผู้ผลิต", f(section.A, 0), "mm²"),
                _row("rx",  "รัศมีไจเรชัน แกน x",   "ตารางผู้ผลิต", f(section.rx, 1), "mm"),
                _row("ry",  "รัศมีไจเรชัน แกน y",   "ตารางผู้ผลิต", f(section.ry, 1), "mm"),
                _row("Sx",  "Section modulus แกน x","ตารางผู้ผลิต", f(section.Sx, 0), "mm³"),
                _row("Sy",  "Section modulus แกน y","ตารางผู้ผลิต", f(section.Sy, 0), "mm³"),
            ]
        },
        {
            "title": "2. อัตราส่วนความชะลูด (Slenderness Ratio)",
            "rows": [
                _row("KL_x",    "ความยาวประสิทธิผล แกน x",
                     "Kx × H",
                     f"{design.Kx} × {f(design.height)} × 1,000",
                     f(KLx, 0), "mm"),
                _row("KL_y",    "ความยาวประสิทธิผล แกน y",
                     "Ky × H",
                     f"{design.Ky} × {f(design.height)} × 1,000",
                     f(KLy, 0), "mm"),
                _row("KL/rx",   "อัตราส่วน แกน x",
                     "KL_x / rx",
                     f"{f(KLx,0)} / {f(section.rx,1)}",
                     f(KLx_rx, 1), ""),
                _row("KL/ry",   "อัตราส่วน แกน y",
                     "KL_y / ry",
                     f"{f(KLy,0)} / {f(section.ry,1)}",
                     f(KLy_ry, 1), ""),
                _row("(KL/r)max","อัตราส่วนวิกฤต",
                     "max(KL/rx, KL/ry)",
                     f"max({f(KLx_rx,1)}, {f(KLy_ry,1)})",
                     f(KLr, 1), ""),
                _row("ขีดจำกัด", "KL/r ≤ 200",
                     "ข้อกำหนดมาตรฐาน",
                     f"{f(KLr,1)} ≤ 200",
                     "ผ่าน" if KLr <= 200 else "ไม่ผ่าน", ""),
            ]
        },
        {
            "title": "3. หน่วยแรงอัดที่ยอมให้ (Allowable Compressive Stress Fa)",
            "rows": [
                _row("Cc", "Critical slenderness parameter",
                     "√(2π²E/Fy)",
                     f"√(2×π²×{COL_E}/{f(Fy,0)})",
                     f(Cc, 1), ""),
                _row("สูตร", "Inelastic / Elastic",
                     "KL/r ≤ Cc → ใช้ inelastic; KL/r > Cc → ใช้ elastic",
                     f"{f(KLr,1)} {'≤' if KLr<=Cc else '>'} {f(Cc,1)}",
                     "Inelastic" if KLr <= Cc else "Elastic", ""),
                _row("Fa", "หน่วยแรงอัดที่ยอมให้",
                     "สูตร ASD วสท. 011038-22",
                     "จากการคำนวณ",
                     f(Fa, 2), "MPa"),
                _row("P_allow", "แรงอัดที่ยอมให้",
                     "Fa × A",
                     f"{f(Fa,2)} × {f(section.A,0)}",
                     f(Fa * section.A / 1000, 1), "kN"),
            ]
        },
        {
            "title": "4. ตรวจสอบแรงอัดและโมเมนต์ร่วม (Combined Check)",
            "rows": [
                _row("P_crit", "แรงอัดวิกฤต (D+L)",
                     "ΣγiPi",
                     f"{f(load.axial_load_D)} + {f(load.axial_load_L)} kN",
                     f(P_crit/1000, 1), "kN"),
                _row("fa",    "หน่วยแรงอัดจริง",
                     "P / A",
                     f"{f(P_crit,0)} N / {f(section.A,0)} mm²",
                     f(fa, 2), "MPa"),
                _row("fa/Fa", "อัตราส่วนแรงอัด",
                     "fa / Fa",
                     f"{f(fa,2)} / {f(Fa,2)}",
                     f(result.axial_ratio, 3), ""),
                _check_row("Interaction", "Unity Check (รวมแรงอัด + โมเมนต์)",
                           "fa/Fa + (fbx/Fbx + fby/Fby) ≤ 1.0",
                           "ดูชุดน้ำหนักวิกฤต",
                           result.interaction_ratio,
                           result.interaction_ratio <= 1.0),
            ]
        },
    ]
    return steps


# ==========================================================================
#  CONNECTION
# ==========================================================================
def _calc_connection(inp):
    conn_type = inp.get("connection_type", "bolted")
    load = ConnectionLoad(
        shear_load_D=float(inp.get("shear_load_D", 0)),
        shear_load_L=float(inp.get("shear_load_L", 0)),
        shear_load_W=float(inp.get("shear_load_W", 0)),
        axial_load_D=float(inp.get("axial_load_D", 0)),
        axial_load_L=float(inp.get("axial_load_L", 0)),
        axial_load_W=float(inp.get("axial_load_W", 0)),
        moment_load_D=float(inp.get("moment_load_D", 0)),
        moment_load_L=float(inp.get("moment_load_L", 0)),
        moment_load_W=float(inp.get("moment_load_W", 0)),
    )
    if conn_type == "bolted":
        bolt_key = inp.get("bolt_size", "M16")
        bolt = BOLTS.get(bolt_key)
        if not bolt:
            raise ValueError(f"ไม่พบสลักเกลียว '{bolt_key}'")
        design = BoltedConnectionDesign(
            bolt=bolt,
            num_bolts=int(inp.get("num_bolts", 4)),
            plate_thickness=float(inp.get("plate_thickness", 10)),
            connected_plate_thickness=float(inp.get("connected_plate_thickness", 10)),
            bolt_grade=str(inp.get("bolt_grade", "4.6")),
            connection_type=str(inp.get("bolt_connection_type", "single_shear")),
        )
    else:
        weld_key = inp.get("weld_size", "E6013")
        weld = WELDS.get(weld_key)
        if not weld:
            raise ValueError(f"ไม่พบรอยเชื่อม '{weld_key}'")
        design = WeldedConnectionDesign(
            weld=weld,
            weld_length=float(inp.get("weld_length", 100)),
            weld_throat=float(inp.get("weld_throat", 6)),
        )
    result = design.check_connection(load)
    return _dataclass_to_dict(result)


# ==========================================================================
#  BASE PLATE
# ==========================================================================
def _calc_baseplate(inp):
    sname   = inp["section_name"]
    section = H_BEAMS.get(sname) or I_BEAMS.get(sname)
    if not section:
        raise ValueError(f"ไม่พบหน้าตัด '{sname}' ในฐานข้อมูล")

    design = BasePlateDesign(
        section=section,
        plate_B=float(inp.get("plate_B", 250)),
        plate_N=float(inp.get("plate_N", 250)),
        plate_t=float(inp.get("plate_t", 20)),
        concrete_Fc=float(inp.get("concrete_Fc", 21)),
        num_anchor_bolts=int(inp.get("num_anchor_bolts", 4)),
        anchor_bolt_diameter=float(inp.get("anchor_bolt_diameter", 20)),
    )
    load = BasePlateLoad(
        axial_load_D=float(inp.get("axial_load_D", 0)),
        axial_load_L=float(inp.get("axial_load_L", 0)),
        axial_load_W=float(inp.get("axial_load_W", 0)),
        moment_x_D=float(inp.get("moment_x_D", 0)),
        moment_x_L=float(inp.get("moment_x_L", 0)),
        moment_x_W=float(inp.get("moment_x_W", 0)),
        shear_x_D=float(inp.get("shear_x_D", 0)),
        shear_x_L=float(inp.get("shear_x_L", 0)),
        shear_x_W=float(inp.get("shear_x_W", 0)),
    )
    result = design.check_base_plate(load)
    return _dataclass_to_dict(result)


# ==========================================================================
#  Shared row builders
# ==========================================================================
def _row(symbol, desc, formula, *args):
    """
    _row(sym, desc, formula, value, unit)        — 5 args
    _row(sym, desc, formula, substitution, value, unit) — 6 args
    """
    if len(args) == 2:
        return {"symbol": symbol, "desc": desc, "formula": formula,
                "substitution": "", "value": str(args[0]), "unit": str(args[1])}
    elif len(args) == 3:
        return {"symbol": symbol, "desc": desc, "formula": formula,
                "substitution": str(args[0]), "value": str(args[1]), "unit": str(args[2])}
    return {"symbol": symbol, "desc": desc, "formula": formula,
            "substitution": "", "value": "", "unit": ""}


def _check_row(symbol, desc, formula, substitution, ratio, is_ok):
    try:    r = float(ratio)
    except: r = 9999.0
    return {
        "symbol": symbol, "desc": desc, "formula": formula,
        "substitution": substitution,
        "value": f"{r:.4f}",
        "unit": "",
        "is_check": True,
        "is_ok": bool(is_ok),
        "ratio": r,
    }


def _dataclass_to_dict(obj):
    if hasattr(obj, '__dict__'):
        d = {}
        for k, v in obj.__dict__.items():
            if isinstance(v, list):
                d[k] = [_dataclass_to_dict(i) if hasattr(i, '__dict__') else i for i in v]
            elif hasattr(v, '__dict__'):
                d[k] = _dataclass_to_dict(v)
            else:
                d[k] = v
        return d
    return obj
