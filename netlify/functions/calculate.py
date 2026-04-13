"""
Netlify Serverless Function — Steel Structure Design Calculator
Returns structured calculation steps for formula display + JSON results.
"""
import json
import sys
import os
import math
from unittest.mock import MagicMock

# ── Bootstrap path ────────────────────────────────────────────────────────────
_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

# Mock GUI libraries for serverless environment
_GUI_MOCKS = [
    'tkinter', 'tkinter.ttk', 'tkinter.messagebox', 'tkinter.filedialog',
    'matplotlib', 'matplotlib.figure', 'matplotlib.backends',
    'matplotlib.backends.backend_tkagg',
]
for _m in _GUI_MOCKS:
    if _m not in sys.modules:
        sys.modules[_m] = MagicMock()

from purlin import PurlinDesign, format_detailed_report
from beam_design import BeamDesign, BeamLoad
from column_design import ColumnDesign, ColumnLoad, E_STEEL as COL_E, PI
from truss_design import TrussDesign, TrussLoad
from footing_design import FootingDesign, FootingLoad
from connection_design import BoltedConnectionDesign, WeldedConnectionDesign, ConnectionLoad
from baseplate_design import BasePlateDesign, BasePlateLoad
from steel_sections import (
    C_CHANNELS, H_BEAMS, I_BEAMS, EQUAL_ANGLES, 
    BOLTS, WELDS, STEEL_PIPES, SHS_SECTIONS, RHS_SECTIONS
)

_CORS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type",
}

def _serial(obj):
    if isinstance(obj, float):
        if math.isnan(obj): return "NaN"
        if math.isinf(obj): return "Inf" if obj > 0 else "-Inf"
    raise TypeError(f"Not serializable: {type(obj)}")

def _ok(data):
    return {"statusCode": 200, "headers": _CORS, "body": json.dumps(data, default=_serial)}

def _err(msg, code=400):
    if code >= 500:
        import traceback
        traceback.print_exc()
    return {"statusCode": code, "headers": _CORS, "body": json.dumps({"error": msg})}

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
        elif module == "truss":    return _ok(_calc_truss(inputs))
        elif module == "footing":  return _ok(_calc_footing(inputs))
        elif module == "connection": return _ok(_calc_connection(inputs))
        elif module == "baseplate":  return _ok(_calc_baseplate(inputs))
        else: return _err(f"ไม่รู้จัก module: '{module}'")
    except (ValueError, KeyError) as e:
        return _err(str(e))
    except Exception as e:
        return _err(f"ข้อผิดพลาดในการคำนวณ: {e}", 500)

def _get_sections():
    return {
        "purlin_sections": list(C_CHANNELS.keys()),
        "c_channels": list(C_CHANNELS.keys()),
        "h_beams": list(H_BEAMS.keys()),
        "i_beams": list(I_BEAMS.keys()),
        "angles": list(EQUAL_ANGLES.keys()),
        "pipes": list(STEEL_PIPES.keys()),
        "shs": list(SHS_SECTIONS.keys()),
        "rhs": list(RHS_SECTIONS.keys()),
        "bolts": list(BOLTS.keys()),
        "welds": list(WELDS.keys()),
    }

def _row(symbol, desc, formula, substitution, value, unit=""):
    return {
        "symbol": symbol, "desc": desc, "formula": formula,
        "substitution": substitution, "value": value, "unit": unit,
        "is_check": False
    }

def _check_row(symbol, desc, formula, substitution, value, is_ok, unit=""):
    return {
        "symbol": symbol, "desc": desc, "formula": formula,
        "substitution": substitution, "value": f"{float(value):.3f}", "unit": unit,
        "is_check": True, "is_ok": is_ok
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

# --------------------------------------------------------------------------
# CALCULATIONS
# --------------------------------------------------------------------------

def _calc_purlin(inp):
    # Dummy for now or recreate
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
    )
    results = design.run_check()
    results["calc_steps"] = []
    return results

def _calc_beam(inp):
    sname   = inp["section_name"]
    section = H_BEAMS.get(sname) or I_BEAMS.get(sname) or C_CHANNELS.get(sname) or RHS_SECTIONS.get(sname) or SHS_SECTIONS.get(sname) or STEEL_PIPES.get(sname)
    if not section: raise ValueError(f"ไม่พบหน้าตัด '{sname}'")

    design = BeamDesign(
        section=section,
        span=float(inp["span"]),
        method=str(inp.get("method", "ASD")),
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
    method = result.method
    steps = [
        {"title": "1. คุณสมบัติหน้าตัด (Section Properties)", "rows": [
            _row("หน้าตัด", "Section", "", section.name, ""),
            _row("Fy", "กำลังคราก", "", f(section.Fy, 0), "MPa"),
            _row("Sx", "Section modulus", "", f(section.Sx, 0), "mm³"),
            _row("Zx", "Plastic modulus", "", f(section.Zx, 0), "mm³"),
            _row("Ix", "Moment of inertia", "", f"{section.Ix:.3e}", "mm⁴"),
        ]}
    ]
    if method == "ASD":
        steps.append({"title": "2. หน่วยแรงที่ยอมให้ (Allowable Stresses - ASD)", "rows": [
            _row("Fb", "หน่วยแรงดัดที่ยอมให้", "วสท. 011038-22", "", f(result.Fb, 1), "MPa"),
            _row("Fv", "หน่วยแรงเฉือนที่ยอมให้", "วสท. 011038-22", "", f(result.Fv, 1), "MPa"),
        ]})
    else:
        steps.append({"title": "2. กำลังที่ออกแบบ (Design Capacities - LRFD)", "rows": [
            _row("φMn", "กำลังดัดที่ออกแบบ", "φ = 0.90", "", f(result.phi_Mn_kNm, 1), "kN-m"),
            _row("φVn", "กำลังเฉือนที่ออกแบบ", "φ = 0.90", "", f(result.phi_Vn_kN, 1), "kN"),
        ]})
    steps.append({"title": f"3. ตรวจสอบความแข็งแรง — กรณีวิกฤต: {result.critical_load_case}", "rows": [
        _row("M_max", "โมเมนต์สูงสุด", "Factored" if method=="LRFD" else "Service", "", f(result.max_moment, 2), "kN-m"),
        _row("V_max", "แรงเฉือนสูงสุด", "Factored" if method=="LRFD" else "Service", "", f(result.max_shear, 2), "kN"),
        _check_row("U.C. (Bending)", "อัตราส่วนโมเมนต์", "", "", result.stress_ratio, result.stress_ratio <= 1.0),
        _check_row("U.C. (Shear)", "อัตราส่วนแรงเฉือน", "", "", result.shear_ratio, result.shear_ratio <= 1.0),
    ]})
    steps.append({"title": "4. ตรวจสอบการแอ่นตัว (Deflection Check)", "rows": [
        _row("δ_max", "การแอ่นตัวสูงสุด", "วิเคราะห์โครงสร้าง", "", f(result.delta_max, 2), "mm"),
        _row("δ_allow", "การแอ่นตัวที่ยอมให้", "L / limit", "", f(result.delta_allowable, 2), "mm"),
        _check_row("δ/δ_allow", "ตรวจสอบ ≤ 1.0", "", "", result.deflection_ratio, result.deflection_ratio <= 1.0),
    ]})
    return steps

def _calc_column(inp):
    sname   = inp["section_name"]
    section = H_BEAMS.get(sname) or I_BEAMS.get(sname) or STEEL_PIPES.get(sname) or SHS_SECTIONS.get(sname) or RHS_SECTIONS.get(sname)
    if not section: raise ValueError(f"ไม่พบหน้าตัด '{sname}'")

    design = ColumnDesign(
        section=section,
        height=float(inp["height"]),
        method=str(inp.get("method", "ASD")),
        Kx=float(inp.get("Kx", 1.0)),
        Ky=float(inp.get("Ky", 1.0)),
    )
    load = ColumnLoad(
        axial_load_D=float(inp.get("axial_load_D", 0)),
        axial_load_L=float(inp.get("axial_load_L", 0)),
    )
    result = design.check_combined_loading(load)
    out = _dataclass_to_dict(result)
    out["calc_steps"] = _column_calc_steps(design, section, load, result)
    return out

def _column_calc_steps(design, section, load, result):
    def f(v, d=2):
        try: return f"{float(v):,.{d}f}"
        except: return str(v)
    method = result.method
    steps = [
        {"title": "1. คุณสมบัติหน้าตัด (Section Properties)", "rows": [
            _row("หน้าตัด", "Section", "", section.name, ""),
            _row("A", "พื้นที่หน้าตัด", "", f(section.A, 0), "mm²"),
            _row("KL/r", "Slenderness", "max(KL/rx, KL/ry)", "", f(result.critical_slenderness, 1), ""),
        ]}
    ]
    if method == "ASD":
        steps.append({"title": "2. หน่วยแรงที่ยอมให้ (ASD)", "rows": [_row("Fa", "Allowable stress", "วสท.", "", f(result.Fa, 2), "MPa")]})
    else:
        steps.append({"title": "2. กำลังที่ออกแบบ (LRFD)", "rows": [_row("φPn", "Design capacity", "φ = 0.90", "", f(result.allowable_axial_load, 1), "kN")]})
    steps.append({"title": f"3. ตรวจสอบแรงรวม — กรณีวิกฤต: {result.critical_load_case}", "rows": [
        _row("P_max", "แรงอัดสูงสุด", "Factored" if method=="LRFD" else "Service", "", f(result.max_axial_load, 1), "kN"),
        _check_row("Interaction", "Unity Check", "", "", result.interaction_ratio, result.interaction_ratio <= 1.0),
    ]})
    return steps

def _calc_truss(inp):
    sname = inp["section_name"]
    section = H_BEAMS.get(sname) or I_BEAMS.get(sname) or EQUAL_ANGLES.get(sname) or STEEL_PIPES.get(sname)
    if not section: raise ValueError(f"ไม่พบหน้าตัด '{sname}'")
    design = TrussDesign(section=section, length=float(inp["length"]), method=str(inp.get("method", "ASD")), K=float(inp.get("K", 1.0)))
    load = TrussLoad(force_D=float(inp.get("force_D", 0)), force_L=float(inp.get("force_L", 0)), force_W=float(inp.get("force_W", 0)))
    result = design.check_member(load)
    out = _dataclass_to_dict(result)
    out["calc_steps"] = _truss_calc_steps(design, section, result)
    return out

def _truss_calc_steps(design, section, result):
    f = lambda v, d=2: f"{float(v):,.{d}f}"
    steps = [
        {"title": "1. คุณสมบัติหน้าตัด", "rows": [_row("A", "พื้นที่หน้าตัด", "", f(section.A, 0), "mm²"), _row("rmin", "รัศมีไจเรชันต่ำสุด", "", f(design.r_min, 1), "mm")]},
        {"title": "2. ความชะลูด", "rows": [_check_row("L/r", "อัตราส่วนความชะลูด", f"{design.K}*L/r", "", result.slenderness, result.slenderness <= result.limit_slenderness)]},
        {"title": "3. กำลังรับแรง", "rows": [_row("Pmax", "แรงสูงสุด", "", f(abs(result.max_force), 1), "kN"), _check_row("P/Pn", "อัตราส่วนกำลัง", "", "", result.ratio, result.ratio <= 1.0)]}
    ]
    return steps

def _calc_footing(inp):
    design = FootingDesign(width=float(inp["width"]), length=float(inp["length"]), thickness=float(inp["thickness"]), allowable_bearing_kPa=float(inp["allowable_bearing_kPa"]))
    load = FootingLoad(axial_load_D=float(inp.get("axial_load_D", 0)), axial_load_L=float(inp.get("axial_load_L", 0)))
    result = design.check_footing(load)
    out = _dataclass_to_dict(result)
    out["calc_steps"] = _footing_calc_steps(design, result)
    return out

def _footing_calc_steps(design, result):
    f = lambda v, d=2: f"{float(v):,.{d}f}"
    steps = [
        {"title": "1. แรงดันดิน", "rows": [_row("Area", "พื้นที่ฐานราก", "", f(result.actual_area, 2), "m²"), _check_row("q/qa", "อัตราส่วนแรงดันดิน", "", "", result.bearing_ratio, result.bearing_ratio <= 1.0)]},
        {"title": "2. แรงเฉือนคอนกรีต", "rows": [_check_row("Vu1/Vc1", "One-way Shear", "", "", result.shear_1way_ratio, result.shear_1way_ratio <= 1.0), _check_row("Vu2/Vc2", "Punching Shear", "", "", result.shear_2way_ratio, result.shear_2way_ratio <= 1.0)]}
    ]
    return steps

def _calc_connection(inp):
    return {}

def _calc_baseplate(inp):
    return {}
