"""
Steel Section Database for Thai Structural Steel Design
Based on Thai Industrial Standards (มอก.) and Engineering Institute of Thailand (วสท.)

มาตรฐานที่เกี่ยวข้อง:
- มอก. 1227-2558: เหล็กรูปพรรณรีดร้อนรูปตัวเอช (Hot-rolled H-shaped steel)
- มอก. 107-2533: เหล็กโครงสร้างรูปพรรณกลวง (Structural hollow sections)
- วสท. 011038-22: มาตรฐานการออกแบบอาคารโครงสร้างเหล็กรูปพรรณ

Material Grades per มอก.:
- SS400: เหล็กโครงสร้างทั่วไป (General structural steel), Fy = 245 MPa, Fu = 400 MPa
- SM400: เหล็กโครงสร้างสำหรับงานเชื่อม (Welded structural steel), Fy = 245 MPa, Fu = 400 MPa
- SM490: เหล็กโครงสร้างความแข็งแรงสูง, Fy = 325 MPa, Fu = 490 MPa
- SM520: เหล็กโครงสร้างความแข็งแรงสูงมาก, Fy = 365 MPa, Fu = 520 MPa
- SS540: เหล็กโครงสร้างความแข็งแรงสูง, Fy = 375 MPa, Fu = 540 MPa

หมายเหตุ:
- ค่าคุณสมบัติหน้าตัดอ้างอิงจาก มอก. และข้อมูลผู้ผลิตในประเทศไทย
- น้ำหนักต่อเมตรคำนวณจากความหนาแน่นเหล็ก 7,850 kg/m³
"""
from dataclasses import dataclass
from typing import Optional

@dataclass
class SteelSection:
    """Represents the properties of a steel section per มอก. standards."""
    name: str
    weight: float      # kg/m (น้ำหนักต่อเมตร)
    Fy: float          # MPa (กำลังรับแรงดึงคราก - Yield strength per มอก.)
    Fu: float          # MPa (กำลังรับแรงดึงสูงสุด - Ultimate strength per มอก.)
    A: float           # mm^2 (พื้นที่หน้าตัด - Cross-sectional area)
    d: float           # mm (ความลึก - Depth)
    tw: float          # mm (ความหนาเว็บ - Web thickness)
    bf: float          # mm (ความกว้างหน้าแปลน - Flange width)
    tf: float          # mm (ความหนาหน้าแปลน - Flange thickness)
    Ix: float          # mm^4 (โมเมนต์ความเฉื่อยแกน X - Moment of inertia about x-axis)
    Sx: float          # mm^3 (โมดูลัสหน้าตัดแกน X - Section modulus about x-axis)
    rx: float          # mm (รัศมีไจเรชันแกน X - Radius of gyration about x-axis)
    Iy: float          # mm^4 (โมเมนต์ความเฉื่อยแกน Y - Moment of inertia about y-axis)
    Sy: float          # mm^3 (โมดูลัสหน้าตัดแกน Y - Section modulus about y-axis)
    ry: float          # mm (รัศมีไจเรชันแกน Y - Radius of gyration about y-axis)
    Zx: float          # mm^3 (โมดูลัสพลาสติกแกน X - Plastic section modulus about x-axis)
    Zy: float          # mm^3 (โมดูลัสพลาสติกแกน Y - Plastic section modulus about y-axis)
    J: float           # mm^4 (ค่าคงที่แรงบิด - Torsional constant)
    Cw: float          # mm^6 (ค่าคงที่การบิดงอ - Warping constant)
    standard: str = "" # มาตรฐานอ้างอิง (e.g., "มอก. 1227-2558")


# ============================================================================
# Material Properties per มอก. 1227-2558
# ============================================================================
@dataclass
class MaterialGrade:
    """Material grade definition per มอก. standard."""
    grade: str
    Fy: float          # MPa - Minimum yield strength
    Fu: float          # MPa - Minimum tensile strength
    application: str   # Typical application
    standard: str      # Reference standard

MATERIAL_GRADES = {
    # Hot-rolled structural steel per มอก. 1227-2558
    "SS400": MaterialGrade(
        grade="SS400", Fy=245, Fu=400,
        application="เหล็กรูปพรรณทั่วไป (General structural steel)",
        standard="มอก. 1227-2558"
    ),
    "SM400": MaterialGrade(
        grade="SM400", Fy=245, Fu=400,
        application="เหล็กรูปพรรณสำหรับงานเชื่อม (Welded structural steel)",
        standard="มอก. 1227-2558"
    ),
    "SM490": MaterialGrade(
        grade="SM490", Fy=325, Fu=490,
        application="เหล็กรูปพรรณความแข็งแรงสูง (Higher strength structural steel)",
        standard="มอก. 1227-2558"
    ),
    "SM520": MaterialGrade(
        grade="SM520", Fy=365, Fu=520,
        application="เหล็กรูปพรรณความแข็งแรงสูงมาก (High strength structural steel)",
        standard="มอก. 1227-2558"
    ),
    "SS540": MaterialGrade(
        grade="SS540", Fy=375, Fu=540,
        application="เหล็กรูปพรรณความแข็งแรงสูง (High strength structural steel)",
        standard="มอก. 1227-2558"
    ),
}


# ============================================================================
# C-CHANNEL (เหล็กรูปตัวซี) - Cold-formed per manufacturer data
# ============================================================================
# หมายเหตุ: เหล็กตัวซีเย็นขึ้นรูปตาม มอก. 107-2533 หรือข้อมูลผู้ผลิต
# ค่า Fy/Fu แตกต่างกันตามความหนาของเหล็ก
C_CHANNELS = {
    "C100x50x20x2.3": SteelSection(
        name="C100x50x20x2.3", weight=3.67, Fy=245, Fu=290, A=467.2, d=100, tw=2.3, bf=50, tf=2.3,
        Ix=1.08e6, Sx=2.15e4, rx=48.0, Iy=0.147e6, Sy=4.4e3, ry=17.7,
        Zx=2.45e4, Zy=6.8e3, J=156, Cw=2.85e9
    ),
    "C100x50x20x3.2": SteelSection(
        name="C100x50x20x3.2", weight=4.99, Fy=245, Fu=290, A=635.8, d=100, tw=3.2, bf=50, tf=3.2,
        Ix=1.45e6, Sx=2.90e4, rx=47.8, Iy=0.194e6, Sy=6.0e3, ry=17.5,
        Zx=3.28e4, Zy=9.2e3, J=287, Cw=3.82e9
    ),
    "C125x50x20x3.2": SteelSection(
        name="C125x50x20x3.2", weight=5.62, Fy=245, Fu=290, A=715.8, d=125, tw=3.2, bf=50, tf=3.2,
        Ix=2.54e6, Sx=4.06e4, rx=59.5, Iy=0.213e6, Sy=6.4e3, ry=17.2,
        Zx=4.58e4, Zy=9.8e3, J=320, Cw=4.25e9
    ),
    "C150x50x20x3.2": SteelSection(
        name="C150x50x20x3.2", weight=6.42, Fy=245, Fu=290, A=817.8, d=150, tw=3.2, bf=50, tf=3.2,
        Ix=4.25e6, Sx=5.67e4, rx=72.1, Iy=0.232e6, Sy=6.8e3, ry=16.8,
        Zx=6.38e4, Zy=10.4e3, J=352, Cw=4.68e9
    ),
    "C150x65x20x4.0": SteelSection(
        name="C150x65x20x4.0", weight=8.78, Fy=245, Fu=290, A=1118.0, d=150, tw=4.0, bf=65, tf=4.0,
        Ix=5.68e6, Sx=7.58e4, rx=71.3, Iy=0.477e6, Sy=10.7e3, ry=20.7,
        Zx=8.52e4, Zy=16.2e3, J=712, Cw=9.56e9
    ),
    "C150x75x25x4.5": SteelSection(
        name="C150x75x25x4.5", weight=11.0, Fy=345, Fu=400, A=1401.0, d=150, tw=4.5, bf=75, tf=4.5,
        Ix=6.91e6, Sx=9.22e4, rx=70.2, Iy=0.822e6, Sy=15.9e3, ry=24.2,
        Zx=1.04e5, Zy=24.1e3, J=1245, Cw=1.68e10
    ),
    "C200x75x25x4.5": SteelSection(
        name="C200x75x25x4.5", weight=12.9, Fy=345, Fu=400, A=1641.0, d=200, tw=4.5, bf=75, tf=4.5,
        Ix=1.45e7, Sx=1.45e5, rx=94.0, Iy=0.908e6, Sy=17.0e3, ry=23.5,
        Zx=1.63e5, Zy=25.8e3, J=1378, Cw=1.85e10
    ),
    "C200x90x25x6.0": SteelSection(
        name="C200x90x25x6.0", weight=17.1, Fy=345, Fu=400, A=2178.0, d=200, tw=6.0, bf=90, tf=6.0,
        Ix=1.89e7, Sx=1.89e5, rx=93.1, Iy=1.64e6, Sy=27.3e3, ry=27.4,
        Zx=2.12e5, Zy=41.2e3, J=2612, Cw=3.52e10
    ),
    "C250x90x25x6.0": SteelSection(
        name="C250x90x25x6.0", weight=19.4, Fy=345, Fu=400, A=2471.0, d=250, tw=6.0, bf=90, tf=6.0,
        Ix=3.25e7, Sx=2.60e5, rx=114.7, Iy=1.78e6, Sy=28.6e3, ry=26.8,
        Zx=2.92e5, Zy=43.2e3, J=2835, Cw=3.82e10
    ),
    "C300x90x25x6.0": SteelSection(
        name="C300x90x25x6.0", weight=21.7, Fy=345, Fu=400, A=2764.0, d=300, tw=6.0, bf=90, tf=6.0,
        Ix=5.18e7, Sx=3.45e5, rx=137.0, Iy=1.92e6, Sy=29.9e3, ry=26.3,
        Zx=3.87e5, Zy=45.2e3, J=3058, Cw=4.12e10
    ),
}

# ============================================================================
# H-BEAM (เหล็กเอชบีม) - มอก. 1227-2558
# Wide Flange / H-Shaped Sections (เหล็กรูปตัวเอชรีดร้อน)
# Material: SS400 (Fy = 245 MPa, Fu = 400 MPa) per มอก. 1227-2558
# ============================================================================
H_BEAMS = {
    "H100x100x6x8": SteelSection("H100x100x6x8", 17.2, 245, 400, 2190, 100, 6, 100, 8, 3.83e6, 7.66e4, 41.8, 1.34e6, 2.68e4, 24.7, 8.58e4, 4.08e4, 9.58e4, 1.25e11),
    "H125x125x6.5x9": SteelSection("H125x125x6.5x9", 23.8, 245, 400, 3031, 125, 6.5, 125, 9, 8.46e6, 1.35e5, 52.8, 2.94e6, 4.70e4, 31.1, 1.51e5, 7.16e4, 2.18e5, 3.82e11),
    "H150x150x7x10": SteelSection("H150x150x7x10", 31.9, 245, 400, 4055, 150, 7, 150, 10, 1.66e7, 2.21e5, 64.0, 5.63e6, 7.51e4, 37.3, 2.48e5, 1.14e5, 4.42e5, 9.56e11),
    "H175x175x7.5x11": SteelSection("H175x175x7.5x11", 40.4, 245, 400, 5143, 175, 7.5, 175, 11, 2.88e7, 3.29e5, 74.8, 9.84e6, 1.12e5, 43.8, 3.69e5, 1.71e5, 7.86e5, 2.12e12),
    "H200x200x8x12": SteelSection("H200x200x8x12", 50.5, 245, 400, 6428, 200, 8, 200, 12, 4.77e7, 4.77e5, 86.2, 1.60e7, 1.60e5, 49.9, 5.36e5, 2.43e5, 1.32e6, 4.25e12),
    "H250x250x9x14": SteelSection("H250x250x9x14", 72.4, 245, 400, 9218, 250, 9, 250, 14, 1.08e8, 8.67e5, 108.4, 3.65e7, 2.92e5, 62.9, 9.74e5, 4.44e5, 2.98e6, 1.38e13),
    "H300x300x10x15": SteelSection("H300x300x10x15", 94.5, 245, 400, 12020, 300, 10, 300, 15, 2.04e8, 1.36e6, 130.3, 6.75e7, 4.50e5, 74.9, 1.53e6, 6.86e5, 5.45e6, 3.38e13),
    "H350x350x12x19": SteelSection("H350x350x12x19", 137.0, 245, 400, 17450, 350, 12, 350, 19, 3.54e8, 2.02e6, 142.5, 1.12e8, 6.40e5, 80.1, 2.27e6, 9.76e5, 1.02e7, 7.82e13),
    "H400x400x13x21": SteelSection("H400x400x13x21", 172.0, 245, 400, 21910, 400, 13, 400, 21, 5.65e8, 2.83e6, 160.5, 1.79e8, 8.95e5, 90.3, 3.19e6, 1.37e6, 1.72e7, 1.56e14),
    "H450x300x11x18": SteelSection("H450x300x11x18", 124.0, 245, 400, 15740, 450, 11, 300, 18, 5.61e8, 2.49e6, 189.0, 8.11e7, 5.41e5, 71.8, 2.78e6, 8.25e5, 4.25e6, 3.82e13),
    "H500x300x11x18": SteelSection("H500x300x11x18", 128.0, 245, 400, 16350, 500, 11, 300, 18, 7.10e8, 2.84e6, 208.0, 8.11e7, 5.41e5, 70.4, 3.18e6, 8.25e5, 4.58e6, 4.68e13),
    "H600x300x12x20": SteelSection("H600x300x12x20", 151.0, 245, 400, 19250, 600, 12, 300, 20, 1.18e9, 3.93e6, 247.0, 9.02e7, 6.01e5, 68.5, 4.45e6, 9.25e5, 6.82e6, 7.25e13),
    "H700x300x13x24": SteelSection("H700x300x13x24", 185.0, 245, 400, 23550, 700, 13, 300, 24, 2.01e9, 5.74e6, 292.0, 1.08e8, 7.22e5, 67.8, 6.52e6, 1.12e6, 1.05e7, 1.25e14),
    "H800x300x14x26": SteelSection("H800x300x14x26", 210.0, 245, 400, 26740, 800, 14, 300, 26, 2.92e9, 7.30e6, 330.0, 1.17e8, 7.82e5, 66.2, 8.28e6, 1.25e6, 1.45e7, 1.82e14),
    "H900x300x16x28": SteelSection("H900x300x16x28", 243.0, 245, 400, 30980, 900, 16, 300, 28, 4.11e9, 9.13e6, 364.0, 1.26e8, 8.42e5, 63.8, 1.04e7, 1.38e6, 1.92e7, 2.56e14),
}

# ============================================================================
# I-BEAM (เหล็กไอบีม) - มอก. 1227-2558
# Standard I-Shaped Sections (เหล็กรูปตัวไอีรีดร้อน)
# Material: SS400 (Fy = 245 MPa, Fu = 400 MPa) per มอก. 1227-2558
# ============================================================================
I_BEAMS = {
    "I100x75x4.5x6": SteelSection("I100x75x4.5x6", 11.1, 245, 400, 1414, 100, 4.5, 75, 6, 2.09e6, 4.18e4, 38.4, 0.51e6, 1.36e4, 19.0, 4.72e4, 2.08e4, 4.82e4, 4.25e10),
    "I150x100x5x7": SteelSection("I150x100x5x7", 18.6, 245, 400, 2370, 150, 5, 100, 7, 8.35e6, 1.11e5, 59.3, 1.34e6, 2.68e4, 23.8, 1.26e5, 4.10e4, 1.28e5, 1.42e11),
    "I200x100x5.5x8": SteelSection("I200x100x5.5x8", 24.2, 245, 400, 3082, 200, 5.5, 100, 8, 1.84e7, 1.84e5, 77.3, 1.55e6, 3.10e4, 22.4, 2.08e5, 4.74e4, 1.52e5, 1.68e11),
    "I250x125x6x9": SteelSection("I250x125x6x9", 34.6, 245, 400, 4410, 250, 6, 125, 9, 4.05e7, 3.24e5, 95.8, 3.13e6, 5.01e4, 26.6, 3.66e5, 7.66e4, 3.12e5, 4.25e11),
    "I300x150x6.5x9": SteelSection("I300x150x6.5x9", 43.2, 245, 400, 5503, 300, 6.5, 150, 9, 7.21e7, 4.81e5, 114.5, 5.08e6, 6.77e4, 30.4, 5.43e5, 1.04e5, 5.12e5, 8.56e11),
    "I450x175x9x13": SteelSection("I450x175x9x13", 71.7, 245, 400, 9129, 450, 9, 175, 13, 2.97e8, 1.32e6, 180.0, 1.17e7, 1.34e5, 35.8, 1.48e6, 2.05e5, 1.25e6, 2.12e12),
    "I600x190x13x25": SteelSection("I600x190x13x25", 133.0, 245, 400, 16940, 600, 13, 190, 25, 9.84e8, 3.28e6, 241.0, 2.86e7, 3.01e5, 41.1, 3.72e6, 4.65e5, 4.82e6, 8.56e12),
}

# ============================================================================
# EQUAL ANGLE (เหล็กฉากเท่า) - มอก. 1227-2558
# Equal Leg Angles (เหล็กรูปตัวแอลขาเท่า)
# Material: SS400 (Fy = 245 MPa, Fu = 400 MPa) per มอก. 1227-2558
# ============================================================================
EQUAL_ANGLES = {
    "L25x25x3": SteelSection("L25x25x3", 1.12, 245, 400, 143, 25, 3, 25, 3, 0.73e4, 0.41e3, 7.1, 0.73e4, 0.41e3, 7.1, 0.58e3, 0.58e3, 0.22e4, 0.12e7),
    "L40x40x4": SteelSection("L40x40x4", 2.42, 245, 400, 308, 40, 4, 40, 4, 3.58e4, 1.24e3, 10.8, 3.58e4, 1.24e3, 10.8, 1.76e3, 1.76e3, 1.08e4, 1.12e7),
    "L50x50x5": SteelSection("L50x50x5", 3.77, 245, 400, 480, 50, 5, 50, 5, 8.94e4, 2.49e3, 13.6, 8.94e4, 2.49e3, 13.6, 3.52e3, 3.52e3, 2.72e4, 4.25e7),
    "L75x75x6": SteelSection("L75x75x6", 6.76, 245, 400, 861, 75, 6, 75, 6, 4.03e5, 7.56e3, 21.6, 4.03e5, 7.56e3, 21.6, 1.07e4, 1.07e4, 1.24e5, 3.82e8),
    "L100x100x10": SteelSection("L100x100x10", 14.8, 245, 400, 1886, 100, 10, 100, 10, 1.77e6, 2.49e4, 30.6, 1.77e6, 2.49e4, 30.6, 3.54e4, 3.54e4, 5.62e5, 2.98e9),
    "L150x150x12": SteelSection("L150x150x12", 27.4, 245, 400, 3488, 150, 12, 150, 12, 7.74e6, 7.36e4, 47.1, 7.74e6, 7.36e4, 47.1, 1.05e5, 1.05e5, 2.52e6, 2.68e10),
    "L200x200x15": SteelSection("L200x200x15", 45.3, 245, 400, 5775, 200, 15, 200, 15, 2.14e7, 1.51e5, 60.9, 2.14e7, 1.51e5, 60.9, 2.15e5, 2.15e5, 6.82e6, 1.25e11),
    "L250x250x25": SteelSection("L250x250x25", 91.6, 245, 400, 11670, 250, 25, 250, 25, 6.62e7, 3.78e5, 75.3, 6.62e7, 3.78e5, 75.3, 5.42e5, 5.42e5, 2.12e7, 4.25e11),
}

# ============================================================================
# UNEQUAL ANGLE (เหล็กฉากไม่เท่า) - มอก. 1227-2558
# Unequal Leg Angles (เหล็กรูปตัวแอลขาไม่เท่า)
# Material: SS400 (Fy = 245 MPa, Fu = 400 MPa) per มอก. 1227-2558
# ============================================================================
C_CHANNELS = {
    "C100x50x20x2.3": SteelSection("C100x50x20x2.3", 3.67, 245, 400, 467, 100, 2.3, 50, 2.3, 1.08e6, 2.15e4, 48.0, 0.147e6, 4.4e3, 17.7, 2.45e4, 6.8e3, 156, 2.85e9),
    "C125x50x20x3.2": SteelSection("C125x50x20x3.2", 5.62, 245, 400, 716, 125, 3.2, 50, 3.2, 2.54e6, 4.06e4, 59.5, 0.213e6, 6.4e3, 17.2, 4.58e4, 9.8e3, 320, 4.25e9),
    "C150x50x20x3.2": SteelSection("C150x50x20x3.2", 6.42, 245, 400, 818, 150, 3.2, 50, 3.2, 4.25e6, 5.67e4, 72.1, 0.232e6, 6.8e3, 16.8, 6.38e4, 1.04e5, 352, 4.68e9),
    "C150x65x20x4.0": SteelSection("C150x65x20x4.0", 8.78, 245, 400, 1118, 150, 4.0, 65, 4.0, 5.68e6, 7.58e4, 71.3, 0.477e6, 10.7e3, 20.7, 8.52e4, 16.2e3, 712, 9.56e9),
    "C200x75x25x4.5": SteelSection("C200x75x25x4.5", 12.9, 245, 400, 1641, 200, 4.5, 75, 4.5, 1.45e7, 1.45e5, 94.0, 0.908e6, 17.0e3, 23.5, 1.63e5, 25.8e3, 1378, 1.85e10),
}

# ============================================================================
# STEEL PIPE (เหล็กท่อกลม) - มอก. 107-2533
# Steel Pipes for General Structure (เหล็กท่อกลมโครงสร้าง)
# Material: STPG400 equivalent to SS400 (Fy = 245 MPa, Fu = 305 MPa) per มอก. 107-2533
# ============================================================================
SHS_SECTIONS = {
    "SHS50x50x2.3": SteelSection("SHS50x50x2.3", 3.42, 245, 400, 436, 50, 2.3, 50, 2.3, 1.96e5, 7.84e3, 21.2, 1.96e5, 7.84e3, 21.2, 9.20e3, 9.20e3, 3.18e5, 0),
    "SHS75x75x3.2": SteelSection("SHS75x75x3.2", 7.15, 245, 400, 910, 75, 3.2, 75, 3.2, 9.28e5, 2.47e4, 31.9, 9.28e5, 2.47e4, 31.9, 2.90e4, 2.90e4, 1.50e6, 0),
    "SHS100x100x4.5": SteelSection("SHS100x100x4.5", 13.4, 245, 400, 1706, 100, 4.5, 100, 4.5, 3.08e6, 6.16e4, 42.5, 3.08e6, 6.16e4, 42.5, 7.18e4, 7.18e4, 4.98e6, 0),
    "SHS150x150x6.0": SteelSection("SHS150x150x6.0", 27.0, 245, 400, 3440, 150, 6.0, 150, 6.0, 1.41e7, 1.88e5, 64.0, 1.41e7, 1.88e5, 64.0, 2.16e5, 2.16e5, 2.27e7, 0),
    "SHS200x200x9.0": SteelSection("SHS200x200x9.0", 53.5, 245, 400, 6810, 200, 9.0, 200, 9.0, 4.82e7, 4.82e5, 84.1, 4.82e7, 4.82e5, 84.1, 5.52e5, 5.52e5, 7.76e7, 0),
}

# ============================================================================
# RHS / SHS (เหล็กกล่องสี่เหลี่ยม) - มอก. 107-2533
# Rectangular/Square Hollow Sections (เหล็กท่อกลวงสี่เหลี่ยม/จัตุรัส)
# Material: STKR400 equivalent to SS400 (Fy = 245 MPa, Fu = 290 MPa) per มอก. 107-2533
# ============================================================================
RHS_SECTIONS = {
    "RHS100x50x3.2": SteelSection("RHS100x50x3.2", 7.15, 245, 400, 910, 100, 3.2, 50, 3.2, 1.25e6, 2.50e4, 37.1, 0.42e6, 1.68e4, 21.5, 3.12e4, 1.95e4, 1.12e6, 0),
    "RHS150x75x4.5": SteelSection("RHS150x75x4.5", 15.2, 245, 400, 1936, 150, 4.5, 75, 4.5, 6.28e6, 8.37e4, 56.9, 2.14e6, 5.71e4, 33.2, 1.05e5, 6.82e4, 5.42e6, 0),
    "RHS200x100x6.0": SteelSection("RHS200x100x6.0", 27.0, 245, 400, 3440, 200, 6.0, 100, 6.0, 1.88e7, 1.88e5, 73.9, 6.42e6, 1.28e5, 43.2, 2.32e5, 1.52e5, 1.68e7, 0),
}

# ============================================================================
# STEEL PLATE (เหล็กแผ่น) - มอก. 1227-2558
# Steel Plates for structural use (เหล็กแผ่นโครงสร้าง)
# Material: SS400/SM400 (Fy = 245 MPa, Fu = 400 MPa) per มอก. 1227-2558
# ============================================================================
STEEL_PIPES = {
    "Pipe50A(60.5x3.2)": SteelSection("Pipe50A(60.5x3.2)", 4.52, 245, 400, 576, 60.5, 3.2, 60.5, 3.2, 2.45e5, 8.10e3, 20.6, 2.45e5, 8.10e3, 20.6, 1.08e4, 1.08e4, 4.90e5, 0),
    "Pipe100A(114.3x4.5)": SteelSection("Pipe100A(114.3x4.5)", 12.2, 245, 400, 1552, 114.3, 4.5, 114.3, 4.5, 2.38e6, 4.16e4, 39.1, 2.38e6, 4.16e4, 39.1, 5.52e4, 5.52e4, 4.76e6, 0),
}

# ============================================================================
# BOLTS & WELDS (มอก.)
# ============================================================================
@dataclass
class BoltProperties:
    name: str
    grade: str
    diameter: float
    area: float
    Fub: float
    shear_strength: float

BOLTS = {
    "M12": BoltProperties("M12", "A325", 12, 113, 830, 207),
    "M16": BoltProperties("M16", "A325", 16, 201, 830, 207),
    "M20": BoltProperties("M20", "A325", 20, 314, 830, 207),
    "M24": BoltProperties("M24", "A325", 24, 452, 830, 207),
    "M30": BoltProperties("M30", "A325", 30, 706, 830, 207),
}

@dataclass
class WeldProperties:
    name: str
    electrode: str
    Fu: float
    shear_strength: float

WELDS = {
    "E60XX": WeldProperties("E60XX", "E60XX", 414, 124),
    "E70XX": WeldProperties("E70XX", "E70XX", 483, 145),
}
 

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_section_standard(section_name: str) -> str:
    """Determine which มอก. standard a section belongs to."""
    if section_name in C_CHANNELS:
        return "มอก. 107-2533 (Cold-formed C-channel)"
    elif section_name in H_BEAMS or section_name in I_BEAMS:
        return "มอก. 1227-2558 (Hot-rolled H/I-beam)"
    elif section_name in EQUAL_ANGLES or section_name in UNEQUAL_ANGLES:
        return "มอก. 1227-2558 (Angle sections)"
    elif section_name in STEEL_PIPES:
        return "มอก. 107-2533 (Steel pipes)"
    elif section_name in RHS_SECTIONS:
        return "มอก. 107-2533 (Hollow sections)"
    elif section_name in STEEL_PLATES:
        return "มอก. 1227-2558 (Steel plates)"
    return "Unknown standard"


def get_tolerances(section_type: str) -> dict:
    """
    Return manufacturing tolerances per มอก. standards.
    
    Tolerances based on มอก. 1227-2558 and มอก. 107-2533:
    - Depth/Width: ±1-3% depending on size
    - Thickness: ±0.2-0.5mm depending on thickness
    - Weight: ±2.5-5% depending on section
    """
    tolerances = {
        "H_beam": {
            "depth": "±1.5% or ±2mm (whichever is greater)",
            "width": "±2% or ±2mm (whichever is greater)",
            "web_thickness": "±0.3mm (t≤8mm), ±0.4mm (t>8mm)",
            "flange_thickness": "±0.3mm (t≤8mm), ±0.4mm (t>8mm)",
            "weight": "±2.5%",
            "standard": "มอก. 1227-2558"
        },
        "I_beam": {
            "depth": "±2% or ±2mm",
            "width": "±2%",
            "web_thickness": "±0.3mm (t≤8mm), ±0.4mm (t>8mm)",
            "flange_thickness": "±0.3mm (t≤8mm), ±0.4mm (t>8mm)",
            "weight": "±3%",
            "standard": "มอก. 1227-2558"
        },
        "angle": {
            "leg_length": "±1.5%",
            "thickness": "±0.3mm (t≤6mm), ±0.5mm (t>6mm)",
            "weight": "±4%",
            "standard": "มอก. 1227-2558"
        },
        "pipe": {
            "outside_diameter": "±0.75%",
            "wall_thickness": "±12.5%",
            "weight": "±3.5%",
            "standard": "มอก. 107-2533"
        },
        "hollow_section": {
            "depth": "±1%",
            "width": "±1%",
            "wall_thickness": "±10%",
            "weight": "±3%",
            "standard": "มอก. 107-2533"
        },
        "C_channel": {
            "depth": "±1.5%",
            "width": "±2%",
            "thickness": "±0.2mm (t≤3mm), ±0.3mm (t>3mm)",
            "weight": "±4%",
            "standard": "Manufacturer data (Cold-formed per มอก. 107-2533)"
        },
        "plate": {
            "thickness": "±0.3mm (t≤5mm), ±0.5mm (5<t≤10mm), ±0.8mm (t>10mm)",
            "width": "±5mm",
            "weight": "±5%",
            "standard": "มอก. 1227-2558"
        },
    }
    return tolerances.get(section_type, {})


def get_all_sections_by_standard() -> dict:
    """Return all sections grouped by their มอก. standard."""
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
            "RHS/SHS": list(RHS_SECTIONS.keys()),
            "C-Channels (Cold-formed)": list(C_CHANNELS.keys()),
        },
    }


def get_section_summary(section_name: str, section_dict: dict = None) -> str:
    """Get a human-readable summary of a section with standard reference."""
    if section_dict is None:
        # Try to find the section
        for d in [C_CHANNELS, H_BEAMS, I_BEAMS, EQUAL_ANGLES, UNEQUAL_ANGLES, 
                  STEEL_PIPES, RHS_SECTIONS]:
            if section_name in d:
                section_dict = d
                break
    
    if section_dict is None or section_name not in section_dict:
        return f"Section '{section_name}' not found"
    
    sec = section_dict[section_name]
    standard = get_section_standard(section_name)
    
    summary = f"""
Section: {section_name}
Standard: {standard}
Weight: {sec.weight} kg/m
Material: Fy={sec.Fy} MPa, Fu={sec.Fu} MPa
Dimensions: d={sec.d}mm, bf={sec.bf}mm, tw={sec.tw}mm, tf={sec.tf}mm
Properties: Ix={sec.Ix/1e6:.2f}×10⁶ mm⁴, Sx={sec.Sx/1e3:.1f}×10³ mm³
    """.strip()
    
    return summary


# ============================================================================
# VALIDATION
# ============================================================================

def validate_section_properties():
    """Validate all section properties for consistency."""
    issues = []
    
    # Check all sections have required properties
    all_sections = {
        "C_CHANNELS": C_CHANNELS,
        "H_BEAMS": H_BEAMS,
        "I_BEAMS": I_BEAMS,
        "EQUAL_ANGLES": EQUAL_ANGLES,
        "UNEQUAL_ANGLES": UNEQUAL_ANGLES,
        "STEEL_PIPES": STEEL_PIPES,
        "RHS_SECTIONS": RHS_SECTIONS,
    }
    
    for category, sections in all_sections.items():
        for name, sec in sections.items():
            # Check Fy and Fu are reasonable
            if sec.Fy < 200 or sec.Fy > 500:
                issues.append(f"{name}: Fy={sec.Fy} MPa outside typical range")
            if sec.Fu < 250 or sec.Fu > 600:
                issues.append(f"{name}: Fu={sec.Fu} MPa outside typical range")
            if sec.Fy >= sec.Fu:
                issues.append(f"{name}: Fy ({sec.Fy}) >= Fu ({sec.Fu}) - invalid!")
            
            # Check geometric consistency
            if sec.d <= 0 or sec.bf <= 0 or sec.tw <= 0 or sec.tf <= 0:
                issues.append(f"{name}: Invalid dimensions")
            if sec.Ix <= 0 or sec.Sx <= 0 or sec.Iy <= 0 or sec.Sy <= 0:
                issues.append(f"{name}: Invalid section properties")
            
            # Check weight reasonableness (should be > 0)
            if sec.weight <= 0:
                issues.append(f"{name}: Invalid weight")
    
    return issues


if __name__ == "__main__":
    print("=" * 70)
    print("Thai Steel Section Database - มอก. Standards Compliance")
    print("=" * 70)
    
    print("\nMaterial Grades per มอก. 1227-2558:")
    for grade, mat in MATERIAL_GRADES.items():
        print(f"  {grade}: Fy={mat.Fy} MPa, Fu={mat.Fu} MPa - {mat.application}")
    
    print(f"\nTotal Sections Available:")
    print(f"  C-Channels: {len(C_CHANNELS)}")
    print(f"  H-Beams: {len(H_BEAMS)}")
    print(f"  I-Beams: {len(I_BEAMS)}")
    print(f"  Equal Angles: {len(EQUAL_ANGLES)}")
    print(f"  Unequal Angles: {len(UNEQUAL_ANGLES)}")
    print(f"  Steel Pipes: {len(STEEL_PIPES)}")
    print(f"  RHS/SHS: {len(RHS_SECTIONS)}")
    print(f"  Steel Plates: {len(STEEL_PLATES)}")
    
    print("\nStandards References:")
    for std, sections in get_all_sections_by_standard().items():
        print(f"\n  {std}:")
        for cat, secs in sections.items():
            print(f"    {cat}: {len(secs)} sections")
    
    issues = validate_section_properties()
    if issues:
        print(f"\nValidation Issues ({len(issues)}):")
        for issue in issues[:10]:
            print(f"  - {issue}")
    else:
        print("\n✓ All section properties validated successfully")
