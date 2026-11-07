"""
BinTimer — Main Window
══════════════════════
Central GUI window managing screen navigation (Setup Screen <-> Timer View),
player zone layouts, keyboard shortcuts, match lifecycle, and post-solve
analytics integration.

Decoupled from low-level BLE and state logic via `BLEManager` and `TimerStateMachine`.
"""

from __future__ import annotations

import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QKeySequence, QShortcut
from PyQt6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QMainWindow,
    QPushButton, QStackedWidget, QVBoxLayout, QWidget,
)

try:
    from bintimer.core.ble_manager import BLEManager
    from bintimer.core.timer_state_machine import TimerStateMachine, TimerPhase
    from bintimer.config_screen import ConfigScreen, MatchConfig
    from bintimer.player_zone import PlayerZone, effective_time_ms, format_time_ms
    from bintimer.completion_overlay import CompletionOverlay
    from bintimer.scramble import generate_scramble
    from bintimer.solve_analyzer import analyze_solve, SolveAnalysis
except ImportError:
    from core.ble_manager import BLEManager
    from core.timer_state_machine import TimerStateMachine, TimerPhase
    from config_screen import ConfigScreen, MatchConfig
    from player_zone import PlayerZone, effective_time_ms, format_time_ms
    from completion_overlay import CompletionOverlay
    from scramble import generate_scramble
    from solve_analyzer import analyze_solve, SolveAnalysis

# Default keybinds for PvP players
KEYBINDS: Dict[int, str] = {1: "Q", 2: "P", 3: "Z", 4: "M"}

IMAGE_NAMES = [
    "hello.png", "hello.jpg", "hello.jpeg", "hello.bmp", "hello.gif",
    "completion.png", "completion.jpg",
]


class MainWindow(QMainWindow):
    """
    Main Application Window for BinTimer.
    Hosts ConfigScreen and TimerPage within a QStackedWidget.
    """

    def __init__(self, base_dir: str, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.base_dir = base_dir
        self.setWindowTitle("BinTimer — Smart Cube & PvP Speedcubing Timer")
        self.setObjectName("mainWindow")
        self.resize(1100, 720)

        # 1. Global BLE Singleton & Core State Machines
        self.ble_manager = BLEManager.get_instance()
        self.timer_state_machines: Dict[int, TimerStateMachine] = {}

        # 2. Match Configuration & Tracking
        self._config: Optional[MatchConfig] = None
        self._current_scramble: str = ""
        self._match_running: bool = False
        self._match_phase: str = "scrambling"  # "scrambling" | "warning" | "inspecting" | "solving" | "stopped"
        self._finish_order: List[Tuple[int, int, str]] = []  # [(pid, elapsed_ms, penalty), ...]
        self._last_analysis: Dict[int, SolveAnalysis] = {}

        # 3. Dynamic UI components
        self.zones: Dict[int, PlayerZone] = {}
        self._shortcuts: List[QShortcut] = []

        # 4. Warning Countdown Timer (3.. 2.. 1.. before inspection)
        self._warning_timer = QTimer(self)
        self._warning_timer.setInterval(1000)
        self._warning_timer.timeout.connect(self._on_warning_tick)
        self._warning_count: int = 3

        # 5. UI Stack Setup
        self._stack = QStackedWidget(self)
        self.setCentralWidget(self._stack)

        # Page 0: Config Setup Screen
        self._config_screen = ConfigScreen(self)
        self._config_screen.start_requested.connect(self._on_config_start)
        self._stack.addWidget(self._config_screen)

        # Page 1: Timer Page (placeholder widget)
        self._timer_page = QWidget()
        self._stack.addWidget(self._timer_page)

        self._stack.setCurrentIndex(0)

        # 6. Global Completion Overlay
        self.overlay = CompletionOverlay(self)
        self.overlay.closed.connect(self._on_overlay_closed)

        # Permanent Global Shortcuts
        self._setup_global_shortcuts()

        # Connect BLE status notifications to status bar
        self.ble_manager.status_changed.connect(
            lambda msg: self.statusBar().showMessage(f"BLE: {msg}", 4000)
        )
        self.ble_manager.error_occurred.connect(
            lambda err: self.statusBar().showMessage(f"⚠ BLE: {err}", 5000)
        )

        self.statusBar().showMessage("Ready — Select mode and click Start")

    # ── Image Discovery ──────────────────────────────────────────────

    def _find_image(self) -> Optional[str]:
        for name in IMAGE_NAMES:
            for sub in ("", "UI"):
                path = os.path.join(self.base_dir, sub, name)
                if os.path.isfile(path):
                    return path
        return None

    # ── Screen Navigation ────────────────────────────────────────────

    def _on_config_start(self, config: MatchConfig) -> None:
        """User clicked Start on Config Screen."""
        self._config = config
        self._build_timer_view()
        self._new_scramble()
        self._stack.setCurrentIndex(1)
        self.statusBar().showMessage(
            f"Mode: {config.mode.upper()} ({config.player_count} player{'s' if config.player_count > 1 else ''}) — Ready for scramble",
            4000
        )

    def _go_to_config(self) -> None:
        """Return to the setup configuration screen."""
        if self._match_running and self._match_phase not in ("scrambling", "stopped"):
            return  # Prevent accidental navigation mid-solve
        self.reset_match()
        self._stack.setCurrentIndex(0)
        self.statusBar().showMessage("Setup Screen", 2000)

    # ── Timer View Construction ──────────────────────────────────────

    def _build_timer_view(self) -> None:
        assert self._config is not None

        # Clean up old timer page and shortcuts
        old_page = self._timer_page
        self._stack.removeWidget(old_page)
        old_page.deleteLater()

        for sc in self._shortcuts:
            sc.setEnabled(False)
            sc.deleteLater()
        self._shortcuts.clear()
        self.zones.clear()

        # Build new Timer Page
        page = QWidget()
        page.setObjectName("centralWidget")
        self._timer_page = page
        self._stack.addWidget(page)

        root = QVBoxLayout(page)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(14)

        # ── Scramble & Action Control Bar ────────────────────────────
        control_frame = QFrame()
        control_frame.setObjectName("scramblePanel")
        cl = QVBoxLayout(control_frame)
        cl.setContentsMargins(20, 14, 20, 14)
        cl.setSpacing(8)

        # Top Bar: Back Button + Title
        top_row = QHBoxLayout()
        self._back_btn = QPushButton("←  Setup")
        self._back_btn.setObjectName("backButton")
        self._back_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._back_btn.clicked.connect(self._go_to_config)

        self._heading_label = QLabel("MATCH SETUP")
        self._heading_label.setObjectName("matchHeading")
        self._heading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        top_row.addWidget(self._back_btn)
        top_row.addStretch()
        top_row.addWidget(self._heading_label)
        top_row.addStretch()
        # Invisible spacer matching back button width for symmetry
        spacer = QWidget()
        spacer.setFixedWidth(80)
        top_row.addWidget(spacer)
        cl.addLayout(top_row)

        # Scramble Display
        self._scramble_label = QLabel("Generating scramble...")
        self._scramble_label.setObjectName("scrambleLabel")
        self._scramble_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._scramble_label.setWordWrap(True)
        cl.addWidget(self._scramble_label)

        # Bottom Button Bar: New Scramble + Ready / Start
        btn_bar = QHBoxLayout()
        btn_bar.setSpacing(12)

        self._new_scr_btn = QPushButton("🔄  New Scramble")
        self._new_scr_btn.setObjectName("newScrambleButton")
        self._new_scr_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._new_scr_btn.clicked.connect(self._new_scramble)

        self.start_btn = QPushButton("⏵   Ready  (Space)")
        self.start_btn.setObjectName("startButton")
        self.start_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.start_btn.clicked.connect(self._on_start_match_clicked)

        btn_bar.addStretch()
        btn_bar.addWidget(self._new_scr_btn)
        btn_bar.addWidget(self.start_btn)
        btn_bar.addStretch()
        cl.addLayout(btn_bar)

        root.addWidget(control_frame)

        # ── Player Zones ─────────────────────────────────────────────
        zone_row = QHBoxLayout()
        zone_row.setSpacing(12)

        count = self._config.player_count
        for pid in range(1, count + 1):
            cube_type = self._config.cube_types.get(pid, "normal")
            is_ble = (cube_type == "bluetooth")

            # Get or create persistent state machine for this player slot
            if pid not in self.timer_state_machines:
                self.timer_state_machines[pid] = TimerStateMachine(
                    ble_manager=self.ble_manager, parent=self, enable_ble=is_ble
                )
            else:
                self.timer_state_machines[pid].enable_ble(is_ble)

            sm = self.timer_state_machines[pid]
            key = "Space" if self._config.mode == "solo" else KEYBINDS.get(pid, f"P{pid}")

            zone = PlayerZone(
                player_id=pid,
                keybind=key,
                timer_sm=sm,
                cube_type=cube_type,
                parent=page,
            )
            zone.timer_stopped.connect(self._on_player_stopped)

            if self._config.mode == "solo":
                zone.name_label.setText("Timer")

            self.zones[pid] = zone
            zone_row.addWidget(zone, 1)

        root.addLayout(zone_row, 1)

        # ── Register Dynamic Key Shortcuts ───────────────────────────
        self._register_zone_shortcuts()

        # Reparent overlay to ensure it sits on top of the new page
        self.overlay.setParent(self)
        self.overlay.setGeometry(self.rect())

    def _setup_global_shortcuts(self) -> None:
        # Spacebar shortcut
        space = QShortcut(QKeySequence(Qt.Key.Key_Space), self)
        space.activated.connect(self._on_space_pressed)

        # Escape shortcut
        esc = QShortcut(QKeySequence(Qt.Key.Key_Escape), self)
        esc.activated.connect(self._on_escape_pressed)

        # Tab shortcut (Sync smart cubes)
        tab = QShortcut(QKeySequence(Qt.Key.Key_Tab), self)
        tab.activated.connect(self._on_tab_pressed)

    def _register_zone_shortcuts(self) -> None:
        if not self._config or self._config.mode == "solo":
            return

        key_map = {
            1: Qt.Key.Key_Q,
            2: Qt.Key.Key_P,
            3: Qt.Key.Key_Z,
            4: Qt.Key.Key_M,
        }
        for pid, key in key_map.items():
            if pid in self.zones:
                sc = QShortcut(QKeySequence(key), self)
                sc.activated.connect(lambda p=pid: self._on_player_key_activated(p))
                self._shortcuts.append(sc)

    # ── Match Lifecycle & Transitions ────────────────────────────────

    def _new_scramble(self) -> None:
        """Generate a new WCA 20-move scramble and configure all state machines."""
        self._current_scramble = generate_scramble(20)
        self._scramble_label.setText(self._current_scramble)
        self._finish_order.clear()
        self._last_analysis.clear()
        self._match_running = False
        self._match_phase = "scrambling"
        self._heading_label.setText("SCRAMBLING")

        for pid, sm in self.timer_state_machines.items():
            if pid in self.zones:
                is_ble = (self._config and self._config.cube_types.get(pid) == "bluetooth")
                sm.setup_round(self._current_scramble, live_scramble_track=False)
                self.zones[pid].reset_display()

        self.start_btn.setEnabled(True)
        self._new_scr_btn.setEnabled(True)
        self._back_btn.setEnabled(True)

    def _on_start_match_clicked(self) -> None:
        """User pressed Start/Ready button."""
        if self._match_running and self._match_phase not in ("scrambling", "stopped"):
            return

        if self._config and self._config.inspection_enabled:
            self._trigger_warning_phase()
        else:
            self._start_all_direct_solves()

    def _trigger_warning_phase(self) -> None:
        """Warning countdown ('Inspection in 3... 2... 1...') prior to inspection."""
        self._match_phase = "warning"
        self._match_running = True
        self._finish_order.clear()

        self.start_btn.setEnabled(False)
        self._new_scr_btn.setEnabled(False)
        self._back_btn.setEnabled(False)
        self.overlay.hide()

        self._warning_count = 3
        self._heading_label.setText("GET READY FOR INSPECTION")
        for z in self.zones.values():
            z.timer_label.setText("3")
            z.status_label.setText("Inspection in 3...")
            z._set_visual_state("warning")
        self._warning_timer.start()

    def _on_warning_tick(self) -> None:
        self._warning_count -= 1
        if self._warning_count > 0:
            for z in self.zones.values():
                z.timer_label.setText(str(self._warning_count))
                z.status_label.setText(f"Inspection in {self._warning_count}...")
        else:
            self._warning_timer.stop()
            self._start_inspection_phase()

    def _start_inspection_phase(self) -> None:
        """Enter INSPECTION phase for all active players."""
        self._match_phase = "inspecting"
        self._heading_label.setText("⏱  INSPECTION")

        for pid in self.zones:
            sm = self.timer_state_machines.get(pid)
            if sm:
                sm.start_inspection()

    def _start_all_direct_solves(self) -> None:
        """Direct start without inspection countdown."""
        self._match_phase = "solving"
        self._match_running = True
        self._heading_label.setText("MATCH IN PROGRESS")
        self.start_btn.setEnabled(False)
        self._new_scr_btn.setEnabled(False)
        self._back_btn.setEnabled(False)

        for pid in self.zones:
            sm = self.timer_state_machines.get(pid)
            if sm:
                sm.manual_start_solve()

    def _on_player_stopped(self, pid: int, elapsed_ms: int, penalty: str) -> None:
        """One player finished their solve."""
        self._finish_order.append((pid, elapsed_ms, penalty))

        # Check if all active players in this match have finished
        if len(self._finish_order) >= len(self.zones):
            self._on_all_players_finished()

    def _on_all_players_finished(self) -> None:
        """All players finished. Compute rankings, CFOP analysis, and show overlay."""
        self._match_running = False
        self._match_phase = "stopped"
        self._heading_label.setText("SOLVE COMPLETE")
        self.start_btn.setEnabled(True)
        self._new_scr_btn.setEnabled(True)
        self._back_btn.setEnabled(True)

        # Sort ranked results: fastest effective time first, DNF last
        ranked = sorted(
            self._finish_order,
            key=lambda x: effective_time_ms(x[1], x[2])
        )

        # Award medals/ranks to zones
        medals = {1: "🥇 #1 WINNER", 2: "🥈 #2", 3: "🥉 #3", 4: "4th"}
        for rank, (pid, _ms, _pen) in enumerate(ranked, 1):
            if pid in self.zones:
                self.zones[pid].rank_label.setText(medals.get(rank, f"#{rank}"))

        # Run CFOP Phase Analysis for Smart Cube players
        for pid in self.zones:
            sm = self.timer_state_machines.get(pid)
            if sm and sm.solve_moves:
                try:
                    moves_ms = [(m, int(t * 1000)) for m, t in sm.solve_moves]
                    total_ms = int(sm.elapsed_solve_seconds * 1000)
                    analysis = analyze_solve(self._current_scramble, moves_ms, total_ms)
                    self._last_analysis[pid] = analysis
                except Exception as e:
                    print(f"[BinTimer] CFOP analysis failed for Player {pid}: {e}")

        # Save record to solves.txt
        self._save_results_to_file(ranked)

        # Display Completion Overlay
        image_path = self._find_image()
        mode = self._config.mode if self._config else "pvp"
        self.overlay.show_results(
            ranked=ranked,
            image_path=image_path,
            mode=mode,
            analyses=self._last_analysis,
        )

    # ── Input & Key Handlers ─────────────────────────────────────────

    def _on_space_pressed(self) -> None:
        if self._stack.currentIndex() != 1:
            return

        # If match is scrambling / not yet running, Space starts the match / inspection
        if self._match_phase == "scrambling" or not self._match_running:
            self._on_start_match_clicked()
        elif self._config and self._config.mode == "solo":
            # For solo manual cubes, Space triggers action
            z = self.zones.get(1)
            if z:
                z.player_action()

    def _on_player_key_activated(self, pid: int) -> None:
        if self._match_running and pid in self.zones:
            self.zones[pid].player_action()

    def _on_escape_pressed(self) -> None:
        if self.overlay.isVisible():
            self.overlay.hide()
            return
        if self._stack.currentIndex() == 1:
            if self._match_running and self._match_phase not in ("scrambling", "stopped"):
                self.reset_match()
            else:
                self._go_to_config()

    def _on_tab_pressed(self) -> None:
        """Tab key: quickly resync all active virtual cubes (Green Front, White Top)."""
        for sm in self.timer_state_machines.values():
            if sm.phase == TimerPhase.SCRAMBLING and sm._current_scramble:
                sm.sync_cube_scramble()
            else:
                sm.sync_cube_solved()
        self.statusBar().showMessage("Synced active virtual cubes (Green Front, White Top) ✓", 3000)

    def _on_overlay_closed(self) -> None:
        self.statusBar().showMessage("Ready for next match — click 'New Scramble' or press Space", 4000)

    def reset_match(self) -> None:
        """Reset the match back to scrambling state."""
        self._warning_timer.stop()
        self._match_running = False
        self._match_phase = "scrambling"
        self._finish_order.clear()
        self._last_analysis.clear()

        for sm in self.timer_state_machines.values():
            sm.reset()

        for z in self.zones.values():
            z.reset_display()

        self._new_scramble()

    # ── Persistence (solves.txt) ─────────────────────────────────────

    def _save_results_to_file(self, ranked: List[Tuple[int, int, str]]) -> None:
        path = os.path.join(self.base_dir, "solves.txt")
        mode = self._config.mode if self._config else "pvp"
        count = self._config.player_count if self._config else 1

        try:
            with open(path, "a", encoding="utf-8") as f:
                f.write(f"\n{'=' * 56}\n")
                now_str = datetime.now().strftime("%Y-%m-%d  %H:%M:%S")
                if mode == "solo":
                    f.write(f"  Solo Solve  •  {now_str}\n")
                else:
                    f.write(f"  PvP Match ({count} Players)  •  {now_str}\n")
                f.write(f"  Scramble: {self._current_scramble}\n")
                f.write(f"{'-' * 56}\n")

                if mode == "solo":
                    pid, ms, pen = ranked[0]
                    eff = effective_time_ms(ms, pen)
                    f.write(f"   Final Time: {format_time_ms(eff, pen)}\n")
                    if pid in self._last_analysis:
                        a = self._last_analysis[pid]
                        f.write(f"   Turns: {a.total_turns} moves | TPS: {a.overall_tps:.2f}\n")
                        f.write("   CFOP Breakdown:\n")
                        for p in a.phases:
                            f.write(f"     {p.name:<7}: {p.moves_str} ({p.time_str}, {p.tps:.2f} TPS)\n")
                else:
                    ord_map = {1: "1st", 2: "2nd", 3: "3rd", 4: "4th"}
                    for rank, (pid, ms, pen) in enumerate(ranked, 1):
                        eff = effective_time_ms(ms, pen)
                        f.write(f"   {ord_map.get(rank, f'#{rank}'):>3}  Player {pid}  —  {format_time_ms(eff, pen)}\n")
                        if pid in self._last_analysis:
                            a = self._last_analysis[pid]
                            f.write(f"         Turns: {a.total_turns} | TPS: {a.overall_tps:.2f}\n")
                f.write(f"{'=' * 56}\n")
        except OSError as e:
            print(f"[BinTimer] Could not write to solves.txt: {e}")

    # ── Resize Overlay Event ─────────────────────────────────────────

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        if self.overlay and self.overlay.isVisible():
            self.overlay.setGeometry(self.rect())
