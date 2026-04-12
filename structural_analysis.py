"""
Structural Analysis Engine (โมดูลวิเคราะห์โครงสร้าง)
Implements 2D Frame Matrix Stiffness Method.

Degrees of freedom per node: [u, v, θ]  (horizontal, vertical, rotation)
Supports: beams, columns, inclined members, point loads, distributed loads.
"""
import math
import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

E_STEEL = 2.0e5   # MPa = N/mm²
G_STEEL = 7.9e4   # MPa


# ============================================================================
# Data classes
# ============================================================================

@dataclass
class Node:
    """2D frame node."""
    id: int
    x: float            # mm - global X coordinate
    y: float            # mm - global Y coordinate
    # Boundary conditions: True = restrained
    fix_u: bool = False
    fix_v: bool = False
    fix_theta: bool = False

    @property
    def dofs(self) -> Tuple[int, int, int]:
        """Global DOF indices (u, v, θ) starting from 0."""
        return (self.id * 3, self.id * 3 + 1, self.id * 3 + 2)


@dataclass
class Section2D:
    """Section properties needed for 2D frame analysis."""
    A: float    # mm² - cross-sectional area
    I: float    # mm⁴ - moment of inertia
    E: float = E_STEEL  # MPa


@dataclass
class Element:
    """2D beam-column element (Euler-Bernoulli)."""
    id: int
    node_i: Node        # start node
    node_j: Node        # end node
    section: Section2D
    # Distributed loads in LOCAL coordinates (N/mm)
    q_local_x: float = 0.0   # axial distributed load
    q_local_y: float = 0.0   # transverse distributed load (gravity → negative in local y)

    @property
    def length(self) -> float:
        dx = self.node_j.x - self.node_i.x
        dy = self.node_j.y - self.node_i.y
        return math.sqrt(dx**2 + dy**2)

    @property
    def angle(self) -> float:
        """Angle of element axis from global X-axis (radians)."""
        dx = self.node_j.x - self.node_i.x
        dy = self.node_j.y - self.node_i.y
        return math.atan2(dy, dx)

    def local_stiffness(self) -> np.ndarray:
        """
        6×6 local stiffness matrix [k_local].
        DOF order: [u_i, v_i, θ_i, u_j, v_j, θ_j]
        """
        E = self.section.E
        A = self.section.A
        I = self.section.I
        L = self.length

        EA_L  = E * A / L
        EI_L  = E * I / L
        EI_L2 = E * I / L**2
        EI_L3 = E * I / L**3

        k = np.array([
            [ EA_L,      0,          0,      -EA_L,       0,          0      ],
            [ 0,    12*EI_L3,   6*EI_L2,      0,   -12*EI_L3,    6*EI_L2   ],
            [ 0,     6*EI_L2,   4*EI_L,       0,    -6*EI_L2,    2*EI_L    ],
            [-EA_L,      0,          0,       EA_L,       0,          0      ],
            [ 0,   -12*EI_L3,  -6*EI_L2,      0,    12*EI_L3,   -6*EI_L2   ],
            [ 0,     6*EI_L2,   2*EI_L,       0,    -6*EI_L2,    4*EI_L    ],
        ])
        return k

    def transformation_matrix(self) -> np.ndarray:
        """6×6 transformation matrix T (local → global)."""
        c = math.cos(self.angle)
        s = math.sin(self.angle)
        R = np.array([
            [ c,  s,  0,  0,  0,  0],
            [-s,  c,  0,  0,  0,  0],
            [ 0,  0,  1,  0,  0,  0],
            [ 0,  0,  0,  c,  s,  0],
            [ 0,  0,  0, -s,  c,  0],
            [ 0,  0,  0,  0,  0,  1],
        ])
        return R

    def global_stiffness(self) -> np.ndarray:
        """6×6 global stiffness matrix: K = T^T · k_local · T"""
        T = self.transformation_matrix()
        k = self.local_stiffness()
        return T.T @ k @ T

    def fixed_end_forces_local(self) -> np.ndarray:
        """
        Fixed-end forces in LOCAL coordinates for distributed loads.
        Returns 6-vector: [N_i, V_i, M_i, N_j, V_j, M_j]
        """
        L = self.length
        qx = self.q_local_x   # axial
        qy = self.q_local_y   # transverse

        # Standard fixed-end reactions for uniform loads:
        # Axial: N = ±qx*L/2
        # Transverse: V = ±qy*L/2,  M = ±qy*L²/12
        fef = np.array([
            -qx * L / 2.0,
            -qy * L / 2.0,
            -qy * L**2 / 12.0,
            -qx * L / 2.0,
            -qy * L / 2.0,
             qy * L**2 / 12.0,
        ])
        return fef

    def fixed_end_forces_global(self) -> np.ndarray:
        """Fixed-end forces transformed to global coordinates."""
        T = self.transformation_matrix()
        fef_local = self.fixed_end_forces_local()
        return T.T @ fef_local

    @property
    def global_dofs(self) -> List[int]:
        """List of 6 global DOF indices for this element."""
        di = self.node_i.dofs
        dj = self.node_j.dofs
        return list(di) + list(dj)


@dataclass
class PointLoad:
    """Nodal point load in global coordinates."""
    node_id: int
    Fx: float = 0.0    # N - force in global X
    Fy: float = 0.0    # N - force in global Y
    Mz: float = 0.0    # N-mm - moment about Z


@dataclass
class AnalysisResult:
    """Results from structural analysis."""
    displacements: np.ndarray            # global DOF displacements (mm, rad)
    reactions: Dict[int, np.ndarray]     # node_id → [Rx, Ry, Mz]
    element_forces: Dict[int, np.ndarray]  # element_id → local forces [N_i,V_i,M_i,N_j,V_j,M_j]
    K_global: np.ndarray                 # assembled global stiffness (for inspection)
    converged: bool = True
    error_msg: str = ""


# ============================================================================
# Structure class
# ============================================================================

class Structure2D:
    """
    2D Frame structural analysis using Matrix Stiffness Method.

    Usage:
        s = Structure2D()
        n1 = s.add_node(0, 0, fix_u=True, fix_v=True, fix_theta=True)
        n2 = s.add_node(0, 3000)
        n3 = s.add_node(6000, 3000)
        n4 = s.add_node(6000, 0, fix_u=True, fix_v=True, fix_theta=True)
        sec = Section2D(A=4055, I=1.66e7)
        s.add_element(n1, n2, sec)
        e = s.add_element(n2, n3, sec, q_local_y=-10.0)   # 10 N/mm downward
        s.add_element(n3, n4, sec)
        s.add_point_load(n2.id, Fx=5000)
        result = s.analyze()
    """

    def __init__(self):
        self.nodes: Dict[int, Node] = {}
        self.elements: Dict[int, Element] = {}
        self.point_loads: List[PointLoad] = []
        self._node_counter = 0
        self._elem_counter = 0

    def add_node(
        self, x: float, y: float,
        fix_u: bool = False, fix_v: bool = False, fix_theta: bool = False
    ) -> Node:
        """Add a node and return it."""
        n = Node(self._node_counter, x, y, fix_u, fix_v, fix_theta)
        self.nodes[n.id] = n
        self._node_counter += 1
        return n

    def add_element(
        self,
        node_i: Node,
        node_j: Node,
        section: Section2D,
        q_local_x: float = 0.0,
        q_local_y: float = 0.0,
    ) -> Element:
        """Add a beam-column element and return it."""
        e = Element(self._elem_counter, node_i, node_j, section,
                    q_local_x=q_local_x, q_local_y=q_local_y)
        self.elements[e.id] = e
        self._elem_counter += 1
        return e

    def add_point_load(self, node_id: int, Fx: float = 0, Fy: float = 0, Mz: float = 0):
        """Add a nodal point load (global coordinates)."""
        self.point_loads.append(PointLoad(node_id, Fx, Fy, Mz))

    def _ndof(self) -> int:
        return len(self.nodes) * 3

    def _assemble_stiffness(self) -> np.ndarray:
        ndof = self._ndof()
        K = np.zeros((ndof, ndof))
        for e in self.elements.values():
            ke = e.global_stiffness()
            dofs = e.global_dofs
            for i, gi in enumerate(dofs):
                for j, gj in enumerate(dofs):
                    K[gi, gj] += ke[i, j]
        return K

    def _assemble_load_vector(self) -> np.ndarray:
        ndof = self._ndof()
        F = np.zeros(ndof)
        # Fixed-end forces from distributed loads (equivalent nodal loads)
        for e in self.elements.values():
            fef = e.fixed_end_forces_global()
            dofs = e.global_dofs
            for i, gi in enumerate(dofs):
                F[gi] -= fef[i]   # sign: fef are reactions, loads are negative
        # Nodal point loads
        for pl in self.point_loads:
            di, dv, dt = self.nodes[pl.node_id].dofs
            F[di] += pl.Fx
            F[dv] += pl.Fy
            F[dt] += pl.Mz
        return F

    def _get_restrained_dofs(self) -> List[int]:
        restrained = []
        for n in self.nodes.values():
            du, dv, dt = n.dofs
            if n.fix_u:
                restrained.append(du)
            if n.fix_v:
                restrained.append(dv)
            if n.fix_theta:
                restrained.append(dt)
        return sorted(restrained)

    def analyze(self) -> AnalysisResult:
        """
        Assemble and solve the global stiffness equations.
        Returns AnalysisResult with displacements, reactions, and element forces.
        """
        ndof = self._ndof()
        K = self._assemble_stiffness()
        F = self._assemble_load_vector()
        restrained = self._get_restrained_dofs()
        free_dofs = [i for i in range(ndof) if i not in restrained]

        if not free_dofs:
            return AnalysisResult(
                displacements=np.zeros(ndof),
                reactions={},
                element_forces={},
                K_global=K,
                converged=False,
                error_msg="No free DOFs — structure is fully fixed.",
            )

        # Partition: solve K_ff * d_f = F_f
        K_ff = K[np.ix_(free_dofs, free_dofs)]
        F_f  = F[free_dofs]

        try:
            d_f = np.linalg.solve(K_ff, F_f)
        except np.linalg.LinAlgError as exc:
            return AnalysisResult(
                displacements=np.zeros(ndof),
                reactions={},
                element_forces={},
                K_global=K,
                converged=False,
                error_msg=f"Singular stiffness matrix: {exc}",
            )

        # Assemble full displacement vector
        d = np.zeros(ndof)
        for i, gi in enumerate(free_dofs):
            d[gi] = d_f[i]

        # Reactions at restrained DOFs
        R_full = K @ d - F
        reactions: Dict[int, np.ndarray] = {}
        for n in self.nodes.values():
            du, dv, dt = n.dofs
            if n.fix_u or n.fix_v or n.fix_theta:
                reactions[n.id] = np.array([R_full[du], R_full[dv], R_full[dt]])

        # Element forces in LOCAL coordinates
        element_forces: Dict[int, np.ndarray] = {}
        for e in self.elements.values():
            dofs = e.global_dofs
            d_e = d[dofs]                       # global displacements of element
            T = e.transformation_matrix()
            d_local = T @ d_e                   # transform to local
            k_local = e.local_stiffness()
            fef_local = e.fixed_end_forces_local()
            # Local forces = k_local * d_local + fef_local (fixed-end reactions)
            f_local = k_local @ d_local + fef_local
            element_forces[e.id] = f_local
            # f_local = [N_i, V_i, M_i, N_j, V_j, M_j]  (sign: positive = local direction)

        return AnalysisResult(
            displacements=d,
            reactions=reactions,
            element_forces=element_forces,
            K_global=K,
            converged=True,
        )


# ============================================================================
# Post-processing helpers
# ============================================================================

def get_node_displacement(result: AnalysisResult, node: Node) -> Tuple[float, float, float]:
    """Returns (u_mm, v_mm, theta_rad) for a node."""
    du, dv, dt = node.dofs
    d = result.displacements
    return d[du], d[dv], d[dt]


def get_element_end_forces(result: AnalysisResult, element: Element) -> dict:
    """
    Returns element end forces in local coordinates as a readable dict.
    Sign convention: positive N = tension, positive V = shear, positive M = sagging.
    """
    f = result.element_forces[element.id]
    return {
        "N_i": -f[0],   # Axial at i-end (positive = tension)
        "V_i":  f[1],   # Shear at i-end
        "M_i":  f[2],   # Moment at i-end
        "N_j":  f[3],   # Axial at j-end
        "V_j": -f[4],   # Shear at j-end
        "M_j":  f[5],   # Moment at j-end
    }


def envelope_forces(result: AnalysisResult, element: Element) -> dict:
    """Max absolute axial, shear, and moment along the element."""
    ef = get_element_end_forces(result, element)
    return {
        "N_max_kN":    max(abs(ef["N_i"]), abs(ef["N_j"])) / 1000.0,
        "V_max_kN":    max(abs(ef["V_i"]), abs(ef["V_j"])) / 1000.0,
        "M_max_kNm":   max(abs(ef["M_i"]), abs(ef["M_j"])) / 1e6,
        "M_midspan_kNm": _midspan_moment(element, ef) / 1e6,
    }


def _midspan_moment(element: Element, ef: dict) -> float:
    """
    Midspan moment for uniform distributed load + end moments (N-mm).
    M_mid = M_i_simple + M_fixed_end_distributed
    """
    L = element.length
    qy = element.q_local_y
    # Simple beam midspan moment from distributed load
    M_dist = qy * L**2 / 8.0  # N-mm (positive = sagging for downward qy<0)
    # Chord moments (linear interpolation of end moments)
    M_chord = (ef["M_i"] + ef["M_j"]) / 2.0
    return M_dist - M_chord   # approximate


def print_analysis_summary(result: AnalysisResult, structure: Structure2D):
    """Print a formatted analysis summary."""
    print("\n" + "="*60)
    print("  STRUCTURAL ANALYSIS RESULTS (Matrix Stiffness Method)")
    print("="*60)

    if not result.converged:
        print(f"  !! ANALYSIS FAILED: {result.error_msg}")
        return

    print("\n  NODE DISPLACEMENTS:")
    print(f"  {'Node':>4}  {'u (mm)':>12}  {'v (mm)':>12}  {'θ (rad)':>12}")
    for n in structure.nodes.values():
        u, v, t = get_node_displacement(result, n)
        print(f"  {n.id:>4}  {u:>12.4f}  {v:>12.4f}  {t:>12.6f}")

    print("\n  SUPPORT REACTIONS:")
    print(f"  {'Node':>4}  {'Rx (kN)':>10}  {'Ry (kN)':>10}  {'Mz (kN-m)':>12}")
    for nid, R in result.reactions.items():
        print(f"  {nid:>4}  {R[0]/1000:>10.3f}  {R[1]/1000:>10.3f}  {R[2]/1e6:>12.4f}")

    print("\n  ELEMENT FORCES (Local):")
    print(f"  {'Elem':>4}  {'N_i (kN)':>10}  {'V_i (kN)':>10}  {'M_i (kNm)':>11}  "
          f"{'N_j (kN)':>10}  {'V_j (kN)':>10}  {'M_j (kNm)':>11}")
    for e in structure.elements.values():
        ef = get_element_end_forces(result, e)
        print(f"  {e.id:>4}  {ef['N_i']/1000:>10.3f}  {ef['V_i']/1000:>10.3f}  "
              f"{ef['M_i']/1e6:>11.4f}  {ef['N_j']/1000:>10.3f}  "
              f"{ef['V_j']/1000:>10.3f}  {ef['M_j']/1e6:>11.4f}")
    print("="*60 + "\n")


# ============================================================================
# Convenience builders for common cases
# ============================================================================

def simply_supported_beam(
    span_mm: float,
    section: Section2D,
    udl_N_mm: float = 0.0,
    point_loads: Optional[List[Tuple[float, float]]] = None,
) -> Tuple["Structure2D", AnalysisResult]:
    """
    Build and analyze a simply supported beam.
    Args:
        span_mm:      Span in mm
        section:      Section2D
        udl_N_mm:     Uniform distributed load (N/mm, downward positive → input as positive)
        point_loads:  List of (position_mm, force_N) tuples (downward positive)
    Returns:
        (Structure2D, AnalysisResult)
    """
    s = Structure2D()
    n0 = s.add_node(0.0, 0.0, fix_u=True, fix_v=True, fix_theta=False)
    n1 = s.add_node(span_mm, 0.0, fix_u=False, fix_v=True, fix_theta=False)

    if point_loads:
        # Split beam at point load locations
        positions = sorted(set([0.0] + [p[0] for p in point_loads] + [span_mm]))
        load_map: Dict[float, float] = {p[0]: p[1] for p in point_loads}
        nodes_by_pos: Dict[float, Node] = {0.0: n0, span_mm: n1}

        for pos in positions[1:-1]:
            nodes_by_pos[pos] = s.add_node(pos, 0.0)

        for k in range(len(positions) - 1):
            xi = positions[k]
            xj = positions[k + 1]
            ni = nodes_by_pos[xi]
            nj = nodes_by_pos[xj]
            seg_len = xj - xi
            s.add_element(ni, nj, section, q_local_y=-udl_N_mm)

        for pos, force in point_loads:
            s.add_point_load(nodes_by_pos[pos].id, Fy=-force)
    else:
        s.add_element(n0, n1, section, q_local_y=-udl_N_mm)

    result = s.analyze()
    return s, result


def portal_frame(
    bay_mm: float,
    height_mm: float,
    col_section: Section2D,
    beam_section: Section2D,
    udl_on_beam_N_mm: float = 0.0,
    lateral_load_N: float = 0.0,
) -> Tuple["Structure2D", AnalysisResult]:
    """
    Build and analyze a single-bay portal frame.
    Columns: pinned bases. Beam: continuous (rigid connections).
    Args:
        lateral_load_N: Horizontal load at beam-left column junction (N)
    """
    s = Structure2D()
    # Nodes: 0=base-left, 1=top-left, 2=top-right, 3=base-right
    n0 = s.add_node(0.0,      0.0,       fix_u=True, fix_v=True, fix_theta=False)
    n1 = s.add_node(0.0,      height_mm)
    n2 = s.add_node(bay_mm,   height_mm)
    n3 = s.add_node(bay_mm,   0.0,       fix_u=True, fix_v=True, fix_theta=False)

    s.add_element(n0, n1, col_section)               # left column
    s.add_element(n1, n2, beam_section, q_local_y=-udl_on_beam_N_mm)  # beam
    s.add_element(n3, n2, col_section)               # right column

    if lateral_load_N:
        s.add_point_load(n1.id, Fx=lateral_load_N)

    result = s.analyze()
    return s, result
