"""
BinTimer — Smart Cube Post-Solve Analytics Dialog with Tabs
═══════════════════════════════════════════════════════════
Displays detailed telemetry, CFOP phase breakdowns (with Recognition vs. Execution times),
and full move reconstructions organized in clean tabs.
"""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QGuiApplication
from PyQt6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

try:
    from bintimer.solve_analyzer import SolveAnalysis
except ImportError:
    from solve_analyzer import SolveAnalysis


class AnalyticsDialog(QDialog):
    """Modern tabbed modal dialog displaying CFOP phase breakdown and reconstruction."""

    def __init__(self, analysis: SolveAnalysis, parent: QWidget | None = None):
        super().__init__(parent)
        self.analysis = analysis
        self.setWindowTitle("📊 Smart Cube Solve Analytics")
        self.setObjectName("analyticsDialog")
        self.resize(760, 580)
        self.setMinimumSize(640, 500)
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(16)

        # ── Header with Global Stats ─────────────────────────────────
        header_frame = QFrame()
        header_frame.setStyleSheet(
            "background-color: #262626; border: 1px solid #3a3a3a; border-radius: 10px; padding: 12px;"
        )
        hl = QHBoxLayout(header_frame)
        hl.setContentsMargins(8, 4, 8, 4)

        def make_stat(title_text: str, val_text: str, color_hex: str = "#f5f5f5") -> QVBoxLayout:
            lay = QVBoxLayout()
            lay.setSpacing(2)
            lbl = QLabel(title_text.upper())
            lbl.setStyleSheet("color: #858585; font-size: 10px; font-weight: 600;")
            val = QLabel(val_text)
            val.setStyleSheet(f"color: {color_hex}; font-size: 22px; font-weight: 700; font-family: 'Roboto Mono';")
            lay.addWidget(lbl)
            lay.addWidget(val)
            return lay

        hl.addLayout(make_stat("Total Time", self.analysis.total_time_str, "#66bb6a"))
        hl.addSpacing(20)
        hl.addLayout(make_stat("Total Turns", f"{self.analysis.total_turns} moves", "#42a5f5"))
        hl.addSpacing(20)
        hl.addLayout(make_stat("Overall TPS", f"{self.analysis.overall_tps:.2f}", "#ffa726"))
        hl.addSpacing(20)
        hl.addLayout(make_stat("Cross Face", f"{self.analysis.cross_face} Face", "#ab47bc"))
        hl.addStretch()

        root.addWidget(header_frame)

        # ── Tabbed Widget ────────────────────────────────────────────
        self.tabs = QTabWidget()
        self.tabs.setObjectName("analyticsTabs")
        self.tabs.setStyleSheet(
            "QTabWidget::pane { border: 1px solid #3a3a3a; background-color: #262626; border-radius: 8px; }"
            "QTabBar::tab { background-color: #1e1e1e; color: #858585; padding: 10px 20px; font-weight: 600; font-size: 12px; border-top-left-radius: 6px; border-top-right-radius: 6px; margin-right: 4px; }"
            "QTabBar::tab:selected { background-color: #262626; color: #f5f5f5; border: 1px solid #3a3a3a; border-bottom: none; }"
            "QTabBar::tab:hover { color: #b3b3b3; }"
        )

        self._build_overview_tab()
        self._build_steps_tab()
        self._build_solution_tab()

        root.addWidget(self.tabs, 1)

        # ── Bottom Action Row ────────────────────────────────────────
        btn_row = QHBoxLayout()
        copy_btn = QPushButton("📋  Copy Solution")
        copy_btn.setStyleSheet(
            "background-color: #2c2c2c; color: #b3b3b3; border: 1px solid #3a3a3a;"
            "border-radius: 6px; padding: 8px 16px; font-size: 11px;"
        )
        copy_btn.clicked.connect(self._copy_reconstruction)
        btn_row.addWidget(copy_btn)
        btn_row.addStretch()

        close_btn = QPushButton("✕  Close")
        close_btn.setStyleSheet(
            "background-color: #1b5e20; color: #a5d6a7; border: 1px solid #2e7d32;"
            "border-radius: 6px; padding: 8px 24px; font-weight: 600; font-size: 12px;"
        )
        close_btn.clicked.connect(self.accept)
        btn_row.addWidget(close_btn)

        root.addLayout(btn_row)

    # ── Tab 1: Overview ──────────────────────────────────────────────

    def _build_overview_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(14)

        intro = QLabel("CFOP High-Level Solve Breakdown")
        intro.setStyleSheet("font-size: 14px; font-weight: 600; color: #f5f5f5;")
        layout.addWidget(intro)

        # Group phases into Cross, F2L, OLL, PLL
        cross_info = next((p for p in self.analysis.phases if p.name == "Cross"), None)
        f2l_phases = [p for p in self.analysis.phases if p.name.startswith("F2L")]
        oll_info = next((p for p in self.analysis.phases if p.name == "OLL"), None)
        pll_info = next((p for p in self.analysis.phases if p.name == "PLL"), None)

        f2l_time = sum(p.time_ms for p in f2l_phases)
        f2l_turns = sum(p.move_count for p in f2l_phases)
        f2l_pct = sum(p.pct_time for p in f2l_phases)

        cards_row = QHBoxLayout()
        cards_row.setSpacing(10)

        def make_phase_card(title: str, dur_ms: int, turns: int, pct: float, color: str) -> QFrame:
            card = QFrame()
            card.setStyleSheet(
                f"background-color: #1e1e1e; border: 1px solid #3a3a3a; border-left: 4px solid {color};"
                "border-radius: 6px; padding: 12px;"
            )
            cl = QVBoxLayout(card)
            cl.setSpacing(4)
            t_lbl = QLabel(title)
            t_lbl.setStyleSheet("font-size: 12px; font-weight: 700; color: #f5f5f5;")
            cl.addWidget(t_lbl)
            time_lbl = QLabel(f"{dur_ms / 1000.0:.2f}s")
            time_lbl.setStyleSheet(f"font-size: 18px; font-weight: 700; color: {color}; font-family: 'Roboto Mono';")
            cl.addWidget(time_lbl)
            sub = QLabel(f"{turns} moves  ·  {pct:.1f}%")
            sub.setStyleSheet("font-size: 11px; color: #858585;")
            cl.addWidget(sub)
            return card

        cards_row.addWidget(make_phase_card("Cross", cross_info.time_ms if cross_info else 0, cross_info.move_count if cross_info else 0, cross_info.pct_time if cross_info else 0.0, "#42a5f5"), 1)
        cards_row.addWidget(make_phase_card("F2L (All 4)", f2l_time, f2l_turns, f2l_pct, "#66bb6a"), 1)
        cards_row.addWidget(make_phase_card("OLL", oll_info.time_ms if oll_info else 0, oll_info.move_count if oll_info else 0, oll_info.pct_time if oll_info else 0.0, "#ffa726"), 1)
        cards_row.addWidget(make_phase_card("PLL", pll_info.time_ms if pll_info else 0, pll_info.move_count if pll_info else 0, pll_info.pct_time if pll_info else 0.0, "#ab47bc"), 1)

        layout.addLayout(cards_row)

        summary_box = QFrame()
        summary_box.setStyleSheet("background-color: #1e1e1e; border: 1px solid #3a3a3a; border-radius: 6px; padding: 12px;")
        sbl = QVBoxLayout(summary_box)
        summary_title = QLabel("Telemetry Insights")
        summary_title.setStyleSheet("font-size: 12px; font-weight: 600; color: #b3b3b3;")
        sbl.addWidget(summary_title)

        total_recog = sum(p.recognition_ms for p in self.analysis.phases)
        total_exec = sum(p.execution_ms for p in self.analysis.phases)
        recog_pct = (total_recog / self.analysis.total_time_ms * 100.0) if self.analysis.total_time_ms > 0 else 0.0
        exec_pct = (total_exec / self.analysis.total_time_ms * 100.0) if self.analysis.total_time_ms > 0 else 0.0

        insights = QLabel(
            f"• Recognition / Pause Time: <b>{total_recog/1000.0:.2f}s</b> ({recog_pct:.1f}% of solve)\n"
            f"• Active Turning Time: <b>{total_exec/1000.0:.2f}s</b> ({exec_pct:.1f}% of solve)\n"
            f"• Average Execution TPS: <b>{(self.analysis.total_turns / (total_exec/1000.0) if total_exec > 0 else 0.0):.2f} turns/sec</b>\n"
            f"• Cross Orientation: <b>{self.analysis.cross_face} layer first</b>"
        )
        insights.setStyleSheet("color: #cccccc; font-size: 12px; line-height: 1.6;")
        sbl.addWidget(insights)
        layout.addWidget(summary_box)
        layout.addStretch()

        self.tabs.addTab(tab, "📊 Overview")

    # ── Tab 2: Steps Table ───────────────────────────────────────────

    def _build_steps_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(14, 14, 14, 14)

        table = QTableWidget()
        table.setColumnCount(7)
        table.setHorizontalHeaderLabels([
            "Phase", "Total Time", "Recognition", "Execution", "Turns", "Exec TPS", "Split %"
        ])
        table.verticalHeader().setVisible(False)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        table.setStyleSheet(
            "QTableWidget { background-color: #1e1e1e; border: 1px solid #3a3a3a; border-radius: 6px; gridline-color: #303030; }"
            "QHeaderView::section { background-color: #2c2c2c; color: #b3b3b3; border: none; padding: 6px; font-weight: 600; font-size: 11px; }"
            "QTableWidget::item { padding: 6px 8px; color: #f5f5f5; font-family: 'Roboto Mono'; font-size: 11px; }"
        )
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        phases = self.analysis.phases
        table.setRowCount(len(phases))

        for row, p in enumerate(phases):
            # Phase Name
            name_item = QTableWidgetItem(p.name)
            name_item.setFont(QFont("Inter", 10, QFont.Weight.Bold))
            table.setItem(row, 0, name_item)

            # Total Time
            time_item = QTableWidgetItem(p.time_str)
            time_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            table.setItem(row, 1, time_item)

            # Recognition
            recog_item = QTableWidgetItem(p.recognition_str)
            recog_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            recog_item.setForeground(Qt.GlobalColor.cyan)
            table.setItem(row, 2, recog_item)

            # Execution
            exec_item = QTableWidgetItem(p.execution_str)
            exec_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            exec_item.setForeground(Qt.GlobalColor.green)
            table.setItem(row, 3, exec_item)

            # Turns
            turns_item = QTableWidgetItem(str(p.move_count))
            turns_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            table.setItem(row, 4, turns_item)

            # Execution TPS
            tps_item = QTableWidgetItem(f"{p.execution_tps:.2f}")
            tps_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if p.execution_tps >= 4.0:
                tps_item.setForeground(Qt.GlobalColor.green)
            table.setItem(row, 5, tps_item)

            # Split %
            split_item = QTableWidgetItem(f"{p.pct_time:.1f}%")
            split_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            table.setItem(row, 6, split_item)

        layout.addWidget(table)
        self.tabs.addTab(tab, "⏱ Steps Table")

    # ── Tab 3: Solution List ─────────────────────────────────────────

    def _build_solution_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        recon_lbl = QLabel("Reconstructed Move Sequence by Phase:")
        recon_lbl.setStyleSheet("color: #b3b3b3; font-size: 11px; font-weight: 600;")
        layout.addWidget(recon_lbl)

        self.recon_edit = QPlainTextEdit()
        self.recon_edit.setReadOnly(True)
        self.recon_edit.setPlainText(self.analysis.get_reconstruction_text())
        self.recon_edit.setStyleSheet(
            "background-color: #1e1e1e; color: #90caf9; border: 1px solid #3a3a3a;"
            "border-radius: 6px; font-family: 'Roboto Mono'; font-size: 12px; padding: 10px; line-height: 1.5;"
        )
        layout.addWidget(self.recon_edit, 1)

        self.tabs.addTab(tab, "📝 Solution List")

    # ── Actions ──────────────────────────────────────────────────────

    def _copy_reconstruction(self):
        clipboard = QGuiApplication.clipboard()
        if clipboard:
            text = (
                f"BinTimer Solve Analysis\n"
                f"Time: {self.analysis.total_time_str} | Turns: {self.analysis.total_turns} | TPS: {self.analysis.overall_tps:.2f}\n"
                f"{'=' * 50}\n"
                f"{self.analysis.get_reconstruction_text()}\n"
            )
            clipboard.setText(text)
            self.sender().setText("✓ Copied!")
