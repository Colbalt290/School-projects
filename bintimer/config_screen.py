"""
BinTimer — Configuration / Setup Screen.

Allows the user to select mode (Solo / PvP), player count,
cube type per player, and inspection settings before starting.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QButtonGroup,
    QCheckBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)


# ── Match configuration ─────────────────────────────────────────────

@dataclass
class MatchConfig:
    """Immutable snapshot of the settings chosen on the config screen."""

    mode: str = "solo"                              # "solo" | "pvp"
    player_count: int = 1                           # 1 (solo) or 2-4
    cube_types: dict[int, str] = field(             # {pid: "normal"|"bluetooth"}
        default_factory=lambda: {i: "normal" for i in range(1, 5)},
    )
    inspection_enabled: bool = False


# ── Config screen widget ────────────────────────────────────────────

class ConfigScreen(QWidget):
    """
    Full-page setup screen.

    Emits :pyqt:`start_requested(MatchConfig)` when the user clicks Start.
    """

    start_requested = pyqtSignal(object)            # emits MatchConfig

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("configScreen")
        self._config = MatchConfig()
        self._build_ui()
        self._on_mode_changed("solo")               # initialise visibility

    # ── UI construction ──────────────────────────────────────────────

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(40, 40, 40, 40)
        root.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # ── Centred card ─────────────────────────────────────────────
        card = QFrame()
        card.setObjectName("configCard")
        card.setMaximumWidth(620)
        card.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum,
        )
        cl = QVBoxLayout(card)
        cl.setSpacing(20)
        cl.setContentsMargins(40, 40, 40, 40)

        # Title
        title = QLabel("🎲  BinTimer")
        title.setObjectName("configTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        cl.addWidget(title)

        subtitle = QLabel("Rubik's Cube Timer")
        subtitle.setObjectName("configSubtitle")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setProperty("role", "secondary")
        cl.addWidget(subtitle)

        cl.addSpacing(12)

        # ── Mode selection ───────────────────────────────────────────
        mode_lbl = QLabel("MODE")
        mode_lbl.setProperty("role", "heading")
        cl.addWidget(mode_lbl)

        mode_row = QHBoxLayout()
        mode_row.setSpacing(10)

        self._solo_btn = QPushButton("🧑  Solo")
        self._solo_btn.setObjectName("modeButton")
        self._solo_btn.setCheckable(True)
        self._solo_btn.setChecked(True)
        self._solo_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        self._pvp_btn = QPushButton("⚔️  PvP")
        self._pvp_btn.setObjectName("modeButton")
        self._pvp_btn.setCheckable(True)
        self._pvp_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        self._mode_group = QButtonGroup(self)
        self._mode_group.setExclusive(True)
        self._mode_group.addButton(self._solo_btn, 0)
        self._mode_group.addButton(self._pvp_btn, 1)

        mode_row.addWidget(self._solo_btn, 1)
        mode_row.addWidget(self._pvp_btn, 1)
        cl.addLayout(mode_row)

        # ── Player count (PvP only) ─────────────────────────────────
        self._count_frame = QFrame()
        self._count_frame.setObjectName("playerCountFrame")
        pcl = QVBoxLayout(self._count_frame)
        pcl.setContentsMargins(0, 0, 0, 0)
        pcl.setSpacing(8)

        pc_lbl = QLabel("PLAYERS")
        pc_lbl.setProperty("role", "heading")
        pcl.addWidget(pc_lbl)

        pc_row = QHBoxLayout()
        pc_row.setSpacing(10)

        self._count_group = QButtonGroup(self)
        self._count_group.setExclusive(True)
        self._count_buttons: dict[int, QPushButton] = {}

        for n in (2, 3, 4):
            btn = QPushButton(str(n))
            btn.setObjectName("countButton")
            btn.setCheckable(True)
            btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            btn.setMinimumWidth(60)
            if n == 2:
                btn.setChecked(True)
            self._count_group.addButton(btn, n)
            self._count_buttons[n] = btn
            pc_row.addWidget(btn, 1)

        pcl.addLayout(pc_row)
        cl.addWidget(self._count_frame)

        # ── Inspection toggle ────────────────────────────────────────
        self._inspection_cb = QCheckBox("  WCA Inspection  (15 s countdown)")
        self._inspection_cb.setObjectName("inspectionCheck")
        self._inspection_cb.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        cl.addWidget(self._inspection_cb)

        # ── Per-player cube type ─────────────────────────────────────
        self._players_frame = QFrame()
        self._players_frame.setObjectName("playersFrame")
        pfl = QVBoxLayout(self._players_frame)
        pfl.setContentsMargins(0, 0, 0, 0)
        pfl.setSpacing(6)

        cube_lbl = QLabel("CUBE TYPE")
        cube_lbl.setProperty("role", "heading")
        pfl.addWidget(cube_lbl)

        self._ble_checks: dict[int, QCheckBox] = {}
        for pid in range(1, 5):
            cb = QCheckBox(f"  Player {pid}:  Use Bluetooth Smart Cube")
            cb.setObjectName("bleCheck")
            cb.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            self._ble_checks[pid] = cb
            pfl.addWidget(cb)

        cl.addWidget(self._players_frame)

        cl.addSpacing(16)

        # ── Start button ────────────────────────────────────────────
        self._start_btn = QPushButton("⏵   Start")
        self._start_btn.setObjectName("configStartButton")
        self._start_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        cl.addWidget(self._start_btn)

        root.addWidget(card)

        # ── Wiring ──────────────────────────────────────────────────
        self._mode_group.idToggled.connect(self._on_mode_toggled)
        self._count_group.idToggled.connect(self._on_count_toggled)
        self._start_btn.clicked.connect(self._on_start)

    # ── Slots ────────────────────────────────────────────────────────

    def _on_mode_toggled(self, btn_id: int, checked: bool):
        if checked:
            self._on_mode_changed("solo" if btn_id == 0 else "pvp")

    def _on_mode_changed(self, mode: str):
        self._config.mode = mode
        is_pvp = (mode == "pvp")
        self._count_frame.setVisible(is_pvp)

        if is_pvp:
            cid = self._count_group.checkedId()
            self._config.player_count = cid if cid >= 2 else 2
        else:
            self._config.player_count = 1

        self._update_player_rows()

    def _on_count_toggled(self, btn_id: int, checked: bool):
        if checked:
            self._config.player_count = btn_id
            self._update_player_rows()

    def _update_player_rows(self):
        """Show / hide player cube-type checkboxes."""
        count = self._config.player_count
        for pid, cb in self._ble_checks.items():
            cb.setVisible(pid <= count)
        if count == 1:
            self._ble_checks[1].setText("  Use Bluetooth Smart Cube")
        else:
            for pid in range(1, 5):
                self._ble_checks[pid].setText(
                    f"  Player {pid}:  Use Bluetooth Smart Cube"
                )

    def _on_start(self):
        count = self._config.player_count
        self._config.inspection_enabled = self._inspection_cb.isChecked()
        self._config.cube_types = {
            pid: ("bluetooth" if self._ble_checks[pid].isChecked() else "normal")
            for pid in range(1, count + 1)
        }
        self.start_requested.emit(self._config)
