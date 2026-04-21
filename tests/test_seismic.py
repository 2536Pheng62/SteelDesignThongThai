"""
Seismic Design Unit Tests
Verifies ELF procedure per มยผ. 1302-61.
"""
import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from seismic_design import (
    get_Fa, get_Fv,
    calc_period_approximate,
    calc_base_shear_elf,
    distribute_story_forces,
    FA_TABLE, FV_TABLE,
    SEISMIC_SYSTEM_FACTORS,
)


class TestSiteCoefficients(unittest.TestCase):
    def test_Fa_tabulated_points(self):
        # Site class D, Ss = 0.25 -> 1.6
        self.assertAlmostEqual(get_Fa("D", 0.25), 1.6, places=3)
        # Site class B is always 1.0
        self.assertAlmostEqual(get_Fa("B", 0.50), 1.0, places=3)

    def test_Fa_interpolates(self):
        # Site class D between 0.25 and 0.50 -> interpolates between 1.6 and 1.4
        fa = get_Fa("D", 0.375)
        self.assertAlmostEqual(fa, 1.5, places=3)

    def test_Fa_clamps_above_and_below(self):
        # Above max Ss
        self.assertAlmostEqual(get_Fa("D", 2.0), 1.0, places=3)
        # Below min Ss
        self.assertAlmostEqual(get_Fa("D", 0.0), 1.6, places=3)

    def test_Fv_tabulated_points(self):
        self.assertAlmostEqual(get_Fv("D", 0.10), 2.4, places=3)
        self.assertAlmostEqual(get_Fv("C", 0.30), 1.5, places=3)

    def test_unknown_site_class_defaults_to_D(self):
        # "Z" -> falls back to "D"
        self.assertAlmostEqual(get_Fa("Z", 0.25), 1.6, places=3)


class TestApproxPeriod(unittest.TestCase):
    def test_steel_mrf_period(self):
        # Ta = 0.0724 * 12^0.8 ~= 0.529s
        T = calc_period_approximate("steel_mrf", 12.0)
        self.assertAlmostEqual(T, 0.529, places=2)

    def test_steel_braced_period(self):
        # Ta = 0.0488 * 20^0.75 ~= 0.462s
        T = calc_period_approximate("steel_braced", 20.0)
        self.assertAlmostEqual(T, 0.462, places=2)

    def test_unknown_type_falls_back_to_other(self):
        T1 = calc_period_approximate("mystery", 15.0)
        T2 = calc_period_approximate("other", 15.0)
        self.assertAlmostEqual(T1, T2, places=6)


class TestELFBaseShear(unittest.TestCase):
    def test_basic_base_shear_chiangmai_like(self):
        """Chiang Mai-like parameters, 3-story SMF, W=5000 kN."""
        res = calc_base_shear_elf(
            Ss=0.25, S1=0.10,
            site_class="C",
            risk_category="II",
            structure_type="steel_mrf",
            seismic_system="steel_smf",
            height_m=12.0,
            total_weight_kN=5000.0,
        )
        # SDS = (2/3)*1.2*0.25 = 0.20
        self.assertAlmostEqual(res.SDS, 0.20, places=3)
        # SD1 = (2/3)*1.7*0.10 ~= 0.1133
        self.assertAlmostEqual(res.SD1, 0.1133, places=3)
        # Cs upper = 0.20/(8/1) = 0.025
        self.assertAlmostEqual(res.details["Cs_upper"], 0.025, places=4)
        # Cs min >= 0.01
        self.assertGreaterEqual(res.details["Cs_min"], 0.01)
        # Base shear reasonable
        self.assertGreater(res.V, 0)
        self.assertLess(res.V, 5000.0)  # V < W for low-seismic region

    def test_importance_factor_applied(self):
        """Risk Category IV (Ie=1.5) should increase base shear."""
        kw = dict(
            Ss=0.5, S1=0.2, site_class="D",
            structure_type="steel_mrf", seismic_system="steel_smf",
            height_m=10.0, total_weight_kN=1000.0,
        )
        r_ii = calc_base_shear_elf(risk_category="II", **kw)
        r_iv = calc_base_shear_elf(risk_category="IV", **kw)
        self.assertGreater(r_iv.V, r_ii.V)

    def test_higher_R_reduces_base_shear(self):
        """Larger R (more ductile system) should reduce V."""
        kw = dict(
            Ss=0.5, S1=0.2, site_class="D", risk_category="II",
            structure_type="steel_mrf", height_m=10.0, total_weight_kN=1000.0,
        )
        r_smf = calc_base_shear_elf(seismic_system="steel_smf", **kw)   # R=8.0
        r_omf = calc_base_shear_elf(seismic_system="steel_omf", **kw)   # R=3.5
        self.assertGreater(r_omf.V, r_smf.V)

    def test_cs_minimum_floor_enforced(self):
        """For very small S1/Ss, Cs should not drop below floor 0.01."""
        res = calc_base_shear_elf(
            Ss=0.05, S1=0.02, site_class="A",
            risk_category="II",
            structure_type="steel_mrf", seismic_system="steel_smf",
            height_m=10.0, total_weight_kN=1000.0,
        )
        self.assertGreaterEqual(res.Cs, 0.01)


class TestStoryDistribution(unittest.TestCase):
    def test_forces_sum_to_base_shear(self):
        V = 125.0
        rows = distribute_story_forces(
            V=V,
            story_weights=[1700, 1700, 1600],
            story_heights=[4, 8, 12],
            T=0.5,
        )
        total = sum(r["Fx_kN"] for r in rows)
        self.assertAlmostEqual(total, V, places=3)

    def test_top_story_gets_largest_force(self):
        rows = distribute_story_forces(
            V=100.0,
            story_weights=[1000, 1000, 1000],
            story_heights=[4, 8, 12],
            T=1.0,
        )
        forces = [r["Fx_kN"] for r in rows]
        # With equal weights, top should have largest share due to hi^k
        self.assertEqual(max(range(3), key=lambda i: forces[i]), 2)

    def test_k_exponent_bounds(self):
        # T <= 0.5 -> k=1
        rows = distribute_story_forces(50.0, [1000]*2, [3, 6], T=0.3)
        self.assertAlmostEqual(rows[0]["k"], 1.0, places=6)
        # T >= 2.5 -> k=2
        rows = distribute_story_forces(50.0, [1000]*2, [3, 6], T=3.0)
        self.assertAlmostEqual(rows[0]["k"], 2.0, places=6)
        # T = 1.5 -> k = 1 + (1.5-0.5)/2 = 1.5
        rows = distribute_story_forces(50.0, [1000]*2, [3, 6], T=1.5)
        self.assertAlmostEqual(rows[0]["k"], 1.5, places=6)


if __name__ == "__main__":
    unittest.main()
