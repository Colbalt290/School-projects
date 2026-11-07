"""
Bluetooth Low Energy smart-cube integration for BinTimer.

Supports:
  • Giiker / GiiKER cubes  (well-documented protocol, with move detection)
  • GAN cubes              (basic notification monitoring)
  • Generic fallback       (subscribe to any notify characteristic)

Emits ``move_detected(str)`` for each individual move (e.g. "U", "R'", "F2")
parsed from BLE state diffs, and ``cube_solved()`` when the cube reaches the
identity permutation.

If the ``bleak`` library is not installed the module still imports
cleanly — all BLE UI simply shows an "install bleak" message.
"""

from __future__ import annotations

import asyncio
import threading
from typing import TYPE_CHECKING

from PyQt6.QtCore import QObject, Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QListWidget, QListWidgetItem, QPushButton,
)

# ── Optional bleak import ────────────────────────────────────────────

try:
    from bleak import BleakScanner, BleakClient     # type: ignore[import]
    HAS_BLEAK = True
except ImportError:
    HAS_BLEAK = False

if TYPE_CHECKING:
    from bleak import BleakClient as _BC            # for type-hints only


# ── Known cube BLE identifiers ──────────────────────────────────────

KNOWN_PREFIXES = [
    "GAN", "Gi", "GiiKER", "Mi Smart",
    "Rubik", "GoCube", "MoYu", "QiYi",
]

# Giiker / GiiKER UUIDs
GIIKER_SVC   = "0000aadb-0000-1000-8000-00805f9b34fb"
GIIKER_STATE = "0000aadc-0000-1000-8000-00805f9b34fb"

# GAN v1
GAN_SVC_V1    = "0000fff0-0000-1000-8000-00805f9b34fb"
GAN_NOTIFY_V1 = "0000fff5-0000-1000-8000-00805f9b34fb"

# GAN v2 (Nordic UART-style)
GAN_SVC_V2    = "6e400001-b5a3-f393-e0a9-e50e24dcca9e"
GAN_NOTIFY_V2 = "28be4cb6-cd67-11e9-a32f-2a2ae2dbcce4"

# Giiker move byte encoding (byte 16 of 20-byte state packet)
# High nibble = face (1=B, 2=D, 3=L, 4=U, 5=R, 6=F)
# Low nibble  = direction (1=CW, 2=CCW, 3=180°)
_GIIKER_FACE_MAP = {1: "B", 2: "D", 3: "L", 4: "U", 5: "R", 6: "F"}
_GIIKER_DIR_MAP  = {1: "", 2: "'", 3: "2"}


def _is_cube(name: str | None) -> bool:
    if not name:
        return False
    return any(name.upper().startswith(p.upper()) for p in KNOWN_PREFIXES)


# ── Cube state tracker ──────────────────────────────────────────────

class CubeState:
    """
    Tracks corner / edge state parsed from BLE notifications.

    Now also detects which move was made by parsing the Giiker
    move byte (byte 16 of the 20-byte state packet).
    """

    def __init__(self):
        self.corners:     list[int] = list(range(1, 9))   # identity
        self.corner_ori:  list[int] = [0] * 8
        self.edges:       list[int] = list(range(1, 13))
        self.edge_ori:    list[int] = [0] * 12
        self._solved = True
        self._move_count = 0          # running counter from Giiker
        self._last_move:  str = ""    # e.g. "U", "R'", "F2"

    # ── Giiker ───────────────────────────────────────────────────────
    def update_giiker(self, data: bytes) -> tuple[bool, str]:
        """
        Parse a 20-byte Giiker state packet.

        Layout (nibble-packed):
          [0-3]   corner positions   (8 × 4-bit)
          [4-7]   corner orientations (8 × 4-bit, only low 2 bits used)
          [8-13]  edge positions     (12 × 4-bit)
          [14-19] edge orientations  (12 × 4-bit, only low 1 bit used)

        The move byte is at data[16] (some variants) or can be
        reconstructed from the last 4 bytes.

        Returns ``(is_solved, move_string)``.
        ``move_string`` is empty if no move was detected (e.g. first packet).
        """
        if len(data) < 20:
            return self._solved, ""

        # Parse permutation state
        for i in range(8):
            b = data[i // 2]
            self.corners[i]    = ((b >> 4) if i % 2 == 0 else (b & 0x0F))
        for i in range(8):
            b = data[4 + i // 2]
            self.corner_ori[i] = ((b >> 4) if i % 2 == 0 else (b & 0x0F))
        for i in range(12):
            b = data[8 + i // 2]
            self.edges[i]      = ((b >> 4) if i % 2 == 0 else (b & 0x0F))

        # Detect move from the Giiker move byte
        # Byte 16: high nibble = face index, low nibble = direction
        # Byte 17: move counter
        move_str = ""
        if len(data) >= 18:
            move_byte = data[16]
            face_idx  = (move_byte >> 4) & 0x0F
            dir_idx   = move_byte & 0x0F
            new_count = data[17]

            if new_count != self._move_count and face_idx in _GIIKER_FACE_MAP:
                face = _GIIKER_FACE_MAP[face_idx]
                direction = _GIIKER_DIR_MAP.get(dir_idx, "")
                move_str = f"{face}{direction}"
                self._last_move = move_str

            self._move_count = new_count

        self._solved = (
            all(self.corners[i] == i + 1 for i in range(8))
            and all(o == 0 for o in self.corner_ori)
            and all(self.edges[i] == i + 1 for i in range(12))
        )
        return self._solved, move_str

    # ── Generic / GAN ────────────────────────────────────────────────
    def update_generic(self, data: bytes) -> tuple[bool, str]:
        """Heuristic solved-detection for unknown protocols."""
        if len(data) >= 4 and len(set(data)) <= 2:
            self._solved = True
        return self._solved, ""

    @property
    def is_solved(self) -> bool:
        return self._solved

    @property
    def last_move(self) -> str:
        return self._last_move


# ── BLE worker (runs an asyncio loop in a daemon thread) ────────────

class BleWorker(QObject):
    """
    Background worker for all BLE I/O.

    Signals are emitted from the asyncio thread but delivered safely
    to the main-thread receivers via Qt's ``QueuedConnection``.
    """

    device_discovered = pyqtSignal(str, str)   # name, address
    scan_finished     = pyqtSignal()
    connected         = pyqtSignal(str)         # device name
    disconnected      = pyqtSignal()
    cube_solved       = pyqtSignal()
    move_detected     = pyqtSignal(str)         # move string, e.g. "U", "R'", "F2"
    error_occurred    = pyqtSignal(str)
    status_changed    = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self._loop:   asyncio.AbstractEventLoop | None = None
        self._client: _BC | None = None
        self._thread: threading.Thread | None = None
        self._cube    = CubeState()
        self._proto   = "unknown"

    @property
    def is_connected(self) -> bool:
        return self._client is not None and self._client.is_connected

    # ── Thread management ────────────────────────────────────────────

    def start_loop(self):
        """Spin up the asyncio event loop in a daemon thread."""
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _run(self):
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        self._loop.run_forever()
        self._loop.close()

    def _submit(self, coro):
        if self._loop and self._loop.is_running():
            return asyncio.run_coroutine_threadsafe(coro, self._loop)
        self.error_occurred.emit("BLE loop not running")
        return None

    def stop_loop(self):
        if self._loop and self._loop.is_running():
            self._loop.call_soon_threadsafe(self._loop.stop)
        if self._thread:
            self._thread.join(timeout=3)

    # ── Scanning ─────────────────────────────────────────────────────

    def scan(self):
        self._submit(self._scan())

    async def _scan(self):
        try:
            self.status_changed.emit("Scanning…")
            devs = await BleakScanner.discover(timeout=8.0)
            for d in devs:
                if _is_cube(d.name):
                    self.device_discovered.emit(d.name or "Unknown", d.address)
        except Exception as exc:
            self.error_occurred.emit(f"Scan error: {exc}")
        finally:
            self.scan_finished.emit()

    # ── Connection ───────────────────────────────────────────────────

    def connect_to(self, address: str):
        self._submit(self._connect(address))

    async def _connect(self, address: str):
        try:
            self.status_changed.emit("Connecting…")
            self._client = BleakClient(
                address,
                disconnected_callback=lambda _c: self.disconnected.emit(),
            )
            await self._client.connect()
            if not self._client.is_connected:
                self.error_occurred.emit("Connection failed.")
                return
            self.connected.emit(address)
            await self._subscribe()
        except Exception as exc:
            self.error_occurred.emit(f"Connect error: {exc}")

    async def _subscribe(self):
        """Detect the cube's protocol and subscribe to state updates."""
        assert self._client is not None
        svcs = self._client.services

        # ── Giiker ───────────────────────────────────────────────────
        for svc in svcs:
            if svc.uuid.lower() == GIIKER_SVC:
                self._proto = "giiker"
                self.status_changed.emit("Giiker detected — monitoring state")
                for ch in svc.characteristics:
                    if ch.uuid.lower() == GIIKER_STATE:
                        await self._client.start_notify(ch.uuid, self._on_giiker)
                        return

        # ── GAN v2 ───────────────────────────────────────────────────
        for svc in svcs:
            if svc.uuid.lower() == GAN_SVC_V2:
                self._proto = "gan_v2"
                self.status_changed.emit("GAN v2 detected — monitoring")
                for ch in svc.characteristics:
                    if ch.uuid.lower() == GAN_NOTIFY_V2:
                        await self._client.start_notify(ch.uuid, self._on_generic)
                        return

        # ── GAN v1 ───────────────────────────────────────────────────
        for svc in svcs:
            if svc.uuid.lower() == GAN_SVC_V1:
                self._proto = "gan_v1"
                self.status_changed.emit("GAN v1 detected — monitoring")
                for ch in svc.characteristics:
                    if ch.uuid.lower() == GAN_NOTIFY_V1:
                        await self._client.start_notify(ch.uuid, self._on_generic)
                        return

        # ── Generic fallback ─────────────────────────────────────────
        self._proto = "generic"
        for svc in svcs:
            for ch in svc.characteristics:
                if "notify" in ch.properties:
                    try:
                        await self._client.start_notify(ch.uuid, self._on_generic)
                        self.status_changed.emit(f"Subscribed to {ch.uuid}")
                        return
                    except Exception:
                        continue
        self.status_changed.emit("No suitable characteristic found")

    # ── Notification handlers ────────────────────────────────────────

    def _on_giiker(self, _sender, data: bytearray):
        solved, move = self._cube.update_giiker(bytes(data))
        if move:
            self.move_detected.emit(move)
        if solved:
            self.cube_solved.emit()

    def _on_generic(self, _sender, data: bytearray):
        solved, move = self._cube.update_generic(bytes(data))
        if move:
            self.move_detected.emit(move)
        if solved:
            self.cube_solved.emit()

    # ── Disconnect ───────────────────────────────────────────────────

    def disconnect_cube(self):
        self._submit(self._disconnect())

    async def _disconnect(self):
        if self._client and self._client.is_connected:
            await self._client.disconnect()
        self._client = None
        self._proto  = "unknown"
        self._cube   = CubeState()
        self.disconnected.emit()


# ── Scan / pick dialog ──────────────────────────────────────────────

class CubeScanDialog(QDialog):
    """Modal dialog: scan for nearby cubes, let the user pick one."""

    device_selected = pyqtSignal(str, str)     # name, address

    def __init__(self, worker: BleWorker, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Connect Smart Cube")
        self.setMinimumSize(420, 320)
        self._worker  = worker
        self._devices: dict[str, str] = {}     # address → name
        self._build_ui()
        self._wire()

    def _build_ui(self):
        lay = QVBoxLayout(self)

        self.status = QLabel("Scanning for smart cubes…")
        self.status.setObjectName("scanStatus")
        lay.addWidget(self.status)

        self.list = QListWidget()
        lay.addWidget(self.list)

        row = QHBoxLayout()
        self.rescan_btn  = QPushButton("🔄  Rescan")
        self.connect_btn = QPushButton("Connect")
        self.cancel_btn  = QPushButton("Cancel")
        self.connect_btn.setEnabled(False)
        row.addWidget(self.rescan_btn)
        row.addStretch()
        row.addWidget(self.connect_btn)
        row.addWidget(self.cancel_btn)
        lay.addLayout(row)

    def _wire(self):
        self._worker.device_discovered.connect(self._on_found)
        self._worker.scan_finished.connect(self._on_scan_done)
        self.list.currentItemChanged.connect(
            lambda: self.connect_btn.setEnabled(self.list.currentItem() is not None)
        )
        self.rescan_btn.clicked.connect(self._do_scan)
        self.connect_btn.clicked.connect(self._on_connect)
        self.cancel_btn.clicked.connect(self.reject)

    # ── slots ────────────────────────────────────────────────────────

    def showEvent(self, ev):
        super().showEvent(ev)
        self._do_scan()

    def _do_scan(self):
        self._devices.clear()
        self.list.clear()
        self.status.setText("Scanning for smart cubes…")
        self.rescan_btn.setEnabled(False)
        self._worker.scan()

    def _on_found(self, name: str, addr: str):
        if addr not in self._devices:
            self._devices[addr] = name
            item = QListWidgetItem(f"{name}   ({addr})")
            item.setData(Qt.ItemDataRole.UserRole, addr)
            self.list.addItem(item)

    def _on_scan_done(self):
        self.rescan_btn.setEnabled(True)
        n = self.list.count()
        self.status.setText(
            f"Found {n} device(s) — select one to connect."
            if n else
            "No smart cubes found.  Make sure your cube is powered on."
        )

    def _on_connect(self):
        item = self.list.currentItem()
        if not item:
            return
        addr = item.data(Qt.ItemDataRole.UserRole)
        name = self._devices.get(addr, "Unknown")
        self.device_selected.emit(name, addr)
        self.accept()


# ── BLE Manager Singleton ───────────────────────────────────────────

class BleManager(QObject):
    """
    Application-wide singleton managing smart cube BLE connections.
    Persistent across all Qt screen navigation (Setup <-> Timer view).
    """
    _instance: BleManager | None = None

    device_discovered = pyqtSignal(int, str, str)  # pid, name, address
    scan_finished     = pyqtSignal(int)            # pid
    connected         = pyqtSignal(int, str)       # pid, device_name
    disconnected      = pyqtSignal(int)            # pid
    move_detected     = pyqtSignal(int, str)       # pid, move_str
    cube_solved       = pyqtSignal(int)            # pid
    status_changed    = pyqtSignal(int, str)       # pid, msg
    error_occurred    = pyqtSignal(int, str)       # pid, msg

    @classmethod
    def get_instance(cls) -> BleManager:
        if cls._instance is None:
            cls._instance = BleManager()
        return cls._instance

    def __init__(self):
        super().__init__()
        self._workers: dict[int, BleWorker] = {}
        self._device_names: dict[int, str] = {}
        self._device_addresses: dict[int, str] = {}

    def get_worker(self, pid: int) -> BleWorker:
        if pid not in self._workers:
            w = BleWorker()
            w.start_loop()
            w.device_discovered.connect(lambda name, addr, p=pid: self.device_discovered.emit(p, name, addr))
            w.scan_finished.connect(lambda p=pid: self.scan_finished.emit(p))
            w.connected.connect(lambda dev, p=pid: self._on_worker_connected(p, dev))
            w.disconnected.connect(lambda p=pid: self._on_worker_disconnected(p))
            w.move_detected.connect(lambda mv, p=pid: self.move_detected.emit(p, mv))
            w.cube_solved.connect(lambda p=pid: self.cube_solved.emit(p))
            w.status_changed.connect(lambda msg, p=pid: self.status_changed.emit(p, msg))
            w.error_occurred.connect(lambda msg, p=pid: self.error_occurred.emit(p, msg))
            self._workers[pid] = w
        return self._workers[pid]

    def _on_worker_connected(self, pid: int, dev: str):
        self._device_names[pid] = dev
        self.connected.emit(pid, dev)

    def _on_worker_disconnected(self, pid: int):
        self._device_names.pop(pid, None)
        self._device_addresses.pop(pid, None)
        self.disconnected.emit(pid)

    def is_connected(self, pid: int) -> bool:
        w = self._workers.get(pid)
        return w is not None and w.is_connected

    def get_device_name(self, pid: int) -> str:
        return self._device_names.get(pid, "Smart Cube")

    def disconnect_cube(self, pid: int):
        w = self._workers.get(pid)
        if w:
            w.disconnect_cube()

    def stop_all(self):
        for w in self._workers.values():
            try:
                w.stop_loop()
            except Exception:
                pass
        self._workers.clear()
