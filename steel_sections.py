"""
Steel Section Database for Thai Structural Steel Design
Based on Thai Industrial Standards (มอก.) and Engineering Institute of Thailand (วสท.)

มาตรฐานที่เกี่ยวข้อง:
- มอก. 1227-2558: เหล็กรูปพรรณรีดร้อนรูปตัวเอช (Hot-rolled H-shaped steel)
- มอก. 107-2533: เหล็กโครงสร้างรูปพรรณกลวง (Structural hollow sections)
- วสท. 011038-22: มาตรฐานการออกแบบอาคารโครงสร้างเหล็กรูปพรรณ

Material Grades per มอก.:
- SS400: เหล็กโครงสร้างทั่วไป, Fy = 245 MPa, Fu = 400 MPa
- SM400: เหล็กโครงสร้างสำหรับงานเชื่อม, Fy = 245 MPa, Fu = 400 MPa
- SM490: เหล็กโครงสร้างความแข็งแรงสูง, Fy = 325 MPa, Fu = 490 MPa
- SM520: เหล็กโครงสร้างความแข็งแรงสูงมาก, Fy = 365 MPa, Fu = 520 MPa
- SS540: เหล็กโครงสร้างความแข็งแรงสูง, Fy = 375 MPa, Fu = 540 MPa
"""
import math
from dataclasses import dataclass
from typing import Optional


# ============================================================================
# Data Classes
# ============================================================================

@dataclass
class SteelSection:
    """Represents the properties of a steel section per มอก. standards."""
    name: str
    weight: float      # kg/m
    Fy: float          # MPa
    Fu: float          # MPa
    A: float           # mm²
    d: float           # mm (depth / outer diameter)
    tw: float          # mm (web thickness / wall thickness)
    bf: float          # mm (flange width / outer width)
    tf: float          # mm (flange thickness / wall thickness)
    Ix: float          # mm⁴
    Sx: float          # mm³
    rx: float          # mm
    Iy: float          # mm⁴
    Sy: float          # mm³
    ry: float          # mm
    Zx: float          # mm³ (plastic section modulus)
    Zy: float          # mm³
    J: float           # mm⁴ (torsional constant)
    Cw: float          # mm⁶ (warping constant)
    standard: str = "" # มาตรฐานอ้างอิง


@dataclass
class MaterialGrade:
    """Material grade definition per มอก. standard."""
    grade: str
    Fy: float
    Fu: float
    application: str
    standard: str


@dataclass
class BoltProperties:
    name: str
    grade: str
    diameter: float
    area: float        # mm²
    Fub: float         # MPa
    shear_strength: float  # MPa


@dataclass
class WeldProperties:
    name: str
    electrode: str
    Fu: float          # MPa
    shear_strength: float  # MPa


# ============================================================================
# Material Grades per มอก. 1227-2558
# ============================================================================

MATERIAL_GRADES = {
    "SS400": MaterialGrade("SS400", 245, 400, "เหล็กรูปพรรณทั่วไป (General structural steel)", "มอก. 1227-2558"),
    "SM400": MaterialGrade("SM400", 245, 400, "เหล็กรูปพรรณสำหรับงานเชื่อม (Welded structural steel)", "มอก. 1227-2558"),
    "SM490": MaterialGrade("SM490", 325, 490, "เหล็กรูปพรรณความแข็งแรงสูง (Higher strength structural steel)", "มอก. 1227-2558"),
    "SM520": MaterialGrade("SM520", 365, 520, "เหล็กรูปพรรณความแข็งแรงสูงมาก (High strength structural steel)", "มอก. 1227-2558"),
    "SS540": MaterialGrade("SS540", 375, 540, "เหล็กรูปพรรณความแข็งแรงสูง (High strength structural steel)", "มอก. 1227-2558"),
}

STEEL_MATERIALS = {
    "SS400 (Fy=245 MPa)": {"Fy": 245, "Fu": 400, "E": 200000, "G": 77000},
    "SM490 (Fy=325 MPa)": {"Fy": 325, "Fu": 490, "E": 200000, "G": 77000},
    "SM520 (Fy=365 MPa)": {"Fy": 365, "Fu": 520, "E": 200000, "G": 77000},
    "SS540 (Fy=375 MPa)": {"Fy": 375, "Fu": 540, "E": 200000, "G": 77000},
}


# ============================================================================
# Factory Functions (คำนวณคุณสมบัติหน้าตัดจากมิติ)
# ============================================================================

_W_FACTOR = 7.85e-3  # kg/m per mm² of cross-section (ρ=7850 kg/m³)


def _h(name, d, b, tw, tf, Fy=245, Fu=400, std="มอก. 1227-2558"):
    """H/I wide flange section properties from dimensions.
    d=depth, b=flange width, tw=web thickness, tf=flange thickness."""
    hw = d - 2 * tf
    A = 2 * b * tf + hw * tw
    Ix = (b * d**3 - (b - tw) * hw**3) / 12
    Sx = Ix / (d / 2)
    rx = math.sqrt(Ix / A)
    Iy = (2 * tf * b**3 + hw * tw**3) / 12
    Sy = Iy / (b / 2)
    ry = math.sqrt(Iy / A)
    Zx = b * tf * (d - tf) + tw * hw**2 / 4
    Zy = b**2 * tf / 2 + tw**2 * hw / 4
    J = (2 * b * tf**3 + hw * tw**3) / 3
    Cw = tf * b**3 * (d - tf)**2 / 24
    w = round(A * _W_FACTOR, 2)
    return SteelSection(name, w, Fy, Fu, round(A, 1), d, tw, b, tf,
                        round(Ix), round(Sx), round(rx, 1),
                        round(Iy), round(Sy), round(ry, 1),
                        round(Zx), round(Zy), round(J), round(Cw), std)


def _pipe(name, OD, t, Fy=245, Fu=305, std="มอก. 107-2533"):
    """Circular hollow section (CHS) properties.
    OD=outer diameter, t=wall thickness."""
    ID = OD - 2 * t
    A = math.pi * (OD**2 - ID**2) / 4
    I = math.pi * (OD**4 - ID**4) / 64
    S = I / (OD / 2)
    r = math.sqrt(I / A)
    Z = (OD**3 - ID**3) / 6
    J = 2 * I
    w = round(A * _W_FACTOR, 2)
    return SteelSection(name, w, Fy, Fu, round(A, 1), OD, t, OD, t,
                        round(I), round(S), round(r, 1),
                        round(I), round(S), round(r, 1),
                        round(Z), round(Z), round(J), 0.0, std)


def _rhs(name, h, b, t, Fy=245, Fu=290, std="มอก. 107-2533"):
    """Rectangular hollow section (RHS) properties.
    h=height, b=width, t=wall thickness."""
    hi = h - 2 * t
    bi = b - 2 * t
    A = h * b - hi * bi
    Ix = (b * h**3 - bi * hi**3) / 12
    Sx = Ix / (h / 2)
    rx = math.sqrt(Ix / A)
    Iy = (h * b**3 - hi * bi**3) / 12
    Sy = Iy / (b / 2)
    ry = math.sqrt(Iy / A)
    Zx = (b * h**2 - bi * hi**2) / 4
    Zy = (h * b**2 - hi * bi**2) / 4
    Am = (h - t) * (b - t)
    pm = 2 * ((h - t) + (b - t))
    J = 4 * Am**2 * t / pm
    w = round(A * _W_FACTOR, 2)
    return SteelSection(name, w, Fy, Fu, round(A, 1), h, t, b, t,
                        round(Ix), round(Sx), round(rx, 1),
                        round(Iy), round(Sy), round(ry, 1),
                        round(Zx), round(Zy), round(J), 0.0, std)


def _shs(name, h, t, Fy=245, Fu=290, std="มอก. 107-2533"):
    """Square hollow section (SHS) = symmetric RHS."""
    return _rhs(name, h, h, t, Fy, Fu, std)


def _angle_eq(name, b, t, Fy=245, Fu=400, std="มอก. 1227-2558"):
    """Equal angle (L-section) properties.
    b=leg width, t=thickness. Properties about centroidal axes parallel to legs."""
    A = t * (2 * b - t)
    # Centroid distance from back of leg
    e = (b**2 + b * t - t**2) / (2 * (2 * b - t))
    # Ix about centroidal axis parallel to horizontal leg
    Ix = (b * t**3 / 12 + b * t * (t / 2 - e)**2 +
          t * (b - t)**3 / 12 + t * (b - t) * ((b - t) / 2 + t - e)**2)
    Sx = Ix / (b - e)
    rx = math.sqrt(Ix / A)
    Iy = Ix  # equal angle: symmetric
    Sy = Sx
    ry = rx
    Zx = A / 2 * (b - e - (A / (4 * b)))
    Zy = Zx
    J = A * t**2 / 3
    Cw = A**2 * (b - t / 2)**2 / (24 * (2 * b - t) * t) if t > 0 else 0
    w = round(A * _W_FACTOR, 2)
    return SteelSection(name, w, Fy, Fu, round(A, 1), b, t, b, t,
                        round(Ix), round(Sx), round(rx, 1),
                        round(Iy), round(Sy), round(ry, 1),
                        round(Zx), round(Zy), round(J), round(Cw), std)


def _angle_uneq(name, H, B, t, Fy=245, Fu=400, std="มอก. 1227-2558"):
    """Unequal angle (L-section) properties.
    H=long leg, B=short leg, t=thickness."""
    A = t * (H + B - t)
    # Centroid from back of long leg (y-axis)
    ey = (H * t * t / 2 + (B - t) * t * (t + (B - t) / 2)) / A
    # Centroid from back of short leg (x-axis)
    ex = (B * t * t / 2 + (H - t) * t * (t + (H - t) / 2)) / A
    # Ix about centroidal axis parallel to B leg
    Ix = (B * t**3 / 12 + B * t * (t / 2 - ex)**2 +
          t * (H - t)**3 / 12 + t * (H - t) * ((H - t) / 2 + t - ex)**2)
    Sx = Ix / (H - ex)
    rx = math.sqrt(Ix / A)
    # Iy about centroidal axis parallel to H leg
    Iy = (H * t**3 / 12 + H * t * (t / 2 - ey)**2 +
          t * (B - t)**3 / 12 + t * (B - t) * ((B - t) / 2 + t - ey)**2)
    Sy = Iy / (B - ey)
    ry = math.sqrt(Iy / A)
    Zx = A / 2 * (H - ex) * 0.9  # approximate
    Zy = A / 2 * (B - ey) * 0.9
    J = A * t**2 / 3
    Cw = 0.0
    w = round(A * _W_FACTOR, 2)
    return SteelSection(name, w, Fy, Fu, round(A, 1), H, t, B, t,
                        round(Ix), round(Sx), round(rx, 1),
                        round(Iy), round(Sy), round(ry, 1),
                        round(Zx), round(Zy), round(J), round(Cw), std)


# ============================================================================
# C-CHANNEL (เหล็กแป / เหล็กรูปตัวซี) - Cold-formed ตามมอก. / ข้อมูลผู้ผลิต
# รูปแบบชื่อ: C[h]x[b]x[c]x[t]  h=ความสูง, b=ปีก, c=ขอบ, t=ความหนา
# ============================================================================

C_CHANNELS = {
    # ---- h=75 ----
    "C75x45x15x2.0": SteelSection("C75x45x15x2.0",   2.52, 245, 290,  321, 75, 2.0, 45, 2.0, 3.85e5, 1.03e4, 34.6, 6.82e4, 2.42e3, 14.6, 1.16e4, 3.72e3,  68,  8.5e8, "ผู้ผลิต/มอก.107"),
    "C75x45x15x2.3": SteelSection("C75x45x15x2.3",   2.88, 245, 290,  367, 75, 2.3, 45, 2.3, 4.36e5, 1.16e4, 34.4, 7.72e4, 2.72e3, 14.5, 1.31e4, 4.18e3,  103, 9.8e8, "ผู้ผลิต/มอก.107"),
    # ---- h=100 ----
    "C100x50x20x2.0": SteelSection("C100x50x20x2.0",  3.24, 245, 290,  413, 100,2.0, 50, 2.0, 8.52e5, 1.70e4, 45.4, 1.08e5, 3.52e3, 16.2, 1.93e4, 5.42e3,  88,  2.12e9,"ผู้ผลิต/มอก.107"),
    "C100x50x20x2.3": SteelSection("C100x50x20x2.3",  3.67, 245, 290,  467, 100,2.3, 50, 2.3, 1.08e6, 2.15e4, 48.0, 1.47e5, 4.40e3, 17.7, 2.45e4, 6.80e3,  156, 2.85e9,"ผู้ผลิต/มอก.107"),
    "C100x50x20x3.2": SteelSection("C100x50x20x3.2",  4.99, 245, 290,  636, 100,3.2, 50, 3.2, 1.45e6, 2.90e4, 47.8, 1.94e5, 6.00e3, 17.5, 3.28e4, 9.20e3,  287, 3.82e9,"ผู้ผลิต/มอก.107"),
    # ---- h=120 ----
    "C120x55x20x2.3": SteelSection("C120x55x20x2.3",  4.22, 245, 290,  537, 120,2.3, 55, 2.3, 1.72e6, 2.87e4, 56.5, 1.85e5, 5.25e3, 18.5, 3.26e4, 8.06e3,  178, 3.52e9,"ผู้ผลิต/มอก.107"),
    "C120x55x20x3.2": SteelSection("C120x55x20x3.2",  5.78, 245, 290,  736, 120,3.2, 55, 3.2, 2.32e6, 3.86e4, 56.1, 2.46e5, 6.92e3, 18.3, 4.37e4, 1.06e4,  332, 4.72e9,"ผู้ผลิต/มอก.107"),
    # ---- h=125 ----
    "C125x50x20x3.2": SteelSection("C125x50x20x3.2",  5.62, 245, 290,  716, 125,3.2, 50, 3.2, 2.54e6, 4.06e4, 59.5, 2.13e5, 6.40e3, 17.2, 4.58e4, 9.80e3,  320, 4.25e9,"ผู้ผลิต/มอก.107"),
    "C125x65x20x3.2": SteelSection("C125x65x20x3.2",  6.42, 245, 290,  818, 125,3.2, 65, 3.2, 2.95e6, 4.72e4, 60.0, 4.28e5, 9.68e3, 22.9, 5.32e4, 1.48e4,  368, 6.82e9,"ผู้ผลิต/มอก.107"),
    # ---- h=150 ----
    "C150x50x20x2.3": SteelSection("C150x50x20x2.3",  4.68, 245, 290,  596, 150,2.3, 50, 2.3, 2.75e6, 3.67e4, 67.9, 1.52e5, 4.52e3, 16.0, 4.16e4, 6.95e3,  215, 2.95e9,"ผู้ผลิต/มอก.107"),
    "C150x50x20x3.2": SteelSection("C150x50x20x3.2",  6.42, 245, 290,  818, 150,3.2, 50, 3.2, 4.25e6, 5.67e4, 72.1, 2.32e5, 6.80e3, 16.8, 6.38e4, 1.04e4,  352, 4.68e9,"ผู้ผลิต/มอก.107"),
    "C150x65x20x3.2": SteelSection("C150x65x20x3.2",  7.55, 245, 290,  962, 150,3.2, 65, 3.2, 5.05e6, 6.74e4, 72.5, 4.12e5, 9.35e3, 20.7, 7.58e4, 1.43e4,  437, 7.85e9,"ผู้ผลิต/มอก.107"),
    "C150x65x20x4.0": SteelSection("C150x65x20x4.0",  8.78, 245, 290, 1118, 150,4.0, 65, 4.0, 5.68e6, 7.58e4, 71.3, 4.77e5, 1.07e4, 20.7, 8.52e4, 1.62e4,  712, 9.56e9,"ผู้ผลิต/มอก.107"),
    "C150x75x25x4.5": SteelSection("C150x75x25x4.5", 11.0,  345, 400, 1401, 150,4.5, 75, 4.5, 6.91e6, 9.22e4, 70.2, 8.22e5, 1.59e4, 24.2, 1.04e5, 2.41e4, 1245,1.68e10,"ผู้ผลิต/มอก.107"),
    # ---- h=175 ----
    "C175x65x20x3.2": SteelSection("C175x65x20x3.2",  8.32, 245, 290, 1060, 175,3.2, 65, 3.2, 7.65e6, 8.74e4, 85.0, 4.25e5, 9.58e3, 20.0, 9.85e4, 1.47e4,  468, 8.25e9,"ผู้ผลิต/มอก.107"),
    "C175x65x20x4.0": SteelSection("C175x65x20x4.0",  9.72, 245, 290, 1238, 175,4.0, 65, 4.0, 8.82e6, 1.01e5, 84.4, 4.92e5, 1.10e4, 19.9, 1.14e5, 1.69e4,  778, 9.88e9,"ผู้ผลิต/มอก.107"),
    # ---- h=200 ----
    "C200x75x25x3.2": SteelSection("C200x75x25x3.2",  9.52, 245, 290, 1212, 200,3.2, 75, 3.2, 1.18e7, 1.18e5, 98.7, 5.52e5, 1.12e4, 21.3, 1.33e5, 1.72e4,  591, 1.18e10,"ผู้ผลิต/มอก.107"),
    "C200x75x25x4.0": SteelSection("C200x75x25x4.0", 11.8,  245, 290, 1502, 200,4.0, 75, 4.0, 1.44e7, 1.44e5, 97.9, 6.75e5, 1.36e4, 21.2, 1.62e5, 2.09e4,  924, 1.45e10,"ผู้ผลิต/มอก.107"),
    "C200x75x25x4.5": SteelSection("C200x75x25x4.5", 12.9,  345, 400, 1641, 200,4.5, 75, 4.5, 1.45e7, 1.45e5, 94.0, 9.08e5, 1.70e4, 23.5, 1.63e5, 2.58e4, 1378, 1.85e10,"ผู้ผลิต/มอก.107"),
    "C200x90x25x6.0": SteelSection("C200x90x25x6.0", 17.1,  345, 400, 2178, 200,6.0, 90, 6.0, 1.89e7, 1.89e5, 93.1, 1.64e6, 2.73e4, 27.4, 2.12e5, 4.12e4, 2612, 3.52e10,"ผู้ผลิต/มอก.107"),
    # ---- h=230 ----
    "C230x75x25x4.0": SteelSection("C230x75x25x4.0", 13.3,  245, 290, 1694, 230,4.0, 75, 4.0, 2.08e7, 1.81e5, 111.0,6.92e5, 1.39e4, 20.2, 2.04e5, 2.14e4,  978, 1.52e10,"ผู้ผลิต/มอก.107"),
    "C230x75x25x4.5": SteelSection("C230x75x25x4.5", 14.9,  245, 290, 1898, 230,4.5, 75, 4.5, 2.32e7, 2.02e5, 110.5,7.68e5, 1.54e4, 20.1, 2.28e5, 2.36e4, 1382, 1.72e10,"ผู้ผลิต/มอก.107"),
    # ---- h=250 ----
    "C250x75x25x4.0": SteelSection("C250x75x25x4.0", 14.4,  245, 290, 1836, 250,4.0, 75, 4.0, 2.72e7, 2.18e5, 121.7,6.98e5, 1.40e4, 19.5, 2.46e5, 2.15e4, 1012, 1.55e10,"ผู้ผลิต/มอก.107"),
    "C250x75x25x4.5": SteelSection("C250x75x25x4.5", 16.1,  245, 290, 2051, 250,4.5, 75, 4.5, 3.04e7, 2.43e5, 121.7,7.78e5, 1.56e4, 19.5, 2.74e5, 2.40e4, 1432, 1.75e10,"ผู้ผลิต/มอก.107"),
    "C250x90x25x6.0": SteelSection("C250x90x25x6.0", 19.4,  345, 400, 2471, 250,6.0, 90, 6.0, 3.25e7, 2.60e5, 114.7,1.78e6, 2.86e4, 26.8, 2.92e5, 4.32e4, 2835, 3.82e10,"ผู้ผลิต/มอก.107"),
    # ---- h=300 ----
    "C300x90x25x6.0": SteelSection("C300x90x25x6.0", 21.7,  345, 400, 2764, 300,6.0, 90, 6.0, 5.18e7, 3.45e5, 137.0,1.92e6, 2.99e4, 26.3, 3.87e5, 4.52e4, 3058, 4.12e10,"ผู้ผลิต/มอก.107"),
    "C300x100x25x6.0":SteelSection("C300x100x25x6.0",23.5,  345, 400, 2995, 300,6.0,100, 6.0, 5.68e7, 3.79e5, 137.7,2.56e6, 3.68e4, 29.2, 4.28e5, 5.62e4, 3285, 5.48e10,"ผู้ผลิต/มอก.107"),
}


# ============================================================================
# H-BEAM (เหล็กเอช-บีม) - มอก. 1227-2558 อ้างอิง JIS G3192
# HW = Wide Flange (ปีกกว้าง), HM = Medium Flange, HN = Narrow Flange
# ============================================================================

H_BEAMS = {
    # ---- HW Series (Wide Flange — ปีกกว้าง bf ≈ d) ----
    "H100x100x6x8":   _h("H100x100x6x8",   100, 100,  6,  8),
    "H125x125x6.5x9": _h("H125x125x6.5x9", 125, 125,  6.5, 9),
    "H150x150x7x10":  _h("H150x150x7x10",  150, 150,  7, 10),
    "H175x175x7.5x11":_h("H175x175x7.5x11",175, 175,  7.5,11),
    "H200x200x8x12":  _h("H200x200x8x12",  200, 200,  8, 12),
    "H244x252x11x11": _h("H244x252x11x11", 244, 252, 11, 11),
    "H250x250x9x14":  _h("H250x250x9x14",  250, 250,  9, 14),
    "H294x302x12x12": _h("H294x302x12x12", 294, 302, 12, 12),
    "H300x300x10x15": _h("H300x300x10x15", 300, 300, 10, 15),
    "H350x350x12x19": _h("H350x350x12x19", 350, 350, 12, 19),
    "H394x398x11x18": _h("H394x398x11x18", 394, 398, 11, 18),
    "H400x400x13x21": _h("H400x400x13x21", 400, 400, 13, 21),
    "H414x405x18x28": _h("H414x405x18x28", 414, 405, 18, 28),
    "H428x407x20x35": _h("H428x407x20x35", 428, 407, 20, 35),
    # ---- HM Series (Medium Flange — bf ≈ d/2) ----
    "H340x250x9x14":  _h("H340x250x9x14",  340, 250,  9, 14),
    "H390x300x10x16": _h("H390x300x10x16", 390, 300, 10, 16),
    "H440x300x11x18": _h("H440x300x11x18", 440, 300, 11, 18),
    "H482x300x11x15": _h("H482x300x11x15", 482, 300, 11, 15),
    "H488x300x11x18": _h("H488x300x11x18", 488, 300, 11, 18),
    "H582x300x12x17": _h("H582x300x12x17", 582, 300, 12, 17),
    "H588x300x12x20": _h("H588x300x12x20", 588, 300, 12, 20),
    "H594x302x14x23": _h("H594x302x14x23", 594, 302, 14, 23),
    # ---- HN Series (Narrow Flange — bf ≈ d/3) ----
    "H150x75x5x7":    _h("H150x75x5x7",    150,  75,  5,  7),
    "H175x90x5x8":    _h("H175x90x5x8",    175,  90,  5,  8),
    "H200x100x5.5x8": _h("H200x100x5.5x8", 200, 100,  5.5, 8),
    "H250x125x6x9":   _h("H250x125x6x9",   250, 125,  6,  9),
    "H300x150x6.5x9": _h("H300x150x6.5x9", 300, 150,  6.5, 9),
    "H350x175x7x11":  _h("H350x175x7x11",  350, 175,  7, 11),
    "H400x200x8x13":  _h("H400x200x8x13",  400, 200,  8, 13),
    "H450x200x9x14":  _h("H450x200x9x14",  450, 200,  9, 14),
    "H500x200x10x16": _h("H500x200x10x16", 500, 200, 10, 16),
    "H550x200x11x19": _h("H550x200x11x19", 550, 200, 11, 19),
    "H600x200x11x17": _h("H600x200x11x17", 600, 200, 11, 17),
    "H700x300x13x24": _h("H700x300x13x24", 700, 300, 13, 24),
    "H800x300x14x26": _h("H800x300x14x26", 800, 300, 14, 26),
    "H900x300x16x28": _h("H900x300x16x28", 900, 300, 16, 28),
}


# ============================================================================
# I-BEAM (เหล็กไอ-บีม) - มอก. 1227-2558 อ้างอิง JIS G3192
# เหล็กรูปตัวไอรีดร้อน (Standard I-shaped sections)
# ============================================================================

I_BEAMS = {
    "I100x75x4.5x7.6": _h("I100x75x4.5x7.6",  100, 75,  4.5, 7.6),
    "I125x74x5x7.5":   _h("I125x74x5x7.5",    125, 74,  5.0, 7.5),
    "I150x75x5.5x7":   _h("I150x75x5.5x7",    150, 75,  5.5, 7.0),
    "I150x100x5x7":    _h("I150x100x5x7",      150,100,  5.0, 7.0),
    "I175x90x5x8":     _h("I175x90x5x8",       175, 90,  5.0, 8.0),
    "I200x100x5.5x8":  _h("I200x100x5.5x8",    200,100,  5.5, 8.0),
    "I230x90x6x9":     _h("I230x90x6x9",       230, 90,  6.0, 9.0),
    "I250x125x6x9":    _h("I250x125x6x9",      250,125,  6.0, 9.0),
    "I300x150x6.5x9":  _h("I300x150x6.5x9",    300,150,  6.5, 9.0),
    "I350x150x7x10":   _h("I350x150x7x10",     350,150,  7.0,10.0),
    "I400x150x8.5x13": _h("I400x150x8.5x13",   400,150,  8.5,13.0),
    "I450x175x9x13":   _h("I450x175x9x13",     450,175,  9.0,13.0),
    "I500x180x10x16":  _h("I500x180x10x16",    500,180, 10.0,16.0),
    "I600x190x13x25":  _h("I600x190x13x25",    600,190, 13.0,25.0),
}


# ============================================================================
# EQUAL ANGLE (เหล็กฉากเท่า) - มอก. 1227-2558 อ้างอิง JIS G3192
# รูปแบบชื่อ: L[b]x[b]x[t]
# ============================================================================

EQUAL_ANGLES = {
    # ---- ขนาดเล็ก ----
    "L25x25x3":   _angle_eq("L25x25x3",    25,  3),
    "L30x30x3":   _angle_eq("L30x30x3",    30,  3),
    "L40x40x3":   _angle_eq("L40x40x3",    40,  3),
    "L40x40x4":   _angle_eq("L40x40x4",    40,  4),
    "L40x40x5":   _angle_eq("L40x40x5",    40,  5),
    "L45x45x3":   _angle_eq("L45x45x3",    45,  3),
    "L45x45x4":   _angle_eq("L45x45x4",    45,  4),
    "L45x45x5":   _angle_eq("L45x45x5",    45,  5),
    # ---- ขนาดกลาง ----
    "L50x50x4":   _angle_eq("L50x50x4",    50,  4),
    "L50x50x5":   _angle_eq("L50x50x5",    50,  5),
    "L50x50x6":   _angle_eq("L50x50x6",    50,  6),
    "L60x60x5":   _angle_eq("L60x60x5",    60,  5),
    "L60x60x6":   _angle_eq("L60x60x6",    60,  6),
    "L60x60x8":   _angle_eq("L60x60x8",    60,  8),
    "L65x65x5":   _angle_eq("L65x65x5",    65,  5),
    "L65x65x6":   _angle_eq("L65x65x6",    65,  6),
    "L65x65x8":   _angle_eq("L65x65x8",    65,  8),
    "L70x70x6":   _angle_eq("L70x70x6",    70,  6),
    "L70x70x7":   _angle_eq("L70x70x7",    70,  7),
    "L70x70x9":   _angle_eq("L70x70x9",    70,  9),
    "L75x75x5":   _angle_eq("L75x75x5",    75,  5),
    "L75x75x6":   _angle_eq("L75x75x6",    75,  6),
    "L75x75x7":   _angle_eq("L75x75x7",    75,  7),
    "L75x75x9":   _angle_eq("L75x75x9",    75,  9),
    "L80x80x6":   _angle_eq("L80x80x6",    80,  6),
    "L80x80x7":   _angle_eq("L80x80x7",    80,  7),
    "L80x80x10":  _angle_eq("L80x80x10",   80, 10),
    # ---- ขนาดกลาง-ใหญ่ ----
    "L90x90x7":   _angle_eq("L90x90x7",    90,  7),
    "L90x90x9":   _angle_eq("L90x90x9",    90,  9),
    "L90x90x10":  _angle_eq("L90x90x10",   90, 10),
    "L100x100x7": _angle_eq("L100x100x7", 100,  7),
    "L100x100x8": _angle_eq("L100x100x8", 100,  8),
    "L100x100x10":_angle_eq("L100x100x10",100, 10),
    "L100x100x13":_angle_eq("L100x100x13",100, 13),
    "L120x120x8": _angle_eq("L120x120x8", 120,  8),
    "L120x120x10":_angle_eq("L120x120x10",120, 10),
    "L120x120x12":_angle_eq("L120x120x12",120, 12),
    "L125x125x8": _angle_eq("L125x125x8", 125,  8),
    "L125x125x10":_angle_eq("L125x125x10",125, 10),
    "L125x125x12":_angle_eq("L125x125x12",125, 12),
    "L130x130x9": _angle_eq("L130x130x9", 130,  9),
    "L130x130x12":_angle_eq("L130x130x12",130, 12),
    # ---- ขนาดใหญ่ ----
    "L150x150x10":_angle_eq("L150x150x10",150, 10),
    "L150x150x12":_angle_eq("L150x150x12",150, 12),
    "L150x150x15":_angle_eq("L150x150x15",150, 15),
    "L175x175x12":_angle_eq("L175x175x12",175, 12),
    "L175x175x15":_angle_eq("L175x175x15",175, 15),
    "L200x200x15":_angle_eq("L200x200x15",200, 15),
    "L200x200x18":_angle_eq("L200x200x18",200, 18),
    "L200x200x20":_angle_eq("L200x200x20",200, 20),
    "L200x200x24":_angle_eq("L200x200x24",200, 24),
    "L250x250x25":_angle_eq("L250x250x25",250, 25),
    "L250x250x28":_angle_eq("L250x250x28",250, 28),
    "L250x250x35":_angle_eq("L250x250x35",250, 35),
}


# ============================================================================
# UNEQUAL ANGLE (เหล็กฉากไม่เท่า) - มอก. 1227-2558 อ้างอิง JIS G3192
# รูปแบบชื่อ: L[H]x[B]x[t]  H=ขาสูง, B=ขากว้าง
# ============================================================================

UNEQUAL_ANGLES = {
    "L65x50x5":    _angle_uneq("L65x50x5",    65,  50,  5),
    "L65x50x6":    _angle_uneq("L65x50x6",    65,  50,  6),
    "L75x50x5":    _angle_uneq("L75x50x5",    75,  50,  5),
    "L75x50x6":    _angle_uneq("L75x50x6",    75,  50,  6),
    "L75x50x7":    _angle_uneq("L75x50x7",    75,  50,  7),
    "L90x75x6":    _angle_uneq("L90x75x6",    90,  75,  6),
    "L90x75x9":    _angle_uneq("L90x75x9",    90,  75,  9),
    "L100x65x7":   _angle_uneq("L100x65x7",  100,  65,  7),
    "L100x65x9":   _angle_uneq("L100x65x9",  100,  65,  9),
    "L100x75x7":   _angle_uneq("L100x75x7",  100,  75,  7),
    "L100x75x9":   _angle_uneq("L100x75x9",  100,  75,  9),
    "L100x75x10":  _angle_uneq("L100x75x10", 100,  75, 10),
    "L125x75x7":   _angle_uneq("L125x75x7",  125,  75,  7),
    "L125x75x9":   _angle_uneq("L125x75x9",  125,  75,  9),
    "L125x75x12":  _angle_uneq("L125x75x12", 125,  75, 12),
    "L125x90x8":   _angle_uneq("L125x90x8",  125,  90,  8),
    "L125x90x10":  _angle_uneq("L125x90x10", 125,  90, 10),
    "L130x65x8":   _angle_uneq("L130x65x8",  130,  65,  8),
    "L130x65x10":  _angle_uneq("L130x65x10", 130,  65, 10),
    "L150x90x9":   _angle_uneq("L150x90x9",  150,  90,  9),
    "L150x90x11":  _angle_uneq("L150x90x11", 150,  90, 11),
    "L150x100x10": _angle_uneq("L150x100x10",150, 100, 10),
    "L150x100x12": _angle_uneq("L150x100x12",150, 100, 12),
    "L150x100x15": _angle_uneq("L150x100x15",150, 100, 15),
    "L175x90x10":  _angle_uneq("L175x90x10", 175,  90, 10),
    "L175x90x12":  _angle_uneq("L175x90x12", 175,  90, 12),
    "L175x100x10": _angle_uneq("L175x100x10",175, 100, 10),
    "L200x100x10": _angle_uneq("L200x100x10",200, 100, 10),
    "L200x100x13": _angle_uneq("L200x100x13",200, 100, 13),
    "L200x100x15": _angle_uneq("L200x100x15",200, 100, 15),
    "L200x150x12": _angle_uneq("L200x150x12",200, 150, 12),
    "L200x150x15": _angle_uneq("L200x150x15",200, 150, 15),
    "L200x150x18": _angle_uneq("L200x150x18",200, 150, 18),
}


# ============================================================================
# STEEL PIPE (เหล็กท่อกลม) - มอก. 107-2533
# รูปแบบชื่อ: Pipe[NPS]A([OD]x[t])   NPS=Nominal Pipe Size
# ============================================================================

STEEL_PIPES = {
    # NPS  OD(mm)   t(mm)
    "Pipe15A(21.7x2.3)":   _pipe("Pipe15A(21.7x2.3)",    21.7,  2.3),
    "Pipe20A(27.2x2.3)":   _pipe("Pipe20A(27.2x2.3)",    27.2,  2.3),
    "Pipe25A(34.0x2.3)":   _pipe("Pipe25A(34.0x2.3)",    34.0,  2.3),
    "Pipe25A(34.0x3.2)":   _pipe("Pipe25A(34.0x3.2)",    34.0,  3.2),
    "Pipe32A(42.7x2.3)":   _pipe("Pipe32A(42.7x2.3)",    42.7,  2.3),
    "Pipe32A(42.7x3.5)":   _pipe("Pipe32A(42.7x3.5)",    42.7,  3.5),
    "Pipe40A(48.6x2.3)":   _pipe("Pipe40A(48.6x2.3)",    48.6,  2.3),
    "Pipe40A(48.6x3.5)":   _pipe("Pipe40A(48.6x3.5)",    48.6,  3.5),
    "Pipe50A(60.5x2.3)":   _pipe("Pipe50A(60.5x2.3)",    60.5,  2.3),
    "Pipe50A(60.5x3.2)":   _pipe("Pipe50A(60.5x3.2)",    60.5,  3.2),
    "Pipe50A(60.5x3.5)":   _pipe("Pipe50A(60.5x3.5)",    60.5,  3.5),
    "Pipe65A(76.3x3.2)":   _pipe("Pipe65A(76.3x3.2)",    76.3,  3.2),
    "Pipe65A(76.3x4.0)":   _pipe("Pipe65A(76.3x4.0)",    76.3,  4.0),
    "Pipe80A(89.1x3.2)":   _pipe("Pipe80A(89.1x3.2)",    89.1,  3.2),
    "Pipe80A(89.1x4.0)":   _pipe("Pipe80A(89.1x4.0)",    89.1,  4.0),
    "Pipe80A(89.1x4.5)":   _pipe("Pipe80A(89.1x4.5)",    89.1,  4.5),
    "Pipe100A(114.3x3.5)": _pipe("Pipe100A(114.3x3.5)",  114.3, 3.5),
    "Pipe100A(114.3x4.5)": _pipe("Pipe100A(114.3x4.5)",  114.3, 4.5),
    "Pipe100A(114.3x6.0)": _pipe("Pipe100A(114.3x6.0)",  114.3, 6.0),
    "Pipe125A(139.8x4.0)": _pipe("Pipe125A(139.8x4.0)",  139.8, 4.0),
    "Pipe125A(139.8x4.5)": _pipe("Pipe125A(139.8x4.5)",  139.8, 4.5),
    "Pipe125A(139.8x6.0)": _pipe("Pipe125A(139.8x6.0)",  139.8, 6.0),
    "Pipe150A(165.2x4.5)": _pipe("Pipe150A(165.2x4.5)",  165.2, 4.5),
    "Pipe150A(165.2x6.0)": _pipe("Pipe150A(165.2x6.0)",  165.2, 6.0),
    "Pipe200A(216.3x6.0)": _pipe("Pipe200A(216.3x6.0)",  216.3, 6.0),
    "Pipe200A(216.3x8.0)": _pipe("Pipe200A(216.3x8.0)",  216.3, 8.0),
    "Pipe250A(267.4x6.0)": _pipe("Pipe250A(267.4x6.0)",  267.4, 6.0),
    "Pipe250A(267.4x9.0)": _pipe("Pipe250A(267.4x9.0)",  267.4, 9.0),
    "Pipe300A(318.5x9.0)": _pipe("Pipe300A(318.5x9.0)",  318.5, 9.0),
    "Pipe300A(318.5x10.0)":_pipe("Pipe300A(318.5x10.0)", 318.5,10.0),
    "Pipe350A(355.6x9.0)": _pipe("Pipe350A(355.6x9.0)",  355.6, 9.0),
    "Pipe350A(355.6x12.0)":_pipe("Pipe350A(355.6x12.0)", 355.6,12.0),
    "Pipe400A(406.4x9.0)": _pipe("Pipe400A(406.4x9.0)",  406.4, 9.0),
    "Pipe400A(406.4x12.0)":_pipe("Pipe400A(406.4x12.0)", 406.4,12.0),
}


# ============================================================================
# RHS (เหล็กกล่องสี่เหลี่ยมผืนผ้า) - มอก. 107-2533
# รูปแบบชื่อ: RHS[h]x[b]x[t]
# ============================================================================

RHS_SECTIONS = {
    "RHS40x20x2.0":  _rhs("RHS40x20x2.0",   40,  20, 2.0),
    "RHS40x20x2.3":  _rhs("RHS40x20x2.3",   40,  20, 2.3),
    "RHS50x25x2.0":  _rhs("RHS50x25x2.0",   50,  25, 2.0),
    "RHS50x25x2.3":  _rhs("RHS50x25x2.3",   50,  25, 2.3),
    "RHS50x25x3.2":  _rhs("RHS50x25x3.2",   50,  25, 3.2),
    "RHS60x30x2.0":  _rhs("RHS60x30x2.0",   60,  30, 2.0),
    "RHS60x30x2.3":  _rhs("RHS60x30x2.3",   60,  30, 2.3),
    "RHS60x30x3.2":  _rhs("RHS60x30x3.2",   60,  30, 3.2),
    "RHS75x45x2.3":  _rhs("RHS75x45x2.3",   75,  45, 2.3),
    "RHS75x45x3.2":  _rhs("RHS75x45x3.2",   75,  45, 3.2),
    "RHS80x40x2.3":  _rhs("RHS80x40x2.3",   80,  40, 2.3),
    "RHS80x40x3.2":  _rhs("RHS80x40x3.2",   80,  40, 3.2),
    "RHS80x40x4.0":  _rhs("RHS80x40x4.0",   80,  40, 4.0),
    "RHS100x50x2.3": _rhs("RHS100x50x2.3",  100,  50, 2.3),
    "RHS100x50x3.2": _rhs("RHS100x50x3.2",  100,  50, 3.2),
    "RHS100x50x4.0": _rhs("RHS100x50x4.0",  100,  50, 4.0),
    "RHS100x50x4.5": _rhs("RHS100x50x4.5",  100,  50, 4.5),
    "RHS120x60x3.2": _rhs("RHS120x60x3.2",  120,  60, 3.2),
    "RHS120x60x4.0": _rhs("RHS120x60x4.0",  120,  60, 4.0),
    "RHS120x60x4.5": _rhs("RHS120x60x4.5",  120,  60, 4.5),
    "RHS150x75x3.2": _rhs("RHS150x75x3.2",  150,  75, 3.2),
    "RHS150x75x4.5": _rhs("RHS150x75x4.5",  150,  75, 4.5),
    "RHS150x75x6.0": _rhs("RHS150x75x6.0",  150,  75, 6.0),
    "RHS150x100x4.5":_rhs("RHS150x100x4.5", 150, 100, 4.5),
    "RHS150x100x6.0":_rhs("RHS150x100x6.0", 150, 100, 6.0),
    "RHS200x100x4.5":_rhs("RHS200x100x4.5", 200, 100, 4.5),
    "RHS200x100x6.0":_rhs("RHS200x100x6.0", 200, 100, 6.0),
    "RHS200x100x8.0":_rhs("RHS200x100x8.0", 200, 100, 8.0),
    "RHS200x150x6.0":_rhs("RHS200x150x6.0", 200, 150, 6.0),
    "RHS200x150x8.0":_rhs("RHS200x150x8.0", 200, 150, 8.0),
    "RHS250x150x6.0":_rhs("RHS250x150x6.0", 250, 150, 6.0),
    "RHS250x150x8.0":_rhs("RHS250x150x8.0", 250, 150, 8.0),
    "RHS250x150x10.0":_rhs("RHS250x150x10.0",250,150,10.0),
    "RHS300x200x8.0":_rhs("RHS300x200x8.0", 300, 200, 8.0),
    "RHS300x200x10.0":_rhs("RHS300x200x10.0",300,200,10.0),
    "RHS400x200x8.0":_rhs("RHS400x200x8.0", 400, 200, 8.0),
    "RHS400x200x10.0":_rhs("RHS400x200x10.0",400,200,10.0),
    "RHS400x200x12.0":_rhs("RHS400x200x12.0",400,200,12.0),
}


# ============================================================================
# SHS (เหล็กกล่องสี่เหลี่ยมจัตุรัส) - มอก. 107-2533
# รูปแบบชื่อ: SHS[h]x[h]x[t]
# ============================================================================

SHS_SECTIONS = {
    "SHS25x25x2.0":  _shs("SHS25x25x2.0",   25, 2.0),
    "SHS30x30x2.0":  _shs("SHS30x30x2.0",   30, 2.0),
    "SHS40x40x2.0":  _shs("SHS40x40x2.0",   40, 2.0),
    "SHS40x40x2.3":  _shs("SHS40x40x2.3",   40, 2.3),
    "SHS40x40x3.2":  _shs("SHS40x40x3.2",   40, 3.2),
    "SHS50x50x2.3":  _shs("SHS50x50x2.3",   50, 2.3),
    "SHS50x50x3.2":  _shs("SHS50x50x3.2",   50, 3.2),
    "SHS50x50x4.0":  _shs("SHS50x50x4.0",   50, 4.0),
    "SHS60x60x2.3":  _shs("SHS60x60x2.3",   60, 2.3),
    "SHS60x60x3.2":  _shs("SHS60x60x3.2",   60, 3.2),
    "SHS60x60x4.0":  _shs("SHS60x60x4.0",   60, 4.0),
    "SHS75x75x3.2":  _shs("SHS75x75x3.2",   75, 3.2),
    "SHS75x75x4.5":  _shs("SHS75x75x4.5",   75, 4.5),
    "SHS75x75x6.0":  _shs("SHS75x75x6.0",   75, 6.0),
    "SHS80x80x3.2":  _shs("SHS80x80x3.2",   80, 3.2),
    "SHS80x80x4.5":  _shs("SHS80x80x4.5",   80, 4.5),
    "SHS80x80x6.0":  _shs("SHS80x80x6.0",   80, 6.0),
    "SHS100x100x3.2":_shs("SHS100x100x3.2", 100, 3.2),
    "SHS100x100x4.5":_shs("SHS100x100x4.5", 100, 4.5),
    "SHS100x100x6.0":_shs("SHS100x100x6.0", 100, 6.0),
    "SHS120x120x4.5":_shs("SHS120x120x4.5", 120, 4.5),
    "SHS120x120x6.0":_shs("SHS120x120x6.0", 120, 6.0),
    "SHS150x150x4.5":_shs("SHS150x150x4.5", 150, 4.5),
    "SHS150x150x6.0":_shs("SHS150x150x6.0", 150, 6.0),
    "SHS150x150x8.0":_shs("SHS150x150x8.0", 150, 8.0),
    "SHS200x200x6.0":_shs("SHS200x200x6.0", 200, 6.0),
    "SHS200x200x8.0":_shs("SHS200x200x8.0", 200, 8.0),
    "SHS200x200x10.0":_shs("SHS200x200x10.0",200,10.0),
    "SHS250x250x8.0":_shs("SHS250x250x8.0", 250, 8.0),
    "SHS250x250x10.0":_shs("SHS250x250x10.0",250,10.0),
    "SHS250x250x12.0":_shs("SHS250x250x12.0",250,12.0),
}


# ============================================================================
# STEEL PLATES (เหล็กแผ่น) - มอก. 1227-2558
# ============================================================================

@dataclass
class SteelPlate:
    thickness: float   # mm
    Fy: float          # MPa
    Fu: float          # MPa
    standard: str

STEEL_PLATES = {
    "PL6":  SteelPlate( 6, 245, 400, "มอก. 1227-2558"),
    "PL8":  SteelPlate( 8, 245, 400, "มอก. 1227-2558"),
    "PL10": SteelPlate(10, 245, 400, "มอก. 1227-2558"),
    "PL12": SteelPlate(12, 245, 400, "มอก. 1227-2558"),
    "PL16": SteelPlate(16, 245, 400, "มอก. 1227-2558"),
    "PL19": SteelPlate(19, 245, 400, "มอก. 1227-2558"),
    "PL22": SteelPlate(22, 245, 400, "มอก. 1227-2558"),
    "PL25": SteelPlate(25, 245, 400, "มอก. 1227-2558"),
    "PL28": SteelPlate(28, 245, 400, "มอก. 1227-2558"),
    "PL32": SteelPlate(32, 245, 400, "มอก. 1227-2558"),
    "PL36": SteelPlate(36, 245, 400, "มอก. 1227-2558"),
    "PL40": SteelPlate(40, 245, 400, "มอก. 1227-2558"),
}


# ============================================================================
# BOLTS & WELDS
# ============================================================================

BOLTS = {
    "M12-4.6": BoltProperties("M12-4.6", "4.6",  12,  84.3, 400, 160),
    "M16-4.6": BoltProperties("M16-4.6", "4.6",  16, 157,   400, 160),
    "M20-4.6": BoltProperties("M20-4.6", "4.6",  20, 245,   400, 160),
    "M12-8.8": BoltProperties("M12-8.8", "8.8",  12,  84.3, 830, 332),
    "M16-8.8": BoltProperties("M16-8.8", "8.8",  16, 157,   830, 332),
    "M20-8.8": BoltProperties("M20-8.8", "8.8",  20, 245,   830, 332),
    "M24-8.8": BoltProperties("M24-8.8", "8.8",  24, 353,   830, 332),
    "M30-8.8": BoltProperties("M30-8.8", "8.8",  30, 561,   830, 332),
    "M20-10.9":BoltProperties("M20-10.9","10.9", 20, 245,  1040, 416),
    "M24-10.9":BoltProperties("M24-10.9","10.9", 24, 353,  1040, 416),
}

WELDS = {
    "E60XX": WeldProperties("E60XX", "E60XX", 414, 124),
    "E70XX": WeldProperties("E70XX", "E70XX", 483, 145),
    "E71T":  WeldProperties("E71T",  "E71T",  490, 147),
    "E80XX": WeldProperties("E80XX", "E80XX", 551, 165),
}


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_section_standard(section_name: str) -> str:
    if section_name in C_CHANNELS:
        return "Cold-formed C-channel / ผู้ผลิต + มอก. 107-2533"
    elif section_name in H_BEAMS or section_name in I_BEAMS:
        return "มอก. 1227-2558 (Hot-rolled H/I-beam, JIS G3192)"
    elif section_name in EQUAL_ANGLES or section_name in UNEQUAL_ANGLES:
        return "มอก. 1227-2558 (Angle sections, JIS G3192)"
    elif section_name in STEEL_PIPES:
        return "มอก. 107-2533 (Steel pipes, JIS G3444)"
    elif section_name in RHS_SECTIONS or section_name in SHS_SECTIONS:
        return "มอก. 107-2533 (Hollow sections, JIS G3466)"
    elif section_name in STEEL_PLATES:
        return "มอก. 1227-2558 (Steel plates)"
    return "Unknown standard"


def get_all_sections_by_standard() -> dict:
    return {
        "มอก. 1227-2558 (Hot-rolled sections)": {
            "H-Beams": list(H_BEAMS.keys()),
            "I-Beams": list(I_BEAMS.keys()),
            "Equal Angles": list(EQUAL_ANGLES.keys()),
            "Unequal Angles": list(UNEQUAL_ANGLES.keys()),
            "Plates": list(STEEL_PLATES.keys()),
        },
        "มอก. 107-2533 (Hollow sections)": {
            "Steel Pipes": list(STEEL_PIPES.keys()),
            "RHS": list(RHS_SECTIONS.keys()),
            "SHS": list(SHS_SECTIONS.keys()),
            "C-Channels (Cold-formed)": list(C_CHANNELS.keys()),
        },
    }


def get_section_summary(section_name: str, section_dict: dict = None) -> str:
    if section_dict is None:
        for d in [C_CHANNELS, H_BEAMS, I_BEAMS, EQUAL_ANGLES, UNEQUAL_ANGLES,
                  STEEL_PIPES, RHS_SECTIONS, SHS_SECTIONS]:
            if section_name in d:
                section_dict = d
                break
    if section_dict is None or section_name not in section_dict:
        return f"Section '{section_name}' not found"
    sec = section_dict[section_name]
    standard = get_section_standard(section_name)
    return (f"Section: {section_name}\nStandard: {standard}\n"
            f"Weight: {sec.weight} kg/m  |  Fy={sec.Fy} MPa, Fu={sec.Fu} MPa\n"
            f"d={sec.d}mm, bf={sec.bf}mm, tw={sec.tw}mm, tf={sec.tf}mm\n"
            f"Ix={sec.Ix/1e6:.2f}×10⁶ mm⁴, Sx={sec.Sx/1e3:.1f}×10³ mm³")


def get_tolerances(section_type: str) -> dict:
    tolerances = {
        "H_beam":         {"depth": "±1.5% or ±2mm", "flange_width": "±2%", "thickness": "±0.3-0.4mm", "weight": "±2.5%", "standard": "มอก. 1227-2558"},
        "I_beam":         {"depth": "±2% or ±2mm",   "flange_width": "±2%", "thickness": "±0.3-0.4mm", "weight": "±3%",   "standard": "มอก. 1227-2558"},
        "angle":          {"leg_length": "±1.5%", "thickness": "±0.3-0.5mm", "weight": "±4%", "standard": "มอก. 1227-2558"},
        "pipe":           {"OD": "±0.75%", "wall_thickness": "±12.5%",      "weight": "±3.5%","standard": "มอก. 107-2533"},
        "hollow_section": {"depth": "±1%", "wall_thickness": "±10%",        "weight": "±3%",  "standard": "มอก. 107-2533"},
        "C_channel":      {"depth": "±1.5%","width": "±2%","thickness": "±0.2-0.3mm","weight":"±4%","standard":"ผู้ผลิต/มอก.107-2533"},
    }
    return tolerances.get(section_type, {})


def validate_section_properties():
    issues = []
    all_sections = {
        "C_CHANNELS":    C_CHANNELS,
        "H_BEAMS":       H_BEAMS,
        "I_BEAMS":       I_BEAMS,
        "EQUAL_ANGLES":  EQUAL_ANGLES,
        "UNEQUAL_ANGLES":UNEQUAL_ANGLES,
        "STEEL_PIPES":   STEEL_PIPES,
        "RHS_SECTIONS":  RHS_SECTIONS,
        "SHS_SECTIONS":  SHS_SECTIONS,
    }
    for category, sections in all_sections.items():
        for name, sec in sections.items():
            if sec.Fy < 200 or sec.Fy > 500:
                issues.append(f"{name}: Fy={sec.Fy} MPa out of range")
            if sec.Fu < 250 or sec.Fu > 600:
                issues.append(f"{name}: Fu={sec.Fu} MPa out of range")
            if sec.Fy >= sec.Fu:
                issues.append(f"{name}: Fy({sec.Fy}) >= Fu({sec.Fu}) invalid!")
            if sec.Ix <= 0 or sec.Sx <= 0:
                issues.append(f"{name}: Invalid Ix/Sx")
    return issues


if __name__ == "__main__":
    print("=" * 70)
    print("Thai Steel Section Database — มอก. Standards")
    print("=" * 70)
    print(f"\nC-Channels:      {len(C_CHANNELS):3d} sections")
    print(f"H-Beams:         {len(H_BEAMS):3d} sections")
    print(f"I-Beams:         {len(I_BEAMS):3d} sections")
    print(f"Equal Angles:    {len(EQUAL_ANGLES):3d} sections")
    print(f"Unequal Angles:  {len(UNEQUAL_ANGLES):3d} sections")
    print(f"Steel Pipes:     {len(STEEL_PIPES):3d} sections")
    print(f"RHS:             {len(RHS_SECTIONS):3d} sections")
    print(f"SHS:             {len(SHS_SECTIONS):3d} sections")
    total = (len(C_CHANNELS) + len(H_BEAMS) + len(I_BEAMS) + len(EQUAL_ANGLES) +
             len(UNEQUAL_ANGLES) + len(STEEL_PIPES) + len(RHS_SECTIONS) + len(SHS_SECTIONS))
    print(f"\nTotal:           {total:3d} sections")
    issues = validate_section_properties()
    if issues:
        print(f"\nValidation issues ({len(issues)}):")
        for i in issues[:10]:
            print(f"  - {i}")
    else:
        print("\nAll sections validated OK")
