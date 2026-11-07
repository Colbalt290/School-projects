"""WCA-style 3×3 scramble generator for BinTimer."""

import random

FACES = ['U', 'D', 'L', 'R', 'F', 'B']
MODIFIERS = ['', "'", '2']

# Faces sharing the same rotation axis (U/D, L/R, F/B)
_AXIS = {'U': 0, 'D': 0, 'L': 1, 'R': 1, 'F': 2, 'B': 2}


def generate_scramble(length: int = 20) -> str:
    """
    Generate a random-move WCA-style 3×3 scramble.

    Constraints enforced:
      1. No two consecutive moves on the same face.
      2. No three consecutive moves on the same axis
         (e.g. U D U is forbidden because U and D share the UD axis).

    Args:
        length: Number of moves (WCA standard is 20 for 3×3).

    Returns:
        Space-separated scramble string, e.g. ``"R2 U' F D2 B ..."``
    """
    moves: list[str] = []
    history: list[str] = []          # face letters only (no modifiers)

    for _ in range(length):
        while True:
            face = random.choice(FACES)
            if history and face == history[-1]:
                continue                                       # rule 1
            if (len(history) >= 2
                    and _AXIS[face] == _AXIS[history[-1]] == _AXIS[history[-2]]):
                continue                                       # rule 2
            break

        modifier = random.choice(MODIFIERS)
        moves.append(f"{face}{modifier}")
        history.append(face)

    return ' '.join(moves)
