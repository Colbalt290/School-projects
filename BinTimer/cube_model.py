"""
BinTimer — Virtual Rubik's Cube State Engine
════════════════════════════════════════════
A pure-Python, dependency-free 3×3×3 Rubik's cube model using the standard
54-facelet representation. Each of the six faces (U, D, F, B, R, L) stores
nine colour characters in reading order:

    0 1 2
    3 4 5
    6 7 8

Supports all 18 standard moves (U, U', U2, …) and provides scramble
application, solved-state detection, reset, and facelet access.
"""

from __future__ import annotations

import copy
from typing import Dict, List, Tuple

# ---------------------------------------------------------------------------
# Colour constants
# ---------------------------------------------------------------------------
_SOLVED_COLOURS: Dict[str, str] = {
    "U": "W",  # Up    → White
    "D": "Y",  # Down  → Yellow
    "F": "G",  # Front → Green
    "B": "B",  # Back  → Blue
    "R": "R",  # Right → Red
    "L": "O",  # Left  → Orange
}

_FACE_ROT = {0: 2, 1: 5, 2: 8, 3: 1, 4: 4, 5: 7, 6: 0, 7: 3, 8: 6}


def _make_perm(
    face: str,
    corners: List[List[Tuple[str, int]]],
    edges: List[List[Tuple[str, int]]],
) -> Dict[Tuple[str, int], Tuple[str, int]]:
    p: Dict[Tuple[str, int], Tuple[str, int]] = {}
    for f in "UDFBLR":
        for i in range(9):
            p[(f, i)] = (f, i)
    for i in range(9):
        p[(face, i)] = (face, _FACE_ROT[i])
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


# Full dictionary of all 18 moves
_PERMS: Dict[str, Dict[Tuple[str, int], Tuple[str, int]]] = {
    "U": _P_U, "D": _P_D, "F": _P_F, "B": _P_B, "R": _P_R, "L": _P_L,
}
for _f in list(_PERMS.keys()):
    _PERMS[f"{_f}'"] = _inv_perm(_PERMS[_f])
    _PERMS[f"{_f}2"] = _comp_perm(_PERMS[_f], _PERMS[_f])


class CubeModel:
    """A 3×3×3 Rubik's cube virtual state engine."""

    def __init__(self) -> None:
        self._state: Dict[str, List[str]] = {}
        self.reset()

    def reset(self) -> None:
        """Restore the cube to the solved state."""
        self._state = {
            face: [colour] * 9
            for face, colour in _SOLVED_COLOURS.items()
        }

    def apply_move(self, move_str: str) -> None:
        """Apply a standard move string (e.g. 'U', 'R'', 'F2')."""
        move_str = move_str.strip()
        if not move_str:
            return

        perm = _PERMS.get(move_str)
        if perm is None:
            raise ValueError(f"Unknown move: {move_str!r}")

        # When piece at pos moves to perm[pos], new_state[perm[pos]] = old_state[pos]
        new_state = {f: ["" for _ in range(9)] for f in "UDFBLR"}
        for (f, i), (dest_f, dest_i) in perm.items():
            new_state[dest_f][dest_i] = self._state[f][i]
        self._state = new_state

    def apply_scramble(self, scramble: str) -> None:
        """Apply a space-separated sequence of moves."""
        for token in scramble.strip().split():
            self.apply_move(token)

    def is_solved(self) -> bool:
        """Return True if all 9 facelets on every face match the face center."""
        for face in ("U", "D", "F", "B", "R", "L"):
            center = self._state[face][4]
            if any(c != center for c in self._state[face]):
                return False
        return True

    def get_facelets(self) -> Dict[str, List[str]]:
        """Return a deep copy of the current 54 facelet state."""
        return copy.deepcopy(self._state)

    def get_face_color(self, face: str) -> str:
        """Return the colour character for a given face's center."""
        face = face.upper()
        if face not in self._state:
            raise KeyError(f"Invalid face name: {face!r}")
        return self._state[face][4]

    def __repr__(self) -> str:
        status = "solved" if self.is_solved() else "scrambled"
        return f"<CubeModel ({status})>"


if __name__ == "__main__":
    cube = CubeModel()
    assert cube.is_solved(), "FAIL: fresh cube should be solved"
    print("✓ Solved after reset")

    for move in ("U", "D", "R", "L", "F", "B"):
        cube.reset()
        for _ in range(4):
            cube.apply_move(move)
        assert cube.is_solved(), f"FAIL: {move}×4 should be identity"
    print("✓ All single CW moves ×4 = identity")

    for move in ("U'", "D'", "R'", "L'", "F'", "B'"):
        cube.reset()
        for _ in range(4):
            cube.apply_move(move)
        assert cube.is_solved(), f"FAIL: {move}×4 should be identity"
    print("✓ All single CCW moves ×4 = identity")

    for move in ("U2", "D2", "R2", "L2", "F2", "B2"):
        cube.reset()
        for _ in range(2):
            cube.apply_move(move)
        assert cube.is_solved(), f"FAIL: {move}×2 should be identity"
    print("✓ All double moves ×2 = identity")

    cube.reset()
    for _ in range(6):
        cube.apply_scramble("R U R' U'")
    assert cube.is_solved(), "FAIL: (R U R' U')×6 should be identity"
    print("✓ (R U R' U')×6 = identity")

    cube.reset()
    t_perm = "R U R' U' R' F R2 U' R' U' R U R' F'"
    cube.apply_scramble(t_perm)
    assert not cube.is_solved(), "FAIL: single T-perm should not be identity"
    cube.apply_scramble(t_perm)
    assert cube.is_solved(), "FAIL: T-perm×2 should be identity"
    print("✓ T-perm × 2 = identity")

    cube.reset()
    superflip = "U R2 F B R B2 R U2 L B2 R U' D' R2 F R' L B2 U2 F2"
    cube.apply_scramble(superflip)
    assert not cube.is_solved()
    cube.apply_scramble(superflip)
    assert cube.is_solved(), "FAIL: Superflip×2 should be identity"
    print("✓ Superflip × 2 = identity")

    print("\nAll checks passed successfully!")
