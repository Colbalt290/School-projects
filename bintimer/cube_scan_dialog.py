"""
BinTimer — Smart Cube BLE Scanner & Connection Dialog
═════════════════════════════════════════════════════
Modal dialog to discover nearby Bluetooth Smart Cubes (GAN, Giiker, MoYu, GoCube, etc.)
and connect via the persistent BLEManager singleton.
"""

from __future__ import annotations

from typing import Optional, Dict

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QCheckBox, QDialog, QHBoxLayout, QLabel, QLineEdit,
    QListWidget, QListWidgetItem, QPushButton, QVBoxLayout, QWidget,
)

try:
    from bintimer.core.ble_manager import BLEManager, HAS_BLEAK
except ImportError:
    from core.ble_manager import BLEManager, HAS_BLEAK


class CubeScanDialog(QDialog):
    """
    Dialog allowing the user to scan for smart cubes and connect.
    Operates strictly via the BLEManager singleton.
    """

    device_selected = pyqtSignal(str, str)  # name, address

    def __init__(self, ble_manager: Optional[BLEManager] = None, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setWindowTitle("🔗 Connect Smart Cube")
        self.setObjectName("cubeScanDialog")
        self.resize(520, 420)
        self.setMinimumSize(460, 360)

        self._ble_mgr = ble_manager or BLEManager.get_instance()
        self._devices: Dict[str, str] = {}  # address -> name

        self._build_ui()
        self._wire_signals()

    def _build_ui(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 20, 20, 20)
        lay.setSpacing(10)

        # 1. Status Label
        self.status_label = QLabel("Initializing Bluetooth scanner...")
        self.status_label.setObjectName("scanStatus")
        self.status_label.setWordWrap(True)
        lay.addWidget(self.status_label)

        # 2. Search & Filter Bar
        filter_row = QHBoxLayout()
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("🔍  Search device name or address...")
        self.search_box.textChanged.connect(self._apply_filter)
        filter_row.addWidget(self.search_box, 1)

        self.show_all_cb = QCheckBox("Show all devices")
        self.show_all_cb.setToolTip("Show all discovered BLE peripherals, even if not recognized as a smart cube")
        self.show_all_cb.toggled.connect(self._on_show_all_toggled)
        filter_row.addWidget(self.show_all_cb)
        lay.addLayout(filter_row)

        # 3. Discovered Devices List
        self.device_list = QListWidget()
        self.device_list.setObjectName("scanDeviceList")
        self.device_list.itemDoubleClicked.connect(self._on_connect_clicked)
        lay.addWidget(self.device_list)

        # 4. OS Pairing Notice Box
        hint_label = QLabel(
            "💡 <b>Tip:</b> Connect directly here. Do <i>not</i> pair the cube in your system's "
            "Bluetooth settings window (if paired in OS settings, click Disconnect there first)."
        )
        hint_label.setWordWrap(True)
        hint_label.setStyleSheet("color: #90caf9; font-size: 11px; padding: 4px;")
        lay.addWidget(hint_label)

        # 5. Buttons Row
        btn_row = QHBoxLayout()
        self.rescan_btn = QPushButton("🔄  Rescan")
        self.rescan_btn.setObjectName("rescanBtn")
        self.rescan_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        self.connect_btn = QPushButton("Connect")
        self.connect_btn.setObjectName("connectBtn")
        self.connect_btn.setEnabled(False)
        self.connect_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setObjectName("cancelBtn")
        self.cancel_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        btn_row.addWidget(self.rescan_btn)
        btn_row.addStretch()
        btn_row.addWidget(self.connect_btn)
        btn_row.addWidget(self.cancel_btn)
        lay.addLayout(btn_row)

    def _wire_signals(self):
        self._ble_mgr.device_discovered.connect(self._on_device_discovered)
        self._ble_mgr.scan_finished.connect(self._on_scan_finished)
        self._ble_mgr.connected.connect(self._on_connected)
        self._ble_mgr.error_occurred.connect(self._on_error)

        self.device_list.currentItemChanged.connect(self._on_selection_changed)
        self.rescan_btn.clicked.connect(self._start_scan)
        self.connect_btn.clicked.connect(self._on_connect_clicked)
        self.cancel_btn.clicked.connect(self.reject)

    def showEvent(self, event):
        super().showEvent(event)
        self._start_scan()

    def _start_scan(self):
        self._devices.clear()
        self.device_list.clear()
        self.connect_btn.setEnabled(False)
        self.rescan_btn.setEnabled(False)

        if not HAS_BLEAK:
            self.status_label.setText("⚠ Bleak is not installed.\nInstall using: pip install bleak (or sudo dnf install python3-bleak)")
            self.rescan_btn.setEnabled(True)
            return

        self.status_label.setText("Scanning for nearby smart cubes (GAN, Giiker, MoYu, GoCube)...")
        show_all = self.show_all_cb.isChecked()
        self._ble_mgr.start_scan(timeout_sec=6.0, show_all=show_all)

    def _on_device_discovered(self, name: str, address: str):
        if address not in self._devices:
            self._devices[address] = name

            # Smart cube icon indicator
            icon = "🎲" if BLEManager.is_smart_cube(name, []) else "📡"
            item = QListWidgetItem(f"{icon}  {name}   [{address}]")
            item.setData(Qt.ItemDataRole.UserRole, address)
            item.setData(Qt.ItemDataRole.UserRole + 1, name)

            # Check search filter
            query = self.search_box.text().strip().lower()
            if query and query not in name.lower() and query not in address.lower():
                item.setHidden(True)

            self.device_list.addItem(item)
            visible_count = sum(1 for i in range(self.device_list.count()) if not self.device_list.item(i).isHidden())
            self.status_label.setText(f"Found {visible_count} device(s). Select your cube to connect:")

    def _on_scan_finished(self):
        self.rescan_btn.setEnabled(True)
        count = self.device_list.count()
        if count == 0:
            if not HAS_BLEAK:
                self.status_label.setText("⚠ Bleak library is not installed.\nInstall with: pip install bleak")
            else:
                self.status_label.setText("No smart cubes found. Ensure your cube is awake and not paired in OS settings.")
        else:
            self.status_label.setText(f"Scan finished. Found {count} device(s).")

    def _apply_filter(self, query: str):
        q = query.strip().lower()
        for i in range(self.device_list.count()):
            item = self.device_list.item(i)
            name = item.data(Qt.ItemDataRole.UserRole + 1) or ""
            addr = item.data(Qt.ItemDataRole.UserRole) or ""
            item.setHidden(bool(q and q not in name.lower() and q not in addr.lower()))

    def _on_show_all_toggled(self, checked: bool):
        self._start_scan()

    def _on_selection_changed(self, current, _previous):
        self.connect_btn.setEnabled(current is not None)

    def _on_connect_clicked(self):
        item = self.device_list.currentItem()
        if not item:
            return
        address = item.data(Qt.ItemDataRole.UserRole)
        name = self._devices.get(address, "Smart Cube")
        self.status_label.setText(f"Connecting to {name} ({address})...")
        self.connect_btn.setEnabled(False)
        self.rescan_btn.setEnabled(False)
        self._ble_mgr.connect_device(address, name)

    def _on_connected(self, device_name: str):
        item = self.device_list.currentItem()
        addr = item.data(Qt.ItemDataRole.UserRole) if item else ""
        self.device_selected.emit(device_name, addr)
        self.accept()

    def _on_error(self, message: str):
        self.status_label.setText(f"⚠ {message}")
        self.rescan_btn.setEnabled(True)
        self.connect_btn.setEnabled(self.device_list.currentItem() is not None)
