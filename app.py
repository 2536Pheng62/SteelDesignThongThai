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
    STEEL_PIPES, SHS_SECTIONS, RHS_SECTIONS, EQUAL_ANGLES,
    BOLTS, WELDS,
)
from load_combinations import DEFLECTION_LIMITS
from beam_design import BeamDesign, BeamLoad, format_beam_report
from column_design import ColumnDesign, ColumnLoad, format_column_report
from truss_design import TrussDesign, TrussLoad, format_truss_report
from footing_design import FootingDesign, FootingLoad, format_footing_report
from connection_design import (
    BoltedConnectionDesign, WeldedConnectionDesign, ConnectionLoad,
    format_bolted_report, format_welded_report,
)
from baseplate_design import (
    BasePlateDesign, BasePlateLoad, format_baseplate_report,
)
from seismic_design import (
    calc_base_shear_elf, distribute_story_forces, format_seismic_report,
    SEISMIC_SYSTEM_FACTORS, PERIOD_COEFFICIENTS, IMPORTANCE_FACTORS,
)

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
(tab_beam, tab_col, tab_truss, tab_footing,
 tab_conn, tab_bp, tab_seismic) = st.tabs([
    "📏 คาน (Beam)",
    "🏛️ เสา (Column)",
    "🔺 โครงถัก (Truss)",
    "🦶 ฐานราก (Footing)",
    "🔩 รอยต่อ (Connection)",
    "🧱 แผ่นฐานเสา (Base Plate)",
    "🌋 แผ่นดินไหว (Seismic)",
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

# ============================================================================
# CONNECTION TAB (Bolted & Welded)
# ============================================================================
with tab_conn:
    st.header("ออกแบบรอยต่อ (Bolted & Welded Connection)")
    sub_bolt, sub_weld = st.tabs(["🔩 สลักเกลียว (Bolted)", "⚡ รอยเชื่อม (Welded)"])

    with sub_bolt:
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("📥 ข้อมูลสลักเกลียว")
            bolt_name = st.selectbox("ขนาดสลักเกลียว", options=list(BOLTS.keys()), index=1, key="bolt_sel")
            n_bolts = st.number_input("จำนวนสลักเกลียว", min_value=1, max_value=50, value=4, step=1, key="bolt_n")
            n_planes = st.selectbox("จำนวนระนาบเฉือน", [1, 2], key="bolt_planes")
            t_plate = st.number_input("ความหนาแผ่นต่อ (mm)", min_value=1.0, value=10.0, step=0.5, key="bolt_tp")
            edge_dist = st.number_input("ระยะขอบ e (mm)", min_value=0.0, value=30.0, step=5.0, key="bolt_e")
            plate_Fu = st.number_input("Fu แผ่นต่อ (MPa)", min_value=200.0, value=400.0, step=10.0, key="bolt_fu")
        with col2:
            st.subheader("⚖️ แรงกระทำ")
            bV_d = st.number_input("Shear DL (kN)", value=50.0, step=5.0, key="bolt_vd")
            bV_l = st.number_input("Shear LL (kN)", value=80.0, step=5.0, key="bolt_vl")
            bV_w = st.number_input("Shear WL (kN)", value=0.0, step=5.0, key="bolt_vw")

        if st.button("คำนวณสลักเกลียว", type="primary", key="btn_bolt"):
            bolt = BOLTS[bolt_name]
            design = BoltedConnectionDesign(
                bolt=bolt, connected_plate_thickness=t_plate,
                edge_distance=edge_dist, plate_Fu=plate_Fu,
            )
            loads = ConnectionLoad(shear_load_D=bV_d, shear_load_L=bV_l, shear_load_W=bV_w)
            res = design.check_connection(loads, num_bolts=int(n_bolts), num_shear_planes=int(n_planes))

            st.markdown("### ผลลัพธ์")
            if res.is_ok: st.success(f"✅ {res.status}")
            else: st.error(f"❌ {res.status}")

            c1, c2, c3 = st.columns(3)
            c1.metric("Shear Ratio", f"{res.shear_ratio:.3f}")
            c2.metric("Bearing Ratio", f"{res.bearing_ratio:.3f}")
            c3.metric("Total Shear Cap. (kN)", f"{res.total_shear_capacity:.1f}")

            st.markdown(f'<div class="report-box">{format_bolted_report(res)}</div>', unsafe_allow_html=True)

    with sub_weld:
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("📥 ข้อมูลรอยเชื่อม")
            weld_name = st.selectbox("ลวดเชื่อม", options=list(WELDS.keys()), index=1, key="weld_sel")
            weld_size = st.number_input("ขนาดรอยเชื่อม leg (mm)", min_value=3.0, value=6.0, step=1.0, key="weld_s")
            weld_len = st.number_input("ความยาวรอยเชื่อมรวม (mm)", min_value=10.0, value=200.0, step=10.0, key="weld_l")
            base_fy = st.number_input("Fy ชิ้นส่วน (MPa)", min_value=200.0, value=245.0, step=10.0, key="weld_fy")
        with col2:
            st.subheader("⚖️ แรงกระทำ")
            wV_d = st.number_input("Shear DL (kN)", value=30.0, step=5.0, key="weld_vd")
            wV_l = st.number_input("Shear LL (kN)", value=50.0, step=5.0, key="weld_vl")
            wV_w = st.number_input("Shear WL (kN)", value=0.0, step=5.0, key="weld_vw")

        if st.button("คำนวณรอยเชื่อม", type="primary", key="btn_weld"):
            weld = WELDS[weld_name]
            design = WeldedConnectionDesign(weld=weld, base_metal_Fy=base_fy)
            loads = ConnectionLoad(shear_load_D=wV_d, shear_load_L=wV_l, shear_load_W=wV_w)
            res = design.check_connection(loads, weld_size=weld_size, weld_length=weld_len)

            st.markdown("### ผลลัพธ์")
            if res.is_ok: st.success(f"✅ {res.status}")
            else: st.error(f"❌ {res.status}")

            c1, c2 = st.columns(2)
            c1.metric("Shear Ratio", f"{res.shear_ratio:.3f}")
            c2.metric("Total Shear Cap. (kN)", f"{res.shear_capacity:.1f}")

            st.markdown(f'<div class="report-box">{format_welded_report(res)}</div>', unsafe_allow_html=True)

# ============================================================================
# BASE PLATE TAB
# ============================================================================
with tab_bp:
    st.header("ออกแบบแผ่นฐานเสา (Column Base Plate)")
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("📥 ข้อมูลแผ่นฐานและเสา")
        bp_col_opts = list(H_BEAMS.keys()) + list(I_BEAMS.keys())
        bp_sec_name = st.selectbox("หน้าตัดเสา", options=bp_col_opts, index=2, key="bp_sec")
        bp_B = st.number_input("ความกว้างแผ่น B (mm)", min_value=50.0, value=300.0, step=10.0, key="bp_B")
        bp_N = st.number_input("ความยาวแผ่น N (mm)", min_value=50.0, value=300.0, step=10.0, key="bp_N")
        bp_tp = st.number_input("ความหนาแผ่น tp (mm)", min_value=5.0, value=20.0, step=1.0, key="bp_tp")
        bp_fc = st.number_input("f'c คอนกรีต (MPa)", min_value=15.0, value=24.0, step=1.0, key="bp_fc")
    with col2:
        st.subheader("⚖️ แรงกระทำ")
        bp_pdl = st.number_input("Axial DL (kN)", value=200.0, step=10.0, key="bp_pdl")
        bp_pll = st.number_input("Axial LL (kN)", value=300.0, step=10.0, key="bp_pll")
        bp_mdl = st.number_input("Moment Mx DL (kN-m)", value=0.0, step=5.0, key="bp_mdl")
        bp_mll = st.number_input("Moment Mx LL (kN-m)", value=0.0, step=5.0, key="bp_mll")

    if st.button("คำนวณแผ่นฐาน", type="primary", key="btn_bp"):
        sec = all_sections[bp_sec_name]
        design = BasePlateDesign(
            section=sec, plate_width=bp_B, plate_length=bp_N,
            plate_thickness=bp_tp, concrete_Fc=bp_fc,
        )
        loads = BasePlateLoad(
            axial_load_D=bp_pdl, axial_load_L=bp_pll,
            moment_x_D=bp_mdl, moment_x_L=bp_mll,
        )
        res = design.check_base_plate(loads)

        st.markdown("### ผลลัพธ์")
        if res.is_ok: st.success(f"✅ {res.status}")
        else: st.error(f"❌ {res.status}")

        c1, c2, c3 = st.columns(3)
        c1.metric("Bearing Ratio", f"{res.bearing_ratio:.3f}")
        c2.metric("Thickness Ratio", f"{res.thickness_ratio:.3f}")
        c3.metric("Required tp (mm)", f"{res.required_thickness:.1f}")

        st.markdown(f'<div class="report-box">{format_baseplate_report(res, bp_sec_name)}</div>', unsafe_allow_html=True)

# ============================================================================
# SEISMIC (ELF) TAB — มยผ. 1302-61
# ============================================================================
with tab_seismic:
    st.header("คำนวณแรงแผ่นดินไหววิธี ELF (มยผ. 1302-61)")
    st.caption("วิธีแรงสถิตเทียบเท่า (Equivalent Lateral Force) สำหรับอาคารปกติ")

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("📥 พารามิเตอร์พื้นที่")
        eq_Ss = st.number_input("Ss (spectral accel. คาบสั้น, g)", min_value=0.0, value=0.25, step=0.01, key="eq_ss")
        eq_S1 = st.number_input("S1 (spectral accel. 1 วินาที, g)", min_value=0.0, value=0.10, step=0.01, key="eq_s1")
        eq_site = st.selectbox("ชั้นดิน (Site Class)", ["A", "B", "C", "D", "E"], index=3, key="eq_site")
        eq_risk = st.selectbox(
            "ประเภทความสำคัญของอาคาร",
            options=list(IMPORTANCE_FACTORS.keys()),
            format_func=lambda k: f"{k} - {IMPORTANCE_FACTORS[k]['name_th']}",
            index=1, key="eq_risk",
        )
    with col2:
        st.subheader("📥 ระบบโครงสร้าง")
        eq_struct = st.selectbox(
            "ชนิดโครงสร้าง (เพื่อคำนวณ Ta)",
            options=list(PERIOD_COEFFICIENTS.keys()),
            format_func=lambda k: PERIOD_COEFFICIENTS[k]["name_th"],
            index=0, key="eq_struct",
        )
        eq_sys = st.selectbox(
            "ระบบต้านแรงด้านข้าง (R factor)",
            options=list(SEISMIC_SYSTEM_FACTORS.keys()),
            format_func=lambda k: SEISMIC_SYSTEM_FACTORS[k]["name_th"],
            index=0, key="eq_sys",
        )
        eq_height = st.number_input("ความสูงอาคาร hn (m)", min_value=1.0, value=12.0, step=0.5, key="eq_h")
        eq_W = st.number_input("น้ำหนักอาคารประสิทธิผล W (kN)", min_value=10.0, value=5000.0, step=100.0, key="eq_w")

    st.markdown("---")
    st.subheader("🏢 การกระจายแรงตามชั้น (ไม่บังคับ)")
    eq_nstory = st.number_input("จำนวนชั้นของอาคาร", min_value=1, max_value=30, value=3, step=1, key="eq_ns")

    default_h = 3.5
    default_w = round(eq_W / max(eq_nstory, 1), 0)
    with st.expander("กำหนดน้ำหนักและความสูงแต่ละชั้น (หากไม่กำหนดจะใช้ค่าเฉลี่ย)"):
        story_weights = []
        story_heights = []
        for i in range(1, int(eq_nstory) + 1):
            cc1, cc2 = st.columns(2)
            w_i = cc1.number_input(f"wi ชั้นที่ {i} (kN)", value=float(default_w), step=50.0, key=f"sw_{i}")
            h_i = cc2.number_input(f"hi ชั้นที่ {i} (m)", value=float(default_h * i), step=0.5, key=f"sh_{i}")
            story_weights.append(w_i)
            story_heights.append(h_i)

    if st.button("คำนวณแรงแผ่นดินไหว", type="primary", key="btn_eq"):
        res = calc_base_shear_elf(
            Ss=eq_Ss, S1=eq_S1,
            site_class=eq_site,
            risk_category=eq_risk,
            structure_type=eq_struct,
            seismic_system=eq_sys,
            height_m=eq_height,
            total_weight_kN=eq_W,
        )
        res.story_forces = distribute_story_forces(
            V=res.V,
            story_weights=story_weights,
            story_heights=story_heights,
            T=res.Ta,
        )

        st.markdown("### ผลลัพธ์")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Ta (s)", f"{res.Ta:.3f}")
        c2.metric("Cs", f"{res.Cs:.4f}")
        c3.metric("SDS (g)", f"{res.SDS:.3f}")
        c4.metric("V (kN)", f"{res.V:,.2f}")

        if res.story_forces:
            st.markdown("#### การกระจายแรงตามชั้น")
            import pandas as pd
            df = pd.DataFrame(res.story_forces)[["level", "wi_kN", "hi_m", "Cvx", "Fx_kN", "Vx_kN"]]
            df.columns = ["ชั้น", "wi (kN)", "hi (m)", "Cvx", "Fx (kN)", "Vx (kN)"]
            st.dataframe(df, use_container_width=True, hide_index=True)

        st.markdown(f'<div class="report-box">{format_seismic_report(res)}</div>', unsafe_allow_html=True)
