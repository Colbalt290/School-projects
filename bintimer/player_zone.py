"""
BinTimer — Player Zone View Component
═════════════════════════════════════
Modern, decoupled UI display zone for a single player (Solo or PvP).
Binds directly to a persistent `TimerStateMachine` and `BLEManager` instance.
"""

from __future__ import annotations

from typing import Optional

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget,
)

try:
    from bintimer.core.timer_state_machine import TimerStateMachine, TimerPhase
    from bintimer.core.ble_manager import BLEManager
    from bintimer.cube_visualizer_3d import CubeVisualizer3D
    from bintimer.cube_scan_dialog import CubeScanDialog
except ImportError:
    from core.timer_state_machine import TimerStateMachine, TimerPhase
    from core.ble_manager import BLEManager
    from cube_visualizer_3d import CubeVisualizer3D
    from cube_scan_dialog import CubeScanDialog


def format_time_ms(ms: int, penalty: str = "") -> str:
    """Format milliseconds into MM:SS.mmm."""
    if penalty.lower() == "dnf":
        return "DNF"
    minutes = ms // 60_000
    seconds = (ms % 60_000) // 1_000
    millis  = ms % 1_000
    base = f"{minutes:02d}:{seconds:02d}.{millis:03d}"
    if penalty == "+2":
        return f"{base}  (+2)"
    return base


def format_time_sec(seconds: float, penalty: str = "") -> str:
    """Format seconds into MM:SS.mmm."""
    return format_time_ms(int(seconds * 1000), penalty)


def effective_time_ms(ms: int, penalty: str = "") -> int:
    """Effective ranking time (penalty added, DNF sorts last)."""
    if penalty.lower() == "dnf":
        return 999_999_999
    if penalty == "+2":
        return ms + 2_000
    return ms


class PlayerZone(QFrame):
    """
    Presentation widget representing one player's timer and cube view.
    Listens to the player's TimerStateMachine and updates reactive UI elements.
    """

    timer_stopped = pyqtSignal(int, int, str)  # pid, elapsed_ms, penalty
    solve_started = pyqtSignal(int)            # pid

    def __init__(
        self,
        player_id: int,
        keybind: str,
        timer_sm: TimerStateMachine,
        cube_type: str = "normal",
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.player_id = player_id
        self.keybind = keybind
        self.timer_sm = timer_sm
        self._cube_type = cube_type  # "normal" | "bluetooth"

        # Local visual state cache
        self.elapsed_ms: int = 0
        self.penalty: str = ""

        # UI Styling Setup
        self.setObjectName("playerZone")
        self.setProperty("player", str(player_id))
        self.setProperty("state", "idle")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(240)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        self._build_ui()
        self._bind_state_machine()
        self._update_cube_type_ui()

    # ── UI Construction ──────────────────────────────────────────────

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 20, 16, 16)
        root.setSpacing(6)

        # 1. Player Name
        self.name_label = QLabel(f"Player {self.player_id}")
        self.name_label.setObjectName("playerName")
        self.name_label.setProperty("player", str(self.player_id))
        self.name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(self.name_label)

        # 2. Rank Label (shown upon match completion)
        self.rank_label = QLabel("")
        self.rank_label.setObjectName("rankLabel")
        self.rank_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(self.rank_label)

        # 3. Main Timer Display
        self.timer_label = QLabel("00:00.000")
        self.timer_label.setObjectName("playerTimer")
        self.timer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(self.timer_label)

        # 4. Penalty Label
        self.penalty_label = QLabel("")
        self.penalty_label.setObjectName("penaltyLabel")
        self.penalty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(self.penalty_label)

        # 5. Keybind indicator pill
        self.key_label = QLabel(self.keybind)
        self.key_label.setObjectName("keycapLabel")
        self.key_label.setProperty("role", "keycap")
        self.key_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.key_label.setFixedWidth(54)

        key_row = QHBoxLayout()
        key_row.addStretch()
        key_row.addWidget(self.key_label)
        key_row.addStretch()
        root.addLayout(key_row)

        # 6. Status text
        self.status_label = QLabel("Waiting")
        self.status_label.setObjectName("playerStatus")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(self.status_label)

        # 7. Move & TPS telemetry
        self.move_label = QLabel("")
        self.move_label.setObjectName("moveLabel")
        self.move_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(self.move_label)

        # 8. 3D Cube Visualizer
        self.visualizer = CubeVisualizer3D()
        self.visualizer.setMaximumHeight(180)
        self.visualizer.setMinimumHeight(140)
        root.addWidget(self.visualizer)

        # 9. Smart Cube Control Buttons
        btn_row = QHBoxLayout()
        self.ble_button = QPushButton("🔗  Connect Cube")
        self.ble_button.setObjectName("bleButton")
        self.ble_button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.ble_button.clicked.connect(self._on_ble_connect_clicked)

        self.sync_button = QPushButton("🔄  Sync Cube")
        self.sync_button.setObjectName("syncButton")
        self.sync_button.setToolTip("Sync virtual cube to reference Green Front / White Top")
        self.sync_button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.sync_button.clicked.connect(self._on_sync_clicked)

        btn_row.addWidget(self.ble_button)
        btn_row.addWidget(self.sync_button)
        root.addLayout(btn_row)

    # ── State Machine Binding ────────────────────────────────────────

    def _bind_state_machine(self) -> None:
        """Bind state machine signals directly to the presentation widgets."""
        self.timer_sm.phase_changed.connect(self._on_phase_changed)
        self.timer_sm.inspection_tick.connect(self._on_inspection_tick)
        self.timer_sm.inspection_penalty_changed.connect(self._on_penalty_changed)
        self.timer_sm.solve_started.connect(self._on_solve_started)
        self.timer_sm.solve_tick.connect(self._on_solve_tick)
        self.timer_sm.move_applied.connect(self._on_move_applied)
        self.timer_sm.cube_state_updated.connect(self.visualizer.update_state)
        self.timer_sm.solve_finished.connect(self._on_solve_finished)
        self.timer_sm.scramble_matched.connect(self._on_scramble_matched)

        # Initial state sync
        self.visualizer.update_state(self.timer_sm.virtual_cube.get_state())

    def _update_cube_type_ui(self) -> None:
        is_ble = (self._cube_type == "bluetooth")
        self.ble_button.setVisible(is_ble)
        self.sync_button.setVisible(is_ble)
        self.visualizer.setVisible(is_ble)
        self.move_label.setVisible(is_ble)

        if is_ble:
            ble = BLEManager.get_instance()
            if ble.is_connected:
                dev = ble.connected_device_name or "Smart Cube"
                self.ble_button.setText(f"✓ {dev}")
            else:
                self.ble_button.setText("🔗  Connect Cube")

    @property
    def cube_type(self) -> str:
        return self._cube_type

    @cube_type.setter
    def cube_type(self, value: str) -> None:
        self._cube_type = value
        self._update_cube_type_ui()

    # ── Reactive Slots ───────────────────────────────────────────────

    def _set_visual_state(self, state_str: str) -> None:
        self.setProperty("state", state_str)
        self.style().unpolish(self)
        self.style().polish(self)

    def _on_phase_changed(self, phase: TimerPhase) -> None:
        if phase == TimerPhase.SCRAMBLING:
            self._set_visual_state("idle")
            self.status_label.setText("Scramble your cube" if self._cube_type == "bluetooth" else "Ready")
        elif phase == TimerPhase.INSPECTION:
            self._set_visual_state("inspecting")
            self.status_label.setText("First turn starts timer!" if self._cube_type == "bluetooth" else "Inspecting")
        elif phase == TimerPhase.SOLVING:
            self._set_visual_state("running")
            self.status_label.setText("SOLVING!")
        elif phase == TimerPhase.SOLVED:
            self._set_visual_state("stopped")
            self.status_label.setText("SOLVED! ✓")

    def _on_inspection_tick(self, remaining: int) -> None:
        self.timer_label.setText(str(remaining))

    def _on_penalty_changed(self, penalty: str) -> None:
        self.penalty = penalty
        self.penalty_label.setText(penalty)
        if penalty == "+2":
            self._set_visual_state("overtime")
        elif penalty == "DNF":
            self._set_visual_state("dnf")

    def _on_solve_started(self) -> None:
        self._set_visual_state("running")
        self.status_label.setText("SOLVING!")
        self.solve_started.emit(self.player_id)

    def _on_solve_tick(self, elapsed_sec: float) -> None:
        self.elapsed_ms = int(elapsed_sec * 1000)
        self.timer_label.setText(format_time_sec(elapsed_sec, self.penalty))

    def _on_move_applied(self, move: str, is_solved: bool) -> None:
        if self.timer_sm.phase == TimerPhase.SCRAMBLING:
            matched, total = self.timer_sm.get_scramble_progress()
            if self.timer_sm.is_scrambled:
                self.status_label.setText("✓ Scramble Matched! Ready (Space)")
                self._set_visual_state("ready")
            elif matched > 0 and total > 0:
                self.status_label.setText(f"Scrambling: {matched}/{total} moves matched")
            else:
                self.status_label.setText("Scramble your cube to match!")
            return

        count = self.timer_sm.move_count
        tps = self.timer_sm.current_tps
        if count > 0:
            self.move_label.setText(f"{count} moves  ({tps:.2f} TPS)")

    def _on_solve_finished(self, elapsed_sec: float, moves: int, tps: float, penalty: str) -> None:
        self.elapsed_ms = int(elapsed_sec * 1000)
        self.penalty = penalty
        self.timer_label.setText(format_time_sec(elapsed_sec, penalty))
        self.move_label.setText(f"{moves} moves  ({tps:.2f} TPS)")
        self._set_visual_state("stopped")
        self.status_label.setText("SOLVED! ✓")
        self.timer_stopped.emit(self.player_id, self.elapsed_ms, penalty)

    def _on_scramble_matched(self) -> None:
        self.status_label.setText("✓ Scramble Matched! Ready (Space)")
        self._set_visual_state("ready")

    # ── User Interaction (Clicks / Keybinds) ─────────────────────────

    def player_action(self) -> None:
        """
        Invoked when the player taps their zone or presses their shortcut key.
        Handles normal manual timer actions safely without interrupting smart cube BLE solves.
        """
        # If using smart cube in SOLVING mode, strictly ignore manual stops!
        # The cube must be solved physically.
        if self._cube_type == "bluetooth" and self.timer_sm.phase == TimerPhase.SOLVING:
            return

        # For normal cubes or inspection trigger:
        if self.timer_sm.phase == TimerPhase.SCRAMBLING:
            if self._cube_type == "bluetooth" and not self.timer_sm.is_scrambled:
                self.status_label.setText("⚠ Scramble to match first!")
                return
            self.timer_sm.start_inspection()
        elif self.timer_sm.phase == TimerPhase.INSPECTION:
            self.timer_sm.manual_start_solve()
        elif self.timer_sm.phase == TimerPhase.SOLVING:
            self.timer_sm.manual_stop_solve()

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.player_action()
        super().mousePressEvent(event)

    def _on_ble_connect_clicked(self) -> None:
        dlg = CubeScanDialog(BLEManager.get_instance(), self)
        dlg.device_selected.connect(self._on_device_connected)
        dlg.exec()

    def _on_device_connected(self, name: str, _addr: str) -> None:
        self.ble_button.setText(f"✓ {name}")
        self.status_label.setText(f"Connected to {name}")

    def _on_sync_clicked(self) -> None:
        self.timer_sm.sync_cube_solved()
        self.status_label.setText("Virtual cube reset to SOLVED ✓")

    def reset_display(self) -> None:
        """Reset player zone visual indicators."""
        self.elapsed_ms = 0
        self.penalty = ""
        self.timer_label.setText("00:00.000")
        self.penalty_label.setText("")
        self.rank_label.setText("")
        self.move_label.setText("")
        self.status_label.setText("Waiting")
        self._set_visual_state("idle")
        self.visualizer.update_state(self.timer_sm.virtual_cube.get_state())
