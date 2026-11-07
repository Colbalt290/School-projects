"""
BinTimer — 3D Interactive Rubik's Cube Visualizer
═════════════════════════════════════════════════
A pure PyQt6 3D Rubik's cube visualizer using mathematical 3D vector
projection and QPainter.

Features:
  • Realistic 3D perspective / isometric projection with dynamic lighting
  • Interactive mouse rotation (click & drag to rotate in 3D)
  • Double-click to reset to default isometric view (U, F, R faces visible)
  • Real-time updates as smart cube moves arrive
  • High-performance vector rendering (no OpenGL driver issues on Linux/Wayland)
"""

from __future__ import annotations

import math
from typing import Dict, List, Tuple

from PyQt6.QtCore import QPoint, QPointF, QRectF, QSize, Qt
from PyQt6.QtGui import (
    QColor,
    QMouseEvent,
    QPainter,
    QPaintEvent,
    QPen,
    QPolygonF,
)
from PyQt6.QtWidgets import QWidget

# ---------------------------------------------------------------------------
# Colors & Theme Constants
# ---------------------------------------------------------------------------

COLOR_MAP: Dict[str, str] = {
    "W": "#FFFFFF",  # Up    → White
    "Y": "#FFD500",  # Down  → Yellow
    "G": "#009B48",  # Front → Green
    "B": "#0045AD",  # Back  → Blue
    "R": "#B71234",  # Right → Red
    "O": "#FF5800",  # Left  → Orange
}

CORE_COLOR = "#121212"
BORDER_PEN_COLOR = "#181818"

# Default isometric viewing angles (radians): looking from top-front-right
# so Up (White), Front (Green), and Right (Red) are visible.
DEFAULT_ROT_X = math.radians(26.0)
DEFAULT_ROT_Y = math.radians(-42.0)

# Light source vector (normalized) pointing from top-front-right
_LIGHT_DIR = (0.35, 0.65, 0.68)
_L_LEN = math.sqrt(sum(c * c for c in _LIGHT_DIR))
LIGHT = (_LIGHT_DIR[0] / _L_LEN, _LIGHT_DIR[1] / _L_LEN, _LIGHT_DIR[2] / _L_LEN)


# ---------------------------------------------------------------------------
# 3D Math Utilities
# ---------------------------------------------------------------------------

def _rotate_y(p: Tuple[float, float, float], rad: float) -> Tuple[float, float, float]:
    x, y, z = p
    c, s = math.cos(rad), math.sin(rad)
    return (x * c + z * s, y, -x * s + z * c)


def _rotate_x(p: Tuple[float, float, float], rad: float) -> Tuple[float, float, float]:
    x, y, z = p
    c, s = math.cos(rad), math.sin(rad)
    return (x, y * c - z * s, y * s + z * c)


def _transform(p: Tuple[float, float, float], rot_x: float, rot_y: float) -> Tuple[float, float, float]:
    return _rotate_x(_rotate_y(p, rot_y), rot_x)


# ---------------------------------------------------------------------------
# Precomputed 3D Facelet Geometry
# ---------------------------------------------------------------------------

def _build_facelet_quads() -> Dict[str, List[Tuple[Tuple[float, float, float], ...]]]:
    """
    Build the 4 3D corner coordinates for each of the 9 facelets on all 6 faces.
    Cube spans from -1.5 to +1.5 on X, Y, Z.
    Stickers have a small margin so the black core is visible between them.
    """
    quads: Dict[str, List[Tuple[Tuple[float, float, float], ...]]] = {}
    gap = 0.05  # margin around each sticker

    # Front (Z = +1.5, normal = (0, 0, 1))
    f_list = []
    for r in range(3):
        y_t = 1.5 - r - gap
        y_b = 0.5 - r + gap
        for c in range(3):
            x_l = -1.5 + c + gap
            x_r = -0.5 + c - gap
            f_list.append(((x_l, y_t, 1.5), (x_r, y_t, 1.5), (x_r, y_b, 1.5), (x_l, y_b, 1.5)))
    quads["F"] = f_list

    # Back (Z = -1.5, normal = (0, 0, -1))
    b_list = []
    for r in range(3):
        y_t = 1.5 - r - gap
        y_b = 0.5 - r + gap
        for c in range(3):
            x_l = 1.5 - c - gap
            x_r = 0.5 - c + gap
            b_list.append(((x_l, y_t, -1.5), (x_r, y_t, -1.5), (x_r, y_b, -1.5), (x_l, y_b, -1.5)))
    quads["B"] = b_list

    # Up (Y = +1.5, normal = (0, 1, 0))
    u_list = []
    for r in range(3):
        z_t = -1.5 + r + gap
        z_b = -0.5 + r - gap
        for c in range(3):
            x_l = -1.5 + c + gap
            x_r = -0.5 + c - gap
            u_list.append(((x_l, 1.5, z_t), (x_r, 1.5, z_t), (x_r, 1.5, z_b), (x_l, 1.5, z_b)))
    quads["U"] = u_list

    # Down (Y = -1.5, normal = (0, -1, 0))
    d_list = []
    for r in range(3):
        z_t = 1.5 - r - gap
        z_b = 0.5 - r + gap
        for c in range(3):
            x_l = -1.5 + c + gap
            x_r = -0.5 + c - gap
            d_list.append(((x_l, -1.5, z_t), (x_r, -1.5, z_t), (x_r, -1.5, z_b), (x_l, -1.5, z_b)))
    quads["D"] = d_list

    # Right (X = +1.5, normal = (1, 0, 0))
    r_list = []
    for r in range(3):
        y_t = 1.5 - r - gap
        y_b = 0.5 - r + gap
        for c in range(3):
            z_l = 1.5 - c - gap
            z_r = 0.5 - c + gap
            r_list.append(((1.5, y_t, z_l), (1.5, y_t, z_r), (1.5, y_b, z_r), (1.5, y_b, z_l)))
    quads["R"] = r_list

    # Left (X = -1.5, normal = (-1, 0, 0))
    l_list = []
    for r in range(3):
        y_t = 1.5 - r - gap
        y_b = 0.5 - r + gap
        for c in range(3):
            z_l = -1.5 + c + gap
            z_r = -0.5 + c - gap
            l_list.append(((-1.5, y_t, z_l), (-1.5, y_t, z_r), (-1.5, y_b, z_r), (-1.5, y_b, z_l)))
    quads["L"] = l_list

    return quads


_FACELET_QUADS = _build_facelet_quads()

_FACE_NORMALS: Dict[str, Tuple[float, float, float]] = {
    "F": (0.0, 0.0, 1.0),
    "B": (0.0, 0.0, -1.0),
    "U": (0.0, 1.0, 0.0),
    "D": (0.0, -1.0, 0.0),
    "R": (1.0, 0.0, 0.0),
    "L": (-1.0, 0.0, 0.0),
}


# ---------------------------------------------------------------------------
# 3D Cube Visualizer Widget
# ---------------------------------------------------------------------------

class CubeVisualizer3D(QWidget):
    """
    Real-time 3D Rubik's cube visualizer.

    Supports mouse drag to freely orbit and view the cube from any angle,
    with shading, perspective, and clean vector rendering.
    """

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("cubeVisualizer3D")
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setMinimumSize(QSize(160, 140))

        self.rot_x = DEFAULT_ROT_X
        self.rot_y = DEFAULT_ROT_Y

        self._last_mouse_pos: QPoint | None = None
        self._facelets: Dict[str, List[str]] = {
            "U": ["W"] * 9,
            "D": ["Y"] * 9,
            "F": ["G"] * 9,
            "B": ["B"] * 9,
            "R": ["R"] * 9,
            "L": ["O"] * 9,
        }

    def sizeHint(self) -> QSize:
        return QSize(220, 180)

    # ── Public API ───────────────────────────────────────────────────

    def update_state(self, facelets: Dict[str, List[str]]) -> None:
        """Update facelet colors and repaint."""
        self._facelets = {k: list(v) for k, v in facelets.items()}
        self.update()

    def reset(self) -> None:
        """Reset facelets to solved state and angles to default."""
        self._facelets = {
            "U": ["W"] * 9,
            "D": ["Y"] * 9,
            "F": ["G"] * 9,
            "B": ["B"] * 9,
            "R": ["R"] * 9,
            "L": ["O"] * 9,
        }
        self.rot_x = DEFAULT_ROT_X
        self.rot_y = DEFAULT_ROT_Y
        self.update()

    # ── Mouse Interaction ────────────────────────────────────────────

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self._last_mouse_pos = event.pos()
            event.accept()

    def mouseMoveEvent(self, event: QMouseEvent):
        if self._last_mouse_pos is not None:
            delta = event.pos() - self._last_mouse_pos
            self._last_mouse_pos = event.pos()
            # Sensitivity factor
            self.rot_y += delta.x() * 0.012
            self.rot_x -= delta.y() * 0.012
            # Clamp X rotation to prevent flipping upside down
            self.rot_x = max(-math.pi / 2 + 0.05, min(math.pi / 2 - 0.05, self.rot_x))
            self.update()
            event.accept()

    def mouseReleaseEvent(self, event: QMouseEvent):
        self._last_mouse_pos = None
        event.accept()

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        """Double click resets viewing angle."""
        self.rot_x = DEFAULT_ROT_X
        self.rot_y = DEFAULT_ROT_Y
        self.update()
        event.accept()

    # ── Painting ────────────────-------------------------------------

    def paintEvent(self, event: QPaintEvent | None):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        w = self.width()
        h = self.height()
        cx = w / 2.0
        cy = h / 2.0

        # Scale factor based on widget size
        base_size = min(w, h)
        scale = base_size * 0.22

        # Perspective distance (camera z distance)
        camera_dist = 6.5

        # 1. Transform face normals and determine which 3 faces are visible
        visible_faces: List[Tuple[str, float]] = []
        for face_name, norm in _FACE_NORMALS.items():
            tx_norm = _transform(norm, self.rot_x, self.rot_y)
            # Normal facing camera (Z > 0)
            if tx_norm[2] > 0.02:
                visible_faces.append((face_name, tx_norm[2]))

        # Sort visible faces by distance/normal Z so back-most of the visible faces draw first
        visible_faces.sort(key=lambda t: t[1])

        # Draw dark cube core background behind stickers
        painter.setPen(QPen(QColor(BORDER_PEN_COLOR), 1.5))

        # 2. Collect visible facelet quads, sort by average depth (Z), and paint
        quads_to_render = []

        for face_name, _ in visible_faces:
            face_norm = _FACE_NORMALS[face_name]
            tx_norm = _transform(face_norm, self.rot_x, self.rot_y)

            # Compute diffuse lighting factor
            dot = max(0.0, tx_norm[0] * LIGHT[0] + tx_norm[1] * LIGHT[1] + tx_norm[2] * LIGHT[2])
            light_factor = 0.65 + 0.35 * dot

            color_list = self._facelets.get(face_name, ["W"] * 9)
            raw_quads = _FACELET_QUADS[face_name]

            for idx in range(9):
                raw_v = raw_quads[idx]
                transformed_v = [_transform(p, self.rot_x, self.rot_y) for p in raw_v]

                # Project each vertex to 2D screen coords with perspective
                screen_pts = []
                avg_z = 0.0
                for px, py, pz in transformed_v:
                    persp = camera_dist / (camera_dist - pz)
                    sx = cx + px * scale * persp
                    sy = cy - py * scale * persp
                    screen_pts.append(QPointF(sx, sy))
                    avg_z += pz
                avg_z /= 4.0

                c_char = color_list[idx] if idx < len(color_list) else "W"
                base_hex = COLOR_MAP.get(c_char, "#FFFFFF")
                base_color = QColor(base_hex)

                # Apply shading
                shaded_r = min(255, int(base_color.red() * light_factor))
                shaded_g = min(255, int(base_color.green() * light_factor))
                shaded_b = min(255, int(base_color.blue() * light_factor))
                final_color = QColor(shaded_r, shaded_g, shaded_b)

                quads_to_render.append((avg_z, screen_pts, final_color))

        # Sort all quads by depth (farthest first)
        quads_to_render.sort(key=lambda t: t[0])

        # Draw all quads
        for _, pts, col in quads_to_render:
            poly = QPolygonF(pts)
            painter.setBrush(col)
            painter.drawPolygon(poly)

        painter.end()
