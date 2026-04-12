"""
Netlify Serverless Function — Steel Structure Design Calculator
Wraps the Python calculation modules for web API use.
"""
import json
import sys
import os
import math
from unittest.mock import MagicMock

# --------------------------------------------------------------------------
# Mock all GUI/plotting libraries BEFORE importing project modules.
# purlin.py has top-level tkinter/matplotlib imports that we must silence.
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

# Add project root to sys.path so we can import the project modules
_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

# Now import the project calculation modules
from purlin import PurlinDesign, STEEL_SECTIONS as PURLIN_SECTIONS, format_detailed_report
from beam_design import BeamDesign, BeamLoad
from column_design import ColumnDesign, ColumnLoad
from connection_design import BoltedConnectionDesign, WeldedConnectionDesign, ConnectionLoad
from baseplate_design import BasePlateDesign, BasePlateLoad
from steel_sections import C_CHANNELS, H_BEAMS, I_BEAMS, EQUAL_ANGLES, BOLTS, WELDS

# --------------------------------------------------------------------------
# CORS headers (Netlify Functions need these for browser access)
# --------------------------------------------------------------------------
_CORS = {
    "Content-Type": "application/json",
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
}


def _serial(obj):
    """JSON serialiser for floats that are inf/nan."""
    if isinstance(obj, float):
        if math.isnan(obj):
            return "NaN"
        if math.isinf(obj):
            return "Inf" if obj > 0 else "-Inf"
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


def _ok(data):
    return {"statusCode": 200, "headers": _CORS, "body": json.dumps(data, default=_serial)}


def _err(msg, code=400):
    return {"statusCode": code, "headers": _CORS, "body": json.dumps({"error": msg})}


# --------------------------------------------------------------------------
# Main handler
# --------------------------------------------------------------------------
def handler(event, context):
    if event.get("httpMethod") == "OPTIONS":
        return {"statusCode": 200, "headers": _CORS, "body": ""}

    try:
        body = json.loads(event.get("body") or "{}")
    except json.JSONDecodeError as exc:
        return _err(f"Invalid JSON body: {exc}")

    module = body.get("module", "")
    inputs = body.get("inputs", {})

    try:
        if module == "sections":
            return _ok(_get_sections())
        elif module == "purlin":
            return _ok(_calc_purlin(inputs))
        elif module == "beam":
            return _ok(_calc_beam(inputs))
        elif module == "column":
            return _ok(_calc_column(inputs))
        elif module == "connection":
            return _ok(_calc_connection(inputs))
        elif module == "baseplate":
            return _ok(_calc_baseplate(inputs))
        else:
            return _err(f"Unknown module: '{module}'. Valid: sections, purlin, beam, column, connection, baseplate")
    except (ValueError, KeyError) as exc:
        return _err(str(exc))
    except Exception as exc:
        return _err(f"Calculation error: {exc}", 500)


# --------------------------------------------------------------------------
# Section catalogue
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


# --------------------------------------------------------------------------
# Purlin
# --------------------------------------------------------------------------
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
        results["report"] = "(รายงานโดยละเอียดไม่พร้อมใช้งาน)"
    return results


# --------------------------------------------------------------------------
# Beam
# --------------------------------------------------------------------------
def _calc_beam(inp):
    section_name = inp["section_name"]
    section = H_BEAMS.get(section_name) or I_BEAMS.get(section_name) or C_CHANNELS.get(section_name)
    if not section:
        raise ValueError(f"Steel section '{section_name}' not found in database")

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
    return _dataclass_to_dict(result)


# --------------------------------------------------------------------------
# Column
# --------------------------------------------------------------------------
def _calc_column(inp):
    section_name = inp["section_name"]
    section = H_BEAMS.get(section_name) or I_BEAMS.get(section_name)
    if not section:
        raise ValueError(f"Steel section '{section_name}' not found in database")

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
    return _dataclass_to_dict(result)


# --------------------------------------------------------------------------
# Connection
# --------------------------------------------------------------------------
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
            raise ValueError(f"Bolt size '{bolt_key}' not found")
        design = BoltedConnectionDesign(
            bolt=bolt,
            num_bolts=int(inp.get("num_bolts", 4)),
            plate_thickness=float(inp.get("plate_thickness", 10)),
            connected_plate_thickness=float(inp.get("connected_plate_thickness", 10)),
            bolt_grade=str(inp.get("bolt_grade", "4.6")),
            connection_type=str(inp.get("bolt_connection_type", "single_shear")),
        )
        result = design.check_connection(load)
    else:
        weld_key = inp.get("weld_size", "E6013")
        weld = WELDS.get(weld_key)
        if not weld:
            raise ValueError(f"Weld type '{weld_key}' not found")
        design = WeldedConnectionDesign(
            weld=weld,
            weld_length=float(inp.get("weld_length", 100)),
            weld_throat=float(inp.get("weld_throat", 6)),
        )
        result = design.check_connection(load)

    return _dataclass_to_dict(result)


# --------------------------------------------------------------------------
# Base Plate
# --------------------------------------------------------------------------
def _calc_baseplate(inp):
    section_name = inp["section_name"]
    section = H_BEAMS.get(section_name) or I_BEAMS.get(section_name)
    if not section:
        raise ValueError(f"Steel section '{section_name}' not found in database")

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


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------
def _dataclass_to_dict(obj):
    """Convert a dataclass instance (or any object with __dict__) to a dict."""
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
