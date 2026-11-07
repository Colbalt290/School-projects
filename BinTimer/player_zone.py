"""
Player zone widget — supports inspection, penalties, cube-type toggling,
and BLE smart-cube mode with virtual cube tracking.

States
------
``idle`` → ``inspecting`` → ``solving`` → ``stopped``
           (or ``idle`` → ``solving`` → ``stopped`` when inspection is off)

BLE workflow adds ``scrambling`` between ``idle`` and ``inspecting``/``solving``:
``idle`` → ``scrambling`` → ``inspecting`` → ``solving`` → ``stopped``
"""

from __future__ import annotations

from PyQt6.QtCore import Qt, QElapsedTimer, QTimer, pyqtSignal
from PyQt6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout,
)


# ── Constants ────────────────────────────────────────────────────────

INSPECTION_LIMIT_MS = 15_000        # standard 15-second inspection
OVERTIME_WINDOW_MS  =  5_000        # +2 penalty window
DNF_LIMIT_MS        = INSPECTION_LIMIT_MS + OVERTIME_WINDOW_MS   # 20 s


# ── Helpers ──────────────────────────────────────────────────────────

def format_time(ms: int, penalty: str = "") -> str:
    """Format *ms* → ``MM:SS.mmm``, appending penalty indicator."""
    if penalty == "dnf":
        return "DNF"
    minutes = ms // 60_000
    seconds = (ms % 60_000) // 1_000
    millis  = ms % 1_000
    base = f"{minutes:02d}:{seconds:02d}.{millis:03d}"
    if penalty == "+2":
        return f"{base}  (+2)"
    return base


def effective_time(ms: int, penalty: str = "") -> int:
    """Return the ranking-sort value (solve + penalty seconds)."""
    if penalty == "dnf":
        return 999_999_999          # always sort last
    if penalty == "+2":
        return ms + 2_000
    return ms


# ── Widget ───────────────────────────────────────────────────────────

class PlayerZone(QFrame):
    """
    Clickable / tappable zone for a single player.

    Signals
    -------
    timer_stopped(player_id, elapsed_ms, penalty)
        Emitted when the player's solve timer stops.
    solve_started(player_id)
        Emitted when the player transitions from inspection to solving.
    sync_requested(player_id)
        Emitted when the user clicks the Sync/Reset button for BLE cubes.
    """

    timer_stopped  = pyqtSignal(int, int, str)   # pid, ms, penalty
    solve_started  = pyqtSignal(int)             # pid
    sync_requested = pyqtSignal(int)             # pid

    def __init__(self, player_id: int, keybind: str, parent=None):
        super().__init__(parent)
        self.player_id = player_id
        self.keybind   = keybind

        # State
        self._state:    str = "idle"            # idle | scrambling | inspecting | solving | stopped
        self.elapsed_ms:  int = 0
        self.penalty:     str = ""              # "" | "+2" | "dnf"
        self._ble_connected: bool = False
        self._cube_type:     str = "normal"     # "normal" | "bluetooth"
        self._ble_mode:      bool = False       # True when BLE auto-stop is active

        # QSS hooks
        self.setObjectName("playerZone")
        self.setProperty("player", str(player_id))
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(200)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        self._build_ui()
        self._init_timer()

    # ── UI construction ──────────────────────────────────────────────

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 24, 16, 16)

        # Player name
        self.name_label = QLabel(f"Player {self.player_id}")
        self.name_label.setObjectName("playerName")
        self.name_label.setProperty("player", str(self.player_id))
        self.name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Rank (shown after finish)
        self.rank_label = QLabel("")
        self.rank_label.setObjectName("rankLabel")
        self.rank_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Timer display
        self.timer_label = QLabel("00:00.000")
        self.timer_label.setObjectName("playerTimer")
        self.timer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Penalty indicator
        self.penalty_label = QLabel("")
        self.penalty_label.setObjectName("penaltyLabel")
        self.penalty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Keybind hint
        self.key_label = QLabel(self.keybind)
        self.key_label.setObjectName("keycapLabel")
        self.key_label.setProperty("role", "keycap")
        self.key_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.key_label.setFixedWidth(36)

        key_row = QHBoxLayout()
        key_row.addStretch()
        key_row.addWidget(self.key_label)
        key_row.addStretch()

        # Status line
        self.status_label = QLabel("Waiting")
        self.status_label.setObjectName("playerStatus")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Move counter (BLE mode only, shows move count during solve)
        self.move_label = QLabel("")
        self.move_label.setObjectName("moveLabel")
        self.move_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # BLE connect button (hidden when cube_type == "normal")
        self.ble_button = QPushButton("🔗  Connect Cube")
        self.ble_button.setObjectName("bleButton")
        self.ble_button.setCheckable(True)
        self.ble_button.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        # Sync/Reset button (BLE mode only)
        self.sync_button = QPushButton("🔄  Sync / Reset")
        self.sync_button.setObjectName("syncButton")
        self.sync_button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.sync_button.clicked.connect(
            lambda: self.sync_requested.emit(self.player_id)
        )

        # Cube visualizer placeholder — will be set from MainWindow
        self._visualizer_slot = QVBoxLayout()

        # Assemble
        root.addStretch(1)
        root.addWidget(self.name_label)
        root.addSpacing(4)
        root.addWidget(self.rank_label)
        root.addSpacing(10)
        root.addWidget(self.timer_label)
        root.addWidget(self.penalty_label)
        root.addWidget(self.move_label)
        root.addSpacing(6)
        root.addLayout(self._visualizer_slot)
        root.addSpacing(10)
        root.addLayout(key_row)
        root.addSpacing(4)
        root.addWidget(self.status_label)
        root.addStretch(1)
        root.addWidget(self.sync_button, 0, Qt.AlignmentFlag.AlignCenter)
        root.addWidget(self.ble_button, 0, Qt.AlignmentFlag.AlignCenter)

    def _init_timer(self):
        self._elapsed = QElapsedTimer()
        self._tick = QTimer(self)
        self._tick.setInterval(11)              # ≈ 90 Hz
        self._tick.timeout.connect(self._refresh)

    # ── Properties ───────────────────────────────────────────────────

    @property
    def state(self) -> str:
        return self._state

    @property
    def running(self) -> bool:
        return self._state == "solving"

    @property
    def stopped(self) -> bool:
        return self._state == "stopped"

    @property
    def cube_type(self) -> str:
        return self._cube_type

    @cube_type.setter
    def cube_type(self, value: str):
        self._cube_type = value
        is_ble = (value == "bluetooth")
        self.ble_button.setVisible(is_ble)
        self.sync_button.setVisible(is_ble)
        self._ble_mode = is_ble
        # In BLE mode, hide the keycap hint (cube stops via solved detection)
        if is_ble:
            self.key_label.setVisible(False)

    @property
    def ble_connected(self) -> bool:
        return self._ble_connected

    @ble_connected.setter
    def ble_connected(self, value: bool):
        self._ble_connected = value
        self.ble_button.setChecked(value)
        self.ble_button.setText(
            "🟢  Cube Connected" if value else "🔗  Connect Cube"
        )

    # ── Public API ───────────────────────────────────────────────────

    def player_action(self):
        """
        Generic action triggered by keypress, touch, or BLE event.
        Behaviour depends on the current state.

        In BLE mode, keyboard/touch cannot stop the timer — only a
        cube-solved signal from the BLE manager can.
        """
        if self._state == "inspecting":
            self.start_solve()
        elif self._state == "solving":
            # Block manual stop in BLE mode — cube must be solved
            if self._ble_mode and self._ble_connected:
                return
            self.stop_timer()

    # ·· Inspection ···················································

    def start_inspection(self):
        """Enter the inspection phase (called by MainWindow)."""
        self._state = "inspecting"
        self.penalty     = ""
        self.elapsed_ms  = 0
        self.rank_label.setText("")
        self.penalty_label.setText("")
        self.timer_label.setText("15")
        self.status_label.setText("INSPECT")
        self._set_visual_state("inspecting")

    def update_inspection(self, elapsed_ms: int):
        """
        Update the inspection countdown display.

        Called every tick by MainWindow with the *global* inspection elapsed time.
        """
        if self._state != "inspecting":
            return

        # ── DNF (exceeded 20 s) ──────────────────────────────────────
        if elapsed_ms >= DNF_LIMIT_MS:
            self.penalty    = "dnf"
            self.elapsed_ms = 0
            self._state     = "stopped"
            self.timer_label.setText("DNF")
            self.penalty_label.setText("")
            self.status_label.setText("Did Not Finish")
            self._set_visual_state("dnf")
            self.timer_stopped.emit(self.player_id, 0, "dnf")
            return

        # ── Overtime (+2 window, 15-20 s) ────────────────────────────
        if elapsed_ms >= INSPECTION_LIMIT_MS:
            overtime_s = (elapsed_ms - INSPECTION_LIMIT_MS) / 1000
            self.timer_label.setText(f"+{overtime_s:.0f}")
            self.penalty_label.setText("⚠  +2 PENALTY")
            self.status_label.setText("START NOW!")
            self._set_visual_state("overtime")
            return

        # ── Normal countdown ─────────────────────────────────────────
        remaining_s = max(0, (INSPECTION_LIMIT_MS - elapsed_ms) // 1000)
        self.timer_label.setText(str(remaining_s))
        if remaining_s <= 3:
            self.status_label.setText("GET READY!")
        else:
            self.status_label.setText("INSPECT")

    def set_inspection_penalty(self, inspection_elapsed_ms: int):
        """Determine penalty based on how long the player inspected."""
        if inspection_elapsed_ms >= INSPECTION_LIMIT_MS:
            self.penalty = "+2"
        else:
            self.penalty = ""

    # ·· Solve timer ··················································

    def start_timer(self):
        """Start the solve timer directly (no inspection)."""
        self._state     = "solving"
        self.penalty    = ""
        self.elapsed_ms = 0
        self.rank_label.setText("")
        self.penalty_label.setText("")
        self.status_label.setText("SOLVING!")
        self._set_visual_state("running")
        self._elapsed.start()
        self._tick.start()

    def start_solve(self):
        """Transition from inspection → solving.  Starts the solve timer."""
        if self._state != "inspecting":
            return
        self._state = "solving"
        self.penalty_label.setText("")
        self.status_label.setText("SOLVING!")
        self._set_visual_state("running")
        self._elapsed.start()
        self._tick.start()
        self.solve_started.emit(self.player_id)   # MainWindow sets penalty

    def stop_timer(self):
        """Stop the solve timer (idempotent)."""
        if self._state != "solving":
            return
        self.elapsed_ms = self._elapsed.elapsed()
        self._tick.stop()
        self._state = "stopped"
        self._refresh()

        # Show penalty on the display
        if self.penalty == "+2":
            eff = self.elapsed_ms + 2_000
            self.penalty_label.setText("+2")
            self.timer_label.setText(format_time(eff))

        self._set_visual_state("stopped")
        self.timer_stopped.emit(self.player_id, self.elapsed_ms, self.penalty)

    # ·· Result / reset ···············································

    def set_finish_position(self, position: int):
        """Display the finishing rank (called by MainWindow)."""
        medals  = {1: "🥇", 2: "🥈", 3: "🥉"}
        ordinal = {1: "1st", 2: "2nd", 3: "3rd", 4: "4th"}.get(
            position, f"{position}th",
        )
        self.rank_label.setText(f"{medals.get(position, '')}  {ordinal}")

        if self.penalty == "dnf":
            self.status_label.setText("DNF")
        else:
            eff = effective_time(self.elapsed_ms, self.penalty)
            self.status_label.setText(format_time(eff, self.penalty))

    def reset(self):
        """Return to the initial idle state."""
        self._tick.stop()
        self._state     = "idle"
        self.elapsed_ms = 0
        self.penalty    = ""
        self.timer_label.setText("00:00.000")
        self.rank_label.setText("")
        self.penalty_label.setText("")
        self.move_label.setText("")
        self.status_label.setText("Waiting")
        self._set_visual_state("")

    def set_move_count(self, count: int):
        """Update the displayed move count (BLE mode)."""
        if self._ble_mode:
            self.move_label.setText(f"{count} moves")

    # ── Internal ─────────────────────────────────────────────────────

    def _refresh(self):
        if self._state == "solving":
            ms = self._elapsed.elapsed()
            self.timer_label.setText(format_time(ms))
        elif self._state == "stopped":
            if self.penalty == "+2":
                self.timer_label.setText(format_time(self.elapsed_ms + 2_000))
            elif self.penalty == "dnf":
                self.timer_label.setText("DNF")
            else:
                self.timer_label.setText(format_time(self.elapsed_ms))

    def _set_visual_state(self, state: str):
        """Update the dynamic QSS property ``state``."""
        self.setProperty("state", state)
        self.style().unpolish(self)
        self.style().polish(self)
        self.update()

    # ── Events ───────────────────────────────────────────────────────

    def mousePressEvent(self, event):
        """Click / tap → player action."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.player_action()
        event.accept()
