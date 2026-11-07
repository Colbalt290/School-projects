"""2D unfolded net visualizer for a Rubik's cube.

Renders the standard cross/net layout using QPainter:

            [U]
        [L] [F] [R] [B]
            [D]

Each face is a 3×3 grid of colored facelets drawn as filled rounded
rectangles with thin dark borders.  The widget scales proportionally
to fit the available space while preserving the 4:3 aspect ratio of
the unfolded net (12 columns × 9 rows).
"""

from __future__ import annotations

from PyQt6.QtCore import QRectF, QSize, Qt
from PyQt6.QtGui import QColor, QPainter, QPaintEvent, QPen
from PyQt6.QtWidgets import QWidget


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

#: Map single-character colour codes to hex colours.
COLOR_MAP: dict[str, str] = {
    "W": "#FFFFFF",  # White
    "Y": "#FFD500",  # Yellow
    "G": "#009B48",  # Green
    "B": "#0045AD",  # Blue
    "R": "#B71234",  # Red
    "O": "#FF5800",  # Orange
}

#: Border colour used around each facelet.
BORDER_COLOR = "#1e1e1e"

#: Solved-state facelet mapping (standard colour scheme).
SOLVED_STATE: dict[str, list[str]] = {
    "U": ["W"] * 9,
    "D": ["Y"] * 9,
    "F": ["G"] * 9,
    "B": ["B"] * 9,
    "R": ["R"] * 9,
    "L": ["O"] * 9,
}

#: Face positions on the unfolded net expressed as (column_offset, row_offset)
#: in units of *faces* (each face occupies a 3×3 block of facelets).
#:
#:  Layout (face units):
#:      col  0   1   2   3
#:  row 0             U
#:  row 1    L   F   R   B
#:  row 2             D
FACE_POSITIONS: dict[str, tuple[int, int]] = {
    "U": (1, 0),
    "L": (0, 1),
    "F": (1, 1),
    "R": (2, 1),
    "B": (3, 1),
    "D": (1, 2),
}

#: Total grid dimensions in facelet cells.
GRID_COLS = 12  # 4 faces × 3
GRID_ROWS = 9   # 3 faces × 3

#: Aspect ratio of the net (width / height).
ASPECT_RATIO = GRID_COLS / GRID_ROWS  # 4 / 3


class CubeVisualizer(QWidget):
    """Widget that renders a 2-D unfolded Rubik's cube net.

    Parameters
    ----------
    parent:
        Optional parent widget.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.setObjectName("cubeVisualizer")
        self.setContentsMargins(0, 0, 0, 0)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

        self.setMinimumSize(QSize(180, 135))

        # Current facelet state – start solved.
        self._facelets: dict[str, list[str]] = {
            face: list(colors) for face, colors in SOLVED_STATE.items()
        }

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def update_state(self, facelets: dict[str, list[str]]) -> None:
        """Update the displayed cube state and repaint.

        Parameters
        ----------
        facelets:
            Dictionary mapping face names (``U``, ``D``, ``F``, ``B``,
            ``R``, ``L``) to a list of 9 single-character colour codes.
            Colour codes are one of ``W``, ``Y``, ``G``, ``B``, ``R``,
            ``O``.
        """
        self._facelets = {face: list(colors) for face, colors in facelets.items()}
        self.update()

    def reset(self) -> None:
        """Reset the visualizer to the solved state."""
        self._facelets = {face: list(colors) for face, colors in SOLVED_STATE.items()}
        self.update()

    # ------------------------------------------------------------------
    # Qt overrides
    # ------------------------------------------------------------------

    def sizeHint(self) -> QSize:
        """Return the preferred size of the widget."""
        return QSize(240, 180)

    def paintEvent(self, event: QPaintEvent | None) -> None:
        """Draw the unfolded cube net scaled to the current widget size."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        # Determine the drawing rectangle that preserves aspect ratio and
        # is centred within the widget.
        w = self.width()
        h = self.height()

        if w / h > ASPECT_RATIO:
            # Widget is wider than the net – constrain by height.
            draw_h = float(h)
            draw_w = draw_h * ASPECT_RATIO
        else:
            # Widget is taller (or exact) – constrain by width.
            draw_w = float(w)
            draw_h = draw_w / ASPECT_RATIO

        x_offset = (w - draw_w) / 2.0
        y_offset = (h - draw_h) / 2.0

        cell_w = draw_w / GRID_COLS
        cell_h = draw_h / GRID_ROWS

        gap = min(2.0, cell_w * 0.08, cell_h * 0.08)  # 1–2 px gap
        corner_radius = min(cell_w, cell_h) * 0.15

        pen = QPen(QColor(BORDER_COLOR))
        pen.setWidthF(max(1.0, min(cell_w, cell_h) * 0.06))
        painter.setPen(pen)

        for face, (face_col, face_row) in FACE_POSITIONS.items():
            colors = self._facelets.get(face, ["W"] * 9)
            for idx in range(9):
                row = idx // 3
                col = idx % 3

                cx = x_offset + (face_col * 3 + col) * cell_w
                cy = y_offset + (face_row * 3 + row) * cell_h

                rect = QRectF(
                    cx + gap / 2.0,
                    cy + gap / 2.0,
                    cell_w - gap,
                    cell_h - gap,
                )

                color_char = colors[idx] if idx < len(colors) else "W"
                fill = QColor(COLOR_MAP.get(color_char, "#888888"))
                painter.setBrush(fill)
                painter.drawRoundedRect(rect, corner_radius, corner_radius)

        painter.end()
