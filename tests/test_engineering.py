"""
Engineering Logic Unit Tests
Tests calculations for Beam, Column, Truss, and Footing (ASD/LRFD)
"""
import unittest
import sys
import os

# Add root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from steel_sections import H_BEAMS, EQUAL_ANGLES
from beam_design import BeamDesign, BeamLoad
from column_design import ColumnDesign, ColumnLoad
from truss_design import TrussDesign, TrussLoad
from footing_design import FootingDesign, FootingLoad

class TestBeamDesign(unittest.TestCase):
    def setUp(self):
        self.section = H_BEAMS["H200x200x8x12"]
        self.loads = BeamLoad(dead_load=5.0, live_load=10.0)

    def test_beam_asd_vs_lrfd(self):
        # ASD calculation
        asd_design = BeamDesign(self.section, span=6.0, method="ASD")
        asd_res = asd_design.check_beam(self.loads)
        
        # LRFD calculation
        lrfd_design = BeamDesign(self.section, span=6.0, method="LRFD")
        lrfd_res = lrfd_design.check_beam(self.loads)
        
        # LRFD factored moment should be higher than ASD service moment
        self.assertGreater(lrfd_res.max_moment, asd_res.max_moment)
        self.assertTrue(hasattr(lrfd_res, 'phi_Mn_kNm'))

class TestColumnDesign(unittest.TestCase):
    def setUp(self):
        self.section = H_BEAMS["H250x250x9x14"]
        self.loads = ColumnLoad(axial_load_D=200.0, axial_load_L=300.0)

    def test_column_slenderness(self):
        design = ColumnDesign(self.section, height=4.0)
        res = design.check_combined_loading(self.loads)
        # KL/r for H250x250 at 4m should be well below 200
        self.assertLess(res.critical_slenderness, 200)
        self.assertTrue(res.is_ok)

class TestTrussDesign(unittest.TestCase):
    def test_tension_vs_compression(self):
        sec = EQUAL_ANGLES["L40x40x4"]
        # Tension
        t_design = TrussDesign(sec, length=2.0, method="LRFD")
        t_res = t_design.check_member(TrussLoad(force_D=50.0))
        self.assertEqual(t_res.member_type, "Tension")
        
        # Compression
        c_design = TrussDesign(sec, length=2.0, method="LRFD")
        c_res = c_design.check_member(TrussLoad(force_D=-50.0))
        self.assertEqual(c_res.member_type, "Compression")
        # Tension capacity is usually higher than compression for same section (no buckling)
        self.assertGreater(t_res.allowable_force, c_res.allowable_force)

class TestFootingDesign(unittest.TestCase):
    def test_footing_bearing(self):
        # Large footing, light load -> Should pass
        fd = FootingDesign(width=2.0, length=2.0, thickness=0.4, allowable_bearing_kPa=150.0)
        res = fd.check_footing(FootingLoad(axial_load_D=100.0, axial_load_L=50.0))
        self.assertTrue(res.is_ok)
        self.assertLess(res.bearing_ratio, 1.0)

        # Small footing, heavy load -> Should fail
        fd_small = FootingDesign(width=0.5, length=0.5, thickness=0.2, allowable_bearing_kPa=50.0)
        res_fail = fd_small.check_footing(FootingLoad(axial_load_D=500.0))
        self.assertFalse(res_fail.is_ok)

if __name__ == '__main__':
    unittest.main()
