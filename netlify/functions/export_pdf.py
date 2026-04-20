"""
Netlify Serverless Function — PDF Report Generator
POST /api/export-pdf
Body: { module, data, project }
Returns: application/pdf binary
"""
import base64
import json
import os
import sys
from unittest.mock import MagicMock

# ── Bootstrap path ────────────────────────────────────────────────────────────
_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

# Mock only GUI/plotting
_GUI_MOCKS = [
    'tkinter', 'tkinter.ttk', 'tkinter.messagebox', 'tkinter.filedialog',
    'matplotlib', 'matplotlib.figure', 'matplotlib.backends',
    'matplotlib.backends.backend_tkagg',
]
for _m in _GUI_MOCKS:
    if _m not in sys.modules:
        sys.modules[_m] = MagicMock()

from report_generator import (
    generate_beam_report, generate_column_report,
    generate_truss_report, generate_footing_report,
    generate_combined_report, ProjectInfo,
)
from beam_design import BeamDesign, BeamLoad
from column_design import ColumnDesign, ColumnLoad
from truss_design import TrussDesign, TrussLoad
from footing_design import FootingDesign, FootingLoad
from steel_sections import H_BEAMS, I_BEAMS, STEEL_PIPES, C_CHANNELS, RHS_SECTIONS, EQUAL_ANGLES


def _get_section(name: str):
    for db in (H_BEAMS, I_BEAMS, STEEL_PIPES, C_CHANNELS, RHS_SECTIONS, EQUAL_ANGLES):
        if name in db:
            return db[name]
    raise ValueError(f"ไม่พบหน้าตัด: {name}")


def _project_from_dict(d: dict) -> ProjectInfo:
    return ProjectInfo(
        project_name=d.get("project_name", "โครงการ"),
        project_no=d.get("project_no", ""),
        engineer=d.get("engineer", ""),
        checker=d.get("checker", ""),
        client=d.get("client", ""),
        location=d.get("location", ""),
    )


def handler(event, context):
    try:
        body = json.loads(event.get("body") or "{}")
        module  = body.get("module", "")
        data    = body.get("data", {})
        project = _project_from_dict(body.get("project", {}))

        pdf_bytes = None

        if module == "beam":
            section_name = data.get("section_name", "")
            span         = float(data.get("span", 6.0))
            sec          = _get_section(section_name)
            loads = BeamLoad(
                dead_load=float(data.get("dead_load", 0)),
                live_load=float(data.get("live_load", 0)),
                point_load_L=float(data.get("point_load_L", 0)),
            )
            bd = BeamDesign(section=sec, span=span, method=data.get("method", "ASD"))
            result = bd.check_beam(loads)
            result.details["properties"] = {"Fy": sec.Fy, "Sx": sec.Sx, "Ix": sec.Ix}
            pdf_bytes = generate_beam_report(result, section_name, span, project)

        elif module == "column":
            section_name = data.get("section_name", "")
            height       = float(data.get("height", 4.0))
            sec          = _get_section(section_name)
            loads = ColumnLoad(
                axial_load_D=float(data.get("axial_load_D", 0)),
                axial_load_L=float(data.get("axial_load_L", 0)),
            )
            cd = ColumnDesign(section=sec, height=height, method=data.get("method", "ASD"))
            result = cd.check_combined_loading(loads)
            result.Fy = sec.Fy
            result.details["properties"] = {"A": sec.A, "rx": sec.rx, "ry": sec.ry}
            pdf_bytes = generate_column_report(result, section_name, height, project)

        elif module == "truss":
            section_name = data.get("section_name", "")
            length       = float(data.get("length", 3.0))
            sec          = _get_section(section_name)
            loads        = TrussLoad(force_D=float(data.get("force_D", 0)), force_L=float(data.get("force_L", 0)))
            td = TrussDesign(section=sec, length=length, method=data.get("method", "ASD"))
            result = td.check_member(loads)
            pdf_bytes = generate_truss_report(result, section_name, length, project)

        elif module == "footing":
            B, L, H = float(data.get("width", 1.5)), float(data.get("length", 1.5)), float(data.get("thickness", 0.3))
            loads = FootingLoad(axial_load_D=float(data.get("axial_load_D", 0)), axial_load_L=float(data.get("axial_load_L", 0)))
            fd = FootingDesign(width=B, length=L, thickness=H, allowable_bearing_kPa=float(data.get("allowable_bearing_kPa", 150)))
            result = fd.check_footing(loads)
            pdf_bytes = generate_footing_report(result, B, L, H, project)

        else:
            return {"statusCode": 400, "body": json.dumps({"error": f"module '{module}' ไม่รองรับ PDF export"})}

        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/pdf",
                "Content-Disposition": f'attachment; filename="calculation_{module}.pdf"',
            },
            "body": base64.b64encode(pdf_bytes).decode("utf-8"),
            "isBase64Encoded": True,
        }

    except Exception as exc:
        return {"statusCode": 500, "body": json.dumps({"error": str(exc)})}
