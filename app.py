"""
Steel Structure Design Web App (โปรแกรมออกแบบโครงสร้างเหล็ก - Streamlit)
Based on Thai Standards (มอก., วสท., มยผ.)
"""
import streamlit as st
import sys
import os

# Add local path to import our modules
sys.path.insert(0, os.path.dirname(__file__))

from steel_sections import (
    get_all_sections, C_CHANNELS, H_BEAMS, I_BEAMS, 
    STEEL_PIPES, SHS_SECTIONS, RHS_SECTIONS, EQUAL_ANGLES
)
from load_combinations import DEFLECTION_LIMITS
from beam_design import BeamDesign, BeamLoad, format_beam_report
from column_design import ColumnDesign, ColumnLoad, format_column_report
from truss_design import TrussDesign, TrussLoad, format_truss_report
from footing_design import FootingDesign, FootingLoad, format_footing_report

# Page config
st.set_page_config(
    page_title="Steel Structure Design",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header { font-size: 2.2rem; color: #1B4F72; font-weight: bold; margin-bottom: 0.5rem; }
    .sub-header { font-size: 1.1rem; color: #5D6D7E; margin-bottom: 2rem; }
    .stButton>button { width: 100%; border-radius: 5px; font-weight: bold; }
    .report-box { background-color: #f8f9fa; padding: 15px; border-radius: 8px; border-left: 4px solid #1B4F72; font-family: monospace; white-space: pre-wrap; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header">🏗️ โปรแกรมออกแบบโครงสร้างเหล็ก</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">มาตรฐาน วสท. 011038-22 | มอก. 1227-2558 | มอก. 107-2533</div>', unsafe_allow_html=True)

all_sections = get_all_sections()

# Tabs
tab_beam, tab_col, tab_truss, tab_footing = st.tabs([
    "📏 คาน (Beam)", "🏛️ เสา (Column)", "🔺 โครงถัก (Truss)", "🦶 ฐานราก (Footing)"
])

# ============================================================================
# BEAM TAB
# ============================================================================
with tab_beam:
    st.header("ออกแบบคานเหล็ก (Beam Design)")
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("📥 ข้อมูลหน้าตัดและเรขาคณิต")
        beam_opts = list(H_BEAMS.keys()) + list(I_BEAMS.keys()) + list(SHS_SECTIONS.keys()) + list(RHS_SECTIONS.keys())
        b_sec_name = st.selectbox("หน้าตัดเหล็ก", options=beam_opts, index=0, key="b_sec")
        b_method = st.selectbox("วิธีการออกแบบ", ["ASD", "LRFD"], key="b_method")
        b_span = st.number_input("ช่วงคาน (m)", min_value=0.5, value=6.0, step=0.5, key="b_span")
        b_type = st.radio("ประเภทคาน", ["Simply Supported", "Cantilever"], horizontal=True, key="b_type")
        b_bracing = st.selectbox("การยึดหน่วงข้าง", ["continuous", "ends_only", "intermediate"], key="b_brace")
        b_defl = st.selectbox("เกณฑ์การแอ่นตัว", list(DEFLECTION_LIMITS.keys()), key="b_defl")
    
    with col2:
        st.subheader("⚖️ น้ำหนักบรรทุก")
        b_dl = st.number_input("Dead Load แบบแผ่ (kN/m)", value=10.0, step=1.0, key="b_dl")
        b_ll = st.number_input("Live Load แบบแผ่ (kN/m)", value=15.0, step=1.0, key="b_ll")
        st.markdown("---")
        b_pdl = st.number_input("Point Dead Load กลางคาน (kN)", value=0.0, step=5.0, key="b_pdl")
        b_pll = st.number_input("Point Live Load กลางคาน (kN)", value=0.0, step=5.0, key="b_pll")

    if st.button("คำนวณคาน", type="primary", key="btn_beam"):
        sec = all_sections[b_sec_name]
        loads = BeamLoad(dead_load=b_dl, live_load=b_ll, point_load_D=b_pdl, point_load_L=b_pll)
        design = BeamDesign(section=sec, span=b_span, method=b_method, is_cantilever=(b_type=="Cantilever"), lateral_bracing=b_bracing, deflection_type=b_defl)
        res = design.check_beam(loads)
        
        st.markdown("### ผลลัพธ์")
        if res.is_ok: st.success(f"✅ {res.status}")
        else: st.error(f"❌ {res.status}")
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Stress Ratio (U.C.)", f"{res.stress_ratio:.3f}")
        c2.metric("Shear Ratio", f"{res.shear_ratio:.3f}")
        c3.metric("Deflection Ratio", f"{res.deflection_ratio:.3f}")
        
        st.markdown(f'<div class="report-box">{format_beam_report(res, b_sec_name, b_span)}</div>', unsafe_allow_html=True)

# ============================================================================
# COLUMN TAB
# ============================================================================
with tab_col:
    st.header("ออกแบบเสาเหล็ก (Column Design)")
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("📥 ข้อมูลหน้าตัดและเรขาคณิต")
        col_opts = list(H_BEAMS.keys()) + list(I_BEAMS.keys()) + list(STEEL_PIPES.keys()) + list(SHS_SECTIONS.keys()) + list(RHS_SECTIONS.keys())
        c_sec_name = st.selectbox("หน้าตัดเหล็ก", options=col_opts, index=0, key="c_sec")
        c_method = st.selectbox("วิธีการออกแบบ", ["ASD", "LRFD"], key="c_method")
        c_height = st.number_input("ความสูงเสา (m)", min_value=0.5, value=4.0, step=0.5, key="c_height")
        cc1, cc2 = st.columns(2)
        c_kx = cc1.number_input("Kx (ตัวคูณความยาว)", min_value=0.1, value=1.0, step=0.1, key="c_kx")
        c_ky = cc2.number_input("Ky (ตัวคูณความยาว)", min_value=0.1, value=1.0, step=0.1, key="c_ky")
        
    with col2:
        st.subheader("⚖️ แรงกระทำ")
        c_pdl = st.number_input("Axial Dead Load (kN)", value=100.0, step=10.0, key="c_pdl")
        c_pll = st.number_input("Axial Live Load (kN)", value=150.0, step=10.0, key="c_pll")
        st.markdown("---")
        cc3, cc4 = st.columns(2)
        c_mx = cc3.number_input("Moment X (kN-m)", value=0.0, step=5.0, key="c_mx")
        c_my = cc4.number_input("Moment Y (kN-m)", value=0.0, step=5.0, key="c_my")

    if st.button("คำนวณเสา", type="primary", key="btn_col"):
        sec = all_sections[c_sec_name]
        loads = ColumnLoad(axial_load_D=c_pdl, axial_load_L=c_pll, moment_x_D=c_mx, moment_y_D=c_my)
        design = ColumnDesign(section=sec, height=c_height, method=c_method, Kx=c_kx, Ky=c_ky)
        res = design.check_combined_loading(loads)
        
        st.markdown("### ผลลัพธ์")
        if res.is_ok: st.success(f"✅ {res.status}")
        else: st.error(f"❌ {res.status}")
        
        c1, c2 = st.columns(2)
        c1.metric("Interaction Ratio (U.C.)", f"{res.interaction_ratio:.3f}")
        c2.metric("Max Slenderness (KL/r)", f"{res.critical_slenderness:.1f}")
        
        st.markdown(f'<div class="report-box">{format_column_report(res, c_sec_name, c_height)}</div>', unsafe_allow_html=True)

# ============================================================================
# TRUSS TAB
# ============================================================================
with tab_truss:
    st.header("ออกแบบชิ้นส่วนโครงถัก (Truss Member)")
    col1, col2 = st.columns(2)
    with col1:
        tr_opts = list(EQUAL_ANGLES.keys()) + list(STEEL_PIPES.keys()) + list(SHS_SECTIONS.keys())
        tr_sec_name = st.selectbox("หน้าตัดเหล็ก", options=tr_opts, index=0, key="tr_sec")
        tr_method = st.selectbox("วิธีการออกแบบ", ["ASD", "LRFD"], key="tr_method")
        tr_length = st.number_input("ความยาวชิ้นส่วน (m)", min_value=0.1, value=3.0, step=0.5, key="tr_len")
        tr_k = st.number_input("K (ตัวคูณความยาว)", min_value=0.1, value=1.0, step=0.1, key="tr_k")
    with col2:
        tr_dl = st.number_input("แรงแนวแกน DL (kN) [+ ดึง, - อัด]", value=50.0, step=10.0, key="tr_dl")
        tr_ll = st.number_input("แรงแนวแกน LL (kN) [+ ดึง, - อัด]", value=30.0, step=10.0, key="tr_ll")

    if st.button("คำนวณโครงถัก", type="primary", key="btn_truss"):
        sec = all_sections[tr_sec_name]
        loads = TrussLoad(force_D=tr_dl, force_L=tr_ll)
        design = TrussDesign(section=sec, length=tr_length, method=tr_method, K=tr_k)
        res = design.check_member(loads)
        
        st.markdown("### ผลลัพธ์")
        if res.is_ok: st.success(f"✅ {res.status}")
        else: st.error(f"❌ {res.status}")
        
        c1, c2 = st.columns(2)
        c1.metric("Force Ratio", f"{res.ratio:.3f}")
        c2.metric("Slenderness (L/r)", f"{res.slenderness:.1f} / {res.limit_slenderness:.0f}")
        
        st.markdown(f'<div class="report-box">{format_truss_report(res, tr_sec_name, tr_length)}</div>', unsafe_allow_html=True)

# ============================================================================
# FOOTING TAB
# ============================================================================
with tab_footing:
    st.header("ออกแบบฐานรากแผ่ (Isolated Footing)")
    col1, col2 = st.columns(2)
    with col1:
        f_w = st.number_input("ความกว้าง B (m)", min_value=0.5, value=1.5, step=0.1, key="f_w")
        f_l = st.number_input("ความยาว L (m)", min_value=0.5, value=1.5, step=0.1, key="f_l")
        f_h = st.number_input("ความหนา H (m)", min_value=0.1, value=0.3, step=0.05, key="f_h")
        f_qa = st.number_input("กำลังแบกทานยอมให้ (kPa)", min_value=10.0, value=150.0, step=10.0, key="f_qa")
    with col2:
        f_dl = st.number_input("Axial DL ลงฐานราก (kN)", value=150.0, step=10.0, key="f_dl")
        f_ll = st.number_input("Axial LL ลงฐานราก (kN)", value=100.0, step=10.0, key="f_ll")

    if st.button("คำนวณฐานราก", type="primary", key="btn_footing"):
        loads = FootingLoad(axial_load_D=f_dl, axial_load_L=f_ll)
        design = FootingDesign(width=f_w, length=f_l, thickness=f_h, allowable_bearing_kPa=f_qa)
        res = design.check_footing(loads)
        
        st.markdown("### ผลลัพธ์")
        if res.is_ok: st.success(f"✅ {res.status}")
        else: st.error(f"❌ {res.status}")
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Bearing Ratio", f"{res.bearing_ratio:.3f}")
        c2.metric("1-Way Shear Ratio", f"{res.shear_1way_ratio:.3f}")
        c3.metric("Punching Shear Ratio", f"{res.shear_2way_ratio:.3f}")
        
        st.markdown(f'<div class="report-box">{format_footing_report(res, f_w, f_l, f_h)}</div>', unsafe_allow_html=True)
