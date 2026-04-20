"""
PDF Report Generation Tests
Tests report_generator.py functions
"""
import unittest
import sys
import os
import io

# Add root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from report_generator import (
    generate_beam_report, generate_column_report,
    generate_truss_report, generate_footing_report,
    ProjectInfo
)
from beam_design import BeamDesign, BeamLoad
from truss_design import TrussDesign, TrussLoad
from footing_design import FootingDesign, FootingLoad
from steel_sections import H_BEAMS, EQUAL_ANGLES

class TestPDFReports(unittest.TestCase):
    def setUp(self):
        self.project = ProjectInfo(project_name="Test Project", engineer="Tester")

    def test_truss_pdf(self):
        sec = EQUAL_ANGLES["L40x40x4"]
        td = TrussDesign(sec, length=3.0, method="LRFD")
        res = td.check_member(TrussLoad(force_D=20.0))
        
        pdf_bytes = generate_truss_report(res, "L50x50x4", 3.0, self.project)
        self.assertIsInstance(pdf_bytes, bytes)
        self.assertGreater(len(pdf_bytes), 1000) # Should be a non-empty PDF

    def test_footing_pdf(self):
        fd = FootingDesign(width=1.5, length=1.5, thickness=0.3, allowable_bearing_kPa=150.0)
        res = fd.check_footing(FootingLoad(axial_load_D=100.0))
        
        pdf_bytes = generate_footing_report(res, 1.5, 1.5, 0.3, self.project)
        self.assertIsInstance(pdf_bytes, bytes)
        self.assertGreater(len(pdf_bytes), 1000)

if __name__ == '__main__':
    unittest.main()
