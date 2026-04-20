# Steel Structure Design Application (โปรแกรมออกแบบโครงสร้างเหล็ก)

A comprehensive steel structure design application based on **Thai Engineering Institute Standards (วสท. 011038-22)** and **Thai Industrial Standards (มอก.)**.

## Thai Standards Compliance (การปฏิบัติตามมาตรฐานไทย)

### Material Standards (มาตรฐานวัสดุ)
| Standard | Description | Implementation |
|----------|-------------|----------------|
| **มอก. 1227-2558** | Hot-rolled structural steel (H-beams, I-beams, angles) | ✅ Full compliance with SS400, SM400, SM490, SM520, SS540 grades |
| **มอก. 107-2533** | Structural hollow sections (pipes, RHS, SHS) | ✅ Full compliance with STKR400 grade |

### Design Standards (มาตรฐานการออกแบบ)
| Standard | Description | Implementation |
|----------|-------------|----------------|
| **วสท. 011038-22** | Structural Steel Buildings Design | ✅ ASD method fully implemented |
| **วสท. 011038-22** | LRFD method | ⚠️ Code exists, not wired to GUI yet |

### Load Standards (มาตรฐานน้ำหนักบรรทุก)
| Standard | Description | Implementation |
|----------|-------------|----------------|
| **มยผ. 1311-50** | Wind load calculations | ⚠️ Currently using ASCE 7 approximation - **Needs update** |
| **มยผ. 1301/1302-61** | Earthquake resistance | ⚠️ Parameters defined, **design procedures not implemented** |

### Material Properties (คุณสมบัติวัสดุ)

| Grade | Fy (MPa) | Fu (MPa) | Application | Standard |
|-------|----------|----------|-------------|----------|
| SS400 | 245 | 400 | General structural steel | มอก. 1227-2558 |
| SM400 | 245 | 400 | Welded structural steel | มอก. 1227-2558 |
| SM490 | 325 | 490 | Higher strength structural steel | มอก. 1227-2558 |
| SM520 | 365 | 520 | High strength structural steel | มอก. 1227-2558 |
| SS540 | 375 | 540 | High strength structural steel | มอก. 1227-2558 |
| STKR400 | 245 | 290 | Hollow sections (pipes, RHS) | มอก. 107-2533 |

### Section Tolerances (ค่าเผื่อการผลิต)

Per มอก. standards, manufacturing tolerances are documented for:
- **H/I-Beams (มอก. 1227-2558)**: Depth ±1.5%, Width ±2%, Thickness ±0.3-0.4mm, Weight ±2.5-3%
- **Angles (มอก. 1227-2558)**: Leg ±1.5%, Thickness ±0.3-0.5mm, Weight ±4%
- **Hollow Sections (มอก. 107-2533)**: OD ±0.75%, Wall ±12.5%, Weight ±3-3.5%

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
pip install -r requirements.txt
```

This will install:
- `matplotlib` - For plotting and visualizations
- `reportlab` - For PDF report generation with Thai fonts
- `openpyxl` - For Excel export of calculation sheets

### Running the Application

```bash
python main_app.py
```

## Export & Reporting

### PDF Reports
The application can generate professional PDF reports with:
- ✅ Thai font support (Tahoma, Arial Unicode)
- ✅ Project metadata (project name, engineer, checker, date)
- ✅ Section properties and material specs
- ✅ Wind load calculations (for purlins)
- ✅ Load combination checks
- ✅ Bending stress, shear stress, and deflection verification
- ✅ **Bending Moment and Shear Force Diagrams** (visual charts)
- ✅ Pass/Fail summary with interaction ratios
- ✅ Professional formatting with color-coded results

### Excel Export
Calculation data can be exported to Excel with:
- ✅ Multiple worksheets (Summary, Load Combinations, Details)
- ✅ Formatted tables with pass/fail highlighting
- ✅ All input parameters and results
- ✅ Ready for further analysis or submission

### How to Export
1. Perform a design calculation (click "คำนวณ")
2. Click "Export PDF รายการคำนวณ" or "Export Excel" button
3. Fill in project metadata (optional, can use defaults)
4. Choose save location and filename
5. Open the generated file

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
- [x] PDF report generation with Thai fonts
- [x] Excel export for calculation sheets
- [x] Bending moment and shear force diagrams in PDF
- [ ] 3D visualization of structures
- [ ] LRFD design method
- [ ] Seismic design per มยผ. 1302-61
- [ ] Steel grade optimization
- [ ] Connection detail drawings
- [ ] Batch report generation for multiple members
- [ ] Multi-language support (Thai/English toggle)

## Disclaimer

This application is designed as an **engineering aid** for preliminary design. All results should be verified by a licensed structural engineer familiar with Thai standards and local requirements.

The wind load calculations use simplified methods. For critical structures, refer to the full provisions of **วสท. 011038-22** and related standards.

## References

### Thai Standards (มาตรฐานไทย)
1. **สำนักงานมาตรฐานผลิตภัณฑ์อุตสาหกรรม (สมอ.)**, **มอก. 1227-2558**: เหล็กรูปพรรณรีดร้อนรูปตัวเอช สำหรับงานโครงสร้าง, กรมอุตสาหกรรมพื้นฐานและการเหมืองแร่, 2558
2. **สำนักงานมาตรฐานผลิตภัณฑ์อุตสาหกรรม (สมอ.)**, **มอก. 107-2533**: เหล็กโครงสร้างรูปพรรณกลวง, กรมอุตสาหกรรมพื้นฐานและการเหมืองแร่, 2533
3. **วิศวกรรมสถานแห่งประเทศไทย ในพระบรมราชูปถัมภ์ (วสท.)**, **มาตรฐานสำหรับการออกแบบอาคารโครงสร้างเหล็กรูปพรรณ พ.ศ. 2565** (วสท. 011038-22)
4. **กรมโยธาธิการและผังเมือง**, **มยผ. 1311-50**: มาตรฐานการออกแบบอาคารรับแรงลม, 2550
5. **กรมโยธาธิการและผังเมือง**, **มยผ. 1301-61**: มาตรฐานการออกแบบอาคารรับแรงแผ่นดินไหว, 2561
6. **กรมโยธาธิการและผังเมือง**, **มยผ. 1302-61**: มาตรฐานการออกแบบอาคารต้านทานแรงแผ่นดินไหว, 2561

### International Standards (มาตรฐานสากล)
7. AISC 360-16, Specification for Structural Steel Buildings
8. ASCE 7-16, Minimum Design Loads for Buildings and Other Structures
9. JIS G 3101:2015, Rolled steels for general structure (Reference for SS/SM grades)

### Building Control Law (กฎหมายควบคุมอาคาร)
10. **พระราชบัญญัติควบคุมอาคาร พ.ศ. 2522** และที่แก้ไขเพิ่มเติม
11. **กฎกระทรวงฉบับที่ 6 (พ.ศ. 2527)** ออกตามความในพระราชบัญญัติควบคุมอาคาร พ.ศ. 2522: เรื่องน้ำหนักบรรทุก

## License

This project is for educational and professional use.

## Contact

For questions or suggestions, please contact the developer.

---

**พัฒนาด้วย ❤️ สำหรับวิศวกรโครงสร้างไทย**
*Developed with ❤️ for Thai Structural Engineers*
