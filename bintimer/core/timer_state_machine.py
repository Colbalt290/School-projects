"""
BinTimer Core — Strict Event-Driven Timer State Machine
═══════════════════════════════════════════════════════
Central state controller for Rubik's Cube timing. Enforces strict lifecycle
phases (SCRAMBLING -> INSPECTION -> SOLVING -> SOLVED) and eliminates premature
timer stops and missed inspection move detections.
"""

from __future__ import annotations

import time
from enum import Enum, auto
from typing import Optional, List, Tuple, Dict, Any

from PyQt6.QtCore import QObject, QTimer, pyqtSignal

try:
    from bintimer.core.virtual_cube import VirtualCube
    from bintimer.core.ble_manager import BLEManager
except ImportError:
    try:
        from core.virtual_cube import VirtualCube
        from core.ble_manager import BLEManager
    except ImportError:
        from .virtual_cube import VirtualCube
        from .ble_manager import BLEManager


class TimerPhase(Enum):
    SCRAMBLING = "SCRAMBLING"
    INSPECTION = "INSPECTION"
    SOLVING    = "SOLVING"
    SOLVED     = "SOLVED"


class TimerStateMachine(QObject):
    """
    State machine managing the Rubik's cube timer lifecycle.

    Architectural guarantees:
      1. Inspection Move Detection:
         During `INSPECTION`, the very first `move_received` instantly stops
         the inspection countdown, transitions to `SOLVING`, and starts the timer.
      2. Virtual Cube Source of Truth:
         During `SOLVING`, moves are applied to `VirtualCube` first.
         The timer MUST ONLY stop if `VirtualCube.is_solved()` returns True.
      3. Zero Screen Coupling:
         Completely independent of UI screens, layouts, or view stacks.
    """

    # Signals
    phase_changed             = pyqtSignal(object)       # TimerPhase
    inspection_tick           = pyqtSignal(int)          # Remaining inspection seconds (e.g. 15..0)
    inspection_penalty_changed = pyqtSignal(str)          # "", "+2", or "DNF"
    solve_started             = pyqtSignal()             # Timer started
    solve_tick                = pyqtSignal(float)        # Current elapsed seconds (e.g. 12.345)
    move_applied              = pyqtSignal(str, bool)    # (move_str, is_solved)
    cube_state_updated        = pyqtSignal(dict)         # 54 facelet dictionary for 2D/3D visualizers
    solve_finished            = pyqtSignal(float, int, float, str)  # (time_sec, moves, tps, penalty)
    scramble_matched          = pyqtSignal()             # Cube reached target scramble state

    def __init__(
        self,
        ble_manager: Optional[BLEManager] = None,
        parent: Optional[QObject] = None,
        enable_ble: bool = True,
    ) -> None:
        super().__init__(parent=parent)

        self._phase: TimerPhase = TimerPhase.SCRAMBLING
        self._virtual_cube: VirtualCube = VirtualCube()
        self._target_cube: Optional[VirtualCube] = None
        self._current_scramble: str = ""

        # High-precision timing & telemetry
        self._solve_start_time: float = 0.0
        self._solve_end_time: float = 0.0
        self._solve_moves: List[Tuple[str, float]] = []  # [(move, elapsed_at_move), ...]
        self._inspection_start_time: float = 0.0
        self._inspection_penalty: str = ""

        # Qt Timers for periodic UI tick emissions
        self._inspection_timer = QTimer(self)
        self._inspection_timer.setInterval(100)  # 100ms precision for inspection countdown
        self._inspection_timer.timeout.connect(self._on_inspection_tick)

        self._solve_timer = QTimer(self)
        self._solve_timer.setInterval(16)        # ~60 FPS update rate for smooth UI timer
        self._solve_timer.timeout.connect(self._on_solve_tick)

        # BLE Manager connection state
        self._ble_enabled: bool = False
        self._ble_manager: BLEManager = ble_manager or BLEManager.get_instance()
        if enable_ble:
            self.enable_ble(True)

    def enable_ble(self, enable: bool = True) -> None:
        """Enable or disable listening to BLEManager move_received signals."""
        if enable and not self._ble_enabled:
            self._ble_manager.move_received.connect(self.on_move_received)
            self._ble_enabled = True
        elif not enable and self._ble_enabled:
            try:
                self._ble_manager.move_received.disconnect(self.on_move_received)
            except Exception:
                pass
            self._ble_enabled = False

    # ── State & Telemetry Properties ─────────────────────────────────

    @property
    def phase(self) -> TimerPhase:
        """Current phase of the state machine."""
        return self._phase

    @property
    def virtual_cube(self) -> VirtualCube:
        """Underlying virtual cube instance."""
        return self._virtual_cube

    @property
    def elapsed_solve_seconds(self) -> float:
        """Current or final solve duration in seconds."""
        if self._phase == TimerPhase.SOLVING:
            return max(0.0, time.perf_counter() - self._solve_start_time)
        elif self._phase == TimerPhase.SOLVED:
            return max(0.0, self._solve_end_time - self._solve_start_time)
        return 0.0

    @property
    def move_count(self) -> int:
        """Number of moves performed during the current solve."""
        return len(self._solve_moves)

    @property
    def solve_moves(self) -> List[Tuple[str, float]]:
        """List of moves and their execution timestamps."""
        return list(self._solve_moves)

    @property
    def current_tps(self) -> float:
        """Turns Per Second for the current solve."""
        elapsed = self.elapsed_solve_seconds
        if elapsed <= 0.0:
            return 0.0
        return self.move_count / elapsed

    @property
    def penalty(self) -> str:
        """Active inspection penalty: '', '+2', or 'DNF'."""
        return self._inspection_penalty

    @property
    def is_scrambled(self) -> bool:
        """True if the cube currently matches the target scramble state."""
        if not self._target_cube or not self._current_scramble:
            return True
        return self._virtual_cube == self._target_cube or getattr(self, "_scramble_completed", False)

    def get_scramble_progress(self) -> Tuple[int, int]:
        """
        Return (moves_matched, total_moves) matching prefix of target scramble.
        """
        tokens = self._current_scramble.split()
        if not tokens:
            return 0, 0
        test_cube = VirtualCube()
        matched = 0
        for i, move in enumerate(tokens):
            test_cube.apply_move(move)
            if self._virtual_cube == test_cube:
                matched = i + 1
        return matched, len(tokens)

    # ── Match / Round Setup ──────────────────────────────────────────

    def setup_round(self, scramble: str, live_scramble_track: bool = True) -> None:
        """
        Configure a new match/round with a scramble sequence.
        The virtual cube strictly starts in the SOLVED state (White Top, Green Front).
        Inspection can only start once the physical cube has been scrambled.
        """
        self._stop_all_timers()
        self._current_scramble = scramble.strip()
        self._solve_moves.clear()
        self._inspection_penalty = ""
        self._scramble_completed = False
        self.inspection_penalty_changed.emit("")

        # Target scrambled cube: strictly assumes White Top, Green Front
        self._target_cube = VirtualCube()
        if self._current_scramble:
            self._target_cube.apply_scramble(self._current_scramble)

        # Virtual cube representation: strictly starts in SOLVED state
        self._virtual_cube = VirtualCube()

        self._phase = TimerPhase.SCRAMBLING
        self.phase_changed.emit(self._phase)
        self.cube_state_updated.emit(self._virtual_cube.get_state())

    def start_inspection(self) -> bool:
        """
        Enter the INSPECTION phase.
        Strict requirement: Inspection starts ONLY IF the cube has been scrambled.
        """
        if self._ble_enabled and self._target_cube and self._current_scramble:
            if not self.is_scrambled:
                return False

        self._stop_all_timers()
        self._phase = TimerPhase.INSPECTION
        self._inspection_start_time = time.perf_counter()
        self._inspection_penalty = ""
        self._solve_moves.clear()

        self.phase_changed.emit(self._phase)
        self.inspection_penalty_changed.emit("")
        self.inspection_tick.emit(15)
        self.cube_state_updated.emit(self._virtual_cube.get_state())
        self._inspection_timer.start()
        return True

    # ── Core Event Router (Fixes Bugs 2 & 3) ─────────────────────────

    def on_move_received(self, move: str) -> None:
        """
        Primary event listener for raw smart-cube turns from BLEManager.
        Routes the move strictly based on the current machine phase.
        """
        norm_move = VirtualCube.normalize_move(move)
        if not norm_move:
            return

        # ── PHASE 1: INSPECTION (Fixes Bug 2) ─────────────────────────
        if self._phase == TimerPhase.INSPECTION:
            # 1. First move instantly halts inspection
            self._inspection_timer.stop()
            insp_elapsed = time.perf_counter() - self._inspection_start_time

            # Compute WCA inspection penalty:
            # <= 15.0s: OK
            # 15.0s < t <= 17.0s: +2 seconds
            # > 17.0s: DNF
            if insp_elapsed > 17.0:
                self._inspection_penalty = "DNF"
            elif insp_elapsed > 15.0:
                self._inspection_penalty = "+2"
            else:
                self._inspection_penalty = ""
            self.inspection_penalty_changed.emit(self._inspection_penalty)

            # 2. Transition state to SOLVING
            self._phase = TimerPhase.SOLVING
            self._solve_start_time = time.perf_counter()
            self._solve_moves.clear()

            self.phase_changed.emit(self._phase)
            self.solve_started.emit()
            self._solve_timer.start()

            # 3. Apply this initial move to the virtual cube
            self._virtual_cube.apply_move(norm_move)
            self._solve_moves.append((norm_move, 0.0))
            is_solved = self._virtual_cube.is_solved()

            self.move_applied.emit(norm_move, is_solved)
            self.cube_state_updated.emit(self._virtual_cube.get_state())

            # Even on the first move, only finish if is_solved() confirms all 6 faces unified
            if is_solved:
                self._finish_solve(0.0)
            return

        # ── PHASE 2: SOLVING (Fixes Bug 3) ───────────────────────────
        if self._phase == TimerPhase.SOLVING:
            now = time.perf_counter()
            elapsed = max(0.0, now - self._solve_start_time)

            # 1. Update virtual cube FIRST
            self._virtual_cube.apply_move(norm_move)
            self._solve_moves.append((norm_move, elapsed))

            # 2. STRICT EVALUATOR: Call is_solved() ONLY AFTER updating the virtual cube
            is_solved = self._virtual_cube.is_solved()

            self.move_applied.emit(norm_move, is_solved)
            self.cube_state_updated.emit(self._virtual_cube.get_state())

            # 3. The timer MUST ONLY stop if is_solved() confirms all 6 faces unified!
            # It will NEVER stop just because a move payload was received.
            if is_solved:
                self._finish_solve(elapsed)
            return

        # ── PHASE 3: SCRAMBLING ──────────────────────────────────────
        if self._phase == TimerPhase.SCRAMBLING:
            self._virtual_cube.apply_move(norm_move)
            self.move_applied.emit(norm_move, False)
            self.cube_state_updated.emit(self._virtual_cube.get_state())

            # Auto-detect if physical cube matched the target scramble
            if self._target_cube and self._virtual_cube == self._target_cube:
                self._scramble_completed = True
                self.scramble_matched.emit()
            else:
                self._scramble_completed = False
            return

        # ── PHASE 4: SOLVED ──────────────────────────────────────────
        if self._phase == TimerPhase.SOLVED:
            # Solve already ended; turns are ignored or optionally tracked
            return

    # ── Solve Completion & Helper Routines ───────────────────────────

    def _finish_solve(self, elapsed: float) -> None:
        """Strict solve termination when VirtualCube confirms solved state."""
        self._solve_timer.stop()
        self._solve_end_time = self._solve_start_time + elapsed
        self._phase = TimerPhase.SOLVED

        move_count = len(self._solve_moves)
        tps = (move_count / elapsed) if elapsed > 0 else 0.0

        self.solve_finished.emit(elapsed, move_count, tps, self._inspection_penalty)
        self.phase_changed.emit(self._phase)

    def manual_start_solve(self) -> None:
        """Manual trigger for starting solve (e.g. keyboard spacebar release)."""
        if self._phase in (TimerPhase.SCRAMBLING, TimerPhase.INSPECTION):
            self._inspection_timer.stop()
            self._phase = TimerPhase.SOLVING
            self._solve_start_time = time.perf_counter()
            self._solve_moves.clear()
            self.phase_changed.emit(self._phase)
            self.solve_started.emit()
            self._solve_timer.start()

    def manual_stop_solve(self) -> None:
        """Manual stop override (e.g. keyboard mode or manual timer pad)."""
        if self._phase == TimerPhase.SOLVING:
            elapsed = max(0.0, time.perf_counter() - self._solve_start_time)
            self._finish_solve(elapsed)

    def sync_cube_solved(self) -> None:
        """Manually synchronize the virtual cube to solved state (White Top, Green Front)."""
        self._virtual_cube.reset()
        self._scramble_completed = False
        self.cube_state_updated.emit(self._virtual_cube.get_state())

    def sync_cube_scramble(self) -> None:
        """Manually synchronize the virtual cube to target scramble (White Top, Green Front)."""
        if self._target_cube:
            self._virtual_cube = self._target_cube.clone()
        elif self._current_scramble:
            self._virtual_cube = VirtualCube()
            self._virtual_cube.apply_scramble(self._current_scramble)
        else:
            self._virtual_cube.reset()
        self.cube_state_updated.emit(self._virtual_cube.get_state())

    def reset(self) -> None:
        """Reset state machine back to idle scrambling state."""
        self._stop_all_timers()
        self._phase = TimerPhase.SCRAMBLING
        self._virtual_cube.reset()
        self._target_cube = None
        self._current_scramble = ""
        self._solve_moves.clear()
        self._inspection_penalty = ""
        self.phase_changed.emit(self._phase)
        self.inspection_penalty_changed.emit("")
        self.cube_state_updated.emit(self._virtual_cube.get_state())

    def _stop_all_timers(self) -> None:
        if self._inspection_timer.isActive():
            self._inspection_timer.stop()
        if self._solve_timer.isActive():
            self._solve_timer.stop()

    def _on_inspection_tick(self) -> None:
        elapsed = time.perf_counter() - self._inspection_start_time
        remaining = max(0, int(15.0 - elapsed))
        self.inspection_tick.emit(remaining)

        # Check penalty thresholds
        if elapsed > 17.0 and self._inspection_penalty != "DNF":
            self._inspection_penalty = "DNF"
            self.inspection_penalty_changed.emit(self._inspection_penalty)
        elif elapsed > 15.0 and self._inspection_penalty == "":
            self._inspection_penalty = "+2"
            self.inspection_penalty_changed.emit(self._inspection_penalty)

    def _on_solve_tick(self) -> None:
        elapsed = max(0.0, time.perf_counter() - self._solve_start_time)
        self.solve_tick.emit(elapsed)
