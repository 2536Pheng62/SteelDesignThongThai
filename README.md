# Steel Structure Design Application (โปรแกรมออกแบบโครงสร้างเหล็ก)

A comprehensive steel structure design application based on **Thai Engineering Institute Standards (วสท. 011038-22)** and **Thai Industrial Standards (TIS)**.

## Features

### 🏗️ Design Modules

The application includes multiple design modules for different steel structural components:

| Module | Thai Name | Description |
|--------|-----------|-------------|
| **Purlin** | แปหลังคา | Roof purlin design with wind load calculation |
| **Beam** | คาน | Steel beam design (H-Beam, I-Beam) |
| **Column** | เสา | Steel column design with combined loading |
| **Bolted Connection** | รอยต่อสลักเกลียว | Bolted connection design |
| **Welded Connection** | รอยเชื่อม | Welded connection design |
| **Base Plate** | แผ่นฐานเสา | Column base plate design |

### 📐 Thai Standards Compliance

- **วสท. 011038-22**: Standard for Structural Steel Buildings
- **TIS 1227**: Hot-rolled H and I sections
- **TIS 1228**: Cold-formed C sections
- **TIS 107**: Steel pipes/tubes
- **มยผ. 1302-61**: Seismic load standards

### 📊 Steel Section Database

Comprehensive database of Thai standard steel sections:

- **C-Channel** (เหล็กรูปตัวซี): 10 sections
- **H-Beam** (เหล็กเอชบีม): 9 sections
- **I-Beam** (เหล็กไอบีม): 8 sections
- **Equal Angle** (เหล็กฉากเท่า): 11 sections
- **Unequal Angle** (เหล็กฉากไม่เท่า): 7 sections
- **Steel Pipe** (เหล็กท่อกลม): 12 sections
- **Steel Plate** (เหล็กแผ่น): 11 thicknesses

### 🔄 Load Combinations

Implements Thai standard load combinations per วสท. 011038-22:

#### ASD (Allowable Stress Design)
- D (Dead load only)
- D + L (Dead + Live)
- D + W (Dead + Wind)
- D + 0.75L + 0.75W
- D + E (Dead + Earthquake)
- 0.6D + W (Overturning check)
- 0.6D + E (Overturning check)

#### Serviceability (Deflection Checks)
- Live Load Only (L/240, L/360)
- Total Load (L/180, L/240)

### ✅ Design Checks

Each module performs comprehensive design checks:

#### Beam Design
- ✅ Bending stress (fb ≤ Fb)
- ✅ Shear stress (fv ≤ Fv)
- ✅ Deflection (δ ≤ δ_allowable)
- ✅ Lateral-torsional buckling consideration
- ✅ Compact/non-compact section classification

#### Column Design
- ✅ Axial compression capacity
- ✅ Slenderness ratio (KL/r ≤ 200)
- ✅ Combined axial + bending interaction
- ✅ Effective length factors (K)

#### Connection Design
- ✅ Bolt shear capacity
- ✅ Bolt bearing capacity
- ✅ Weld shear capacity
- ✅ Edge distance requirements

#### Base Plate Design
- ✅ Concrete bearing pressure
- ✅ Base plate thickness
- ✅ Eccentric loading consideration

## Installation

### Prerequisites

- Python 3.8 or higher
- Required packages:

```bash
pip install matplotlib reportlab
```

### Running the Application

```bash
python main_app.py
```

## Usage Guide

### 1. Purlin Design Tab
- Select C-Channel section
- Enter span, spacing, roof slope
- Enter dead load, live load
- Enter wind parameters (speed, height, exposure)
- Click "คำนวณ" to check design
- Click "ค้นหาหน้าตัดประหยัดสุด" to find optimal section

### 2. Beam Design Tab
- Select H-Beam or I-Beam section
- Enter beam span and type (simply supported/cantilever)
- Select lateral bracing condition
- Enter distributed and point loads
- Click "คำนวณคาน" to check design

### 3. Column Design Tab
- Select column section (H-Beam, I-Beam, or Pipe)
- Enter column height and effective length factors (Kx, Ky)
- Enter axial loads and moments
- Click "คำนวณเสา" to check design

### 4. Connection Design Tab

#### Bolted Connection
- Select bolt size and grade
- Enter number of bolts and plate thickness
- Enter shear loads
- Click "คำนวณรอยต่อสลักเกลียว"

#### Welded Connection
- Select electrode type (E60XX, E70XX, E80XX)
- Enter weld size and length
- Enter shear loads
- Click "คำนวณรอยเชื่อม"

### 5. Base Plate Design Tab
- Select column section
- Enter base plate dimensions (B x N x tp)
- Enter concrete strength (f'c)
- Enter axial loads and moments
- Click "คำนวณแผ่นฐาน"

## Design Standards Reference

### Material Properties

| Grade | Fy (MPa) | Fu (MPa) | Application |
|-------|----------|----------|-------------|
| SS400 | 245 | 400 | General structural |
| SM400 | 245 | 400 | Structural (welded) |
| SM490 | 325 | 490 | Higher strength |
| SM520 | 365 | 520 | High strength |

### Safety Factors (ASD)

| Check Type | Safety Factor (ω) |
|------------|-------------------|
| Tension - Yielding | 1.67 |
| Tension - Rupture | 2.00 |
| Compression | 1.67 |
| Bending | 1.67 |
| Shear | 1.50 |
| Bolt Shear | 2.00 |
| Bolt Bearing | 2.00 |
| Weld Shear | 2.00 |

### Deflection Limits

| Member | Load Type | Limit |
|--------|-----------|-------|
| Beam | Live Load | L/360 |
| Beam | Total Load | L/240 |
| Purlin | Live Load | L/240 |
| Purlin | Total Load | L/180 |
| Column Top | Wind/Earthquake | H/300 |
| Cantilever | Live Load | L/180 |
| Cantilever | Total Load | L/120 |

### Wind Load Parameters

| City | Basic Wind Speed (m/s) |
|------|------------------------|
| Bangkok | 30.0 |
| Chiang Mai | 25.0 |
| Phuket | 35.0 |
| Pattaya | 32.0 |

### Exposure Categories

| Category | Description |
|----------|-------------|
| B | Urban/suburban, wooded areas |
| C | Open terrain with scattered obstructions |
| D | Flat, unobstructed coastal areas |

## File Structure

```
Purlin_Disign/
├── main_app.py              # Main application with GUI
├── purlin.py                # Purlin design module (existing)
├── steel_sections.py        # Steel section database
├── load_combinations.py     # Load combinations per Thai standards
├── beam_design.py           # Beam design module
├── column_design.py         # Column design module
├── connection_design.py     # Bolted & welded connection design
├── baseplate_design.py      # Base plate design module
└── README.md                # This file
```

## Future Enhancements

- [ ] Truss design module (โครงถัก)
- [ ] Footing/Foundation design (ฐานราก)
- [ ] PDF report generation with Thai fonts
- [ ] 3D visualization of structures
- [ ] LRFD design method
- [ ] Seismic design per มยผ. 1302-61
- [ ] Steel grade optimization
- [ ] Connection detail drawings
- [ ] Export to Excel calculation sheets
- [ ] Multi-language support (Thai/English toggle)

## Disclaimer

This application is designed as an **engineering aid** for preliminary design. All results should be verified by a licensed structural engineer familiar with Thai standards and local requirements.

The wind load calculations use simplified methods. For critical structures, refer to the full provisions of **วสท. 011038-22** and related standards.

## References

1. วิศวกรรมสถานแห่งประเทศไทย ในพระบรมราชูปถัมภ์ (วสท.), **มาตรฐานสำหรับการออกแบบอาคารโครงสร้างเหล็กรูปพรรณ พ.ศ. 2565**
2. กรมพัฒนาพลังงานทดแทนและอนุรักษ์พลังงาน, **มาตรฐานการออกแบบอาคารประหยัดพลังงาน**
3. AISC 360-16, Specification for Structural Steel Buildings
4. ASCE 7-16, Minimum Design Loads for Buildings and Other Structures
5. TIS 1227, TIS 1228, TIS 107 - Thai Industrial Standards for steel sections

## License

This project is for educational and professional use.

## Contact

For questions or suggestions, please contact the developer.

---

**พัฒนาด้วย ❤️ สำหรับวิศวกรโครงสร้างไทย**
*Developed with ❤️ for Thai Structural Engineers*
