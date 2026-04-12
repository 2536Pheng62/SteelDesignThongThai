"""
Steel Structure Design Application (โปรแกรมออกแบบโครงสร้างเหล็ก)
Based on Thai Standards (วสท. 011038-22, TIS)
Main Application with Tabbed Interface
"""
import math
import os
import re
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import Dict, Optional

# Third-party imports for plotting
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# Third-party imports for PDF Export
try:
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

# Import our modules
from steel_sections import (
    STEEL_MATERIALS, C_CHANNELS, H_BEAMS, I_BEAMS, EQUAL_ANGLES,
    UNEQUAL_ANGLES, STEEL_PIPES, RHS_SECTIONS, STEEL_PLATES, BOLTS, WELDS
)
from load_combinations import (
    LOAD_COMBINATIONS_ASD, DEFLECTION_LIMITS, WIND_LOAD_PARAMS
)
from purlin import PurlinDesign, format_detailed_report as format_purlin_report
from beam_design import BeamDesign, BeamLoad, format_beam_report
from column_design import ColumnDesign, ColumnLoad, format_column_report
from connection_design import (
    BoltedConnectionDesign, WeldedConnectionDesign, ConnectionLoad,
    format_bolted_report, format_welded_report
)
from baseplate_design import BasePlateDesign, BasePlateLoad, format_baseplate_report


# ============================================================================
# Constants
# ============================================================================
G = 9.81  # Gravitational acceleration (m/s²)
E_STEEL = 2.0e5  # MPa
MPA_TO_PA = 1e6
KPA_TO_PA = 1000
MM3_TO_M3 = 1e-9
MM4_TO_M4 = 1e-12


# ============================================================================
# Main Application Class
# ============================================================================
class SteelStructureDesignApp:
    def __init__(self, master):
        self.master = master
        master.title("โปรแกรมออกแบบโครงสร้างเหล็ก - Steel Structure Design (วสท. 011038-22)")
        master.geometry("1200x900")
        
        # Configure style
        style = ttk.Style(master)
        try:
            style.theme_use('clam')
        except tk.TclError:
            pass
        style.configure('.', font=('Tahoma', 11))
        style.configure('TLabelframe.Label', font=('Tahoma', 12, 'bold'))
        style.configure('TButton', font=('Tahoma', 11))
        style.configure('Header.TLabel', font=('Tahoma', 14, 'bold'), foreground='darkblue')
        
        # Validation command
        self.vcmd = (master.register(self._validate_float_input), '%P')
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(master)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create tabs
        self.create_purlin_tab()
        self.create_beam_tab()
        self.create_column_tab()
        self.create_connection_tab()
        self.create_baseplate_tab()
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("พร้อมใช้งาน - Ready")
        status_bar = ttk.Label(
            master, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W
        )
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def _validate_float_input(self, P):
        """Validates that the input is a valid floating-point number string."""
        if P == "" or P == "-":
            return True
        try:
            float(P)
            return True
        except ValueError:
            self.master.bell()
            return False
    
    def get_float_from_entry(self, entry_widget, name):
        try:
            val = entry_widget.get().strip()
            if not val:
                raise ValueError(f"กรุณาป้อนค่าสำหรับ '{name}'")
            return float(val)
        except ValueError:
            raise ValueError(f"กรุณาป้อนตัวเลขที่ถูกต้องสำหรับ '{name}'")
    
    def create_entry_field(self, parent, label, row, default_value="0.0", width=15):
        """Helper to create a labeled entry field"""
        ttk.Label(parent, text=label).grid(row=row, column=0, padx=5, pady=3, sticky="w")
        entry = ttk.Entry(parent, validate="key", validatecommand=self.vcmd, width=width)
        entry.grid(row=row, column=1, padx=5, pady=3, sticky="ew")
        entry.insert(0, str(default_value))
        return entry
    
    def create_combo_box(self, parent, label, row, values, default=None):
        """Helper to create a labeled combo box"""
        ttk.Label(parent, text=label).grid(row=row, column=0, padx=5, pady=3, sticky="w")
        combo = ttk.Combobox(parent, values=values, state="readonly")
        combo.grid(row=row, column=1, padx=5, pady=3, sticky="ew")
        if default and default in values:
            combo.set(default)
        elif values:
            combo.set(values[0])
        return combo
    
    # ========================================================================
    # PURLIN TAB
    # ========================================================================
    def create_purlin_tab(self):
        self.purlin_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.purlin_tab, text='ออกแบบแป (Purlin)')
        
        # Create scrolled frame for inputs
        canvas = tk.Canvas(self.purlin_tab)
        scrollbar = ttk.Scrollbar(self.purlin_tab, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Input frame
        input_frame = ttk.LabelFrame(scrollable_frame, text="ข้อมูลนำเข้า - Purlin Design")
        input_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        input_frame.grid_columnconfigure(1, weight=1)
        
        row = 0
        # Section selection
        self.purlin_section_var = tk.StringVar()
        self.purlin_section_combo = self.create_combo_box(
            input_frame, "หน้าตัดเหล็ก:", row, 
            list(C_CHANNELS.keys()), "C150x65x20x4.0"
        )
        row += 1
        
        # Geometry
        self.purlin_span_entry = self.create_entry_field(input_frame, "ความยาวช่วงแป (m):", row, "6.0")
        row += 1
        self.purlin_spacing_entry = self.create_entry_field(input_frame, "ระยะห่างแป (m):", row, "1.2")
        row += 1
        self.purlin_slope_entry = self.create_entry_field(input_frame, "มุมลาดชันหลังคา (°):", row, "15.0")
        row += 1
        
        # Loads
        ttk.Label(input_frame, text="--- น้ำหนักบรรทุก ---").grid(row=row, column=0, columnspan=2, pady=5)
        row += 1
        self.purlin_dl_entry = self.create_entry_field(input_frame, "น้ำหนักบรรทุกคงที่ (kPa):", row, "0.147")
        row += 1
        self.purlin_ll_entry = self.create_entry_field(input_frame, "น้ำหนักบรรทุกจร (kPa):", row, "0.50")
        row += 1
        
        # Wind loads
        ttk.Label(input_frame, text="--- น้ำหนักลม ---").grid(row=row, column=0, columnspan=2, pady=5)
        row += 1
        self.purlin_wind_speed_entry = self.create_entry_field(input_frame, "ความเร็วลม (m/s):", row, "30.0")
        row += 1
        self.purlin_height_entry = self.create_entry_field(input_frame, "ความสูงอาคาร (m):", row, "6.0")
        row += 1
        self.purlin_exposure_var = tk.StringVar()
        self.purlin_exposure_combo = self.create_combo_box(
            input_frame, "ประเภทสภาพภูมิ:", row, ['B', 'C', 'D'], "C"
        )
        row += 1
        self.purlin_cpi_pos_entry = self.create_entry_field(input_frame, "Cpi (บวก):", row, "0.18")
        row += 1
        self.purlin_cpi_neg_entry = self.create_entry_field(input_frame, "Cpi (ลบ):", row, "-0.18")
        
        # Buttons
        button_frame = ttk.Frame(scrollable_frame)
        button_frame.grid(row=1, column=0, padx=10, pady=10)
        
        ttk.Button(button_frame, text="คำนวณ (Calculate)", command=self.calculate_purlin).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="ค้นหาหน้าตัดประหยัดสุด", command=self.find_purlin_section).pack(side=tk.LEFT, padx=5)
        
        # Output frame
        output_frame = ttk.LabelFrame(scrollable_frame, text="ผลลัพธ์ - Results")
        output_frame.grid(row=2, column=0, padx=10, pady=10, sticky="nsew")
        output_frame.grid_columnconfigure(0, weight=1)
        output_frame.grid_rowconfigure(0, weight=1)
        
        self.purlin_results_text = tk.Text(output_frame, wrap="word", height=20, font=('Consolas', 11))
        self.purlin_results_text.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
        
        purlin_scrollbar = ttk.Scrollbar(output_frame, orient="vertical", command=self.purlin_results_text.yview)
        purlin_scrollbar.grid(row=0, column=1, sticky="ns")
        self.purlin_results_text.config(yscrollcommand=purlin_scrollbar.set)
        
        # Pack canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
    def calculate_purlin(self):
        try:
            inputs = {
                "section_name": self.purlin_section_var.get(),
                "purlin_span": self.get_float_from_entry(self.purlin_span_entry, "ความยาวช่วงแป"),
                "purlin_spacing": self.get_float_from_entry(self.purlin_spacing_entry, "ระยะห่างแป"),
                "roof_slope_degree": self.get_float_from_entry(self.purlin_slope_entry, "มุมลาดชัน"),
                "dead_load_kPa": self.get_float_from_entry(self.purlin_dl_entry, "DL"),
                "live_load_kPa": self.get_float_from_entry(self.purlin_ll_entry, "LL"),
                "basic_wind_speed_mps": self.get_float_from_entry(self.purlin_wind_speed_entry, "ความเร็วลม"),
                "building_height_m": self.get_float_from_entry(self.purlin_height_entry, "ความสูง"),
                "exposure_category": self.purlin_exposure_var.get(),
                "internal_pressure_coeff_pos": self.get_float_from_entry(self.purlin_cpi_pos_entry, "Cpi+"),
                "internal_pressure_coeff_neg": self.get_float_from_entry(self.purlin_cpi_neg_entry, "Cpi-"),
            }
            
            design = PurlinDesign(
                section_name=inputs['section_name'],
                purlin_span=inputs['purlin_span'],
                purlin_spacing=inputs['purlin_spacing'],
                roof_slope_degree=inputs['roof_slope_degree'],
                dead_load_kPa=inputs['dead_load_kPa'],
                live_load_kPa=inputs['live_load_kPa'],
                basic_wind_speed_mps=inputs['basic_wind_speed_mps'],
                building_height_m=inputs['building_height_m'],
                exposure_category=inputs['exposure_category'],
                internal_pressure_coeff_pos=inputs['internal_pressure_coeff_pos'],
                internal_pressure_coeff_neg=inputs['internal_pressure_coeff_neg'],
            )
            results = design.run_check()
            report = format_purlin_report(design, results)
            
            self.purlin_results_text.delete(1.0, tk.END)
            self.purlin_results_text.insert(tk.END, report)
            
            status = "ผ่าน" if results['is_ok'] else "ไม่ผ่าน"
            self.status_var.set(f"Purlin: {status} - {inputs['section_name']}")
            
        except Exception as e:
            messagebox.showerror("ข้อผิดพลาด", str(e))
    
    def find_purlin_section(self):
        try:
            inputs = {
                "purlin_span": self.get_float_from_entry(self.purlin_span_entry, "ความยาวช่วงแป"),
                "purlin_spacing": self.get_float_from_entry(self.purlin_spacing_entry, "ระยะห่างแป"),
                "roof_slope_degree": self.get_float_from_entry(self.purlin_slope_entry, "มุมลาดชัน"),
                "dead_load_kPa": self.get_float_from_entry(self.purlin_dl_entry, "DL"),
                "live_load_kPa": self.get_float_from_entry(self.purlin_ll_entry, "LL"),
                "basic_wind_speed_mps": self.get_float_from_entry(self.purlin_wind_speed_entry, "ความเร็วลม"),
                "building_height_m": self.get_float_from_entry(self.purlin_height_entry, "ความสูง"),
                "exposure_category": self.purlin_exposure_var.get(),
                "internal_pressure_coeff_pos": self.get_float_from_entry(self.purlin_cpi_pos_entry, "Cpi+"),
                "internal_pressure_coeff_neg": self.get_float_from_entry(self.purlin_cpi_neg_entry, "Cpi-"),
            }
            
            sorted_sections = sorted(C_CHANNELS.keys(), key=lambda k: C_CHANNELS[k].weight)
            found = None
            
            self.purlin_results_text.delete(1.0, tk.END)
            self.purlin_results_text.insert(tk.END, "กำลังค้นหาหน้าตัดที่ประหยัดที่สุด...\n\n")
            
            for section in sorted_sections:
                self.purlin_results_text.insert(tk.END, f"ตรวจสอบ: {section}...")
                self.master.update_idletasks()
                
                design = PurlinDesign(
                    section_name=section,
                    purlin_span=inputs['purlin_span'],
                    purlin_spacing=inputs['purlin_spacing'],
                    roof_slope_degree=inputs['roof_slope_degree'],
                    dead_load_kPa=inputs['dead_load_kPa'],
                    live_load_kPa=inputs['live_load_kPa'],
                    basic_wind_speed_mps=inputs['basic_wind_speed_mps'],
                    building_height_m=inputs['building_height_m'],
                    exposure_category=inputs['exposure_category'],
                    internal_pressure_coeff_pos=inputs['internal_pressure_coeff_pos'],
                    internal_pressure_coeff_neg=inputs['internal_pressure_coeff_neg'],
                )
                results = design.run_check()
                
                if results['is_ok']:
                    self.purlin_results_text.insert(tk.END, " ผ่าน\n")
                    found = section
                    report = format_purlin_report(design, results)
                    self.purlin_results_text.delete(1.0, tk.END)
                    self.purlin_results_text.insert(tk.END, report)
                    self.purlin_section_var.set(found)
                    self.status_var.set(f"พบหน้าตัดประหยัดสุด: {found}")
                    break
                else:
                    self.purlin_results_text.insert(tk.END, " ไม่ผ่าน\n")
            
            if not found:
                self.purlin_results_text.insert(tk.END, "\nไม่พบหน้าตัดที่เหมาะสม")
                messagebox.showwarning("ไม่พบ", "ไม่พบหน้าตัดที่เหมาะสมในฐานข้อมูล")
                
        except Exception as e:
            messagebox.showerror("ข้อผิดพลาด", str(e))
    
    # ========================================================================
    # BEAM TAB
    # ========================================================================
    def create_beam_tab(self):
        self.beam_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.beam_tab, text='ออกแบบคาน (Beam)')
        
        canvas = tk.Canvas(self.beam_tab)
        scrollbar = ttk.Scrollbar(self.beam_tab, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Input frame
        input_frame = ttk.LabelFrame(scrollable_frame, text="ข้อมูลนำเข้า - Beam Design")
        input_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        input_frame.grid_columnconfigure(1, weight=1)
        
        row = 0
        self.beam_section_var = tk.StringVar()
        self.beam_section_combo = self.create_combo_box(
            input_frame, "หน้าตัดเหล็ก:", row, 
            list(H_BEAMS.keys()) + list(I_BEAMS.keys()), "H200x200x8x12"
        )
        row += 1
        
        self.beam_span_entry = self.create_entry_field(input_frame, "ช่วงคาน (m):", row, "6.0")
        row += 1
        
        self.beam_type_var = tk.StringVar(value="simply_supported")
        ttk.Label(input_frame, text="ประเภทคาน:").grid(row=row, column=0, padx=5, pady=3, sticky="w")
        type_frame = ttk.Frame(input_frame)
        type_frame.grid(row=row, column=1, padx=5, pady=3, sticky="w")
        ttk.Radiobutton(type_frame, text="Simply Supported", variable=self.beam_type_var, value="simply_supported").pack(side=tk.LEFT)
        ttk.Radiobutton(type_frame, text="Cantilever", variable=self.beam_type_var, value="cantilever").pack(side=tk.LEFT)
        row += 1
        
        self.beam_bracing_var = tk.StringVar()
        self.beam_bracing_combo = self.create_combo_box(
            input_frame, "การยึดหน่วงข้าง:", row, 
            ["continuous", "ends_only", "intermediate"], "continuous"
        )
        row += 1
        
        self.beam_deflection_var = tk.StringVar()
        self.beam_deflection_combo = self.create_combo_box(
            input_frame, "เกณฑ์การแอ่นตัว:", row, 
            list(DEFLECTION_LIMITS.keys()), "beam_live_load"
        )
        row += 1
        
        # Loads
        ttk.Label(input_frame, text="--- Distributed Loads (kN/m) ---").grid(row=row, column=0, columnspan=2, pady=5)
        row += 1
        self.beam_dl_entry = self.create_entry_field(input_frame, "Dead Load:", row, "10.0")
        row += 1
        self.beam_ll_entry = self.create_entry_field(input_frame, "Live Load:", row, "15.0")
        row += 1
        self.beam_wl_entry = self.create_entry_field(input_frame, "Wind Load:", row, "0.0")
        row += 1
        
        ttk.Label(input_frame, text="--- Point Loads at Midspan (kN) ---").grid(row=row, column=0, columnspan=2, pady=5)
        row += 1
        self.beam_point_dl_entry = self.create_entry_field(input_frame, "Point DL:", row, "0.0")
        row += 1
        self.beam_point_ll_entry = self.create_entry_field(input_frame, "Point LL:", row, "0.0")
        row += 1
        
        # Buttons
        button_frame = ttk.Frame(scrollable_frame)
        button_frame.grid(row=1, column=0, padx=10, pady=10)
        ttk.Button(button_frame, text="คำนวณคาน (Calculate)", command=self.calculate_beam).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="ค้นหาหน้าตัดประหยัดสุด", command=self.find_beam_section).pack(side=tk.LEFT, padx=5)
        
        # Output
        output_frame = ttk.LabelFrame(scrollable_frame, text="ผลลัพธ์ - Beam Results")
        output_frame.grid(row=2, column=0, padx=10, pady=10, sticky="nsew")
        output_frame.grid_columnconfigure(0, weight=1)
        
        self.beam_results_text = tk.Text(output_frame, wrap="word", height=20, font=('Consolas', 11))
        self.beam_results_text.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
        
        beam_scrollbar = ttk.Scrollbar(output_frame, orient="vertical", command=self.beam_results_text.yview)
        beam_scrollbar.grid(row=0, column=1, sticky="ns")
        self.beam_results_text.config(yscrollcommand=beam_scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
    def calculate_beam(self):
        try:
            section_name = self.beam_section_var.get()
            if section_name in H_BEAMS:
                section = H_BEAMS[section_name]
            elif section_name in I_BEAMS:
                section = I_BEAMS[section_name]
            else:
                raise ValueError(f"ไม่พบหน้าตัด {section_name}")
            
            span = self.get_float_from_entry(self.beam_span_entry, "ช่วงคาน")
            is_cantilever = self.beam_type_var.get() == "cantilever"
            bracing = self.beam_bracing_var.get()
            defl_type = self.beam_deflection_var.get()
            
            loads = BeamLoad(
                dead_load=self.get_float_from_entry(self.beam_dl_entry, "DL"),
                live_load=self.get_float_from_entry(self.beam_ll_entry, "LL"),
                wind_load=self.get_float_from_entry(self.beam_wl_entry, "WL"),
                point_load_D=self.get_float_from_entry(self.beam_point_dl_entry, "Point DL"),
                point_load_L=self.get_float_from_entry(self.beam_point_ll_entry, "Point LL"),
            )
            
            design = BeamDesign(
                section=section, span=span,
                is_cantilever=is_cantilever,
                lateral_bracing=bracing,
                deflection_type=defl_type
            )
            result = design.check_beam(loads)
            report = format_beam_report(result, section_name, span)
            
            self.beam_results_text.delete(1.0, tk.END)
            self.beam_results_text.insert(tk.END, report)
            
            status = "ผ่าน" if result.is_ok else "ไม่ผ่าน"
            self.status_var.set(f"Beam: {status} - {section_name}")
            
        except Exception as e:
            messagebox.showerror("ข้อผิดพลาด", str(e))
    
    def find_beam_section(self):
        try:
            span = self.get_float_from_entry(self.beam_span_entry, "ช่วงคาน")
            is_cantilever = self.beam_type_var.get() == "cantilever"
            bracing = self.beam_bracing_var.get()
            defl_type = self.beam_deflection_var.get()
            
            loads = BeamLoad(
                dead_load=self.get_float_from_entry(self.beam_dl_entry, "DL"),
                live_load=self.get_float_from_entry(self.beam_ll_entry, "LL"),
                wind_load=self.get_float_from_entry(self.beam_wl_entry, "WL"),
                point_load_D=self.get_float_from_entry(self.beam_point_dl_entry, "Point DL"),
                point_load_L=self.get_float_from_entry(self.beam_point_ll_entry, "Point LL"),
            )
            
            all_sections = {**H_BEAMS, **I_BEAMS}
            sorted_sections = sorted(all_sections.keys(), key=lambda k: all_sections[k].weight)
            found = None
            
            self.beam_results_text.delete(1.0, tk.END)
            self.beam_results_text.insert(tk.END, "กำลังค้นหาหน้าตัดที่ประหยัดที่สุด...\n\n")
            
            for section_name in sorted_sections:
                section = all_sections[section_name]
                self.beam_results_text.insert(tk.END, f"ตรวจสอบ: {section_name}...")
                self.master.update_idletasks()
                
                design = BeamDesign(
                    section=section, span=span,
                    is_cantilever=is_cantilever,
                    lateral_bracing=bracing,
                    deflection_type=defl_type
                )
                result = design.check_beam(loads)
                
                if result.is_ok:
                    self.beam_results_text.insert(tk.END, " ผ่าน\n")
                    found = section_name
                    report = format_beam_report(result, section_name, span)
                    self.beam_results_text.delete(1.0, tk.END)
                    self.beam_results_text.insert(tk.END, report)
                    self.beam_section_var.set(found)
                    self.status_var.set(f"พบหน้าตัดประหยัดสุด: {found}")
                    break
                else:
                    self.beam_results_text.insert(tk.END, " ไม่ผ่าน\n")
            
            if not found:
                self.beam_results_text.insert(tk.END, "\nไม่พบหน้าตัดที่เหมาะสม")
                messagebox.showwarning("ไม่พบ", "ไม่พบหน้าตัดที่เหมาะสมในฐานข้อมูล")
                
        except Exception as e:
            messagebox.showerror("ข้อผิดพลาด", str(e))
    
    # ========================================================================
    # COLUMN TAB
    # ========================================================================
    def create_column_tab(self):
        self.column_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.column_tab, text='ออกแบบเสา (Column)')
        
        canvas = tk.Canvas(self.column_tab)
        scrollbar = ttk.Scrollbar(self.column_tab, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Input frame
        input_frame = ttk.LabelFrame(scrollable_frame, text="ข้อมูลนำเข้า - Column Design")
        input_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        input_frame.grid_columnconfigure(1, weight=1)
        
        row = 0
        self.column_section_var = tk.StringVar()
        self.column_section_combo = self.create_combo_box(
            input_frame, "หน้าตัดเหล็ก:", row, 
            list(H_BEAMS.keys()) + list(I_BEAMS.keys()) + list(STEEL_PIPES.keys()), "H250x250x9x14"
        )
        row += 1
        
        self.column_height_entry = self.create_entry_field(input_frame, "ความสูงเสา (m):", row, "4.0")
        row += 1
        
        # Effective length factors
        ttk.Label(input_frame, text="--- Effective Length Factors ---").grid(row=row, column=0, columnspan=2, pady=5)
        row += 1
        self.column_kx_entry = self.create_entry_field(input_frame, "Kx (แกนเข้ม):", row, "1.0")
        row += 1
        self.column_ky_entry = self.create_entry_field(input_frame, "Ky (แกนอ่อน):", row, "1.0")
        row += 1
        
        # Loads
        ttk.Label(input_frame, text="--- Axial Loads (kN) ---").grid(row=row, column=0, columnspan=2, pady=5)
        row += 1
        self.column_axial_dl_entry = self.create_entry_field(input_frame, "Axial DL:", row, "500.0")
        row += 1
        self.column_axial_ll_entry = self.create_entry_field(input_frame, "Axial LL:", row, "300.0")
        row += 1
        self.column_axial_wl_entry = self.create_entry_field(input_frame, "Axial WL:", row, "0.0")
        row += 1
        
        ttk.Label(input_frame, text="--- Moments about X-axis (kN-m) ---").grid(row=row, column=0, columnspan=2, pady=5)
        row += 1
        self.column_mx_dl_entry = self.create_entry_field(input_frame, "Mx DL:", row, "0.0")
        row += 1
        self.column_mx_ll_entry = self.create_entry_field(input_frame, "Mx LL:", row, "0.0")
        row += 1
        self.column_mx_wl_entry = self.create_entry_field(input_frame, "Mx WL:", row, "0.0")
        row += 1
        
        ttk.Label(input_frame, text="--- Moments about Y-axis (kN-m) ---").grid(row=row, column=0, columnspan=2, pady=5)
        row += 1
        self.column_my_dl_entry = self.create_entry_field(input_frame, "My DL:", row, "0.0")
        row += 1
        self.column_my_ll_entry = self.create_entry_field(input_frame, "My LL:", row, "0.0")
        row += 1
        self.column_my_wl_entry = self.create_entry_field(input_frame, "My WL:", row, "0.0")
        
        # Buttons
        button_frame = ttk.Frame(scrollable_frame)
        button_frame.grid(row=1, column=0, padx=10, pady=10)
        ttk.Button(button_frame, text="คำนวณเสา (Calculate)", command=self.calculate_column).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="ค้นหาหน้าตัดประหยัดสุด", command=self.find_column_section).pack(side=tk.LEFT, padx=5)
        
        # Output
        output_frame = ttk.LabelFrame(scrollable_frame, text="ผลลัพธ์ - Column Results")
        output_frame.grid(row=2, column=0, padx=10, pady=10, sticky="nsew")
        output_frame.grid_columnconfigure(0, weight=1)
        
        self.column_results_text = tk.Text(output_frame, wrap="word", height=20, font=('Consolas', 11))
        self.column_results_text.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
        
        column_scrollbar = ttk.Scrollbar(output_frame, orient="vertical", command=self.column_results_text.yview)
        column_scrollbar.grid(row=0, column=1, sticky="ns")
        self.column_results_text.config(yscrollcommand=column_scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
    def calculate_column(self):
        try:
            section_name = self.column_section_var.get()
            all_sections = {**H_BEAMS, **I_BEAMS, **STEEL_PIPES}
            if section_name not in all_sections:
                raise ValueError(f"ไม่พบหน้าตัด {section_name}")
            section = all_sections[section_name]
            
            height = self.get_float_from_entry(self.column_height_entry, "ความสูงเสา")
            Kx = self.get_float_from_entry(self.column_kx_entry, "Kx")
            Ky = self.get_float_from_entry(self.column_ky_entry, "Ky")
            
            loads = ColumnLoad(
                axial_load_D=self.get_float_from_entry(self.column_axial_dl_entry, "Axial DL"),
                axial_load_L=self.get_float_from_entry(self.column_axial_ll_entry, "Axial LL"),
                axial_load_W=self.get_float_from_entry(self.column_axial_wl_entry, "Axial WL"),
                moment_x_D=self.get_float_from_entry(self.column_mx_dl_entry, "Mx DL"),
                moment_x_L=self.get_float_from_entry(self.column_mx_ll_entry, "Mx LL"),
                moment_x_W=self.get_float_from_entry(self.column_mx_wl_entry, "Mx WL"),
                moment_y_D=self.get_float_from_entry(self.column_my_dl_entry, "My DL"),
                moment_y_L=self.get_float_from_entry(self.column_my_ll_entry, "My LL"),
                moment_y_W=self.get_float_from_entry(self.column_my_wl_entry, "My WL"),
            )
            
            design = ColumnDesign(section=section, height=height, Kx=Kx, Ky=Ky)
            result = design.check_combined_loading(loads)
            report = format_column_report(result, section_name, height)
            
            self.column_results_text.delete(1.0, tk.END)
            self.column_results_text.insert(tk.END, report)
            
            status = "ผ่าน" if result.is_ok else "ไม่ผ่าน"
            self.status_var.set(f"Column: {status} - {section_name}")
            
        except Exception as e:
            messagebox.showerror("ข้อผิดพลาด", str(e))
    
    def find_column_section(self):
        try:
            height = self.get_float_from_entry(self.column_height_entry, "ความสูงเสา")
            Kx = self.get_float_from_entry(self.column_kx_entry, "Kx")
            Ky = self.get_float_from_entry(self.column_ky_entry, "Ky")
            
            loads = ColumnLoad(
                axial_load_D=self.get_float_from_entry(self.column_axial_dl_entry, "Axial DL"),
                axial_load_L=self.get_float_from_entry(self.column_axial_ll_entry, "Axial LL"),
                axial_load_W=self.get_float_from_entry(self.column_axial_wl_entry, "Axial WL"),
                moment_x_D=self.get_float_from_entry(self.column_mx_dl_entry, "Mx DL"),
                moment_x_L=self.get_float_from_entry(self.column_mx_ll_entry, "Mx LL"),
                moment_x_W=self.get_float_from_entry(self.column_mx_wl_entry, "Mx WL"),
                moment_y_D=self.get_float_from_entry(self.column_my_dl_entry, "My DL"),
                moment_y_L=self.get_float_from_entry(self.column_my_ll_entry, "My LL"),
                moment_y_W=self.get_float_from_entry(self.column_my_wl_entry, "My WL"),
            )
            
            all_sections = {**H_BEAMS, **I_BEAMS, **STEEL_PIPES}
            sorted_sections = sorted(all_sections.keys(), key=lambda k: all_sections[k].weight)
            found = None
            
            self.column_results_text.delete(1.0, tk.END)
            self.column_results_text.insert(tk.END, "กำลังค้นหาหน้าตัดที่ประหยัดที่สุด...\n\n")
            
            for section_name in sorted_sections:
                section = all_sections[section_name]
                self.column_results_text.insert(tk.END, f"ตรวจสอบ: {section_name}...")
                self.master.update_idletasks()
                
                design = ColumnDesign(section=section, height=height, Kx=Kx, Ky=Ky)
                result = design.check_combined_loading(loads)
                
                if result.is_ok:
                    self.column_results_text.insert(tk.END, " ผ่าน\n")
                    found = section_name
                    report = format_column_report(result, section_name, height)
                    self.column_results_text.delete(1.0, tk.END)
                    self.column_results_text.insert(tk.END, report)
                    self.column_section_var.set(found)
                    self.status_var.set(f"พบหน้าตัดประหยัดสุด: {found}")
                    break
                else:
                    self.column_results_text.insert(tk.END, " ไม่ผ่าน\n")
            
            if not found:
                self.column_results_text.insert(tk.END, "\nไม่พบหน้าตัดที่เหมาะสม")
                messagebox.showwarning("ไม่พบ", "ไม่พบหน้าตัดที่เหมาะสมในฐานข้อมูล")
                
        except Exception as e:
            messagebox.showerror("ข้อผิดพลาด", str(e))
    
    # ========================================================================
    # CONNECTION TAB
    # ========================================================================
    def create_connection_tab(self):
        self.connection_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.connection_tab, text='รอยต่อ (Connection)')
        
        # Create notebook for bolted/welded
        conn_notebook = ttk.Notebook(self.connection_tab)
        conn_notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Bolted sub-tab
        bolted_frame = ttk.Frame(conn_notebook)
        conn_notebook.add(bolted_frame, text='สลักเกลียว (Bolted)')
        
        row = 0
        ttk.Label(bolted_frame, text="--- Bolt Properties ---").grid(row=row, column=0, columnspan=2, pady=5)
        row += 1
        
        self.bolt_grade_var = tk.StringVar()
        self.bolt_grade_combo = self.create_combo_box(
            bolted_frame, "เกรดสลักเกลียว:", row, 
            list(BOLTS.keys()), "M20"
        )
        row += 1
        
        self.num_bolts_entry = self.create_entry_field(bolted_frame, "จำนวน bolts:", row, "4")
        row += 1
        
        self.shear_planes_var = tk.StringVar(value="1")
        self.shear_planes_combo = self.create_combo_box(
            bolted_frame, "ระนาบเฉือน:", row, ["1 (Single)", "2 (Double)"], "1 (Single)"
        )
        row += 1
        
        self.plate_thickness_entry = self.create_entry_field(bolted_frame, "ความหนาแผ่นต่อ (mm):", row, "10.0")
        row += 1
        
        self.edge_distance_entry = self.create_entry_field(bolted_frame, "ระยะถึงขอบ (mm):", row, "40.0")
        row += 1
        
        ttk.Label(bolted_frame, text="--- Loads (kN) ---").grid(row=row, column=0, columnspan=2, pady=5)
        row += 1
        self.bolt_shear_dl_entry = self.create_entry_field(bolted_frame, "Shear DL:", row, "50.0")
        row += 1
        self.bolt_shear_ll_entry = self.create_entry_field(bolted_frame, "Shear LL:", row, "30.0")
        row += 1
        self.bolt_shear_wl_entry = self.create_entry_field(bolted_frame, "Shear WL:", row, "0.0")
        
        ttk.Button(bolted_frame, text="คำนวณรอยต่อสลักเกลียว", command=self.calculate_bolted).grid(row=row+1, column=0, columnspan=2, pady=10)
        
        self.bolted_results_text = tk.Text(bolted_frame, wrap="word", height=15, font=('Consolas', 11))
        self.bolted_results_text.grid(row=row+2, column=0, columnspan=2, padx=5, pady=5, sticky="nsew")
        
        # Welded sub-tab
        welded_frame = ttk.Frame(conn_notebook)
        conn_notebook.add(welded_frame, text='รอยเชื่อม (Welded)')
        
        row = 0
        ttk.Label(welded_frame, text="--- Weld Properties ---").grid(row=row, column=0, columnspan=2, pady=5)
        row += 1
        
        self.weld_electrode_var = tk.StringVar()
        self.weld_electrode_combo = self.create_combo_box(
            welded_frame, "ลวดเชื่อม:", row, 
            list(WELDS.keys()), "E70XX"
        )
        row += 1
        
        self.weld_size_entry = self.create_entry_field(welded_frame, "ขนาดรอยเชื่อม (mm):", row, "6.0")
        row += 1
        
        self.weld_length_entry = self.create_entry_field(welded_frame, "ความยาวรอยเชื่อม (mm):", row, "200.0")
        row += 1
        
        ttk.Label(welded_frame, text="--- Loads (kN) ---").grid(row=row, column=0, columnspan=2, pady=5)
        row += 1
        self.weld_shear_dl_entry = self.create_entry_field(welded_frame, "Shear DL:", row, "50.0")
        row += 1
        self.weld_shear_ll_entry = self.create_entry_field(welded_frame, "Shear LL:", row, "30.0")
        row += 1
        self.weld_shear_wl_entry = self.create_entry_field(welded_frame, "Shear WL:", row, "0.0")
        
        ttk.Button(welded_frame, text="คำนวณรอยเชื่อม", command=self.calculate_welded).grid(row=row+1, column=0, columnspan=2, pady=10)
        
        self.welded_results_text = tk.Text(welded_frame, wrap="word", height=15, font=('Consolas', 11))
        self.welded_results_text.grid(row=row+2, column=0, columnspan=2, padx=5, pady=5, sticky="nsew")
    
    def calculate_bolted(self):
        try:
            bolt_name = self.bolt_grade_var.get()
            bolt = BOLTS[bolt_name]
            num_bolts = int(self.get_float_from_entry(self.num_bolts_entry, "จำนวน bolts"))
            shear_planes = 1 if "Single" in self.shear_planes_var.get() else 2
            plate_thickness = self.get_float_from_entry(self.plate_thickness_entry, "ความหนาแผ่น")
            edge_distance = self.get_float_from_entry(self.edge_distance_entry, "ระยะขอบ")
            
            loads = ConnectionLoad(
                shear_load_D=self.get_float_from_entry(self.bolt_shear_dl_entry, "Shear DL"),
                shear_load_L=self.get_float_from_entry(self.bolt_shear_ll_entry, "Shear LL"),
                shear_load_W=self.get_float_from_entry(self.bolt_shear_wl_entry, "Shear WL"),
            )
            
            design = BoltedConnectionDesign(
                bolt=bolt, connected_plate_thickness=plate_thickness,
                edge_distance=edge_distance
            )
            result = design.check_connection(loads, num_bolts, shear_planes)
            report = format_bolted_report(result)
            
            self.bolted_results_text.delete(1.0, tk.END)
            self.bolted_results_text.insert(tk.END, report)
            
            status = "ผ่าน" if result.is_ok else "ไม่ผ่าน"
            self.status_var.set(f"Bolted: {status}")
            
        except Exception as e:
            messagebox.showerror("ข้อผิดพลาด", str(e))
    
    def calculate_welded(self):
        try:
            weld_name = self.weld_electrode_var.get()
            weld = WELDS[weld_name]
            weld_size = self.get_float_from_entry(self.weld_size_entry, "ขนาดรอยเชื่อม")
            weld_length = self.get_float_from_entry(self.weld_length_entry, "ความยาวรอยเชื่อม")
            
            loads = ConnectionLoad(
                shear_load_D=self.get_float_from_entry(self.weld_shear_dl_entry, "Shear DL"),
                shear_load_L=self.get_float_from_entry(self.weld_shear_ll_entry, "Shear LL"),
                shear_load_W=self.get_float_from_entry(self.weld_shear_wl_entry, "Shear WL"),
            )
            
            design = WeldedConnectionDesign(weld=weld)
            result = design.check_connection(loads, weld_size, weld_length)
            report = format_welded_report(result)
            
            self.welded_results_text.delete(1.0, tk.END)
            self.welded_results_text.insert(tk.END, report)
            
            status = "ผ่าน" if result.is_ok else "ไม่ผ่าน"
            self.status_var.set(f"Welded: {status}")
            
        except Exception as e:
            messagebox.showerror("ข้อผิดพลาด", str(e))
    
    # ========================================================================
    # BASE PLATE TAB
    # ========================================================================
    def create_baseplate_tab(self):
        self.baseplate_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.baseplate_tab, text='แผ่นฐาน (Base Plate)')
        
        canvas = tk.Canvas(self.baseplate_tab)
        scrollbar = ttk.Scrollbar(self.baseplate_tab, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Input frame
        input_frame = ttk.LabelFrame(scrollable_frame, text="ข้อมูลนำเข้า - Base Plate Design")
        input_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        input_frame.grid_columnconfigure(1, weight=1)
        
        row = 0
        self.baseplate_section_var = tk.StringVar()
        self.baseplate_section_combo = self.create_combo_box(
            input_frame, "หน้าตัดเสา:", row, 
            list(H_BEAMS.keys()) + list(I_BEAMS.keys()), "H250x250x9x14"
        )
        row += 1
        
        ttk.Label(input_frame, text="--- Base Plate Dimensions (mm) ---").grid(row=row, column=0, columnspan=2, pady=5)
        row += 1
        self.baseplate_width_entry = self.create_entry_field(input_frame, "ความกว้าง B (mm):", row, "400.0")
        row += 1
        self.baseplate_length_entry = self.create_entry_field(input_frame, "ความยาว N (mm):", row, "400.0")
        row += 1
        self.baseplate_thickness_entry = self.create_entry_field(input_frame, "ความหนา tp (mm):", row, "25.0")
        row += 1
        
        self.concrete_fc_entry = self.create_entry_field(input_frame, "กำลังคอนกรีต f'c (MPa):", row, "24.0")
        row += 1
        
        ttk.Label(input_frame, text="--- Loads ---").grid(row=row, column=0, columnspan=2, pady=5)
        row += 1
        self.baseplate_axial_dl_entry = self.create_entry_field(input_frame, "Axial DL (kN):", row, "800.0")
        row += 1
        self.baseplate_axial_ll_entry = self.create_entry_field(input_frame, "Axial LL (kN):", row, "500.0")
        row += 1
        self.baseplate_axial_wl_entry = self.create_entry_field(input_frame, "Axial WL (kN):", row, "0.0")
        row += 1
        
        self.baseplate_mx_dl_entry = self.create_entry_field(input_frame, "Mx DL (kN-m):", row, "0.0")
        row += 1
        self.baseplate_mx_ll_entry = self.create_entry_field(input_frame, "Mx LL (kN-m):", row, "0.0")
        row += 1
        self.baseplate_mx_wl_entry = self.create_entry_field(input_frame, "Mx WL (kN-m):", row, "0.0")
        
        # Buttons
        button_frame = ttk.Frame(scrollable_frame)
        button_frame.grid(row=1, column=0, padx=10, pady=10)
        ttk.Button(button_frame, text="คำนวณแผ่นฐาน (Calculate)", command=self.calculate_baseplate).pack(side=tk.LEFT, padx=5)
        
        # Output
        output_frame = ttk.LabelFrame(scrollable_frame, text="ผลลัพธ์ - Base Plate Results")
        output_frame.grid(row=2, column=0, padx=10, pady=10, sticky="nsew")
        output_frame.grid_columnconfigure(0, weight=1)
        
        self.baseplate_results_text = tk.Text(output_frame, wrap="word", height=20, font=('Consolas', 11))
        self.baseplate_results_text.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
        
        bp_scrollbar = ttk.Scrollbar(output_frame, orient="vertical", command=self.baseplate_results_text.yview)
        bp_scrollbar.grid(row=0, column=1, sticky="ns")
        self.baseplate_results_text.config(yscrollcommand=bp_scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
    def calculate_baseplate(self):
        try:
            section_name = self.baseplate_section_var.get()
            all_sections = {**H_BEAMS, **I_BEAMS}
            if section_name not in all_sections:
                raise ValueError(f"ไม่พบหน้าตัด {section_name}")
            section = all_sections[section_name]
            
            B = self.get_float_from_entry(self.baseplate_width_entry, "ความกว้าง B")
            N = self.get_float_from_entry(self.baseplate_length_entry, "ความยาว N")
            tp = self.get_float_from_entry(self.baseplate_thickness_entry, "ความหนา tp")
            fc = self.get_float_from_entry(self.concrete_fc_entry, "f'c")
            
            loads = BasePlateLoad(
                axial_load_D=self.get_float_from_entry(self.baseplate_axial_dl_entry, "Axial DL"),
                axial_load_L=self.get_float_from_entry(self.baseplate_axial_ll_entry, "Axial LL"),
                axial_load_W=self.get_float_from_entry(self.baseplate_axial_wl_entry, "Axial WL"),
                moment_x_D=self.get_float_from_entry(self.baseplate_mx_dl_entry, "Mx DL"),
                moment_x_L=self.get_float_from_entry(self.baseplate_mx_ll_entry, "Mx LL"),
                moment_x_W=self.get_float_from_entry(self.baseplate_mx_wl_entry, "Mx WL"),
            )
            
            design = BasePlateDesign(
                section=section, plate_width=B, plate_length=N,
                plate_thickness=tp, concrete_Fc=fc
            )
            result = design.check_base_plate(loads)
            report = format_baseplate_report(result, section_name)
            
            self.baseplate_results_text.delete(1.0, tk.END)
            self.baseplate_results_text.insert(tk.END, report)
            
            status = "ผ่าน" if result.is_ok else "ไม่ผ่าน"
            self.status_var.set(f"Base Plate: {status}")
            
        except Exception as e:
            messagebox.showerror("ข้อผิดพลาด", str(e))


# ============================================================================
# MAIN EXECUTION
# ============================================================================
if __name__ == "__main__":
    root = tk.Tk()
    app = SteelStructureDesignApp(root)
    root.mainloop()
