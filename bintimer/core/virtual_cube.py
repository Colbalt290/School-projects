"""
BinTimer Core — Virtual Cube Evaluator
═══════════════════════════════════════
Pure-Python 3×3×3 Rubik's Cube state representation and move evaluator.
Maintains standard 54-facelet representation and performs strict is_solved()
validation based on unified face monochromaticity.
"""

from __future__ import annotations

import copy
from typing import Dict, List, Tuple, Any

# Face naming convention:
# U = Up (White)
# D = Down (Yellow)
# F = Front (Green)
# B = Back (Blue)
# L = Left (Orange)
# R = Right (Red)
FACES = ("U", "D", "F", "B", "L", "R")

DEFAULT_SOLVED_COLORS: Dict[str, str] = {
    "U": "W",  # White
    "D": "Y",  # Yellow
    "F": "G",  # Green
    "B": "B",  # Blue
    "L": "O",  # Orange
    "R": "R",  # Red
}

# Clockwise rotation permutation for the 9 facelets of a single face:
# 0 1 2       6 3 0
# 3 4 5  -->  7 4 1
# 6 7 8       8 5 2
_FACE_ROT_CW = {0: 2, 1: 5, 2: 8, 3: 1, 4: 4, 5: 7, 6: 0, 7: 3, 8: 6}


def _make_perm(
    face: str,
    corners: List[List[Tuple[str, int]]],
    edges: List[List[Tuple[str, int]]],
) -> Dict[Tuple[str, int], Tuple[str, int]]:
    """Build a complete 54-facelet permutation map for a single face turn."""
    p: Dict[Tuple[str, int], Tuple[str, int]] = {}
    for f in FACES:
        for i in range(9):
            p[(f, i)] = (f, i)
    for i in range(9):
        p[(face, i)] = (face, _FACE_ROT_CW[i])
    for c_src, c_dst in zip(corners, corners[1:] + [corners[0]]):
        for f_s, f_d in zip(c_src, c_dst):
            p[f_s] = f_d
    for e_src, e_dst in zip(edges, edges[1:] + [edges[0]]):
        for f_s, f_d in zip(e_src, e_dst):
            p[f_s] = f_d
    return p


# Precompute base quarter-turn permutations (CW)
_P_U = _make_perm(
    "U",
    [[("B", 2), ("L", 0)], [("R", 2), ("B", 0)], [("F", 2), ("R", 0)], [("L", 2), ("F", 0)]],
    [[("B", 1)], [("R", 1)], [("F", 1)], [("L", 1)]],
)

_P_D = _make_perm(
    "D",
    [[("F", 6), ("L", 8)], [("R", 6), ("F", 8)], [("B", 6), ("R", 8)], [("L", 6), ("B", 8)]],
    [[("F", 7)], [("R", 7)], [("B", 7)], [("L", 7)]],
)

_P_F = _make_perm(
    "F",
    [[("L", 2), ("U", 6)], [("U", 8), ("R", 0)], [("R", 6), ("D", 2)], [("D", 0), ("L", 8)]],
    [[("U", 7)], [("R", 3)], [("D", 1)], [("L", 5)]],
)

_P_B = _make_perm(
    "B",
    [[("R", 2), ("U", 2)], [("U", 0), ("L", 0)], [("L", 6), ("D", 6)], [("D", 8), ("R", 8)]],
    [[("U", 1)], [("L", 3)], [("D", 7)], [("R", 5)]],
)

_P_R = _make_perm(
    "R",
    [[("U", 8), ("F", 2)], [("B", 0), ("U", 2)], [("D", 8), ("B", 6)], [("F", 8), ("D", 2)]],
    [[("U", 5)], [("B", 3)], [("D", 5)], [("F", 5)]],
)

_P_L = _make_perm(
    "L",
    [[("U", 0), ("B", 2)], [("F", 0), ("U", 6)], [("D", 0), ("F", 6)], [("B", 8), ("D", 6)]],
    [[("U", 3)], [("F", 3)], [("D", 3)], [("B", 5)]],
)


def _inv_perm(p: Dict[Tuple[str, int], Tuple[str, int]]) -> Dict[Tuple[str, int], Tuple[str, int]]:
    return {v: k for k, v in p.items()}


def _comp_perm(
    p1: Dict[Tuple[str, int], Tuple[str, int]],
    p2: Dict[Tuple[str, int], Tuple[str, int]],
) -> Dict[Tuple[str, int], Tuple[str, int]]:
    return {k: p2[v] for k, v in p1.items()}


# Full table of all 18 standard moves
_PERMS: Dict[str, Dict[Tuple[str, int], Tuple[str, int]]] = {
    "U": _P_U, "D": _P_D, "F": _P_F, "B": _P_B, "R": _P_R, "L": _P_L,
}
for _face in list(_PERMS.keys()):
    _PERMS[f"{_face}'"] = _inv_perm(_PERMS[_face])
    _PERMS[f"{_face}2"] = _comp_perm(_PERMS[_face], _PERMS[_face])


class VirtualCube:
    """
    Dedicated 3x3 Rubik's Cube state representation and evaluator.
    
    Provides:
      • Standard 54-facelet tracking across 6 faces (U, D, F, B, L, R).
      • Strict move validation and application (U, R', F2, etc.).
      • Strict is_solved() validation: returns True IF AND ONLY IF all 6 faces
        are completely unified (monochromatic with distinct centers).
    """

    def __init__(self, initial_state: Dict[str, List[str]] | None = None) -> None:
        self._state: Dict[str, List[str]] = {}
        if initial_state:
            self.set_state(initial_state)
        else:
            self.reset()

    def reset(self) -> None:
        """Restore all 6 faces to solved monochromatic states."""
        self._state = {
            face: [color] * 9
            for face, color in DEFAULT_SOLVED_COLORS.items()
        }

    def clone(self) -> VirtualCube:
        """Create an independent deep copy of this virtual cube."""
        return VirtualCube(self.get_state())

    def get_state(self) -> Dict[str, List[str]]:
        """Return a deep copy of the 54-facelet state dictionary."""
        return copy.deepcopy(self._state)

    def get_facelets(self) -> Dict[str, List[str]]:
        """Alias for get_state() for backwards-compatibility."""
        return self.get_state()

    def set_state(self, state: Dict[str, List[str]]) -> None:
        """Set the cube state directly from a 54-facelet dictionary."""
        for face in FACES:
            if face not in state or len(state[face]) != 9:
                raise ValueError(f"Invalid state for face '{face}': expected 9 facelets.")
        self._state = copy.deepcopy(state)

    @staticmethod
    def normalize_move(move_str: str) -> str:
        """
        Normalize various move notations into standard uppercase format.
        Examples: 'r' -> 'R', \"r'\" -> \"R'\", \"r’\" -> \"R'\", 'U2' -> 'U2'.
        """
        m = move_str.strip().replace("’", "'").replace("`", "'")
        if not m:
            return ""
        face = m[0].upper()
        suffix = m[1:]
        if suffix in ("", "'", "2"):
            return f"{face}{suffix}"
        raise ValueError(f"Invalid move notation: '{move_str}'")

    def apply_move(self, move_str: str) -> bool:
        """
        Apply a single standard move (e.g. 'U', 'R'', 'F2').
        Returns True if the move was recognized and applied, False otherwise.
        """
        norm = self.normalize_move(move_str)
        if not norm:
            return False

        perm = _PERMS.get(norm)
        if perm is None:
            raise ValueError(f"Unsupported move: '{norm}'")

        new_state = {f: ["" for _ in range(9)] for f in FACES}
        for (f, i), (dest_f, dest_i) in perm.items():
            new_state[dest_f][dest_i] = self._state[f][i]
        self._state = new_state
        return True

    def apply_scramble(self, scramble: str) -> None:
        """Apply a sequence of whitespace-separated moves."""
        for token in scramble.strip().split():
            self.apply_move(token)

    def is_solved(self) -> bool:
        """
        Strictly evaluate whether the cube is in a solved state.
        
        Returns True IF AND ONLY IF:
          1. All 9 facelets on every face match that face's center piece.
          2. All 6 face center pieces are distinct.
          
        It will NEVER return True on an intermediate move or incomplete face.
        """
        centers = []
        for face in FACES:
            facelets = self._state[face]
            center = facelets[4]
            centers.append(center)
            # All 9 facelets on this face must match the center color
            if any(color != center for color in facelets):
                return False

        # All 6 face centers must be distinct colors
        if len(set(centers)) != 6:
            return False

        return True

    def get_face_color(self, face: str) -> str:
        """Return the center color of a given face."""
        f = face.upper()
        if f not in self._state:
            raise KeyError(f"Invalid face name: '{face}'")
        return self._state[f][4]

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, VirtualCube):
            return False
        return self._state == other._state

    def __repr__(self) -> str:
        status = "SOLVED" if self.is_solved() else "SCRAMBLED"
        return f"<VirtualCube status={status}>"
