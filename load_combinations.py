"""
Load Combinations per Thai Engineering Institute (วสท.) Standards
Based on วสท. 011038-22 and related standards for steel structure design
"""
from dataclasses import dataclass
from typing import Dict, List


@dataclass
class LoadCombination:
    """Represents a load combination per Thai standards."""
    name: str
    name_th: str
    factors: Dict[str, float]
    description: str = ""


# ============================================================================
# LOAD COMBINATIONS - ASD (Allowable Stress Design)
# According to วสท. 011038-22 (Based on AISC ASD)
# ============================================================================
LOAD_COMBINATIONS_ASD = [
    LoadCombination(
        name="D",
        name_th="น้ำหนักบรรทุกคงที่",
        factors={"D": 1.0, "L": 0.0, "W": 0.0, "E": 0.0, "S": 0.0, "R": 0.0},
        description="Dead load only"
    ),
    LoadCombination(
        name="D + L",
        name_th="น้ำหนักบรรทุกคงที่ + น้ำหนักบรรทุกจร",
        factors={"D": 1.0, "L": 1.0, "W": 0.0, "E": 0.0, "S": 0.0, "R": 0.0},
        description="Dead + Live load"
    ),
    LoadCombination(
        name="D + W",
        name_th="น้ำหนักบรรทุกคงที่ + น้ำหนักลม",
        factors={"D": 1.0, "L": 0.0, "W": 1.0, "E": 0.0, "S": 0.0, "R": 0.0},
        description="Dead + Wind load"
    ),
    LoadCombination(
        name="D + 0.75L + 0.75W",
        name_th="น้ำหนักบรรทุกคงที่ + 0.75น้ำหนักบรรทุกจร + 0.75น้ำหนักลม",
        factors={"D": 1.0, "L": 0.75, "W": 0.75, "E": 0.0, "S": 0.0, "R": 0.0},
        description="Dead + 0.75Live + 0.75Wind"
    ),
    LoadCombination(
        name="D + E",
        name_th="น้ำหนักบรรทุกคงที่ + น้ำหนักแผ่นดินไหว",
        factors={"D": 1.0, "L": 0.0, "W": 0.0, "E": 1.0, "S": 0.0, "R": 0.0},
        description="Dead + Earthquake load"
    ),
    LoadCombination(
        name="D + 0.75L + 0.75E",
        name_th="น้ำหนักบรรทุกคงที่ + 0.75น้ำหนักบรรทุกจร + 0.75น้ำหนักแผ่นดินไหว",
        factors={"D": 1.0, "L": 0.75, "W": 0.0, "E": 0.75, "S": 0.0, "R": 0.0},
        description="Dead + 0.75Live + 0.75Earthquake"
    ),
    LoadCombination(
        name="0.6D + W",
        name_th="0.6น้ำหนักบรรทุกคงที่ + น้ำหนักลม (ตรวจสอบการพลิกคว่ำ)",
        factors={"D": 0.6, "L": 0.0, "W": 1.0, "E": 0.0, "S": 0.0, "R": 0.0},
        description="0.6Dead + Wind (overturning check)"
    ),
    LoadCombination(
        name="0.6D + E",
        name_th="0.6น้ำหนักบรรทุกคงที่ + น้ำหนักแผ่นดินไหว (ตรวจสอบการพลิกคว่ำ)",
        factors={"D": 0.6, "L": 0.0, "W": 0.0, "E": 1.0, "S": 0.0, "R": 0.0},
        description="0.6Dead + Earthquake (overturning check)"
    ),
    LoadCombination(
        name="D + S",
        name_th="น้ำหนักบรรทุกคงที่ + น้ำหนักหิมะ",
        factors={"D": 1.0, "L": 0.0, "W": 0.0, "E": 0.0, "S": 1.0, "R": 0.0},
        description="Dead + Snow load"
    ),
    LoadCombination(
        name="D + R",
        name_th="น้ำหนักบรรทุกคงที่ + น้ำหนักฝน",
        factors={"D": 1.0, "L": 0.0, "W": 0.0, "E": 0.0, "S": 0.0, "R": 1.0},
        description="Dead + Rain load"
    ),
]

# ============================================================================
# LOAD COMBINATIONS - LRFD (Load and Resistance Factor Design)
# According to วสท. 011038-22 (Based on AISC LRFD)
# ============================================================================
LOAD_COMBINATIONS_LRFD = [
    LoadCombination(
        name="1.4D",
        name_th="1.4น้ำหนักบรรทุกคงที่",
        factors={"D": 1.4, "L": 0.0, "W": 0.0, "E": 0.0, "S": 0.0, "R": 0.0},
        description="1.4Dead load"
    ),
    LoadCombination(
        name="1.2D + 1.6L + 0.5S",
        name_th="1.2น้ำหนักบรรทุกคงที่ + 1.6น้ำหนักบรรทุกจร + 0.5น้ำหนักหิมะ",
        factors={"D": 1.2, "L": 1.6, "W": 0.0, "E": 0.0, "S": 0.5, "R": 0.0},
        description="1.2Dead + 1.6Live + 0.5Snow"
    ),
    LoadCombination(
        name="1.2D + 1.6S + 0.5L",
        name_th="1.2น้ำหนักบรรทุกคงที่ + 1.6น้ำหนักหิมะ + 0.5น้ำหนักบรรทุกจร",
        factors={"D": 1.2, "L": 0.5, "W": 0.0, "E": 0.0, "S": 1.6, "R": 0.0},
        description="1.2Dead + 1.6Snow + 0.5Live"
    ),
    LoadCombination(
        name="1.2D + 1.6W + 0.5L + 0.5S",
        name_th="1.2น้ำหนักบรรทุกคงที่ + 1.6น้ำหนักลม + 0.5น้ำหนักบรรทุกจร + 0.5น้ำหนักหิมะ",
        factors={"D": 1.2, "L": 0.5, "W": 1.6, "E": 0.0, "S": 0.5, "R": 0.0},
        description="1.2Dead + 1.6Wind + 0.5Live + 0.5Snow"
    ),
    LoadCombination(
        name="1.2D + 1.0E + 0.5L + 0.2S",
        name_th="1.2น้ำหนักบรรทุกคงที่ + 1.0น้ำหนักแผ่นดินไหว + 0.5น้ำหนักบรรทุกจร + 0.2น้ำหนักหิมะ",
        factors={"D": 1.2, "L": 0.5, "W": 0.0, "E": 1.0, "S": 0.2, "R": 0.0},
        description="1.2Dead + 1.0Earthquake + 0.5Live + 0.2Snow"
    ),
    LoadCombination(
        name="0.9D + 1.6W",
        name_th="0.9น้ำหนักบรรทุกคงที่ + 1.6น้ำหนักลม (ตรวจสอบการพลิกคว่ำ)",
        factors={"D": 0.9, "L": 0.0, "W": 1.6, "E": 0.0, "S": 0.0, "R": 0.0},
        description="0.9Dead + 1.6Wind (overturning check)"
    ),
    LoadCombination(
        name="0.9D + 1.0E",
        name_th="0.9น้ำหนักบรรทุกคงที่ + 1.0น้ำหนักแผ่นดินไหว (ตรวจสอบการพลิกคว่ำ)",
        factors={"D": 0.9, "L": 0.0, "W": 0.0, "E": 1.0, "S": 0.0, "R": 0.0},
        description="0.9Dead + 1.0Earthquake (overturning check)"
    ),
    LoadCombination(
        name="1.2D + 1.6R",
        name_th="1.2น้ำหนักบรรทุกคงที่ + 1.6น้ำหนักฝน",
        factors={"D": 1.2, "L": 0.0, "W": 0.0, "E": 0.0, "S": 0.0, "R": 1.6},
        description="1.2Dead + 1.6Rain load"
    ),
]

# ============================================================================
# SERVICEABILITY LOAD COMBINATIONS (For deflection checks)
# ============================================================================
SERVICEABILITY_COMBINATIONS = [
    LoadCombination(
        name="L (Live Load Only)",
        name_th="น้ำหนักบรรทุกจรอย่างเดียว (ตรวจสอบการแอ่นตัว)",
        factors={"D": 0.0, "L": 1.0, "W": 0.0, "E": 0.0, "S": 0.0, "R": 0.0},
        description="Live load only for deflection check"
    ),
    LoadCombination(
        name="D + L",
        name_th="น้ำหนักบรรทุกคงที่ + น้ำหนักบรรทุกจร (ตรวจสอบการแอ่นตัวรวม)",
        factors={"D": 1.0, "L": 1.0, "W": 0.0, "E": 0.0, "S": 0.0, "R": 0.0},
        description="Dead + Live for total deflection"
    ),
    LoadCombination(
        name="D + W",
        name_th="น้ำหนักบรรทุกคงที่ + น้ำหนักลม (ตรวจสอบการแอ่นตัวจากลม)",
        factors={"D": 1.0, "L": 0.0, "W": 1.0, "E": 0.0, "S": 0.0, "R": 0.0},
        description="Dead + Wind for deflection"
    ),
]

# ============================================================================
# LOAD TYPES DEFINITION
# ============================================================================
LOAD_TYPES = {
    "D": {"name": "Dead Load", "name_th": "น้ำหนักบรรทุกคงที่", "unit": "kN/m² or kN"},
    "L": {"name": "Live Load", "name_th": "น้ำหนักบรรทุกจร", "unit": "kN/m² or kN"},
    "W": {"name": "Wind Load", "name_th": "น้ำหนักลม", "unit": "kN/m² or kN"},
    "E": {"name": "Earthquake Load", "name_th": "น้ำหนักแผ่นดินไหว", "unit": "kN/m² or kN"},
    "S": {"name": "Snow Load", "name_th": "น้ำหนักหิมะ", "unit": "kN/m²"},
    "R": {"name": "Rain Load", "name_th": "น้ำหนักฝน", "unit": "kN/m²"},
}

# ============================================================================
# DEFLECTION LIMITS per วสท. 011038-22
# ============================================================================
DEFLECTION_LIMITS = {
    "beam_live_load": {
        "name_th": "คาน - น้ำหนักบรรทุกจร",
        "limit_ratio": 360,  # L/360
        "description": "Beam deflection under live load only"
    },
    "beam_total_load": {
        "name_th": "คาน - น้ำหนักรวม",
        "limit_ratio": 240,  # L/240
        "description": "Beam deflection under total load"
    },
    "purlin_live_load": {
        "name_th": "แป - น้ำหนักบรรทุกจร",
        "limit_ratio": 240,  # L/240
        "description": "Purlin deflection under live load only"
    },
    "purlin_total_load": {
        "name_th": "แป - น้ำหนักรวม",
        "limit_ratio": 180,  # L/180
        "description": "Purlin deflection under total load"
    },
    "column_top": {
        "name_th": "เสา - ยอดเสา",
        "limit_ratio": 300,  # H/300
        "description": "Column top deflection under wind/earthquake"
    },
    "cantilever_live_load": {
        "name_th": "คานยื่น - น้ำหนักบรรทุกจร",
        "limit_ratio": 180,  # L/180
        "description": "Cantilever deflection under live load only"
    },
    "cantilever_total_load": {
        "name_th": "คานยื่น - น้ำหนักรวม",
        "limit_ratio": 120,  # L/120
        "description": "Cantilever deflection under total load"
    },
    "wall_girt_live_load": {
        "name_th": "แปผนัง - น้ำหนักบรรทุกจร",
        "limit_ratio": 180,  # L/180
        "description": "Wall girt deflection under live load only"
    },
    "wall_girt_total_load": {
        "name_th": "แปผนัง - น้ำหนักรวม",
        "limit_ratio": 120,  # L/120
        "description": "Wall girt deflection under total load"
    },
}

# ============================================================================
# SAFETY FACTORS per วสท. 011038-22
# ============================================================================
SAFETY_FACTORS = {
    "tension_yielding": {
        "name_th": "แรงดึง - การคราก",
        "omega": 1.67,  # ASD safety factor
        "phi": 0.90,    # LRFD resistance factor
    },
    "tension_rupture": {
        "name_th": "แรงดึง - การขาด",
        "omega": 2.00,
        "phi": 0.75,
    },
    "compression": {
        "name_th": "แรงอัด",
        "omega": 1.67,
        "phi": 0.90,
    },
    "bending": {
        "name_th": "โมเมนต์ดัด",
        "omega": 1.67,
        "phi": 0.90,
    },
    "shear": {
        "name_th": "แรงเฉือน",
        "omega": 1.50,
        "phi": 0.90,
    },
    "bolt_shear": {
        "name_th": "สลักเกลียว - แรงเฉือน",
        "omega": 2.00,
        "phi": 0.75,
    },
    "bolt_bearing": {
        "name_th": "สลักเกลียว - แรงตปะ",
        "omega": 2.00,
        "phi": 0.75,
    },
    "weld_shear": {
        "name_th": "รอยเชื่อม - แรงเฉือน",
        "omega": 2.00,
        "phi": 0.75,
    },
}

# ============================================================================
# EFFECTIVE LENGTH FACTOR (K) for columns
# ============================================================================
EFFECTIVE_LENGTH_FACTORS = {
    "fixed-fixed": {"K": 0.65, "name_th": "ยึดแน่น-ยึดแน่น", "description": "Both ends fixed"},
    "fixed-pinned": {"K": 0.80, "name_th": "ยึดแน่น-หมุด", "description": "One end fixed, one end pinned"},
    "pinned-pinned": {"K": 1.00, "name_th": "หมุด-หมุด", "description": "Both ends pinned (typical)"},
    "fixed-free": {"K": 2.10, "name_th": "ยึดแน่น-อิสระ", "description": "One end fixed, one end free (cantilever)"},
    "fixed-roller": {"K": 1.00, "name_th": "ยึดแน่น-ลูกกลิ้ง", "description": "One end fixed, one end roller"},
}

# ============================================================================
# WIND LOAD PARAMETERS per Thai Standards
# ============================================================================
WIND_LOAD_PARAMS = {
    "basic_wind_speed": {
        "Bangkok": 30.0,  # m/s
        "Chiang_Mai": 25.0,
        "Phuket": 35.0,
        "Pattaya": 32.0,
        "default": 30.0,
    },
    "exposure_categories": {
        "B": {
            "name_th": "พื้นที่เมืองและชานเมือง",
            "description": "Urban and suburban areas, wooded areas",
            "z_min": 4.5,
            "alpha": 7.0,
            "z_g": 365.0,
        },
        "C": {
            "name_th": "พื้นที่โล่ง",
            "description": "Open terrain with scattered obstructions",
            "z_min": 4.5,
            "alpha": 9.5,
            "z_g": 275.0,
        },
        "D": {
            "name_th": "พื้นที่ริมฝั่งทะเล",
            "description": "Flat, unobstructed areas exposed to wind from large bodies of water",
            "z_min": 4.5,
            "alpha": 11.5,
            "z_g": 215.0,
        },
    },
}

# ============================================================================
# SEISMIC LOAD PARAMETERS per Thai Standards (มยผ. 1302-61)
# ============================================================================
SEISMIC_PARAMS = {
    "Bangkok": {
        "PGA": 0.11,  # Peak ground acceleration (g)
        "Ss": 0.15,   # Short period spectral acceleration
        "S1": 0.06,   # 1-second period spectral acceleration
        "site_class": "D",  # Default site class
    },
    "Chiang_Mai": {
        "PGA": 0.18,
        "Ss": 0.25,
        "S1": 0.10,
        "site_class": "C",
    },
    "Phuket": {
        "PGA": 0.08,
        "Ss": 0.10,
        "S1": 0.04,
        "site_class": "D",
    },
    "default": {
        "PGA": 0.11,
        "Ss": 0.15,
        "S1": 0.06,
        "site_class": "D",
    },
}
