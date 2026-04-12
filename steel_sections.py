"""
Steel Section Database for Thai Structural Steel Design
Based on TIS (Thai Industrial Standard) and manufacturer data
"""
from dataclasses import dataclass


@dataclass
class SteelSection:
    """Represents the properties of a steel section."""
    name: str
    weight: float      # kg/m
    Fy: float          # MPa (Yield strength)
    Fu: float          # MPa (Ultimate strength)
    A: float           # mm^2 (Cross-sectional area)
    d: float           # mm (Depth)
    tw: float          # mm (Web thickness)
    bf: float          # mm (Flange width)
    tf: float          # mm (Flange thickness)
    Ix: float          # mm^4 (Moment of inertia about x-axis)
    Sx: float          # mm^3 (Section modulus about x-axis)
    rx: float          # mm (Radius of gyration about x-axis)
    Iy: float          # mm^4 (Moment of inertia about y-axis)
    Sy: float          # mm^3 (Section modulus about y-axis)
    ry: float          # mm (Radius of gyration about y-axis)
    Zx: float          # mm^3 (Plastic section modulus about x-axis)
    Zy: float          # mm^3 (Plastic section modulus about y-axis)
    J: float           # mm^4 (Torsional constant)
    Cw: float          # mm^6 (Warping constant)


# ============================================================================
# C-CHANNEL (เหล็กรูปตัวซี) - TIS 1228
# ============================================================================
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
# H-BEAM (เหล็กเอชบีม) - TIS 1227
# Wide Flange / H-Shaped Sections
# ============================================================================
H_BEAMS = {
    "H100x100x6x8": SteelSection(
        name="H100x100x6x8", weight=17.2, Fy=245, Fu=400, A=2190, d=100, tw=6, bf=100, tf=8,
        Ix=3.83e6, Sx=7.66e4, rx=41.8, Iy=1.34e6, Sy=2.68e4, ry=24.7,
        Zx=8.58e4, Zy=4.08e4, J=9.58e4, Cw=1.25e11
    ),
    "H125x125x6.5x9": SteelSection(
        name="H125x125x6.5x9", weight=23.8, Fy=245, Fu=400, A=3031, d=125, tw=6.5, bf=125, tf=9,
        Ix=8.46e6, Sx=1.35e5, rx=52.8, Iy=2.94e6, Sy=4.70e4, ry=31.1,
        Zx=1.51e5, Zy=7.16e4, J=2.18e5, Cw=3.82e11
    ),
    "H150x150x7x10": SteelSection(
        name="H150x150x7x10", weight=31.9, Fy=245, Fu=400, A=4055, d=150, tw=7, bf=150, tf=10,
        Ix=1.66e7, Sx=2.21e5, rx=64.0, Iy=5.63e6, Sy=7.51e4, ry=37.3,
        Zx=2.48e5, Zy=1.14e5, J=4.42e5, Cw=9.56e11
    ),
    "H175x175x7.5x11": SteelSection(
        name="H175x175x7.5x11", weight=40.4, Fy=245, Fu=400, A=5143, d=175, tw=7.5, bf=175, tf=11,
        Ix=2.88e7, Sx=3.29e5, rx=74.8, Iy=9.84e6, Sy=1.12e5, ry=43.8,
        Zx=3.69e5, Zy=1.71e5, J=7.86e5, Cw=2.12e12
    ),
    "H200x200x8x12": SteelSection(
        name="H200x200x8x12", weight=50.5, Fy=245, Fu=400, A=6428, d=200, tw=8, bf=200, tf=12,
        Ix=4.77e7, Sx=4.77e5, rx=86.2, Iy=1.60e7, Sy=1.60e5, ry=49.9,
        Zx=5.36e5, Zy=2.43e5, J=1.32e6, Cw=4.25e12
    ),
    "H250x250x9x14": SteelSection(
        name="H250x250x9x14", weight=72.4, Fy=245, Fu=400, A=9218, d=250, tw=9, bf=250, tf=14,
        Ix=1.08e8, Sx=8.67e5, rx=108.4, Iy=3.65e7, Sy=2.92e5, ry=62.9,
        Zx=9.74e5, Zy=4.44e5, J=2.98e6, Cw=1.38e13
    ),
    "H300x300x10x15": SteelSection(
        name="H300x300x10x15", weight=94.5, Fy=245, Fu=400, A=12020, d=300, tw=10, bf=300, tf=15,
        Ix=2.04e8, Sx=1.36e6, rx=130.3, Iy=6.75e7, Sy=4.50e5, ry=74.9,
        Zx=1.53e6, Zy=6.86e5, J=5.45e6, Cw=3.38e13
    ),
    "H350x350x12x19": SteelSection(
        name="H350x350x12x19", weight=137.0, Fy=245, Fu=400, A=17450, d=350, tw=12, bf=350, tf=19,
        Ix=3.54e8, Sx=2.02e6, rx=142.5, Iy=1.12e8, Sy=6.40e5, ry=80.1,
        Zx=2.27e6, Zy=9.76e5, J=1.02e7, Cw=7.82e13
    ),
    "H400x400x13x21": SteelSection(
        name="H400x400x13x21", weight=172.0, Fy=245, Fu=400, A=21910, d=400, tw=13, bf=400, tf=21,
        Ix=5.65e8, Sx=2.83e6, rx=160.5, Iy=1.79e8, Sy=8.95e5, ry=90.3,
        Zx=3.19e6, Zy=1.37e6, J=1.72e7, Cw=1.56e14
    ),
}

# ============================================================================
# I-BEAM (เหล็กไอบีม) - TIS 1227
# Standard I-Shaped Sections
# ============================================================================
I_BEAMS = {
    "I100x75x4.5x6": SteelSection(
        name="I100x75x4.5x6", weight=11.1, Fy=245, Fu=400, A=1414, d=100, tw=4.5, bf=75, tf=6,
        Ix=2.09e6, Sx=4.18e4, rx=38.4, Iy=0.51e6, Sy=1.36e4, ry=19.0,
        Zx=4.72e4, Zy=2.08e4, J=4.82e4, Cw=4.25e10
    ),
    "I125x75x4.5x6": SteelSection(
        name="I125x75x4.5x6", weight=12.5, Fy=245, Fu=400, A=1591, d=125, tw=4.5, bf=75, tf=6,
        Ix=3.77e6, Sx=6.03e4, rx=48.7, Iy=0.55e6, Sy=1.47e4, ry=18.6,
        Zx=6.79e4, Zy=2.25e4, J=5.18e4, Cw=4.68e10
    ),
    "I150x100x5x7": SteelSection(
        name="I150x100x5x7", weight=18.6, Fy=245, Fu=400, A=2370, d=150, tw=5, bf=100, tf=7,
        Ix=8.35e6, Sx=1.11e5, rx=59.3, Iy=1.34e6, Sy=2.68e4, ry=23.8,
        Zx=1.26e5, Zy=4.10e4, J=1.28e5, Cw=1.42e11
    ),
    "I200x100x5.5x8": SteelSection(
        name="I200x100x5.5x8", weight=24.2, Fy=245, Fu=400, A=3082, d=200, tw=5.5, bf=100, tf=8,
        Ix=1.84e7, Sx=1.84e5, rx=77.3, Iy=1.55e6, Sy=3.10e4, ry=22.4,
        Zx=2.08e5, Zy=4.74e4, J=1.52e5, Cw=1.68e11
    ),
    "I250x125x6x9": SteelSection(
        name="I250x125x6x9", weight=34.6, Fy=245, Fu=400, A=4410, d=250, tw=6, bf=125, tf=9,
        Ix=4.05e7, Sx=3.24e5, rx=95.8, Iy=3.13e6, Sy=5.01e4, ry=26.6,
        Zx=3.66e5, Zy=7.66e4, J=3.12e5, Cw=4.25e11
    ),
    "I300x150x6.5x9": SteelSection(
        name="I300x150x6.5x9", weight=43.2, Fy=245, Fu=400, A=5503, d=300, tw=6.5, bf=150, tf=9,
        Ix=7.21e7, Sx=4.81e5, rx=114.5, Iy=5.08e6, Sy=6.77e4, ry=30.4,
        Zx=5.43e5, Zy=1.04e5, J=5.12e5, Cw=8.56e11
    ),
    "I350x175x7x11": SteelSection(
        name="I350x175x7x11", weight=60.0, Fy=245, Fu=400, A=7636, d=350, tw=7, bf=175, tf=11,
        Ix=1.37e8, Sx=7.83e5, rx=133.9, Iy=9.84e6, Sy=1.12e5, ry=35.9,
        Zx=8.82e5, Zy=1.72e5, J=9.82e5, Cw=2.12e12
    ),
    "I400x200x8x13": SteelSection(
        name="I400x200x8x13", weight=78.1, Fy=245, Fu=400, A=9953, d=400, tw=8, bf=200, tf=13,
        Ix=2.37e8, Sx=1.19e6, rx=154.3, Iy=1.74e7, Sy=1.74e5, ry=41.8,
        Zx=1.34e6, Zy=2.67e5, J=1.78e6, Cw=4.68e12
    ),
}

# ============================================================================
# EQUAL ANGLE (เหล็กฉากเท่า) - TIS 1227
# ============================================================================
EQUAL_ANGLES = {
    "L25x25x3": SteelSection(
        name="L25x25x3", weight=1.12, Fy=245, Fu=400, A=143, d=25, tw=3, bf=25, tf=3,
        Ix=0.73e4, Sx=0.41e3, rx=7.1, Iy=0.73e4, Sy=0.41e3, ry=7.1,
        Zx=0.58e3, Zy=0.58e3, J=0.22e4, Cw=0.12e7
    ),
    "L30x30x3": SteelSection(
        name="L30x30x3", weight=1.36, Fy=245, Fu=400, A=174, d=30, tw=3, bf=30, tf=3,
        Ix=1.32e4, Sx=0.62e3, rx=8.7, Iy=1.32e4, Sy=0.62e3, ry=8.7,
        Zx=0.88e3, Zy=0.88e3, J=0.40e4, Cw=0.28e7
    ),
    "L40x40x4": SteelSection(
        name="L40x40x4", weight=2.42, Fy=245, Fu=400, A=308, d=40, tw=4, bf=40, tf=4,
        Ix=3.58e4, Sx=1.24e3, rx=10.8, Iy=3.58e4, Sy=1.24e3, ry=10.8,
        Zx=1.76e3, Zy=1.76e3, J=1.08e4, Cw=1.12e7
    ),
    "L50x50x5": SteelSection(
        name="L50x50x5", weight=3.77, Fy=245, Fu=400, A=480, d=50, tw=5, bf=50, tf=5,
        Ix=8.94e4, Sx=2.49e3, rx=13.6, Iy=8.94e4, Sy=2.49e3, ry=13.6,
        Zx=3.52e3, Zy=3.52e3, J=2.72e4, Cw=4.25e7
    ),
    "L65x65x6": SteelSection(
        name="L65x65x6", weight=5.82, Fy=245, Fu=400, A=741, d=65, tw=6, bf=65, tf=6,
        Ix=2.38e5, Sx=5.17e3, rx=17.9, Iy=2.38e5, Sy=5.17e3, ry=17.9,
        Zx=7.32e3, Zy=7.32e3, J=7.28e4, Cw=1.68e8
    ),
    "L75x75x6": SteelSection(
        name="L75x75x6", weight=6.76, Fy=245, Fu=400, A=861, d=75, tw=6, bf=75, tf=6,
        Ix=4.03e5, Sx=7.56e3, rx=21.6, Iy=4.03e5, Sy=7.56e3, ry=21.6,
        Zx=1.07e4, Zy=1.07e4, J=1.24e5, Cw=3.82e8
    ),
    "L90x90x9": SteelSection(
        name="L90x90x9", weight=11.9, Fy=245, Fu=400, A=1514, d=90, tw=9, bf=90, tf=9,
        Ix=1.08e6, Sx=1.66e4, rx=26.7, Iy=1.08e6, Sy=1.66e4, ry=26.7,
        Zx=2.36e4, Zy=2.36e4, J=3.36e5, Cw=1.42e9
    ),
    "L100x100x10": SteelSection(
        name="L100x100x10", weight=14.8, Fy=245, Fu=400, A=1886, d=100, tw=10, bf=100, tf=10,
        Ix=1.77e6, Sx=2.49e4, rx=30.6, Iy=1.77e6, Sy=2.49e4, ry=30.6,
        Zx=3.54e4, Zy=3.54e4, J=5.62e5, Cw=2.98e9
    ),
    "L125x125x12": SteelSection(
        name="L125x125x12", weight=22.7, Fy=245, Fu=400, A=2891, d=125, tw=12, bf=125, tf=12,
        Ix=4.39e6, Sx=4.96e4, rx=39.0, Iy=4.39e6, Sy=4.96e4, ry=39.0,
        Zx=7.06e4, Zy=7.06e4, J=1.42e6, Cw=1.12e10
    ),
    "L150x150x12": SteelSection(
        name="L150x150x12", weight=27.4, Fy=245, Fu=400, A=3488, d=150, tw=12, bf=150, tf=12,
        Ix=7.74e6, Sx=7.36e4, rx=47.1, Iy=7.74e6, Sy=7.36e4, ry=47.1,
        Zx=1.05e5, Zy=1.05e5, J=2.52e6, Cw=2.68e10
    ),
    "L150x150x16": SteelSection(
        name="L150x150x16", weight=35.9, Fy=245, Fu=400, A=4568, d=150, tw=16, bf=150, tf=16,
        Ix=9.93e6, Sx=9.28e4, rx=46.6, Iy=9.93e6, Sy=9.28e4, ry=46.6,
        Zx=1.33e5, Zy=1.33e5, J=3.28e6, Cw=3.42e10
    ),
}

# ============================================================================
# UNEQUAL ANGLE (เหล็กฉากไม่เท่า) - TIS 1227
# ============================================================================
UNEQUAL_ANGLES = {
    "L65x50x5": SteelSection(
        name="L65x50x5", weight=4.30, Fy=245, Fu=400, A=548, d=65, tw=5, bf=50, tf=5,
        Ix=2.62e5, Sx=5.68e3, rx=21.9, Iy=1.38e5, Sy=3.82e3, ry=15.9,
        Zx=8.06e3, Zy=5.42e3, J=4.82e4, Cw=1.12e8
    ),
    "L75x50x6": SteelSection(
        name="L75x50x6", weight=5.62, Fy=245, Fu=400, A=716, d=75, tw=6, bf=50, tf=6,
        Ix=4.56e5, Sx=8.52e3, rx=25.2, Iy=1.68e5, Sy=4.62e3, ry=15.3,
        Zx=1.21e4, Zy=6.56e3, J=7.28e4, Cw=1.68e8
    ),
    "L90x60x8": SteelSection(
        name="L90x60x8", weight=8.82, Fy=245, Fu=400, A=1123, d=90, tw=8, bf=60, tf=8,
        Ix=1.08e6, Sx=1.68e4, rx=31.0, Iy=4.52e5, Sy=1.02e4, ry=20.1,
        Zx=2.38e4, Zy=1.46e4, J=1.82e5, Cw=5.68e8
    ),
    "L100x75x8": SteelSection(
        name="L100x75x8", weight=10.6, Fy=245, Fu=400, A=1347, d=100, tw=8, bf=75, tf=8,
        Ix=1.68e6, Sx=2.38e4, rx=35.3, Iy=8.52e5, Sy=1.56e4, ry=25.2,
        Zx=3.36e4, Zy=2.22e4, J=2.82e5, Cw=1.12e9
    ),
    "L125x75x10": SteelSection(
        name="L125x75x10", weight=15.2, Fy=245, Fu=400, A=1936, d=125, tw=10, bf=75, tf=10,
        Ix=3.58e6, Sx=4.12e4, rx=43.0, Iy=1.42e6, Sy=2.58e4, ry=27.1,
        Zx=5.78e4, Zy=3.68e4, J=5.82e5, Cw=3.25e9
    ),
    "L150x90x10": SteelSection(
        name="L150x90x10", weight=18.3, Fy=245, Fu=400, A=2331, d=150, tw=10, bf=90, tf=10,
        Ix=6.28e6, Sx=6.12e4, rx=51.9, Iy=2.18e6, Sy=3.42e4, ry=30.6,
        Zx=8.72e4, Zy=4.88e4, J=8.52e5, Cw=6.82e9
    ),
    "L150x90x12": SteelSection(
        name="L150x90x12", weight=21.8, Fy=245, Fu=400, A=2776, d=150, tw=12, bf=90, tf=12,
        Ix=7.38e6, Sx=7.12e4, rx=51.6, Iy=2.52e6, Sy=3.92e4, ry=30.2,
        Zx=1.02e5, Zy=5.58e4, J=9.82e5, Cw=7.82e9
    ),
}

# ============================================================================
# STEEL PIPE (เหล็กท่อกลม) - TIS 107
# ============================================================================
STEEL_PIPES = {
    "SGP15A(21.7x2.8)": SteelSection(
        name="SGP15A(21.7x2.8)", weight=1.31, Fy=245, Fu=305, A=167, d=21.7, tw=2.8, bf=21.7, tf=2.8,
        Ix=0.58e4, Sx=0.53e3, rx=5.9, Iy=0.58e4, Sy=0.53e3, ry=5.9,
        Zx=0.72e3, Zy=0.72e3, J=1.16e4, Cw=0
    ),
    "SGP20A(27.2x2.8)": SteelSection(
        name="SGP20A(27.2x2.8)", weight=1.69, Fy=245, Fu=305, A=215, d=27.2, tw=2.8, bf=27.2, tf=2.8,
        Ix=1.38e4, Sx=1.01e3, rx=8.0, Iy=1.38e4, Sy=1.01e3, ry=8.0,
        Zx=1.38e3, Zy=1.38e3, J=2.76e4, Cw=0
    ),
    "SGP25A(34.0x3.2)": SteelSection(
        name="SGP25A(34.0x3.2)", weight=2.43, Fy=245, Fu=305, A=309, d=34.0, tw=3.2, bf=34.0, tf=3.2,
        Ix=3.42e4, Sx=2.01e3, rx=10.5, Iy=3.42e4, Sy=2.01e3, ry=10.5,
        Zx=2.72e3, Zy=2.72e3, J=6.84e4, Cw=0
    ),
    "SGP32A(42.7x3.2)": SteelSection(
        name="SGP32A(42.7x3.2)", weight=3.11, Fy=245, Fu=305, A=396, d=42.7, tw=3.2, bf=42.7, tf=3.2,
        Ix=8.52e4, Sx=3.98e3, rx=14.6, Iy=8.52e4, Sy=3.98e3, ry=14.6,
        Zx=5.38e3, Zy=5.38e3, J=1.70e5, Cw=0
    ),
    "SGP40A(48.6x3.2)": SteelSection(
        name="SGP40A(48.6x3.2)", weight=3.58, Fy=245, Fu=305, A=455, d=48.6, tw=3.2, bf=48.6, tf=3.2,
        Ix=1.32e5, Sx=5.42e3, rx=17.0, Iy=1.32e5, Sy=5.42e3, ry=17.0,
        Zx=6.88e3, Zy=6.88e3, J=2.64e5, Cw=0
    ),
    "SGP50A(60.5x3.5)": SteelSection(
        name="SGP50A(60.5x3.5)", weight=4.92, Fy=245, Fu=305, A=626, d=60.5, tw=3.5, bf=60.5, tf=3.5,
        Ix=2.92e5, Sx=9.64e3, rx=21.6, Iy=2.92e5, Sy=9.64e3, ry=21.6,
        Zx=1.22e4, Zy=1.22e4, J=5.84e5, Cw=0
    ),
    "SGP65A(76.3x3.5)": SteelSection(
        name="SGP65A(76.3x3.5)", weight=6.28, Fy=245, Fu=305, A=800, d=76.3, tw=3.5, bf=76.3, tf=3.5,
        Ix=6.28e5, Sx=1.65e4, rx=28.0, Iy=6.28e5, Sy=1.65e4, ry=28.0,
        Zx=2.08e4, Zy=2.08e4, J=1.26e6, Cw=0
    ),
    "SGP80A(89.1x3.5)": SteelSection(
        name="SGP80A(89.1x3.5)", weight=7.39, Fy=245, Fu=305, A=940, d=89.1, tw=3.5, bf=89.1, tf=3.5,
        Ix=1.08e6, Sx=2.42e4, rx=33.9, Iy=1.08e6, Sy=2.42e4, ry=33.9,
        Zx=3.06e4, Zy=3.06e4, J=2.16e6, Cw=0
    ),
    "SGP100A(114.3x3.5)": SteelSection(
        name="SGP100A(114.3x3.5)", weight=9.56, Fy=245, Fu=305, A=1216, d=114.3, tw=3.5, bf=114.3, tf=3.5,
        Ix=2.68e6, Sx=4.68e4, rx=47.0, Iy=2.68e6, Sy=4.68e4, ry=47.0,
        Zx=5.92e4, Zy=5.92e4, J=5.36e6, Cw=0
    ),
    "SGP125A(139.8x3.5)": SteelSection(
        name="SGP125A(139.8x3.5)", weight=11.8, Fy=245, Fu=305, A=1500, d=139.8, tw=3.5, bf=139.8, tf=3.5,
        Ix=5.28e6, Sx=7.56e4, rx=59.4, Iy=5.28e6, Sy=7.56e4, ry=59.4,
        Zx=9.56e4, Zy=9.56e4, J=1.06e7, Cw=0
    ),
    "SGP150A(165.2x4.5)": SteelSection(
        name="SGP150A(165.2x4.5)", weight=17.8, Fy=245, Fu=305, A=2268, d=165.2, tw=4.5, bf=165.2, tf=4.5,
        Ix=1.18e7, Sx=1.43e5, rx=72.1, Iy=1.18e7, Sy=1.43e5, ry=72.1,
        Zx=1.82e5, Zy=1.82e5, J=2.36e7, Cw=0
    ),
    "SGP200A(216.3x4.5)": SteelSection(
        name="SGP200A(216.3x4.5)", weight=23.5, Fy=245, Fu=305, A=2995, d=216.3, tw=4.5, bf=216.3, tf=4.5,
        Ix=3.08e7, Sx=2.85e5, rx=101.4, Iy=3.08e7, Sy=2.85e5, ry=101.4,
        Zx=3.62e5, Zy=3.62e5, J=6.16e7, Cw=0
    ),
}

# ============================================================================
# STEEL PLATE (เหล็กแผ่น)
# ============================================================================
@dataclass
class SteelPlate:
    """Represents a steel plate section."""
    name: str
    thickness: float     # mm
    Fy: float           # MPa
    Fu: float           # MPa
    weight_per_m2: float  # kg/m²


STEEL_PLATES = {
    "t3.2mm": SteelPlate(name="t3.2mm", thickness=3.2, Fy=245, Fu=400, weight_per_m2=25.1),
    "t4.5mm": SteelPlate(name="t4.5mm", thickness=4.5, Fy=245, Fu=400, weight_per_m2=35.3),
    "t6.0mm": SteelPlate(name="t6.0mm", thickness=6.0, Fy=245, Fu=400, weight_per_m2=47.1),
    "t9.0mm": SteelPlate(name="t9.0mm", thickness=9.0, Fy=245, Fu=400, weight_per_m2=70.7),
    "t12mm": SteelPlate(name="t12mm", thickness=12, Fy=245, Fu=400, weight_per_m2=94.2),
    "t16mm": SteelPlate(name="t16mm", thickness=16, Fy=245, Fu=400, weight_per_m2=125.6),
    "t19mm": SteelPlate(name="t19mm", thickness=19, Fy=245, Fu=400, weight_per_m2=149.2),
    "t22mm": SteelPlate(name="t22mm", thickness=22, Fy=245, Fu=400, weight_per_m2=172.7),
    "t25mm": SteelPlate(name="t25mm", thickness=25, Fy=245, Fu=400, weight_per_m2=196.3),
    "t28mm": SteelPlate(name="t28mm", thickness=28, Fy=245, Fu=400, weight_per_m2=219.8),
    "t32mm": SteelPlate(name="t32mm", thickness=32, Fy=245, Fu=400, weight_per_m2=251.2),
}

# ============================================================================
# MATERIAL PROPERTIES
# ============================================================================
@dataclass
class SteelMaterial:
    """Steel material properties per TIS standards."""
    name: str
    grade: str
    Fy: float       # MPa - Yield strength
    Fu: float       # MPa - Ultimate tensile strength
    E: float        # MPa - Modulus of elasticity
    G: float        # MPa - Shear modulus
    nu: float       # Poisson's ratio
    density: float  # kg/m³
    epsilon_u: float  # Ultimate strain


STEEL_MATERIALS = {
    "SS400": SteelMaterial(
        name="SS400", grade="SS400", Fy=245, Fu=400, E=2.0e5, G=7.9e4, nu=0.3, density=7850, epsilon_u=0.21
    ),
    "SM400": SteelMaterial(
        name="SM400", grade="SM400", Fy=245, Fu=400, E=2.0e5, G=7.9e4, nu=0.3, density=7850, epsilon_u=0.21
    ),
    "SM490": SteelMaterial(
        name="SM490", grade="SM490", Fy=325, Fu=490, E=2.0e5, G=7.9e4, nu=0.3, density=7850, epsilon_u=0.18
    ),
    "SM520": SteelMaterial(
        name="SM520", grade="SM520", Fy=365, Fu=520, E=2.0e5, G=7.9e4, nu=0.3, density=7850, epsilon_u=0.16
    ),
    "SS540": SteelMaterial(
        name="SS540", grade="SS540", Fy=375, Fu=540, E=2.0e5, G=7.9e4, nu=0.3, density=7850, epsilon_u=0.16
    ),
}

# ============================================================================
# BOLT PROPERTIES
# ============================================================================
@dataclass
class BoltProperties:
    """Bolt properties per TIS standards."""
    name: str
    grade: str
    diameter: float       # mm
    area: float          # mm²
    Fub: float          # MPa - Ultimate tensile strength
    Fyb: float          # MPa - Yield strength
    shear_strength: float  # MPa - Allowable shear stress
    bearing_strength: float  # MPa - Allowable bearing stress


BOLTS = {
    "M12": BoltProperties(name="M12", grade="A325", diameter=12, area=113, Fub=830, Fyb=660, shear_strength=207, bearing_strength=414),
    "M16": BoltProperties(name="M16", grade="A325", diameter=16, area=201, Fub=830, Fyb=660, shear_strength=207, bearing_strength=414),
    "M20": BoltProperties(name="M20", grade="A325", diameter=20, area=314, Fub=830, Fyb=660, shear_strength=207, bearing_strength=414),
    "M22": BoltProperties(name="M22", grade="A325", diameter=22, area=380, Fub=830, Fyb=660, shear_strength=207, bearing_strength=414),
    "M24": BoltProperties(name="M24", grade="A325", diameter=24, area=452, Fub=830, Fyb=660, shear_strength=207, bearing_strength=414),
    "M27": BoltProperties(name="M27", grade="A325", diameter=27, area=573, Fub=830, Fyb=660, shear_strength=207, bearing_strength=414),
    "M30": BoltProperties(name="M30", grade="A325", diameter=30, area=706, Fub=830, Fyb=660, shear_strength=207, bearing_strength=414),
}

# ============================================================================
# WELD PROPERTIES
# ============================================================================
@dataclass
class WeldProperties:
    """Weld electrode properties per TIS standards."""
    name: str
    electrode: str
    Fu: float           # MPa - Ultimate tensile strength
    shear_strength: float  # MPa - Allowable shear stress


WELDS = {
    "E60XX": WeldProperties(name="E60XX", electrode="E60XX", Fu=414, shear_strength=124),
    "E70XX": WeldProperties(name="E70XX", electrode="E70XX", Fu=483, shear_strength=145),
    "E80XX": WeldProperties(name="E80XX", electrode="E80XX", Fu=552, shear_strength=166),
}
