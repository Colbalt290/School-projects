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
    from ble_manager import BleWorker, CubeScanDialog, HAS_BLEAK
except Exception:
    HAS_BLEAK = False

try:
    from cube_model      import CubeModel
    from cube_visualizer import CubeVisualizer
    HAS_CUBE_MODEL = True
except Exception:
    HAS_CUBE_MODEL = False


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

        close_btn = QPushButton("✕  Close")
        close_btn.setObjectName("overlayCloseBtn")
        close_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        close_btn.clicked.connect(self._dismiss)
        cl.addWidget(close_btn, 0, Qt.AlignmentFlag.AlignCenter)

        outer.addWidget(self.card)

    # ── Public ───────────────────────────────────────────────────────

    def show_results(
        self,
        ranked: list[tuple[int, int, str]],
        image_path: str | None,
        *,
        mode: str = "pvp",
    ):
        """
        Populate and display the overlay.

        *ranked* is ``[(player_id, elapsed_ms, penalty), ...]``
        sorted by effective time (fastest first, DNFs last).
        """
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
            self.rankings_label.setText(format_time(eff, pen))
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

        # BLE workers (lazy, one per player)
        self._ble_workers: dict[int, "BleWorker"] = {}

        # Virtual cube models and visualizers (one per BLE player)
        self._cube_models:      dict[int, "CubeModel"]      = {}
        self._cube_visualizers: dict[int, "CubeVisualizer"]  = {}
        self._ble_move_counts:  dict[int, int]               = {}

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
                zone.ble_button.clicked.connect(
                    lambda checked, p=pid: self._on_ble_toggle(p, checked)
                )
                zone.sync_requested.connect(self._on_sync_requested)
                # Create virtual cube model + visualizer
                if HAS_CUBE_MODEL:
                    model = CubeModel()
                    self._cube_models[pid] = model
                    vis = CubeVisualizer()
                    vis.setMaximumHeight(160)
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
        # Space — start match (or player action in solo)
        sc = QShortcut(QKeySequence(Qt.Key.Key_Space), self)
        sc.activated.connect(self._on_space)
        self._shortcuts.append(sc)

        if self._config and self._config.mode == "pvp":
            for pid, ch in active_keys.items():
                key = getattr(Qt.Key, f"Key_{ch}")
                sc = QShortcut(QKeySequence(key), self)
                sc.activated.connect(
                    lambda p=pid: self.zones[p].player_action()
                )
                self._shortcuts.append(sc)

    def _update_hint(self, active_keys: dict[int, str]):
        if self._config and self._config.mode == "solo":
            parts = ["Space — start / stop", "Esc — back"]
            if self._config.inspection_enabled:
                parts.insert(1, "inspection → solve → stop")
        else:
            keys_str = " / ".join(active_keys.values())
            parts = [
                "Space — start",
                "Esc — back / reset",
                f"{keys_str} — stop player",
            ]
        self._hint_label.setText("  ·  ".join(parts))

    # ── Scramble ─────────────────────────────────────────────────────

    def _new_scramble(self):
        self._current_scramble = generate_scramble(20)
        self.scramble_label.setText(self._current_scramble)
        self._heading_label.setText("NEXT SCRAMBLE")
        # Apply scramble to any active BLE cube models so they match the scramble
        for pid, model in self._cube_models.items():
            model.reset()
            try:
                model.apply_scramble(self._current_scramble)
            except Exception:
                pass
            vis = self._cube_visualizers.get(pid)
            if vis:
                vis.update_state(model.get_facelets())
            self._ble_move_counts[pid] = 0

    # ═════════════════════════════════════════════════════════════════
    #  Space key handler
    # ═════════════════════════════════════════════════════════════════

    def _on_space(self):
        if not self._match_running:
            self.start_match()
        elif self._config and self._config.mode == "solo":
            # In solo mode Space also acts as the player action
            z = self.zones.get(1)
            if z:
                z.player_action()

    # ═════════════════════════════════════════════════════════════════
    #  Match flow
    # ═════════════════════════════════════════════════════════════════

    def start_match(self):
        """Start a match: either inspection phase or direct timers."""
        if self._match_running:
            return
        self._match_running = True
        self._finish_order.clear()
        self.start_btn.setEnabled(False)
        self._back_btn.setEnabled(False)
        if self.overlay:
            self.overlay.hide()

        if self._config and self._config.inspection_enabled:
            self._start_inspection()
        else:
            self._start_all_timers()

    def _start_all_timers(self):
        """Start solve timers for every active zone simultaneously."""
        self._heading_label.setText("MATCH IN PROGRESS")
        for z in self.zones.values():
            z.start_timer()

    # ── Inspection ───────────────────────────────────────────────────

    def _start_inspection(self):
        self._inspection_running = True
        self._heading_label.setText("⏱  INSPECTION")
        for z in self.zones.values():
            z.start_inspection()
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
            # Update heading if anyone is still solving
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

        # All done?
        if all(z.stopped for z in self.zones.values()):
            self._match_complete()

    def _match_complete(self):
        self._match_running = False
        self._inspection_running = False
        self._inspection_tick.stop()
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
            ranked, self._image_path, mode=mode,
        ))

    def reset_match(self):
        """Reset everything and generate a fresh scramble."""
        self._match_running = False
        self._inspection_running = False
        self._inspection_tick.stop()
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
        self._new_scramble()
        self.statusBar().showMessage("Reset — ready for next match", 3000)

    # ── Navigation ───────────────────────────────────────────────────

    def _go_to_config(self):
        """Return to the config screen."""
        if self._match_running:
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
                else:
                    ord_map = {1: "1st", 2: "2nd", 3: "3rd", 4: "4th"}
                    for rank, (pid, ms, pen) in enumerate(ranked, 1):
                        eff = effective_time(ms, pen)
                        time_str = format_time(eff, pen)
                        f.write(
                            f"   {ord_map.get(rank, ''):\u003e3}  "
                            f"Player {pid}  —  {time_str}\n"
                        )
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
        if pid not in self._ble_workers:
            w = BleWorker()
            w.start_loop()
            w.move_detected.connect(lambda mv, p=pid: self._on_cube_move(p, mv))
            w.cube_solved.connect(lambda p=pid: self._on_cube_solved(p))
            w.disconnected.connect(lambda p=pid: self._on_cube_disconnected(p))
            w.status_changed.connect(
                lambda msg: self.statusBar().showMessage(msg, 5000),
            )
            w.error_occurred.connect(
                lambda msg: self.statusBar().showMessage(f"⚠ {msg}", 5000),
            )
            self._ble_workers[pid] = w

        worker = self._ble_workers[pid]
        dlg = CubeScanDialog(worker, self)
        dlg.device_selected.connect(
            lambda name, addr, p=pid: self._ble_finish_connect(p, addr),
        )
        if dlg.exec() != dlg.DialogCode.Accepted:
            self.zones[pid].ble_button.setChecked(False)

    def _ble_finish_connect(self, pid: int, addr: str):
        w = self._ble_workers.get(pid)
        if not w:
            return
        w.connected.connect(
            lambda _a, p=pid: self._on_cube_connected(p),
        )
        w.connect_to(addr)

    def _on_cube_connected(self, pid: int):
        z = self.zones.get(pid)
        if z:
            z.ble_connected = True
        self.statusBar().showMessage(
            f"Player {pid}: smart cube connected ✓", 4000,
        )

    def _on_cube_disconnected(self, pid: int):
        z = self.zones.get(pid)
        if z:
            z.ble_connected = False
        self.statusBar().showMessage(
            f"Player {pid}: cube disconnected", 4000,
        )

    def _on_sync_requested(self, pid: int):
        """Reset and synchronize the virtual cube model with the current scramble."""
        model = self._cube_models.get(pid)
        zone = self.zones.get(pid)
        if model:
            model.reset()
            # If idle or inspecting, re-apply current scramble so visualizer matches
            if zone and zone.state in ("idle", "inspecting"):
                if self._current_scramble:
                    try:
                        model.apply_scramble(self._current_scramble)
                    except Exception:
                        pass
            vis = self._cube_visualizers.get(pid)
            if vis:
                vis.update_state(model.get_facelets())
        self._ble_move_counts[pid] = 0
        if zone:
            zone.set_move_count(0)
        self.statusBar().showMessage(f"Player {pid}: Cube synchronized ✓", 3000)

    def _on_cube_move(self, pid: int, move: str):
        """Handle a move detected from a smart cube."""
        zone = self.zones.get(pid)
        if not zone:
            return

        # If in inspection, first move starts the solve timer!
        if zone.state == "inspecting":
            zone.start_solve()

        # Update move count during solve
        if zone.state == "solving":
            self._ble_move_counts[pid] = self._ble_move_counts.get(pid, 0) + 1
            zone.set_move_count(self._ble_move_counts[pid])

        # Apply move to virtual model
        model = self._cube_models.get(pid)
        if model:
            try:
                model.apply_move(move)
                vis = self._cube_visualizers.get(pid)
                if vis:
                    vis.update_state(model.get_facelets())

                # Check if solve is complete
                if zone.state == "solving" and model.is_solved():
                    zone.stop_timer()
                    self.statusBar().showMessage(
                        f"Player {pid}: Cube solved in {self._ble_move_counts.get(pid, 0)} moves! ✓",
                        4000,
                    )
            except Exception as e:
                print(f"[BinTimer] Error applying move {move}: {e}")

    def _on_cube_solved(self, pid: int):
        """
        BLE reports the cube state packet is identity.
        Only stop if the virtual cube agrees or after sufficient solve duration.
        """
        zone = self.zones.get(pid)
        if not zone or zone.state != "solving":
            return

        model = self._cube_models.get(pid)
        if model:
            if model.is_solved():
                zone.stop_timer()
            elif zone.elapsed_ms > 2000 and self._ble_move_counts.get(pid, 0) > 8:
                # Accept solve if timer ran for > 2s and > 8 moves took place
                model.reset()
                vis = self._cube_visualizers.get(pid)
                if vis:
                    vis.update_state(model.get_facelets())
                zone.stop_timer()
        else:
            if zone.elapsed_ms > 1500:
                zone.stop_timer()

    def _ble_disconnect(self, pid: int):
        w = self._ble_workers.get(pid)
        if w:
            w.disconnect_cube()
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
        for w in self._ble_workers.values():
            try:
                w.stop_loop()
            except Exception:
                pass
        super().closeEvent(ev)
