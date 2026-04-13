"""
Steel Structure Design Web App - Gradio Version
Deployable on Netlify via Python web server
Based on Thai Standards (มอก., วสท., มยผ.)
"""
import gradio as gr
import math
import json
from datetime import datetime
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from steel_sections import C_CHANNELS, H_BEAMS, I_BEAMS, STEEL_PIPES, MATERIAL_GRADES
from load_combinations import DEFLECTION_LIMITS
from purlin import PurlinDesign
from beam_design import BeamDesign, BeamLoad
from column_design import ColumnDesign, ColumnLoad

# ============================================================================
# PURLIN DESIGN
# ============================================================================
def design_purlin(section_name, span, spacing, slope, dl, ll, wind_speed, height, exposure, cpi_pos, cpi_neg):
    """Calculate purlin design"""
    try:
        design = PurlinDesign(
            section_name=section_name,
            purlin_span=float(span),
            purlin_spacing=float(spacing),
            roof_slope_degree=float(slope),
            dead_load_kPa=float(dl),
            live_load_kPa=float(ll),
            basic_wind_speed_mps=float(wind_speed),
            building_height_m=float(height),
            exposure_category=exposure,
            internal_pressure_coeff_pos=float(cpi_pos),
            internal_pressure_coeff_neg=float(cpi_neg),
        )
        results = design.run_check()
        
        is_ok = results.get('is_ok', False)
        stress_ratio = results.get('Stress Check', {}).get('Interaction Ratio', 0)
        shear_ratio = results.get('Shear Check', {}).get('Ratio', 0)
        defl_ll = results.get('Calculated Deflection (mm)', {}).get('Live Load Vertical', 0)
        
        status = "✅ ผ่าน (ADEQUATE)" if is_ok else "❌ ไม่ผ่าน (INADEQUATE)"
        
        result_text = f"""
## 📊 ผลลัพธ์การออกแบบแป

**สถานะ:** {status}

| รายการ | ค่า |
|--------|-----|
| Stress Ratio | {stress_ratio:.3f} |
| Shear Ratio | {shear_ratio:.3f} |
| Deflection (LL) | {defl_ll:.2f} mm |
| หน้าตัด | {section_name} |
| ช่วงแป | {span} m |
| ระยะห่าง | {spacing} m |

**สรุป:** {results.get('Final Result', '')}
        """.strip()
        
        return status, result_text
        
    except Exception as e:
        return "❌ เกิดข้อผิดพลาด", f"ข้อผิดพลาด: {str(e)}"

# ============================================================================
# BEAM DESIGN
# ============================================================================
def design_beam(section_name, span, beam_type, bracing, dl, ll, wl, point_dl, point_ll):
    """Calculate beam design"""
    try:
        beam_sections = {**H_BEAMS, **I_BEAMS}
        section = beam_sections[section_name]
        
        loads = BeamLoad(
            dead_load=float(dl),
            live_load=float(ll),
            wind_load=float(wl),
            point_load_D=float(point_dl),
            point_load_L=float(point_ll),
        )
        
        design = BeamDesign(
            section=section,
            span=float(span),
            is_cantilever=(beam_type == "Cantilever"),
            lateral_bracing=bracing,
            deflection_type="beam_live_load"
        )
        result = design.check_beam(loads)
        
        status = "✅ ผ่าน (ADEQUATE)" if result.is_ok else "❌ ไม่ผ่าน (INADEQUATE)"
        
        result_text = f"""
## 📊 ผลลัพธ์การออกแบบคาน

**สถานะ:** {status}

| รายการ | ค่า |
|--------|-----|
| Stress Ratio | {result.stress_ratio:.3f} |
| Shear Ratio | {result.shear_ratio:.3f} |
| Deflection Ratio | {result.deflection_ratio:.3f} |
| Max Moment | {result.max_moment:.2f} kN-m |
| Max Shear | {result.max_shear:.2f} kN |
| หน้าตัด | {section_name} |
| ช่วงคาน | {span} m |
        """.strip()
        
        return status, result_text
        
    except Exception as e:
        return "❌ เกิดข้อผิดพลาด", f"ข้อผิดพลาด: {str(e)}"

# ============================================================================
# COLUMN DESIGN
# ============================================================================
def design_column(section_name, height, kx, ky, axial_dl, axial_ll, mx, my):
    """Calculate column design"""
    try:
        col_sections = {**H_BEAMS, **I_BEAMS, **STEEL_PIPES}
        section = col_sections[section_name]
        
        loads = ColumnLoad(
            axial_dead=float(axial_dl),
            axial_live=float(axial_ll),
            moment_x=float(mx),
            moment_y=float(my),
        )
        
        design = ColumnDesign(
            section=section,
            height=float(height),
            kx=float(kx),
            ky=float(ky)
        )
        result = design.check_column(loads)
        
        status = "✅ ผ่าน (ADEQUATE)" if result.is_ok else "❌ ไม่ผ่าน (INADEQUATE)"
        
        result_text = f"""
## 📊 ผลลัพธ์การออกแบบเสา

**สถานะ:** {status}

| รายการ | ค่า |
|--------|-----|
| Axial Ratio | {result.axial_ratio:.3f} |
| Interaction Ratio | {result.interaction_ratio:.3f} |
| หน้าตัด | {section_name} |
| ความสูง | {height} m |
| Kx | {kx} |
| Ky | {ky} |
| Axial Load | {float(axial_dl) + float(axial_ll):.1f} kN |
        """.strip()
        
        return status, result_text
        
    except Exception as e:
        return "❌ เกิดข้อผิดพลาด", f"ข้อผิดพลาด: {str(e)}"

# ============================================================================
# GRADIO INTERFACE
# ============================================================================
with gr.Blocks(title="Steel Structure Design - วสท. 011038-22", theme=gr.themes.Soft()) as app:
    
    gr.Markdown("""
    # 🏗️ โปรแกรมออกแบบโครงสร้างเหล็ก
    ## Steel Structure Design per วสท. 011038-22 | มอก. 1227-2558 | มอก. 107-2533
    """)
    
    with gr.Tabs():
        
        # TAB 1: PURLIN
        with gr.Tab("🏠 ออกแบบแป (Purlin)"):
            with gr.Row():
                with gr.Column():
                    gr.Markdown("### 📥 ข้อมูลนำเข้า")
                    purlin_section = gr.Dropdown(
                        choices=list(C_CHANNELS.keys()),
                        value="C150x65x20x4.0",
                        label="หน้าตัดเหล็ก (C-Channel)"
                    )
                    purlin_span = gr.NumberBox(value=6.0, label="ความยาวช่วงแป (m)")
                    purlin_spacing = gr.NumberBox(value=1.2, label="ระยะห่างแป (m)")
                    roof_slope = gr.NumberBox(value=15.0, label="มุมลาดชันหลังคา (°)")
                    
                    gr.Markdown("### ⚖️ น้ำหนักบรรทุก")
                    purlin_dl = gr.NumberBox(value=0.147, label="Dead Load (kPa)")
                    purlin_ll = gr.NumberBox(value=0.50, label="Live Load (kPa)")
                    
                    gr.Markdown("### 💨 น้ำหนักลม")
                    wind_speed = gr.NumberBox(value=30.0, label="ความเร็วลม (m/s)")
                    building_height = gr.NumberBox(value=6.0, label="ความสูงอาคาร (m)")
                    exposure = gr.Dropdown(choices=['B', 'C', 'D'], value='C', label="ประเภทสภาพภูมิ")
                    cpi_pos = gr.NumberBox(value=0.18, label="Cpi (บวก)")
                    cpi_neg = gr.NumberBox(value=-0.18, label="Cpi (ลบ)")
                    
                    purlin_btn = gr.Button("🔢 คำนวณแป", variant="primary")
                    
                with gr.Column():
                    purlin_status = gr.Textbox(label="สถานะ", interactive=False)
                    purlin_result = gr.Markdown(label="ผลลัพธ์")
        
        # TAB 2: BEAM
        with gr.Tab("📏 ออกแบบคาน (Beam)"):
            with gr.Row():
                with gr.Column():
                    gr.Markdown("### 📥 ข้อมูลนำเข้า")
                    beam_sections_list = list(H_BEAMS.keys()) + list(I_BEAMS.keys())
                    beam_section = gr.Dropdown(
                        choices=beam_sections_list,
                        value="H200x200x8x12",
                        label="หน้าตัดเหล็ก"
                    )
                    beam_span = gr.NumberBox(value=6.0, label="ช่วงคาน (m)")
                    beam_type = gr.Radio(["Simply Supported", "Cantilever"], value="Simply Supported", label="ประเภทคาน")
                    bracing = gr.Dropdown(["continuous", "ends_only", "intermediate"], value="continuous", label="การยึดหน่วงข้าง")
                    
                    gr.Markdown("### ⚖️ น้ำหนักบรรทุก")
                    beam_dl = gr.NumberBox(value=10.0, label="Dead Load (kN/m)")
                    beam_ll = gr.NumberBox(value=15.0, label="Live Load (kN/m)")
                    beam_wl = gr.NumberBox(value=0.0, label="Wind Load (kN/m)")
                    point_dl = gr.NumberBox(value=0.0, label="Point DL (kN)")
                    point_ll = gr.NumberBox(value=0.0, label="Point LL (kN)")
                    
                    beam_btn = gr.Button("🔢 คำนวณคาน", variant="primary")
                    
                with gr.Column():
                    beam_status = gr.Textbox(label="สถานะ", interactive=False)
                    beam_result = gr.Markdown(label="ผลลัพธ์")
        
        # TAB 3: COLUMN
        with gr.Tab("🏛️ ออกแบบเสา (Column)"):
            with gr.Row():
                with gr.Column():
                    gr.Markdown("### 📥 ข้อมูลนำเข้า")
                    col_sections_list = list(H_BEAMS.keys()) + list(I_BEAMS.keys()) + list(STEEL_PIPES.keys())
                    col_section = gr.Dropdown(
                        choices=col_sections_list,
                        value="H250x250x9x14",
                        label="หน้าตัดเหล็ก"
                    )
                    col_height = gr.NumberBox(value=4.0, label="ความสูงเสา (m)")
                    kx = gr.NumberBox(value=1.0, label="Kx")
                    ky = gr.NumberBox(value=1.0, label="Ky")
                    
                    gr.Markdown("### ⚖️ แรงกระทำ")
                    axial_dl = gr.NumberBox(value=100.0, label="Axial DL (kN)")
                    axial_ll = gr.NumberBox(value=150.0, label="Axial LL (kN)")
                    moment_x = gr.NumberBox(value=0.0, label="Moment X (kN-m)")
                    moment_y = gr.NumberBox(value=0.0, label="Moment Y (kN-m)")
                    
                    col_btn = gr.Button("🔢 คำนวณเสา", variant="primary")
                    
                with gr.Column():
                    col_status = gr.Textbox(label="สถานะ", interactive=False)
                    col_result = gr.Markdown(label="ผลลัพธ์")
    
    # Event handlers
    purlin_btn.click(
        fn=design_purlin,
        inputs=[purlin_section, purlin_span, purlin_spacing, roof_slope, purlin_dl, purlin_ll, 
                wind_speed, building_height, exposure, cpi_pos, cpi_neg],
        outputs=[purlin_status, purlin_result]
    )
    
    beam_btn.click(
        fn=design_beam,
        inputs=[beam_section, beam_span, beam_type, bracing, beam_dl, beam_ll, beam_wl, point_dl, point_ll],
        outputs=[beam_status, beam_result]
    )
    
    col_btn.click(
        fn=design_column,
        inputs=[col_section, col_height, kx, ky, axial_dl, axial_ll, moment_x, moment_y],
        outputs=[col_status, col_result]
    )
    
    gr.Markdown("""
    ---
    **📐 มาตรฐานการออกแบบ:**
    - วัสดุ: มอก. 1227-2558, มอก. 107-2533
    - การออกแบบ: วสท. 011038-22 (ASD)
    - แรงลม: มยผ. 1311-50
    - แผ่นดินไหว: มยผ. 1301/1302-61
    
    ⚠️ โปรแกรมเป็นเครื่องมือช่วยคำนวณเบื้องต้น ควรตรวจสอบผลลัพธ์ด้วยวิศวกรโครงสร้าง
    """)

if __name__ == "__main__":
    app.launch(server_name="0.0.0.0", server_port=7860)
