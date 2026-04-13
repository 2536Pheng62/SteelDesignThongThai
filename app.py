"""
Steel Structure Design Web App (โปรแกรมออกแบบโครงสร้างเหล็ก - เว็บแอป)
Based on Thai Standards (มอก., วสท., มยผ.)
Streamlit Web Application for Netlify Deployment
"""
import streamlit as st
import math
import json
from datetime import datetime

# Import our design modules
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from steel_sections import C_CHANNELS, H_BEAMS, I_BEAMS, STEEL_PIPES, RHS_SECTIONS, MATERIAL_GRADES
from load_combinations import LOAD_COMBINATIONS_ASD, DEFLECTION_LIMITS
from purlin import PurlinDesign
from beam_design import BeamDesign, BeamLoad
from column_design import ColumnDesign, ColumnLoad

# Page configuration
st.set_page_config(
    page_title="Steel Structure Design - วสท. 011038-22",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1B4F72;
        text-align: center;
        font-weight: bold;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #5D6D7E;
        text-align: center;
        margin-bottom: 2rem;
    }
    .pass-box {
        background-color: #D4F5E4;
        border-left: 5px solid #1A7A4A;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
    .fail-box {
        background-color: #FDE8E8;
        border-left: 5px solid #C0392B;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
    .info-box {
        background-color: #E8F4FD;
        border-left: 5px solid #2E86AB;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Session state for results
if 'purlin_result' not in st.session_state:
    st.session_state.purlin_result = None
if 'beam_result' not in st.session_state:
    st.session_state.beam_result = None
if 'column_result' not in st.session_state:
    st.session_state.column_result = None

# ============================================================================
# HEADER
# ============================================================================
st.markdown('<div class="main-header">🏗️ โปรแกรมออกแบบโครงสร้างเหล็ก</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Steel Structure Design per วสท. 011038-22 | มอก. 1227-2558 | มอก. 107-2533</div>', unsafe_allow_html=True)

# ============================================================================
# SIDEBAR - Project Info
# ============================================================================
with st.sidebar:
    st.header("📋 ข้อมูลโครงการ")
    project_name = st.text_input("ชื่อโครงการ", value="โครงการออกแบบโครงสร้างเหล็ก")
    engineer = st.text_input("ผู้ออกแบบ", value="")
    checker = st.text_input("ผู้ตรวจสอบ", value="")
    project_date = st.date_input("วันที่", value=datetime.now())
    
    st.divider()
    st.header("📐 มาตรฐานการออกแบบ")
    st.info("""
    **วัสดุ:** มอก. 1227-2558, มอก. 107-2533  
    **การออกแบบ:** วสท. 011038-22 (ASD)  
    **แรงลม:** มยผ. 1311-50  
    **แผ่นดินไหว:** มยผ. 1301/1302-61
    """)
    
    st.divider()
    st.header("🔧 เกรดวัสดุ")
    selected_grade = st.selectbox(
        "Material Grade",
        options=list(MATERIAL_GRADES.keys()),
        help="เลือกเกรดเหล็กตาม มอก. 1227-2558"
    )
    st.caption(f"Fy = {MATERIAL_GRADES[selected_grade].Fy} MPa, Fu = {MATERIAL_GRADES[selected_grade].Fu} MPa")

# ============================================================================
# MAIN CONTENT - Tabs
# ============================================================================
tab1, tab2, tab3 = st.tabs(["🏠 ออกแบบแป (Purlin)", "📏 ออกแบบคาน (Beam)", "🏛️ ออกแบบเสา (Column)"])

# ============================================================================
# TAB 1: PURLIN DESIGN
# ============================================================================
with tab1:
    st.header("🏠 ออกแบบแปหลังคา (Roof Purlin Design)")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📥 ข้อมูลนำเข้า")
        
        # Section selection
        section_name = st.selectbox(
            "หน้าตัดเหล็ก (C-Channel)",
            options=list(C_CHANNELS.keys()),
            index=4  # Default to C150x65x20x4.0
        )
        
        # Geometry
        st.markdown("**เรขาคณิต**")
        purlin_span = st.number_input("ความยาวช่วงแป (m)", min_value=1.0, max_value=20.0, value=6.0, step=0.5)
        purlin_spacing = st.number_input("ระยะห่างแป (m)", min_value=0.5, max_value=3.0, value=1.2, step=0.1)
        roof_slope = st.number_input("มุมลาดชันหลังคา (°)", min_value=0.0, max_value=45.0, value=15.0, step=1.0)
        
    with col2:
        st.subheader("⚖️ น้ำหนักบรรทุก")
        
        # Loads
        st.markdown("**น้ำหนักคงที่และจร**")
        dl_kPa = st.number_input("Dead Load (kPa)", min_value=0.0, value=0.147, step=0.01)
        ll_kPa = st.number_input("Live Load (kPa)", min_value=0.0, value=0.50, step=0.05)
        
        # Wind loads
        st.markdown("**น้ำหนักลม**")
        wind_speed = st.number_input("ความเร็วลม (m/s)", min_value=20.0, max_value=50.0, value=30.0, step=1.0)
        building_height = st.number_input("ความสูงอาคาร (m)", min_value=3.0, max_value=50.0, value=6.0, step=1.0)
        exposure_cat = st.selectbox("ประเภทสภาพภูมิ", options=['B', 'C', 'D'], index=1)
        cpi_pos = st.number_input("Cpi (บวก)", value=0.18, step=0.01)
        cpi_neg = st.number_input("Cpi (ลบ)", value=-0.18, step=0.01)
    
    # Calculate button
    if st.button("🔢 คำนวณแป (Calculate Purlin)", type="primary", use_container_width=True):
        try:
            design = PurlinDesign(
                section_name=section_name,
                purlin_span=purlin_span,
                purlin_spacing=purlin_spacing,
                roof_slope_degree=roof_slope,
                dead_load_kPa=dl_kPa,
                live_load_kPa=ll_kPa,
                basic_wind_speed_mps=wind_speed,
                building_height_m=building_height,
                exposure_category=exposure_cat,
                internal_pressure_coeff_pos=cpi_pos,
                internal_pressure_coeff_neg=cpi_neg,
            )
            results = design.run_check()
            st.session_state.purlin_result = results
            
            st.success(f"✅ การคำนวณเสร็จสิ้น - {section_name}")
        except Exception as e:
            st.error(f"❌ เกิดข้อผิดพลาด: {str(e)}")
    
    # Display results
    if st.session_state.purlin_result:
        results = st.session_state.purlin_result
        
        st.divider()
        st.subheader("📊 ผลลัพธ์การออกแบบ")
        
        is_ok = results.get('is_ok', False)
        if is_ok:
            st.markdown('<div class="pass-box">✅ <b>ผ่าน (ADEQUATE)</b> - หน้าตัดสามารถรับน้ำหนักได้</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="fail-box">❌ <b>ไม่ผ่าน (INADEQUATE)</b> - หน้าตัดไม่สามารถรับน้ำหนักได้</div>', unsafe_allow_html=True)
        
        # Display key results
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Stress Ratio", f"{results.get('Stress Check', {}).get('Interaction Ratio', 0):.3f}")
        col2.metric("Shear Ratio", f"{results.get('Shear Check', {}).get('Ratio', 0):.3f}")
        col3.metric("Deflection LL (mm)", f"{results.get('Calculated Deflection (mm)', {}).get('Live Load Vertical', 0):.2f}")
        col4.metric("Final Result", "✅ ผ่าน" if is_ok else "❌ ไม่ผ่าน")
        
        # Detailed results
        with st.expander("📄 ดูรายละเอียดการคำนวณ"):
            st.json(results, expanded=False)

# ============================================================================
# TAB 2: BEAM DESIGN
# ============================================================================
with tab2:
    st.header("📏 ออกแบบคานเหล็ก (Steel Beam Design)")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📥 ข้อมูลนำเข้า")
        
        # Section selection
        beam_sections = {**H_BEAMS, **I_BEAMS}
        section_name = st.selectbox(
            "หน้าตัดเหล็ก",
            options=list(beam_sections.keys()),
            index=4  # Default to H200x200x8x12
        )
        
        span = st.number_input("ช่วงคาน (m)", min_value=1.0, max_value=30.0, value=6.0, step=0.5)
        beam_type = st.radio("ประเภทคาน", ["Simply Supported", "Cantilever"], horizontal=True)
        bracing = st.selectbox("การยึดหน่วงข้าง", ["continuous", "ends_only", "intermediate"])
        defl_type = st.selectbox("เกณฑ์การแอ่นตัว", list(DEFLECTION_LIMITS.keys()))
        
    with col2:
        st.subheader("⚖️ น้ำหนักบรรทุก")
        
        st.markdown("**Distributed Loads (kN/m)**")
        beam_dl = st.number_input("Dead Load", min_value=0.0, value=10.0, step=1.0)
        beam_ll = st.number_input("Live Load", min_value=0.0, value=15.0, step=1.0)
        beam_wl = st.number_input("Wind Load", min_value=0.0, value=0.0, step=0.5)
        
        st.markdown("**Point Loads at Midspan (kN)**")
        point_dl = st.number_input("Point DL", min_value=0.0, value=0.0, step=5.0)
        point_ll = st.number_input("Point LL", min_value=0.0, value=0.0, step=5.0)
    
    if st.button("🔢 คำนวณคาน (Calculate Beam)", type="primary", use_container_width=True):
        try:
            section = beam_sections[section_name]
            loads = BeamLoad(
                dead_load=beam_dl,
                live_load=beam_ll,
                wind_load=beam_wl,
                point_load_D=point_dl,
                point_load_L=point_ll,
            )
            
            design = BeamDesign(
                section=section,
                span=span,
                is_cantilever=(beam_type == "Cantilever"),
                lateral_bracing=bracing,
                deflection_type=defl_type
            )
            result = design.check_beam(loads)
            st.session_state.beam_result = {
                'result': result,
                'section_name': section_name,
                'span': span
            }
            
            st.success(f"✅ การคำนวณเสร็จสิ้น - {section_name}")
        except Exception as e:
            st.error(f"❌ เกิดข้อผิดพลาด: {str(e)}")
    
    if st.session_state.beam_result:
        beam_data = st.session_state.beam_result
        result = beam_data['result']
        
        st.divider()
        st.subheader("📊 ผลลัพธ์การออกแบบ")
        
        if result.is_ok:
            st.markdown('<div class="pass-box">✅ <b>ผ่าน (ADEQUATE)</b></div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="fail-box">❌ <b>ไม่ผ่าน (INADEQUATE)</b></div>', unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Stress Ratio", f"{result.stress_ratio:.3f}")
        col2.metric("Shear Ratio", f"{result.shear_ratio:.3f}")
        col3.metric("Deflection Ratio", f"{result.deflection_ratio:.3f}")

# ============================================================================
# TAB 3: COLUMN DESIGN
# ============================================================================
with tab3:
    st.header("🏛️ ออกแบบเสาเหล็ก (Steel Column Design)")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📥 ข้อมูลนำเข้า")
        
        col_sections = {**H_BEAMS, **I_BEAMS, **STEEL_PIPES}
        section_name = st.selectbox(
            "หน้าตัดเหล็ก",
            options=list(col_sections.keys()),
            index=5
        )
        
        height = st.number_input("ความสูงเสา (m)", min_value=1.0, max_value=20.0, value=4.0, step=0.5)
        kx = st.number_input("Kx (Effective Length Factor X)", min_value=0.5, max_value=2.5, value=1.0, step=0.1)
        ky = st.number_input("Ky (Effective Length Factor Y)", min_value=0.5, max_value=2.5, value=1.0, step=0.1)
        
    with col2:
        st.subheader("⚖️ แรงกระทำ")
        
        st.markdown("**Axial Loads (kN)**")
        axial_dl = st.number_input("Axial DL", min_value=0.0, value=100.0, step=10.0)
        axial_ll = st.number_input("Axial LL", min_value=0.0, value=150.0, step=10.0)
        
        st.markdown("**Moments (kN-m)**")
        mx = st.number_input("Moment X", min_value=0.0, value=0.0, step=5.0)
        my = st.number_input("Moment Y", min_value=0.0, value=0.0, step=5.0)
    
    if st.button("🔢 คำนวณเสา (Calculate Column)", type="primary", use_container_width=True):
        try:
            section = col_sections[section_name]
            loads = ColumnLoad(
                axial_dead=axial_dl,
                axial_live=axial_ll,
                moment_x=mx,
                moment_y=my,
            )
            
            design = ColumnDesign(
                section=section,
                height=height,
                kx=kx,
                ky=ky
            )
            result = design.check_column(loads)
            st.session_state.column_result = {
                'result': result,
                'section_name': section_name,
                'height': height
            }
            
            st.success(f"✅ การคำนวณเสร็จสิ้น - {section_name}")
        except Exception as e:
            st.error(f"❌ เกิดข้อผิดพลาด: {str(e)}")
    
    if st.session_state.column_result:
        col_data = st.session_state.column_result
        result = col_data['result']
        
        st.divider()
        st.subheader("📊 ผลลัพธ์การออกแบบ")
        
        if result.is_ok:
            st.markdown('<div class="pass-box">✅ <b>ผ่าน (ADEQUATE)</b></div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="fail-box">❌ <b>ไม่ผ่าน (INADEQUATE)</b></div>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        col1.metric("Axial Ratio", f"{result.axial_ratio:.3f}")
        col2.metric("Interaction Ratio", f"{result.interaction_ratio:.3f}")

# ============================================================================
# FOOTER
# ============================================================================
st.divider()
st.markdown(f"""
<div style="text-align: center; color: #5D6D7E; font-size: 0.9rem;">
    <p>🏗️ Steel Structure Design Application | วสท. 011038-22 | มอก. 1227-2558 | มอก. 107-2533</p>
    <p>Project: {project_name} | Engineer: {engineer or '—'} | Date: {project_date.strftime('%d/%m/%Y')}</p>
    <p>⚠️ โปรแกรมเป็นเครื่องมือช่วยคำนวณเบื้องต้น ควรตรวจสอบผลลัพธ์ด้วยวิศวกรโครงสร้าง</p>
</div>
""", unsafe_allow_html=True)
