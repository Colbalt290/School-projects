"""
BinTimer — Main Window.

Manages a stacked layout (config screen ↔ timer view),
dynamic player zones, inspection logic, solo / PvP modes,
the completion overlay, BLE integration with virtual cube
state tracking and move-by-move visualization, and data saving.
"""

from __future__ import annotations

import os
import random
from datetime import datetime

from PyQt6.QtCore    import Qt, QElapsedTimer, QEvent, QTimer, pyqtSignal
from PyQt6.QtGui     import QColor, QKeySequence, QPainter, QPixmap, QShortcut
from PyQt6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QMainWindow, QMessageBox,
    QPushButton, QSizePolicy, QStackedWidget, QVBoxLayout, QWidget,
)

from config_screen import ConfigScreen, MatchConfig
from scramble      import generate_scramble
from player_zone   import PlayerZone, format_time, effective_time

try:
    from ble_manager import BleManager, BleWorker, CubeScanDialog, HAS_BLEAK
except Exception:
    HAS_BLEAK = False

try:
    from cube_model         import CubeModel
    from cube_visualizer    import CubeVisualizer
    from cube_visualizer_3d import CubeVisualizer3D
    HAS_CUBE_MODEL = True
except Exception:
    HAS_CUBE_MODEL = False

try:
    from solve_analyzer   import analyze_solve, SolveAnalysis
    from analytics_dialog import AnalyticsDialog
    HAS_ANALYZER = True
except Exception:
    HAS_ANALYZER = False


# ── Constants ────────────────────────────────────────────────────────

QUOTES = [
    "Pang kids lang diba?",
    "KVL lang yan.",
    "Tah keh hom eh",
    "Hello Hello Hello",
    "Ayun Ayun Ayun",
    "Kidstincts",
    "LEOOO LEOOO LEOOO",
]

# Keybinds per player slot (always defined for up to 4)
KEYBINDS: dict[int, str] = {1: "Q", 2: "P", 3: "Z", 4: "M"}

IMAGE_NAMES = [
    "hello.png", "hello.jpg", "hello.jpeg", "hello.bmp", "hello.gif",
    "completion.png", "completion.jpg",
]


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  Completion overlay
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class _CompletionCard(QFrame):
    """Inner card — absorbs clicks so the overlay behind it isn't dismissed."""
    def mousePressEvent(self, ev):
        ev.accept()


class CompletionOverlay(QWidget):
    """
    Semi-transparent overlay shown when every player has finished.

    Adapts its content for solo vs PvP mode.
    """

    closed = pyqtSignal()

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("completionOverlay")
        self.hide()
        self._build()

    def _build(self):
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

        self._analyses: dict[int, "SolveAnalysis"] = {}

    def _open_analytics(self):
        if not self._analyses or not HAS_ANALYZER:
            return
        # Display analytics for first available player
        pid = next(iter(self._analyses))
        analysis = self._analyses[pid]
        dlg = AnalyticsDialog(analysis, self)
        dlg.exec()

    # ── Public ───────────────────────────────────────────────────────

    def show_results(
        self,
        ranked: list[tuple[int, int, str]],
        image_path: str | None,
        *,
        mode: str = "pvp",
        analyses: dict[int, "SolveAnalysis"] | None = None,
    ):
        """
        Populate and display the overlay.

        *ranked* is ``[(player_id, elapsed_ms, penalty), ...]``
        sorted by effective time (fastest first, DNFs last).
        """
        self._analyses = analyses or {}
        if self._analyses and HAS_ANALYZER:
            self.analytics_btn.show()
        else:
            self.analytics_btn.hide()
        # Image
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
            eff = effective_time(ms, pen)
            base_str = format_time(eff, pen)
            if pid in self._analyses:
                a = self._analyses[pid]
                self.rankings_label.setText(f"{base_str}\n\n⚡ {a.total_turns} moves · {a.overall_tps:.2f} TPS")
            else:
                self.rankings_label.setText(base_str)
        else:
            self.title_label.setText("🏁  Match Complete!")
            medals  = {1: "🥇", 2: "🥈", 3: "🥉"}
            ordinal = {1: "1st", 2: "2nd", 3: "3rd", 4: "4th"}
            lines: list[str] = []
            for rank, (pid, ms, pen) in enumerate(ranked, 1):
                m = medals.get(rank, "    ")
                o = ordinal.get(rank, f"{rank}th")
                eff = effective_time(ms, pen)
                lines.append(
                    f"{m}  {o}   Player {pid}   {format_time(eff, pen)}"
                )
            self.rankings_label.setText("\n".join(lines))

        self.quote_label.setText(f'"{random.choice(QUOTES)}"')

        if self.parent():
            self.setGeometry(self.parent().rect())
        self.raise_()
        self.show()

    # ── Paint translucent backdrop ───────────────────────────────────

    def paintEvent(self, ev):
        p = QPainter(self)
        p.fillRect(self.rect(), QColor(0, 0, 0, 185))
        p.end()

    # ── Dismiss ──────────────────────────────────────────────────────

    def _dismiss(self):
        self.hide()
        self.closed.emit()

    def mousePressEvent(self, ev):
        self._dismiss()
        ev.accept()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  Main window
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class MainWindow(QMainWindow):
    """
    Top-level window with a config screen and a dynamic timer view.

    Supports solo (1 player) and PvP (2-4 players) modes, optional
    WCA-style inspection, per-player Bluetooth/normal cube selection,
    and a fully resizable desktop layout.
    """

    def __init__(self, base_dir: str):
        super().__init__()
        self.base_dir = base_dir
        self.setWindowTitle("BinTimer")
        self.setMinimumSize(800, 500)

        # Accept multi-touch at the top level
        self.setAttribute(Qt.WidgetAttribute.WA_AcceptTouchEvents, True)

        # Shared state
        self._config: MatchConfig | None = None
        self._match_running  = False
        self._finish_order: list[tuple[int, int, str]] = []   # (pid, ms, penalty)
        self._current_scramble = ""
        self._image_path = self._find_image()

        # Inspection state
        self._inspection_running = False
        self._inspection_elapsed = QElapsedTimer()
        self._inspection_tick = QTimer(self)
        self._inspection_tick.setInterval(30)       # ≈ 33 Hz
        self._inspection_tick.timeout.connect(self._on_inspection_tick)

        # Persistent BLE connection manager singleton
        if HAS_BLEAK:
            self._ble_mgr = BleManager.get_instance()
            self._ble_mgr.move_detected.connect(self._on_cube_move)
            self._ble_mgr.cube_solved.connect(self._on_cube_solved)
            self._ble_mgr.connected.connect(self._on_cube_connected)
            self._ble_mgr.disconnected.connect(self._on_cube_disconnected)
            self._ble_mgr.status_changed.connect(
                lambda pid, msg: self.statusBar().showMessage(f"Player {pid}: {msg}", 4000)
            )
            self._ble_mgr.error_occurred.connect(
                lambda pid, msg: self.statusBar().showMessage(f"⚠ Player {pid}: {msg}", 4000)
            )
        else:
            self._ble_mgr = None

        # Warning countdown timer (3.. 2.. 1.. before inspection)
        self._warning_timer = QTimer(self)
        self._warning_timer.setInterval(1000)
        self._warning_timer.timeout.connect(self._on_warning_tick)
        self._warning_count = 3

        # Scramble matching and phase tracking
        self._target_cube = CubeModel() if HAS_CUBE_MODEL else None
        self._match_phase = "scrambling"  # scrambling | warning | inspecting | solving | stopped

        # Virtual cube models and visualizers (one per BLE player)
        self._cube_models:      dict[int, "CubeModel"]      = {}
        self._cube_visualizers: dict[int, "CubeVisualizer3D"] = {}
        self._ble_move_counts:  dict[int, int]               = {}
        self._solve_moves:      dict[int, list[tuple[str, int]]] = {}
        self._last_analysis:    dict[int, "SolveAnalysis"]  = {}

        # Keyboard shortcuts (managed dynamically)
        self._shortcuts: list[QShortcut] = []

        # Player zones (populated per match)
        self.zones: dict[int, PlayerZone] = {}

        # Overlay (created once, reparented later)
        self.overlay: CompletionOverlay | None = None

        self._build_chrome()

    # ── Image discovery ──────────────────────────────────────────────

    def _find_image(self) -> str | None:
        for name in IMAGE_NAMES:
            for sub in ("", "UI"):
                path = os.path.join(self.base_dir, sub, name)
                if os.path.isfile(path):
                    return path
        try:
            for f in os.listdir(self.base_dir):
                if os.path.splitext(f)[1].lower() in (
                    ".png", ".jpg", ".jpeg", ".bmp", ".gif",
                ):
                    return os.path.join(self.base_dir, f)
        except OSError:
            pass
        return None

    # ── Top-level UI (stacked widget) ────────────────────────────────

    def _build_chrome(self):
        self._stack = QStackedWidget()
        self._stack.setObjectName("centralWidget")
        self.setCentralWidget(self._stack)

        # Page 0 — Config
        self._config_screen = ConfigScreen()
        self._config_screen.start_requested.connect(self._on_config_start)
        self._stack.addWidget(self._config_screen)

        # Page 1 — Timer (placeholder; rebuilt each match)
        self._timer_page = QWidget()
        self._stack.addWidget(self._timer_page)

        self._stack.setCurrentIndex(0)

        # Permanent shortcuts (work on both pages)
        esc = QShortcut(QKeySequence(Qt.Key.Key_Escape), self)
        esc.activated.connect(self._on_escape)

        self.statusBar().showMessage("Ready")

    # ── Transition: config → timer ───────────────────────────────────

    def _on_config_start(self, config: MatchConfig):
        self._config = config
        self._build_timer_view()
        self._stack.setCurrentIndex(1)

    # ── Timer view construction (dynamic) ────────────────────────────

    def _build_timer_view(self):
        assert self._config is not None

        # Tear down previous timer page
        old = self._timer_page
        self._stack.removeWidget(old)
        old.deleteLater()

        # Clean up old shortcuts (except Escape which is permanent)
        for sc in self._shortcuts:
            sc.setEnabled(False)
            sc.deleteLater()
        self._shortcuts.clear()

        # Clean up old zones and cube models
        self.zones.clear()
        self._cube_models.clear()
        self._cube_visualizers.clear()
        self._ble_move_counts.clear()
        self._solve_moves.clear()
        self._last_analysis.clear()

        # New timer page
        page = QWidget()
        page.setObjectName("centralWidget")
        self._timer_page = page
        self._stack.addWidget(page)

        root = QVBoxLayout(page)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(12)

        # ── Scramble / control panel ─────────────────────────────────
        scr_frame = QFrame()
        scr_frame.setObjectName("scramblePanel")
        sl = QVBoxLayout(scr_frame)
        sl.setContentsMargins(24, 16, 24, 16)
        sl.setSpacing(10)

        # Top row: back button + heading
        top_row = QHBoxLayout()
        self._back_btn = QPushButton("←  Setup")
        self._back_btn.setObjectName("backButton")
        self._back_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._back_btn.clicked.connect(self._go_to_config)
        top_row.addWidget(self._back_btn)
        top_row.addStretch()

        self._heading_label = QLabel("NEXT SCRAMBLE")
        self._heading_label.setObjectName("scrambleHeading")
        top_row.addWidget(self._heading_label)
        top_row.addStretch()

        # Spacer to balance the back button
        spacer = QWidget()
        spacer.setFixedWidth(self._back_btn.sizeHint().width())
        top_row.addWidget(spacer)

        sl.addLayout(top_row)

        # Scramble text
        self.scramble_label = QLabel()
        self.scramble_label.setObjectName("scrambleText")
        self.scramble_label.setWordWrap(True)
        self.scramble_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sl.addWidget(self.scramble_label)

        # Controls row
        btn_row = QHBoxLayout()
        btn_row.setSpacing(14)
        btn_row.addStretch()

        self.start_btn = QPushButton("⏵   Start Match")
        self.start_btn.setObjectName("startButton")
        self.start_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.start_btn.clicked.connect(self.start_match)

        self.reset_btn = QPushButton("↺   Reset")
        self.reset_btn.setObjectName("resetButton")
        self.reset_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.reset_btn.clicked.connect(self.reset_match)

        btn_row.addWidget(self.start_btn)
        btn_row.addWidget(self.reset_btn)
        btn_row.addStretch()
        sl.addLayout(btn_row)

        # Hint line (dynamic)
        self._hint_label = QLabel()
        self._hint_label.setProperty("role", "muted")
        self._hint_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sl.addWidget(self._hint_label)

        root.addWidget(scr_frame)

        # ── Player zones ─────────────────────────────────────────────
        zone_row = QHBoxLayout()
        zone_row.setSpacing(8)

        count = self._config.player_count
        active_keys = {}

        if self._config.mode == "solo":
            active_keys = {1: "Space"}
        else:
            for pid in range(1, count + 1):
                active_keys[pid] = KEYBINDS[pid]

        for pid in range(1, count + 1):
            kb = active_keys.get(pid, "")
            zone = PlayerZone(pid, kb)
            zone.cube_type = self._config.cube_types.get(pid, "normal")
            zone.timer_stopped.connect(self._on_timer_stopped)
            zone.solve_started.connect(self._on_solve_started)
            if zone.cube_type == "bluetooth":
                # Check persistent singleton connection state!
                if self._ble_mgr and self._ble_mgr.is_connected(pid):
                    zone.ble_connected = True
                    self.statusBar().showMessage(
                        f"Player {pid}: Smart cube active ✓ ({self._ble_mgr.get_device_name(pid)})", 3000
                    )
                else:
                    zone.ble_connected = False

                zone.ble_button.clicked.connect(
                    lambda checked, p=pid: self._on_ble_toggle(p, checked)
                )
                zone.sync_requested.connect(self._on_sync_requested)
                # Create virtual cube model + 3D visualizer
                if HAS_CUBE_MODEL:
                    model = CubeModel()
                    self._cube_models[pid] = model
                    vis = CubeVisualizer3D()
                    vis.setMaximumHeight(190)
                    self._cube_visualizers[pid] = vis
                    zone._visualizer_slot.addWidget(vis)
                self._ble_move_counts[pid] = 0
            # Solo mode: label just "Timer" instead of "Player 1"
            if self._config.mode == "solo":
                zone.name_label.setText("Timer")
            self.zones[pid] = zone
            zone_row.addWidget(zone, 1)

        root.addLayout(zone_row, 1)

        # ── Overlay ──────────────────────────────────────────────────
        self.overlay = CompletionOverlay(page)
        self.overlay.closed.connect(self._on_overlay_closed)

        # ── Dynamic shortcuts ────────────────────────────────────────
        self._bind_keys(active_keys)

        # ── Hint text ────────────────────────────────────────────────
        self._update_hint(active_keys)

        # ── Initial scramble ─────────────────────────────────────────
        self._new_scramble()
        self._match_running = False
        self._finish_order.clear()

    # ── Keyboard shortcuts ───────────────────────────────────────────

    def _bind_keys(self, active_keys: dict[int, str]):
        # Space — start match / done scrambling
        sc = QShortcut(QKeySequence(Qt.Key.Key_Space), self)
        sc.activated.connect(self._on_space)
        self._shortcuts.append(sc)

        # Tab — Sync/Reset Virtual Cube (BLE)
        sc_tab = QShortcut(QKeySequence(Qt.Key.Key_Tab), self)
        sc_tab.activated.connect(self._on_sync_active_cubes)
        self._shortcuts.append(sc_tab)

        if self._config and self._config.mode == "pvp":
            for pid, ch in active_keys.items():
                key = getattr(Qt.Key, f"Key_{ch}")
                sc = QShortcut(QKeySequence(key), self)
                sc.activated.connect(
                    lambda p=pid: self.zones[p].player_action()
                )
                self._shortcuts.append(sc)

    def _update_hint(self, active_keys: dict[int, str]):
        has_ble = any(z.cube_type == "bluetooth" for z in self.zones.values())
        if self._config and self._config.mode == "solo":
            parts = []
            if has_ble:
                parts.append("Space — done scrambling → inspect")
                parts.append("Turn cube — start solve")
                parts.append("Tab — sync cube")
            else:
                parts.append("Space — start / stop")
                if self._config.inspection_enabled:
                    parts.append("inspection → solve → stop")
            parts.append("Esc — back")
        else:
            keys_str = " / ".join(active_keys.values())
            parts = [
                "Space — done scrambling / start",
                "Esc — back / reset",
                f"{keys_str} — stop player",
            ]
            if has_ble:
                parts.append("Tab — sync cube")
        self._hint_label.setText("  ·  ".join(parts))

    # ── Scramble ─────────────────────────────────────────────────────

    def _new_scramble(self):
        self._current_scramble = generate_scramble(20)
        self.scramble_label.setText(self._current_scramble)
        self._heading_label.setText("SCRAMBLE CUBE")
        self.start_btn.setText("⏵   Ready (Skip to Inspect)")
        self.start_btn.setEnabled(True)
        self._match_phase = "scrambling"
        self._match_running = False

        # Set target scramble model for auto-detection
        if HAS_CUBE_MODEL:
            self._target_cube = CubeModel()
            try:
                self._target_cube.apply_scramble(self._current_scramble)
            except Exception:
                pass

        for z in self.zones.values():
            z.set_scrambling()

        # Initialise virtual models representing current physical cube state
        for pid, model in self._cube_models.items():
            model.reset()
            vis = self._cube_visualizers.get(pid)
            if vis:
                vis.update_state(model.get_facelets())
            self._ble_move_counts[pid] = 0
            if pid in self._solve_moves:
                self._solve_moves[pid].clear()

    # ═════════════════════════════════════════════════════════════════
    #  Space key handler
    # ═════════════════════════════════════════════════════════════════

    def _on_space(self):
        if self._match_phase == "scrambling" or not self._match_running:
            self.start_match()
        elif self._config and self._config.mode == "solo":
            z = self.zones.get(1)
            if z:
                # Strictly block Space from stopping the solve in Bluetooth Smart Cube mode
                if z.state == "solving" and z._ble_mode and z._ble_connected:
                    return
                z.player_action()

    # ═════════════════════════════════════════════════════════════════
    #  Match flow & Automated Transitions
    # ═════════════════════════════════════════════════════════════════

    def start_match(self):
        """User indicates ready / done scrambling → trigger warning countdown & inspection."""
        if self._match_running and self._match_phase != "scrambling":
            return
        self._trigger_warning_phase()

    def _trigger_warning_phase(self):
        """Transition to brief warning phase ('Inspection in 3... 2... 1...') then inspection."""
        if self._match_phase in ("warning", "inspecting", "solving"):
            return
        self._match_phase = "warning"
        self._match_running = True
        self._finish_order.clear()
        self.start_btn.setEnabled(False)
        self._back_btn.setEnabled(False)
        if self.overlay:
            self.overlay.hide()

        # Reset move recordings
        for pid in self.zones:
            self._solve_moves[pid] = []
            self._ble_move_counts[pid] = 0

        self._warning_count = 3
        self._heading_label.setText("GET READY FOR INSPECTION")
        for z in self.zones.values():
            z.timer_label.setText("3")
            z.status_label.setText("Inspection in 3...")
        self._warning_timer.start()

    def _on_warning_tick(self):
        self._warning_count -= 1
        if self._warning_count > 0:
            for z in self.zones.values():
                z.timer_label.setText(str(self._warning_count))
                z.status_label.setText(f"Inspection in {self._warning_count}...")
        else:
            self._warning_timer.stop()
            self._start_inspection()

    def _start_all_timers(self):
        """Start solve timers for every active zone simultaneously."""
        self._heading_label.setText("MATCH IN PROGRESS")
        self._match_phase = "solving"
        for z in self.zones.values():
            z.start_timer()

    # ── Inspection ───────────────────────────────────────────────────

    def _start_inspection(self):
        self._match_phase = "inspecting"
        self._inspection_running = True
        self._heading_label.setText("⏱  INSPECTION")
        for z in self.zones.values():
            z.start_inspection()
            if z.cube_type == "bluetooth":
                z.status_label.setText("First turn starts timer!")
        self._inspection_elapsed.start()
        self._inspection_tick.start()

    def _on_inspection_tick(self):
        elapsed = self._inspection_elapsed.elapsed()
        any_inspecting = False
        for z in self.zones.values():
            if z.state == "inspecting":
                any_inspecting = True
                z.update_inspection(elapsed)
        if not any_inspecting:
            self._inspection_tick.stop()
            self._inspection_running = False
            if any(z.state == "solving" for z in self.zones.values()):
                self._heading_label.setText("MATCH IN PROGRESS")

    def _on_solve_started(self, pid: int):
        """A player transitioned from inspection → solving."""
        if self._inspection_running:
            elapsed = self._inspection_elapsed.elapsed()
            self.zones[pid].set_inspection_penalty(elapsed)

    # ── Timer stopped ────────────────────────────────────────────────

    def _on_timer_stopped(self, pid: int, ms: int, penalty: str):
        """Slot: a single player just finished."""
        self._finish_order.append((pid, ms, penalty))
        pos = len(self._finish_order)
        self.zones[pid].set_finish_position(pos)

        # Compute post-solve CFOP analytics for BLE player
        if HAS_ANALYZER and pid in self._solve_moves and self._solve_moves[pid]:
            analysis = analyze_solve(
                self._current_scramble,
                self._solve_moves[pid],
                ms,
            )
            self._last_analysis[pid] = analysis

        # All done?
        if all(z.stopped for z in self.zones.values()):
            self._match_complete()

    def _match_complete(self):
        self._match_running = False
        self._inspection_running = False
        self._inspection_tick.stop()
        self._warning_timer.stop()
        self._match_phase = "stopped"
        self.start_btn.setEnabled(True)
        self._back_btn.setEnabled(True)

        # Rank by effective time (DNFs last)
        ranked = sorted(
            self._finish_order,
            key=lambda t: effective_time(t[1], t[2]),
        )
        for rank, (pid, _ms, _pen) in enumerate(ranked, 1):
            self.zones[pid].set_finish_position(rank)

        self._save_data(ranked)

        mode = self._config.mode if self._config else "pvp"
        QTimer.singleShot(400, lambda: self.overlay.show_results(
            ranked, self._image_path, mode=mode, analyses=self._last_analysis,
        ))

        # In solo mode, if smart cube analysis is available, automatically show the AnalyticsDialog!
        if mode == "solo" and 1 in self._last_analysis and HAS_ANALYZER:
            QTimer.singleShot(750, lambda: self._show_analytics_dialog(1))

    def _show_analytics_dialog(self, pid: int = 1):
        if pid in self._last_analysis and HAS_ANALYZER:
            dlg = AnalyticsDialog(self._last_analysis[pid], self)
            dlg.exec()

    def reset_match(self):
        """Reset everything and generate a fresh scramble."""
        self._match_running = False
        self._inspection_running = False
        self._inspection_tick.stop()
        self._warning_timer.stop()
        self._match_phase = "scrambling"
        self._finish_order.clear()
        self.start_btn.setEnabled(True)
        self._back_btn.setEnabled(True)
        if self.overlay:
            self.overlay.hide()
        for z in self.zones.values():
            z.reset()
        for pid, model in self._cube_models.items():
            model.reset()
            self._ble_move_counts[pid] = 0
            if pid in self._solve_moves:
                self._solve_moves[pid].clear()
        self._last_analysis.clear()
        self._new_scramble()
        self.statusBar().showMessage("Reset — ready for next match", 3000)

    # ── Navigation ───────────────────────────────────────────────────

    def _go_to_config(self):
        """Return to the config screen."""
        if self._match_running and self._match_phase not in ("scrambling", "stopped"):
            return      # don't navigate away mid-match
        self.reset_match()
        self._stack.setCurrentIndex(0)

    # ── Data persistence ─────────────────────────────────────────────

    def _save_data(self, ranked: list[tuple[int, int, str]]):
        path = os.path.join(self.base_dir, "solves.txt")
        mode = self._config.mode if self._config else "pvp"
        count = self._config.player_count if self._config else 1
        try:
            with open(path, "a", encoding="utf-8") as f:
                f.write(f"\n{'=' * 52}\n")
                if mode == "solo":
                    f.write(
                        f"  Solo  "
                        f"{datetime.now().strftime('%Y-%m-%d  %H:%M:%S')}\n"
                    )
                else:
                    f.write(
                        f"  PvP Match ({count} players)  "
                        f"{datetime.now().strftime('%Y-%m-%d  %H:%M:%S')}\n"
                    )
                f.write(f"  Scramble: {self._current_scramble}\n")
                f.write(f"{'-' * 52}\n")

                if mode == "solo":
                    _pid, ms, pen = ranked[0]
                    eff = effective_time(ms, pen)
                    time_str = format_time(eff, pen)
                    f.write(f"   Time: {time_str}\n")
                    if _pid in self._last_analysis:
                        a = self._last_analysis[_pid]
                        f.write(f"   Turns: {a.total_turns} moves | TPS: {a.overall_tps:.2f}\n")
                        f.write("   Reconstruction:\n")
                        for p in a.phases:
                            f.write(f"     {p.name:<7}: {p.moves_str} ({p.time_str}, {p.tps:.2f} TPS)\n")
                else:
                    ord_map = {1: "1st", 2: "2nd", 3: "3rd", 4: "4th"}
                    for rank, (pid, ms, pen) in enumerate(ranked, 1):
                        eff = effective_time(ms, pen)
                        time_str = format_time(eff, pen)
                        f.write(
                            f"   {ord_map.get(rank, ''):\u003e3}  "
                            f"Player {pid}  —  {time_str}\n"
                        )
                        if pid in self._last_analysis:
                            a = self._last_analysis[pid]
                            f.write(f"         Turns: {a.total_turns} | TPS: {a.overall_tps:.2f}\n")
                f.write(f"{'=' * 52}\n")
        except OSError as exc:
            print(f"[BinTimer] Could not write solves.txt: {exc}")

    # ═════════════════════════════════════════════════════════════════
    #  BLE integration
    # ═════════════════════════════════════════════════════════════════

    def _on_ble_toggle(self, pid: int, checked: bool):
        if not HAS_BLEAK:
            self.zones[pid].ble_button.setChecked(False)
            QMessageBox.information(
                self,
                "Bluetooth Not Available",
                'BLE smart-cube support requires the "bleak" library.\n\n'
                "Install it with:\n    pip install bleak",
            )
            return
        if checked:
            self._ble_connect(pid)
        else:
            self._ble_disconnect(pid)

    def _ble_connect(self, pid: int):
        if not self._ble_mgr:
            return
        worker = self._ble_mgr.get_worker(pid)
        dlg = CubeScanDialog(worker, self)
        dlg.device_selected.connect(
            lambda name, addr, p=pid: self._ble_finish_connect(p, addr),
        )
        if dlg.exec() != dlg.DialogCode.Accepted:
            if not self._ble_mgr.is_connected(pid):
                self.zones[pid].ble_button.setChecked(False)

    def _ble_finish_connect(self, pid: int, addr: str):
        if not self._ble_mgr:
            return
        worker = self._ble_mgr.get_worker(pid)
        worker.connect_to(addr)

    def _on_cube_connected(self, pid: int, name: str = ""):
        z = self.zones.get(pid)
        if z:
            z.ble_connected = True
        label = f" ({name})" if name else ""
        self.statusBar().showMessage(
            f"Player {pid}: smart cube connected{label} ✓", 4000,
        )

    def _on_cube_disconnected(self, pid: int):
        z = self.zones.get(pid)
        if z:
            z.ble_connected = False
        self.statusBar().showMessage(
            f"Player {pid}: cube disconnected", 4000,
        )

    def _on_sync_requested(self, pid: int):
        """Reset internal virtual cube to solved state to recover from BLE packet drop."""
        model = self._cube_models.get(pid)
        zone = self.zones.get(pid)
        if model:
            model.reset()
            vis = self._cube_visualizers.get(pid)
            if vis:
                vis.update_state(model.get_facelets())
        self._ble_move_counts[pid] = 0
        if pid in self._solve_moves:
            self._solve_moves[pid].clear()
        if zone:
            zone.set_move_count(0)
        self.statusBar().showMessage(f"Player {pid}: Virtual cube synced to SOLVED state ✓", 3000)

    def _on_sync_active_cubes(self):
        """Keybind handler (Tab) to sync virtual cubes."""
        for pid in self._cube_models:
            self._on_sync_requested(pid)

    def _on_cube_move(self, pid: int, move: str):
        """Handle a move detected from a smart cube."""
        zone = self.zones.get(pid)
        if not zone:
            return

        # Phase 1: Scrambling — track moves & auto-detect target scramble match
        if self._match_phase == "scrambling" or zone.state == "scrambling":
            model = self._cube_models.get(pid)
            if model:
                try:
                    model.apply_move(move)
                    vis = self._cube_visualizers.get(pid)
                    if vis:
                        vis.update_state(model.get_facelets())
                    if hasattr(self, "_target_cube") and self._target_cube:
                        if model.get_facelets() == self._target_cube.get_facelets():
                            self.statusBar().showMessage(f"Player {pid}: Scramble matched! Starting inspection...", 3000)
                            self._trigger_warning_phase()
                except Exception as e:
                    print(f"[BinTimer] Scramble move tracking error: {e}")
            return

        # Phase 2: Warning countdown (3.. 2.. 1..) — track moves without starting
        if self._match_phase == "warning":
            model = self._cube_models.get(pid)
            if model:
                try:
                    model.apply_move(move)
                    vis = self._cube_visualizers.get(pid)
                    if vis:
                        vis.update_state(model.get_facelets())
                except Exception:
                    pass
            return

        # Phase 3: Inspection countdown — first physical turn instantly starts the solve timer!
        if zone.state == "inspecting" or self._match_phase == "inspecting":
            zone.start_solve()
            self._match_phase = "solving"
            self._heading_label.setText("MATCH IN PROGRESS")

        # Phase 4: Solving — record telemetry, update TPS, apply to model, and check is_solved
        if zone.state == "solving":
            elapsed_ms = zone.current_elapsed_ms()
            if pid not in self._solve_moves:
                self._solve_moves[pid] = []
            self._solve_moves[pid].append((move, elapsed_ms))

            move_count = len(self._solve_moves[pid])
            tps = (move_count / (elapsed_ms / 1000.0)) if elapsed_ms > 0 else 0.0
            zone.set_move_count(move_count, tps)

            # Apply move to virtual model
            model = self._cube_models.get(pid)
            if model:
                try:
                    model.apply_move(move)
                    vis = self._cube_visualizers.get(pid)
                    if vis:
                        vis.update_state(model.get_facelets())

                    # Hardware-driven stop: solve timer stops ONLY when cube is solved
                    if model.is_solved():
                        zone.stop_timer()
                        self.statusBar().showMessage(
                            f"Player {pid}: Cube solved in {elapsed_ms/1000.0:.2f}s ({move_count} moves, {tps:.2f} TPS)! ✓",
                            5000,
                        )
                except Exception as e:
                    print(f"[BinTimer] Error applying move {move}: {e}")

    def _on_cube_solved(self, pid: int):
        """
        BLE reports the cube state packet is identity.
        The timer will ONLY stop if the virtual cube agrees or after sufficient solve duration.
        """
        zone = self.zones.get(pid)
        if not zone or zone.state != "solving":
            return

        model = self._cube_models.get(pid)
        if model:
            if model.is_solved():
                zone.stop_timer()
            elif zone.current_elapsed_ms() > 3000 and len(self._solve_moves.get(pid, [])) >= 10:
                model.reset()
                vis = self._cube_visualizers.get(pid)
                if vis:
                    vis.update_state(model.get_facelets())
                zone.stop_timer()
        else:
            if zone.current_elapsed_ms() > 2000:
                zone.stop_timer()

    def _ble_disconnect(self, pid: int):
        if self._ble_mgr:
            self._ble_mgr.disconnect_cube(pid)
        z = self.zones.get(pid)
        if z:
            z.ble_connected = False

    # ═════════════════════════════════════════════════════════════════
    #  Events
    # ═════════════════════════════════════════════════════════════════

    def _on_escape(self):
        if self.overlay and self.overlay.isVisible():
            self.overlay.hide()
        elif self._match_running:
            self.reset_match()
        elif self._stack.currentIndex() == 1:
            self._go_to_config()
        elif self.isFullScreen():
            self.showNormal()
        else:
            self.close()

    def _on_overlay_closed(self):
        pass

    # ── Multi-touch routing ──────────────────────────────────────────

    def event(self, ev: QEvent) -> bool:
        t = ev.type()
        if t in (QEvent.Type.TouchBegin, QEvent.Type.TouchUpdate):
            try:
                for pt in ev.points():
                    gpos = pt.globalPosition().toPoint()
                    for zone in self.zones.values():
                        local = zone.mapFromGlobal(gpos)
                        if zone.rect().contains(local):
                            # Block touch stop in BLE mode while solving
                            if zone.state == "solving" and zone._ble_mode and zone._ble_connected:
                                break
                            zone.player_action()
                            break
            except Exception:
                pass
            ev.accept()
            return True
        return super().event(ev)

    def resizeEvent(self, ev):
        super().resizeEvent(ev)
        if self.overlay and self.overlay.parent():
            self.overlay.setGeometry(self.overlay.parent().rect())

    def closeEvent(self, ev):
        if self._ble_mgr:
            self._ble_mgr.stop_all()
        super().closeEvent(ev)
