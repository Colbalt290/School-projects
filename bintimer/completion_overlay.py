"""
BinTimer — Completion Overlay
═════════════════════════════
Semi-transparent overlay card shown when a solve or PvP match finishes.
Displays rankings, medals, solve times, random quotes, and a button to view
full CFOP analytics.
"""

from __future__ import annotations

import os
import random
from typing import Dict, List, Optional, Tuple

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QPainter, QPixmap
from PyQt6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget,
)

try:
    from bintimer.player_zone import format_time_ms
    from bintimer.analytics_dialog import AnalyticsDialog
    from bintimer.solve_analyzer import SolveAnalysis
except ImportError:
    from player_zone import format_time_ms
    from analytics_dialog import AnalyticsDialog
    from solve_analyzer import SolveAnalysis

QUOTES = [
    "Pang kids lang diba?",
    "KVL lang yan.",
    "Tah keh hom eh",
    "Hello Hello Hello",
    "Ayun Ayun Ayun",
    "Kidstincts",
    "LEOOO LEOOO LEOOO",
]


def effective_time_ms(ms: int, penalty: str = "") -> int:
    if penalty.lower() == "dnf":
        return 999_999_999
    if penalty == "+2":
        return ms + 2_000
    return ms


class _CompletionCard(QFrame):
    """Card container that absorbs clicks so the overlay is not prematurely dismissed."""
    def mousePressEvent(self, ev):
        ev.accept()


class CompletionOverlay(QWidget):
    """
    Semi-transparent overlay covering the window when every player finishes.
    """

    closed = pyqtSignal()

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName("completionOverlay")
        self.hide()
        self._analyses: Dict[int, SolveAnalysis] = {}
        self._build_ui()

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.card = _CompletionCard()
        self.card.setObjectName("completionCard")
        self.card.setMaximumWidth(620)
        cl = QVBoxLayout(self.card)
        cl.setSpacing(18)
        cl.setContentsMargins(36, 36, 36, 36)

        self.title_label = QLabel()
        self.title_label.setObjectName("completionTitle")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setProperty("role", "heading")
        cl.addWidget(self.title_label)

        self.image_label = QLabel()
        self.image_label.setObjectName("completionImage")
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setMaximumHeight(260)
        cl.addWidget(self.image_label)

        self.rankings_label = QLabel()
        self.rankings_label.setObjectName("rankingsLabel")
        self.rankings_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.rankings_label.setWordWrap(True)
        cl.addWidget(self.rankings_label)

        self.quote_label = QLabel()
        self.quote_label.setObjectName("quoteLabel")
        self.quote_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.quote_label.setWordWrap(True)
        cl.addWidget(self.quote_label)

        btn_box = QHBoxLayout()
        btn_box.setSpacing(12)
        btn_box.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.analytics_btn = QPushButton("📊  View CFOP Analytics")
        self.analytics_btn.setObjectName("analyticsBtn")
        self.analytics_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.analytics_btn.setStyleSheet(
            "background-color: #1e3a5f; color: #90caf9; border: 1px solid #1976d2;"
            "border-radius: 8px; padding: 9px 18px; font-weight: 600; font-size: 13px;"
        )
        self.analytics_btn.clicked.connect(self._open_analytics)
        self.analytics_btn.hide()
        btn_box.addWidget(self.analytics_btn)

        close_btn = QPushButton("✕  Close")
        close_btn.setObjectName("overlayCloseBtn")
        close_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        close_btn.clicked.connect(self._dismiss)
        btn_box.addWidget(close_btn)

        cl.addLayout(btn_box)
        outer.addWidget(self.card)

    def _open_analytics(self):
        if not self._analyses:
            return
        pid = next(iter(self._analyses))
        analysis = self._analyses[pid]
        dlg = AnalyticsDialog(analysis, self)
        dlg.exec()

    def show_results(
        self,
        ranked: List[Tuple[int, int, str]],  # [(pid, ms, penalty), ...]
        image_path: Optional[str] = None,
        *,
        mode: str = "pvp",
        analyses: Optional[Dict[int, SolveAnalysis]] = None,
    ):
        self._analyses = analyses or {}
        if self._analyses:
            self.analytics_btn.show()
        else:
            self.analytics_btn.hide()

        if image_path and os.path.isfile(image_path):
            px = QPixmap(image_path).scaledToHeight(
                240, Qt.TransformationMode.SmoothTransformation,
            )
            self.image_label.setPixmap(px)
        else:
            self.image_label.setText("🏆")

        if mode == "solo":
            self.title_label.setText("🏁  Solve Complete!")
            pid, ms, pen = ranked[0]
            eff = effective_time_ms(ms, pen)
            base_str = format_time_ms(eff, pen)
            if pid in self._analyses:
                a = self._analyses[pid]
                self.rankings_label.setText(f"{base_str}\n\n⚡ {a.total_turns} moves · {a.overall_tps:.2f} TPS")
            else:
                self.rankings_label.setText(base_str)
        else:
            self.title_label.setText("🏁  Match Complete!")
            medals = {1: "🥇", 2: "🥈", 3: "🥉"}
            ordinal = {1: "1st", 2: "2nd", 3: "3rd", 4: "4th"}
            lines: List[str] = []
            for rank, (pid, ms, pen) in enumerate(ranked, 1):
                m = medals.get(rank, "    ")
                o = ordinal.get(rank, f"{rank}th")
                eff = effective_time_ms(ms, pen)
                lines.append(f"{m}  {o}   Player {pid}   {format_time_ms(eff, pen)}")
            self.rankings_label.setText("\n".join(lines))

        self.quote_label.setText(f'"{random.choice(QUOTES)}"')

        if self.parent():
            self.setGeometry(self.parent().rect())
        self.raise_()
        self.show()

    def paintEvent(self, ev):
        p = QPainter(self)
        p.fillRect(self.rect(), QColor(0, 0, 0, 185))
        p.end()

    def _dismiss(self):
        self.hide()
        self.closed.emit()

    def mousePressEvent(self, ev):
        self._dismiss()
