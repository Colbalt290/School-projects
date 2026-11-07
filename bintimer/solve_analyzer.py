"""
BinTimer — Solve Analyzer & CFOP Phase Detection Engine
═══════════════════════════════════════════════════════
Analyzes telemetry from smart cubes (move sequences with timestamps)
to reconstruct the solve and break it down into standard CFOP phases:
  • Cross
  • F2L Slot 1
  • F2L Slot 2
  • F2L Slot 3
  • F2L Slot 4
  • OLL (Orientation of the Last Layer)
  • PLL (Permutation of the Last Layer)

Calculates total turns, execution time per phase, split percentages,
turns per second (TPS), and full move reconstructions grouped by phase.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

try:
    from bintimer.core import VirtualCube as CubeModel
except ImportError:
    try:
        from core import VirtualCube as CubeModel
    except ImportError:
        from .core import VirtualCube as CubeModel


@dataclass
class PhaseInfo:
    """Statistics and reconstruction for a single CFOP phase."""
    name: str                           # e.g. "Cross", "F2L 1", "OLL", "PLL"
    moves: List[str] = field(default_factory=list)
    move_count: int = 0
    time_ms: int = 0                    # total phase duration (recognition + execution)
    recognition_ms: int = 0             # pause before first turn in this phase
    execution_ms: int = 0               # active turning time
    tps: float = 0.0                    # total TPS (move_count / total time)
    execution_tps: float = 0.0          # execution TPS (move_count / execution time)
    pct_time: float = 0.0

    @property
    def time_str(self) -> str:
        s = self.time_ms / 1000.0
        return f"{s:.2f}s"

    @property
    def recognition_str(self) -> str:
        s = self.recognition_ms / 1000.0
        return f"{s:.2f}s"

    @property
    def execution_str(self) -> str:
        s = self.execution_ms / 1000.0
        return f"{s:.2f}s"

    @property
    def moves_str(self) -> str:
        return " ".join(self.moves) if self.moves else "—"


@dataclass
class SolveAnalysis:
    """Full post-solve breakdown with global stats and CFOP phases."""
    total_time_ms: int = 0
    total_turns: int = 0
    overall_tps: float = 0.0
    cross_face: str = "D"
    phases: List[PhaseInfo] = field(default_factory=list)
    raw_moves: List[Tuple[str, int]] = field(default_factory=list)

    @property
    def total_time_str(self) -> str:
        minutes = self.total_time_ms // 60_000
        seconds = (self.total_time_ms % 60_000) // 1_000
        millis = self.total_time_ms % 1_000
        if minutes > 0:
            return f"{minutes}:{seconds:02d}.{millis:03d}"
        return f"{seconds}.{millis:03d}s"

    def get_reconstruction_text(self) -> str:
        """Return formatted multi-line CFOP reconstruction."""
        lines = []
        for p in self.phases:
            lines.append(f"{p.name:<8}: {p.moves_str} ({p.move_count} moves, {p.time_str}, {p.tps:.2f} TPS)")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Cube Topology: Cross edges and F2L slots for all 6 faces
# ---------------------------------------------------------------------------

_OPPOSITE_FACE = {
    "U": "D", "D": "U",
    "F": "B", "B": "F",
    "R": "L", "L": "R",
}

_CROSS_EDGES: Dict[str, List[Tuple[Tuple[str, int], Tuple[str, int]]]] = {
    "D": [
        (("D", 1), ("F", 7)),
        (("D", 5), ("R", 7)),
        (("D", 7), ("B", 7)),
        (("D", 3), ("L", 7)),
    ],
    "U": [
        (("U", 1), ("B", 1)),
        (("U", 5), ("R", 1)),
        (("U", 7), ("F", 1)),
        (("U", 3), ("L", 1)),
    ],
    "F": [
        (("F", 1), ("U", 7)),
        (("F", 5), ("R", 3)),
        (("F", 7), ("D", 1)),
        (("F", 3), ("L", 5)),
    ],
    "B": [
        (("B", 1), ("U", 1)),
        (("B", 5), ("L", 3)),
        (("B", 7), ("D", 7)),
        (("B", 3), ("R", 5)),
    ],
    "R": [
        (("R", 1), ("U", 5)),
        (("R", 5), ("B", 3)),
        (("R", 7), ("D", 5)),
        (("R", 3), ("F", 5)),
    ],
    "L": [
        (("L", 1), ("U", 3)),
        (("L", 5), ("F", 3)),
        (("L", 7), ("D", 3)),
        (("L", 3), ("B", 5)),
    ],
}

_F2L_SLOTS: Dict[str, List[Tuple[Tuple[Tuple[str, int], ...], Tuple[Tuple[str, int], ...]]]] = {
    "D": [
        ((("D", 2), ("F", 8), ("R", 6)), (("F", 5), ("R", 3))),
        ((("D", 0), ("F", 6), ("L", 8)), (("F", 3), ("L", 5))),
        ((("D", 8), ("B", 6), ("R", 8)), (("B", 3), ("R", 5))),
        ((("D", 6), ("B", 8), ("L", 6)), (("B", 5), ("L", 3))),
    ],
    "U": [
        ((("U", 8), ("F", 2), ("R", 0)), (("F", 5), ("R", 3))),
        ((("U", 6), ("F", 0), ("L", 2)), (("F", 3), ("L", 5))),
        ((("U", 2), ("B", 0), ("R", 2)), (("B", 3), ("R", 5))),
        ((("U", 0), ("B", 2), ("L", 0)), (("B", 5), ("L", 3))),
    ],
    "F": [
        ((("F", 2), ("U", 8), ("R", 0)), (("U", 5), ("R", 1))),
        ((("F", 0), ("U", 6), ("L", 2)), (("U", 3), ("L", 1))),
        ((("F", 8), ("D", 2), ("R", 6)), (("D", 5), ("R", 7))),
        ((("F", 6), ("D", 0), ("L", 8)), (("D", 3), ("L", 7))),
    ],
    "B": [
        ((("B", 0), ("U", 2), ("R", 2)), (("U", 5), ("R", 1))),
        ((("B", 2), ("U", 0), ("L", 0)), (("U", 3), ("L", 1))),
        ((("B", 6), ("D", 8), ("R", 8)), (("D", 5), ("R", 7))),
        ((("B", 8), ("D", 6), ("L", 6)), (("D", 3), ("L", 7))),
    ],
    "R": [
        ((("R", 0), ("U", 8), ("F", 2)), (("U", 7), ("F", 1))),
        ((("R", 2), ("U", 2), ("B", 0)), (("U", 1), ("B", 1))),
        ((("R", 6), ("D", 2), ("F", 8)), (("D", 1), ("F", 7))),
        ((("R", 8), ("D", 8), ("B", 6)), (("D", 7), ("B", 7))),
    ],
    "L": [
        ((("L", 2), ("U", 6), ("F", 0)), (("U", 7), ("F", 1))),
        ((("L", 0), ("U", 0), ("B", 2)), (("U", 1), ("B", 1))),
        ((("L", 8), ("D", 0), ("F", 6)), (("D", 1), ("F", 7))),
        ((("L", 6), ("D", 6), ("B", 8)), (("D", 7), ("B", 7))),
    ],
}


def _is_cross_solved(st: Dict[str, List[str]], face: str) -> bool:
    """Check if all 4 cross edges on *face* are correctly placed and oriented."""
    for (f1, i1), (f2, i2) in _CROSS_EDGES[face]:
        if st[f1][i1] != st[f1][4] or st[f2][i2] != st[f2][4]:
            return False
    return True


def _count_solved_f2l_slots(st: Dict[str, List[str]], cross_face: str) -> int:
    """Count how many of the 4 F2L slots are currently solved."""
    count = 0
    for corner, edge in _F2L_SLOTS[cross_face]:
        corner_ok = all(st[f][i] == st[f][4] for f, i in corner)
        edge_ok = all(st[f][i] == st[f][4] for f, i in edge)
        if corner_ok and edge_ok:
            count += 1
    return count


def _is_oll_solved(st: Dict[str, List[str]], cross_face: str) -> bool:
    """Check if the opposite face of *cross_face* is completely uniform (oriented)."""
    top_face = _OPPOSITE_FACE[cross_face]
    center_col = st[top_face][4]
    return all(c == center_col for c in st[top_face])


# ---------------------------------------------------------------------------
# CFOP Analyzer
# ---------------------------------------------------------------------------

def analyze_solve(
    scramble: str,
    recorded_moves: List[Tuple[str, int]],
    total_time_ms: int,
) -> SolveAnalysis:
    """
    Replay the recorded moves against the scrambled cube to detect CFOP phases.

    Parameters
    ----------
    scramble : str
        The initial scramble string applied before the solve.
    recorded_moves : list of (move_str, timestamp_ms)
        Each move executed during the solve along with its timestamp in ms from timer start.
    total_time_ms : int
        The total solve duration in milliseconds.

    Returns
    -------
    SolveAnalysis
        Populated analysis dataclass with global and per-phase metrics.
    """
    if not recorded_moves:
        return SolveAnalysis(
            total_time_ms=total_time_ms,
            total_turns=0,
            overall_tps=0.0,
            phases=[],
            raw_moves=[],
        )

    # Clean and filter moves
    moves: List[Tuple[str, int]] = []
    for mv, ts in recorded_moves:
        mv_clean = mv.strip()
        if mv_clean:
            moves.append((mv_clean, max(0, ts)))

    total_turns = len(moves)
    overall_tps = (total_turns / (total_time_ms / 1000.0)) if total_time_ms > 0 else 0.0

    # Initialize cube with scramble
    cube = CubeModel()
    if scramble.strip():
        try:
            cube.apply_scramble(scramble)
        except Exception:
            pass

    # Step 1: Detect cross face
    # We replay moves and see which face's cross solves first
    cross_face: Optional[str] = None
    cross_idx: int = -1

    temp_cube = CubeModel()
    if scramble.strip():
        try:
            temp_cube.apply_scramble(scramble)
        except Exception:
            pass

    for i, (mv, _ts) in enumerate(moves):
        try:
            temp_cube.apply_move(mv)
        except Exception:
            continue
        st = temp_cube.get_facelets()
        for f in ("D", "U", "F", "B", "R", "L"):
            if _is_cross_solved(st, f):
                cross_face = f
                cross_idx = i
                break
        if cross_face is not None:
            break

    # If no cross was detected before end, default to 'D' (white or yellow cross)
    if cross_face is None:
        cross_face = "D"

    # Step 2: Track progression through Cross -> F2L 1..4 -> OLL -> PLL
    cube.reset()
    if scramble.strip():
        try:
            cube.apply_scramble(scramble)
        except Exception:
            pass

    phase_end_indices: Dict[str, int] = {
        "Cross": -1,
        "F2L 1": -1,
        "F2L 2": -1,
        "F2L 3": -1,
        "F2L 4": -1,
        "OLL": -1,
        "PLL": -1,
    }

    curr_f2l_target = 1

    for i, (mv, _ts) in enumerate(moves):
        try:
            cube.apply_move(mv)
        except Exception:
            continue
        st = cube.get_facelets()

        # Check cross
        if phase_end_indices["Cross"] == -1 and _is_cross_solved(st, cross_face):
            phase_end_indices["Cross"] = i

        # Check F2L slots
        if phase_end_indices["Cross"] != -1 and phase_end_indices["F2L 4"] == -1:
            solved_slots = _count_solved_f2l_slots(st, cross_face)
            while curr_f2l_target <= 4 and solved_slots >= curr_f2l_target:
                slot_key = f"F2L {curr_f2l_target}"
                if phase_end_indices[slot_key] == -1:
                    phase_end_indices[slot_key] = i
                curr_f2l_target += 1

        # Check OLL
        if (
            phase_end_indices["F2L 4"] != -1
            and phase_end_indices["OLL"] == -1
            and _is_oll_solved(st, cross_face)
        ):
            phase_end_indices["OLL"] = i

        # Check PLL / fully solved
        if phase_end_indices["OLL"] != -1 and cube.is_solved():
            phase_end_indices["PLL"] = i
            break

    # If the solve ended solved, mark PLL as final index
    if phase_end_indices["PLL"] == -1 and total_turns > 0:
        phase_end_indices["PLL"] = total_turns - 1

    # Fill in any missing boundaries monotonically
    # If a phase was skipped or not detected, clamp to previous or next
    phase_order = ["Cross", "F2L 1", "F2L 2", "F2L 3", "F2L 4", "OLL", "PLL"]
    last_idx = -1
    for p_name in phase_order:
        idx = phase_end_indices[p_name]
        if idx != -1:
            last_idx = idx
        else:
            # Fallback if undetected: distribute evenly across remaining
            phase_end_indices[p_name] = last_idx

    # Build PhaseInfo objects
    start_move_idx = 0
    start_time_ms = 0
    phases: List[PhaseInfo] = []

    for idx, p_name in enumerate(phase_order):
        end_move_idx = phase_end_indices[p_name]
        is_last_phase = (idx == len(phase_order) - 1)

        if end_move_idx >= start_move_idx and end_move_idx < total_turns:
            phase_moves = [moves[k][0] for k in range(start_move_idx, end_move_idx + 1)]
            first_turn_time = moves[start_move_idx][1]
            last_turn_time = moves[end_move_idx][1]

            # If this is the last phase and total_time_ms > last_turn_time, cap at total_time_ms
            end_time_ms = total_time_ms if is_last_phase and total_time_ms > last_turn_time else last_turn_time

            recognition_ms = max(0, first_turn_time - start_time_ms)
            execution_ms = max(0, end_time_ms - first_turn_time)
            dur_ms = recognition_ms + execution_ms
        else:
            phase_moves = []
            dur_ms = 0
            recognition_ms = 0
            execution_ms = 0
            end_time_ms = start_time_ms

        m_count = len(phase_moves)
        tps = (m_count / (dur_ms / 1000.0)) if dur_ms > 0 else 0.0
        exec_tps = (m_count / (execution_ms / 1000.0)) if execution_ms > 0 else tps
        pct = (dur_ms / total_time_ms * 100.0) if total_time_ms > 0 else 0.0

        phases.append(
            PhaseInfo(
                name=p_name,
                moves=phase_moves,
                move_count=m_count,
                time_ms=dur_ms,
                recognition_ms=recognition_ms,
                execution_ms=execution_ms,
                tps=round(tps, 2),
                execution_tps=round(exec_tps, 2),
                pct_time=round(pct, 1),
            )
        )

        start_move_idx = max(start_move_idx, end_move_idx + 1)
        start_time_ms = end_time_ms

    return SolveAnalysis(
        total_time_ms=total_time_ms,
        total_turns=total_turns,
        overall_tps=round(overall_tps, 2),
        cross_face=cross_face,
        phases=phases,
        raw_moves=moves,
    )
