"""
BinTimer Core — Global BLE Manager Singleton
════════════════════════════════════════════
Persistent, application-wide Bluetooth Low Energy manager for Smart Cubes.
Lives independently of any Qt Screen, View, or Dialog, ensuring connections
are never dropped during UI navigation.

Supports:
  • Real-time discovery (GAN, Giiker, MoYu, GoCube, QiYi, etc.)
  • Automatic extraction of names from BLE Advertising Data (adv.local_name)
  • Full hardware decryption for GAN Gen 2 / i Carry / i 3 / Monster Go (AES-128 ECB)
  • Priority characteristic matching for GAN v1/v2, Giiker, and Nordic UART
  • Emits `move_received(str)` on every physical turn with strict face/direction mapping.
"""

from __future__ import annotations

import asyncio
import math
import threading
from typing import Optional, TYPE_CHECKING, Dict, List, Set, Any, Tuple

from PyQt6.QtCore import QObject, pyqtSignal

try:
    from bleak import BleakScanner, BleakClient  # type: ignore[import]
    HAS_BLEAK = True
except ImportError:
    HAS_BLEAK = False

if TYPE_CHECKING:
    from bleak import BleakClient as _BleakClient

# Known smart cube keywords (case-insensitive substring match)
KNOWN_KEYWORDS = (
    "GAN", "GI", "GIIKER", "MI SMART",
    "RUBIK", "GOCUBE", "MOYU", "QIYI", "MGC", "MONSTER", "CUBE", "SMART"
)

# Known smart cube Service UUID snippets
KNOWN_UUID_SNIPPETS = (
    "fff0",      # GAN v1 / QiYi
    "6e400001",  # GAN v2 / Nordic UART / GoCube
    "aadb",      # Giiker
    "1000",      # MoYu
    "28be4cb6",  # GAN v2 characteristic
)

# Priority Characteristics to listen on (in order of preference)
PRIORITY_CHARACTERISTICS = (
    "28be4cb6-cd67-11e9-a32f-2a2ae2dbcce4",  # GAN Gen 2 / i Carry / 356i v2
    "0000fff5-0000-1000-8000-00805f9b34fb",  # GAN Gen 1
    "0000aadc-0000-1000-8000-00805f9b34fb",  # Giiker
    "6e400003-b5a3-f393-e0a9-e50e24dcca9e",  # Nordic UART TX / GoCube
    "00001002-0000-1000-8000-00805f9b34fb",  # MoYu
)

# Standard Bleak Giiker move parsing mappings
_GIIKER_FACE_MAP: Dict[int, str] = {1: "B", 2: "D", 3: "L", 4: "U", 5: "R", 6: "F"}
_GIIKER_DIR_MAP: Dict[int, str]  = {1: "", 2: "2", 3: "'"}

# Standard GAN move byte mapping (Face * 3 + Dir)
# Face: 0=U, 1=R, 2=F, 3=D, 4=L, 5=B
# Dir:  +0=CW, +1=Double, +2=CCW (')
GAN_MOVE_MAP: Dict[int, str] = {
    0: "U", 1: "U2", 2: "U'",
    3: "R", 4: "R2", 5: "R'",
    6: "F", 7: "F2", 8: "F'",
    9: "D", 10: "D2", 11: "D'",
    12: "L", 13: "L2", 14: "L'",
    15: "B", 16: "B2", 17: "B'",
}

# GAN Key constants from cubing.js / gan-web-bluetooth
GAN_KEY_10 = bytes([198, 202, 21, 223, 79, 110, 19, 182, 119, 13, 230, 89, 58, 175, 186, 162])
GAN_KEY_11 = bytes([67, 226, 91, 214, 125, 220, 120, 216, 7, 96, 163, 218, 130, 60, 1, 241])

# Standard GATT characteristics for device info
UUID_VERSION_CHAR   = "00002a28-0000-1000-8000-00805f9b34fb"
UUID_SYSTEM_ID_CHAR = "00002a23-0000-1000-8000-00805f9b34fb"


# ── Pure-Python AES-128 ECB Decryptor (Zero External Dependencies) ─────────

S_BOX = [
    0x63, 0x7c, 0x77, 0x7b, 0xf2, 0x6b, 0x6f, 0xc5, 0x30, 0x01, 0x67, 0x2b, 0xfe, 0xd7, 0xab, 0x76,
    0xca, 0x82, 0xc9, 0x7d, 0xfa, 0x59, 0x47, 0xf0, 0xad, 0xd4, 0xa2, 0xaf, 0x9c, 0xa4, 0x72, 0xc0,
    0xb7, 0xfd, 0x93, 0x26, 0x36, 0x3f, 0xf7, 0xcc, 0x34, 0xa5, 0xe5, 0xf1, 0x71, 0xd8, 0x31, 0x15,
    0x04, 0xc7, 0x23, 0xc3, 0x18, 0x96, 0x05, 0x9a, 0x07, 0x12, 0x80, 0xe2, 0xeb, 0x27, 0xb2, 0x75,
    0x09, 0x83, 0x2c, 0x1a, 0x1b, 0x6e, 0x5a, 0xa0, 0x52, 0x3b, 0xd6, 0xb3, 0x29, 0xe3, 0x2f, 0x84,
    0x53, 0xd1, 0x00, 0xed, 0x20, 0xfc, 0xb1, 0x5b, 0x6a, 0xcb, 0xbe, 0x39, 0x4a, 0x4c, 0x58, 0xcf,
    0xd0, 0xef, 0xaa, 0xfb, 0x43, 0x4d, 0x33, 0x85, 0x45, 0xf9, 0x02, 0x7f, 0x50, 0x3c, 0x9f, 0xa8,
    0x51, 0xa3, 0x40, 0x8f, 0x92, 0x9d, 0x38, 0xf5, 0xbc, 0xb6, 0xda, 0x21, 0x10, 0xff, 0xf3, 0xd2,
    0xcd, 0x0c, 0x13, 0xec, 0x5f, 0x97, 0x44, 0x17, 0xc4, 0xa7, 0x7e, 0x3d, 0x64, 0x5d, 0x19, 0x73,
    0x60, 0x81, 0x4f, 0xdc, 0x22, 0x2a, 0x90, 0x88, 0x46, 0xee, 0xb8, 0x14, 0xde, 0x5e, 0x0b, 0xdb,
    0xe0, 0x32, 0x3a, 0x0a, 0x49, 0x06, 0x24, 0x5c, 0xc2, 0xd3, 0xac, 0x62, 0x91, 0x95, 0xe4, 0x79,
    0xe7, 0xc8, 0x37, 0x6d, 0x8d, 0xd5, 0x4e, 0xa9, 0x6c, 0x56, 0xf4, 0xea, 0x65, 0x7a, 0xae, 0x08,
    0xba, 0x78, 0x25, 0x2e, 0x1c, 0xa6, 0xb4, 0xc6, 0xe8, 0xdd, 0x74, 0x1f, 0x4b, 0xbd, 0x8b, 0x8a,
    0x70, 0x3e, 0xb5, 0x66, 0x48, 0x03, 0xf6, 0x0e, 0x61, 0x35, 0x57, 0xb9, 0x86, 0xc1, 0x1d, 0x9e,
    0xe1, 0xf8, 0x98, 0x11, 0x69, 0xd9, 0x8e, 0x94, 0x9b, 0x1e, 0x87, 0xe9, 0xce, 0x55, 0x28, 0xdf,
    0x8c, 0xa1, 0x89, 0x0d, 0xbf, 0xe6, 0x42, 0x68, 0x41, 0x99, 0x2d, 0x0f, 0xb0, 0x54, 0xbb, 0x16
]

INV_S_BOX = [0] * 256
for _i, _x in enumerate(S_BOX):
    INV_S_BOX[_x] = _i

RCON = [0x00, 0x01, 0x02, 0x04, 0x08, 0x10, 0x20, 0x40, 0x80, 0x1b, 0x36]


def _xtimes(a: int) -> int:
    return ((a << 1) ^ 0x1B) & 0xFF if (a & 0x80) else (a << 1)


def _mul(a: int, b: int) -> int:
    res = 0
    while b:
        if b & 1:
            res ^= a
        a = _xtimes(a)
        b >>= 1
    return res


class AES128:
    """Zero-dependency AES-128 ECB block decryptor (NIST SP 800-38A compliant)."""

    def __init__(self, key: bytes):
        if len(key) != 16:
            raise ValueError(f"AES-128 requires 16-byte key, got {len(key)}")
        self._round_keys = self._key_expansion(key)

    def _key_expansion(self, key: bytes) -> List[List[int]]:
        w = [list(key[i:i + 4]) for i in range(0, 16, 4)]
        for i in range(4, 44):
            temp = list(w[i - 1])
            if i % 4 == 0:
                temp = temp[1:] + temp[:1]
                temp = [S_BOX[b] for b in temp]
                temp[0] ^= RCON[i // 4]
            w.append([w[i - 4][j] ^ temp[j] for j in range(4)])

        round_keys = []
        for r in range(11):
            rk = []
            for c in range(4):
                rk.extend(w[r * 4 + c])
            round_keys.append(rk)
        return round_keys

    def decrypt_block(self, ciphertext: bytes) -> bytes:
        if len(ciphertext) != 16:
            raise ValueError("Ciphertext block must be exactly 16 bytes")

        state = [[ciphertext[r + 4 * c] for c in range(4)] for r in range(4)]

        def add_round_key(rk: List[int]):
            for r in range(4):
                for c in range(4):
                    state[r][c] ^= rk[r + 4 * c]

        def inv_shift_rows():
            state[1][0], state[1][1], state[1][2], state[1][3] = state[1][3], state[1][0], state[1][1], state[1][2]
            state[2][0], state[2][1], state[2][2], state[2][3] = state[2][2], state[2][3], state[2][0], state[2][1]
            state[3][0], state[3][1], state[3][2], state[3][3] = state[3][1], state[3][2], state[3][3], state[3][0]

        def inv_sub_bytes():
            for r in range(4):
                for c in range(4):
                    state[r][c] = INV_S_BOX[state[r][c]]

        def inv_mix_columns():
            for c in range(4):
                s0, s1, s2, s3 = state[0][c], state[1][c], state[2][c], state[3][c]
                state[0][c] = _mul(s0, 0x0e) ^ _mul(s1, 0x0b) ^ _mul(s2, 0x0d) ^ _mul(s3, 0x09)
                state[1][c] = _mul(s0, 0x09) ^ _mul(s1, 0x0e) ^ _mul(s2, 0x0b) ^ _mul(s3, 0x0d)
                state[2][c] = _mul(s0, 0x0d) ^ _mul(s1, 0x09) ^ _mul(s2, 0x0e) ^ _mul(s3, 0x0b)
                state[3][c] = _mul(s0, 0x0b) ^ _mul(s1, 0x0d) ^ _mul(s2, 0x09) ^ _mul(s3, 0x0e)

        # Round 10
        add_round_key(self._round_keys[10])
        inv_shift_rows()
        inv_sub_bytes()

        # Rounds 9 down to 1
        for r in range(9, 0, -1):
            add_round_key(self._round_keys[r])
            inv_mix_columns()
            inv_shift_rows()
            inv_sub_bytes()

        # Round 0
        add_round_key(self._round_keys[0])

        out = bytearray(16)
        for r in range(4):
            for c in range(4):
                out[r + 4 * c] = state[r][c]
        return bytes(out)


def _decrypt_gan_packet(data: bytes, aes: AES128) -> bytes:
    """Decrypt GAN Gen 2 19-byte packet using 2 overlapping 16-byte ECB blocks."""
    if len(data) < 19:
        return data
    arr = bytearray(data)
    block1 = aes.decrypt_block(bytes(arr[3:19]))
    arr[3:19] = block1
    block0 = aes.decrypt_block(bytes(arr[0:16]))
    arr[0:16] = block0
    return bytes(arr)


def _probably_decoded_correctly(data: bytes) -> bool:
    """Validate decrypted GAN packet by checking valid move code range (< 18) for recent moves."""
    if len(data) < 19:
        return False
    return all(data[i] < 0x12 for i in range(13, 19))


# ── Global BLE Manager ───────────────────────────────────────────────

class BLEManager(QObject):
    """
    Global BLE Singleton managing smart cube Bluetooth connections.
    """

    _instance: Optional[BLEManager] = None
    _singleton_lock: threading.Lock = threading.Lock()

    # Qt Signals
    move_received     = pyqtSignal(str)       # Emitted on EVERY verified turn, e.g. "U", "D", "R'", "F2"
    device_discovered = pyqtSignal(str, str)  # name, address
    scan_finished     = pyqtSignal()
    connected         = pyqtSignal(str)       # device_name
    disconnected      = pyqtSignal()
    status_changed    = pyqtSignal(str)
    error_occurred    = pyqtSignal(str)

    def __new__(cls, *args: Any, **kwargs: Any) -> BLEManager:
        with cls._singleton_lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
        return cls._instance

    @classmethod
    def get_instance(cls) -> BLEManager:
        if cls._instance is None:
            return cls()
        return cls._instance

    def __init__(self, parent: Optional[QObject] = None) -> None:
        if getattr(self, "_initialized", False):
            return
        super().__init__(parent=None)
        self._initialized = True

        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._thread: Optional[threading.Thread] = None
        self._client: Optional[_BleakClient] = None
        self._scanner: Any = None

        self._device_name: str = ""
        self._device_address: str = ""
        self._is_scanning: bool = False

        # Protocol state tracking
        self._last_giiker_counter: int = -1
        self._last_gan_counter: int = -1
        self._gan_ciphers: List[AES128] = []
        self._active_gan_cipher: Optional[Any] = None  # AES128 instance or False (unencrypted)

        self._start_event_loop()

    # ── Background Thread & Event Loop ───────────────────────────────

    def _start_event_loop(self) -> None:
        ready_event = threading.Event()

        def _runner():
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)
            ready_event.set()
            self._loop.run_forever()

        self._thread = threading.Thread(target=_runner, daemon=True, name="BLEManagerAsyncLoop")
        self._thread.start()
        ready_event.wait()

    def _submit(self, coro) -> None:
        if self._loop and self._loop.is_running():
            asyncio.run_coroutine_threadsafe(coro, self._loop)

    # ── Cube Device Classification ───────────────────────────────────

    @staticmethod
    def is_smart_cube(name: str, service_uuids: List[str]) -> bool:
        """
        Check if a device matches known smart cube names or service UUIDs.
        Handles prefixes, substrings, and UUIDs like GAN (6e400001, fff0), Giiker (aadb).
        """
        clean = (name or "").strip().upper()
        if any(k in clean for k in KNOWN_KEYWORDS):
            return True

        for u in service_uuids:
            u_clean = str(u).lower().replace("-", "")
            if any(snip in u_clean for snip in KNOWN_UUID_SNIPPETS):
                return True

        return False

    # ── Connection Management ────────────────────────────────────────

    @property
    def is_connected(self) -> bool:
        return self._client is not None and self._client.is_connected

    @property
    def connected_device_name(self) -> str:
        return self._device_name

    @property
    def connected_device_address(self) -> str:
        return self._device_address

    def start_scan(self, timeout_sec: float = 6.0, show_all: bool = False) -> None:
        """Start real-time BLE scanning."""
        if not HAS_BLEAK:
            self.error_occurred.emit("Bleak library is not installed.")
            self.scan_finished.emit()
            return

        if self._is_scanning:
            return

        self._is_scanning = True
        self.status_changed.emit("Scanning for smart cubes...")
        self._submit(self._async_scan(timeout_sec, show_all))

    def stop_scan(self) -> None:
        self._is_scanning = False

    async def _async_scan(self, timeout_sec: float, show_all: bool) -> None:
        seen_addresses: Set[str] = set()

        def _on_detected(device: Any, adv: Any) -> None:
            addr = device.address
            name = (adv.local_name or device.name or "").strip()
            uuids = [str(u) for u in (adv.service_uuids or [])]

            if not name and not show_all:
                return

            is_cube = self.is_smart_cube(name, uuids)

            if (is_cube or show_all) and addr not in seen_addresses:
                seen_addresses.add(addr)
                disp_name = name or f"Unknown [{addr[-5:]}]"
                self.device_discovered.emit(disp_name, addr)

        try:
            self._scanner = BleakScanner(detection_callback=_on_detected)
            await self._scanner.start()

            step = 0.25
            elapsed = 0.0
            while elapsed < timeout_sec and self._is_scanning:
                await asyncio.sleep(step)
                elapsed += step

            await self._scanner.stop()
            self._scanner = None

            if not seen_addresses:
                discs = await BleakScanner.discover(timeout=2.0, return_adv=True)
                for dev, adv in discs.values():
                    _on_detected(dev, adv)

        except Exception as e:
            self.error_occurred.emit(f"BLE Scan error: {e}")
        finally:
            self._is_scanning = False
            self.scan_finished.emit()
            self.status_changed.emit("Scan completed.")

    def connect_device(self, address: str, name: str = "") -> None:
        """Connect to the smart cube by MAC address."""
        if not HAS_BLEAK:
            self.error_occurred.emit("Bleak library is not installed.")
            return
        self.status_changed.emit(f"Connecting to {name or address}...")
        self._submit(self._async_connect(address, name))

    async def _async_connect(self, address: str, name: str) -> None:
        await self._async_disconnect()
        try:
            self._client = BleakClient(address, disconnected_callback=self._on_ble_disconnected)
            await self._client.connect()
            self._device_name = name or address
            self._device_address = address
            self._last_giiker_counter = -1
            self._last_gan_counter = -1
            self._active_gan_cipher = None
            self._gan_ciphers.clear()

            # Pre-generate candidate ciphers from address immediately
            self._generate_candidate_ciphers(address)

            # Retrieve GATT System ID for additional exact candidates
            await self._prepare_gan_crypto(address)

            await self._subscribe_notifications()
            self.connected.emit(self._device_name)
            self.status_changed.emit(f"Connected to {self._device_name}")
        except Exception as e:
            self._client = None
            self.error_occurred.emit(f"Connection failed: {e}")
            self.status_changed.emit("Disconnected")

    def _generate_candidate_ciphers(self, address: str, sys_id: Optional[bytes] = None) -> None:
        """
        Generate candidate AES-128 ciphers for GAN Gen 2 / i Carry cubes across
        all known protocol variants and salt derivations (6-byte MAC and 8-byte System ID).
        """
        salts: List[List[int]] = []

        # 1. System ID from GATT (if available)
        if sys_id and len(sys_id) >= 6:
            sid_bytes = list(sys_id)
            salts.append(sid_bytes)
            salts.append(list(reversed(sid_bytes)))

        # 2. Salts derived from hardware MAC address
        if address and ":" in address:
            try:
                parts = [int(p, 16) for p in address.split(":") if len(p) == 2]
                if len(parts) == 6:
                    # 6-byte raw MAC salt (direct and reversed)
                    salts.append(parts)
                    salts.append(list(reversed(parts)))

                    # 8-byte Bluetooth SIG System ID (EUI-64 format)
                    eui64_a = [parts[0], parts[1], parts[2], 0xFF, 0xFE, parts[3], parts[4], parts[5]]
                    eui64_b = [parts[5], parts[4], parts[3], 0xFE, 0xFF, parts[2], parts[1], parts[0]]
                    salts.append(eui64_a)
                    salts.append(list(reversed(eui64_a)))
                    salts.append(eui64_b)
            except Exception:
                pass

        if not salts:
            return

        ciphers: List[AES128] = []
        for base_key in (GAN_KEY_11, GAN_KEY_10):
            for salt in salts:
                for mod in (256, 255):
                    # Formula A: salt modifies first len(salt) bytes
                    k1 = bytearray(base_key)
                    for i in range(min(len(salt), 16)):
                        k1[i] = (k1[i] + salt[i]) % mod
                    try:
                        ciphers.append(AES128(bytes(k1)))
                    except Exception:
                        pass

                    # Formula B: wrap salt across all 16 bytes
                    k2 = bytearray(base_key)
                    for i in range(16):
                        k2[i] = (k2[i] + salt[i % len(salt)]) % mod
                    try:
                        ciphers.append(AES128(bytes(k2)))
                    except Exception:
                        pass

        self._gan_ciphers = ciphers

    async def _prepare_gan_crypto(self, address: str) -> None:
        """
        Attempt to read Bluetooth System ID characteristic (0x2A23)
        to augment candidate AES-128 ciphers.
        """
        if not self._client or not self._client.is_connected:
            return

        sys_id: Optional[bytes] = None
        try:
            sys_id = await self._client.read_gatt_char(UUID_SYSTEM_ID_CHAR)
        except Exception:
            pass

        if sys_id:
            self._generate_candidate_ciphers(address, sys_id=sys_id)

    def disconnect_device(self) -> None:
        self._submit(self._async_disconnect())

    async def _async_disconnect(self) -> None:
        if self._client and self._client.is_connected:
            try:
                await self._client.disconnect()
            except Exception:
                pass
        self._client = None
        self._device_name = ""
        self._device_address = ""
        self._active_gan_cipher = None
        self._gan_ciphers.clear()

    def _on_ble_disconnected(self, _client: _BleakClient) -> None:
        self._device_name = ""
        self._device_address = ""
        self._active_gan_cipher = None
        self._gan_ciphers.clear()
        self.disconnected.emit()
        self.status_changed.emit("Disconnected")

    # ── Notification Handlers ────────────────────────────────────────

    async def _subscribe_notifications(self) -> None:
        """Subscribe to the cube's primary data/turn characteristic."""
        if not self._client or not self._client.is_connected:
            return

        services = self._client.services

        # 1. Match against known smart cube characteristics by priority
        for target_uuid in PRIORITY_CHARACTERISTICS:
            for svc in services:
                for char in svc.characteristics:
                    if char.uuid.lower() == target_uuid.lower() and "notify" in char.properties:
                        await self._client.start_notify(char, self._handle_cube_notification)
                        self.status_changed.emit(f"Connected & listening on {char.uuid[:8]}...")
                        return

        # 2. Fallback: Find notify characteristic avoiding standard SIG services
        for svc in services:
            for char in svc.characteristics:
                u = char.uuid.lower()
                if "notify" in char.properties and not any(ex in u for ex in ("00002a19", "00002a00", "00002a01", "00002a23", "00002a28")):
                    try:
                        await self._client.start_notify(char, self._handle_cube_notification)
                        self.status_changed.emit(f"Connected (fallback characteristic: {char.uuid[:8]}...)")
                        return
                    except Exception:
                        continue

        self.error_occurred.emit("No supported notify characteristic found on device.")

    def _handle_cube_notification(self, _sender: Any, data: bytearray) -> None:
        """Central decoder for incoming smart cube notifications."""
        payload = bytes(data)
        if not payload:
            return

        # 1. Attempt Giiker 20-byte packet decode
        if len(payload) >= 18 and self._try_decode_giiker(payload):
            return

        # 2. Attempt GAN Gen 2 / i Carry encrypted/unencrypted decode
        if self._try_decode_gan(payload):
            return

        # Note: If packet is unparsed, NEVER fall back to emitting a fake "U" move!
        # Moves are only emitted when verified from the hardware packet.

    def _try_decode_giiker(self, payload: bytes) -> bool:
        """Parse Giiker 20-byte packet nibbles."""
        move_byte = payload[16]
        face_idx  = (move_byte >> 4) & 0x0F
        dir_idx   = move_byte & 0x0F
        counter   = payload[17]

        if counter != self._last_giiker_counter and face_idx in _GIIKER_FACE_MAP:
            face = _GIIKER_FACE_MAP[face_idx]
            dir_str = _GIIKER_DIR_MAP.get(dir_idx, "")
            self._last_giiker_counter = counter
            self.move_received.emit(f"{face}{dir_str}")
            return True
        return False

    def _try_decode_gan(self, payload: bytes) -> bool:
        """
        Decode GAN Gen 1 / Gen 2 / i Carry / Monster Go packet stream.
        Handles AES-128 decryption, validates bounds, and extracts sequential moves.
        """
        if len(payload) < 19:
            return False

        # If candidate ciphers not yet built, build them from device address immediately
        if not self._gan_ciphers and self._device_address:
            self._generate_candidate_ciphers(self._device_address)

        decrypted: Optional[bytes] = None

        # 1. If an active cipher is already locked in, use it
        if self._active_gan_cipher is not None:
            cipher, offset = self._active_gan_cipher
            if cipher is False:
                decrypted = payload[offset : offset + 19]
            else:
                decrypted = _decrypt_gan_packet(payload[offset : offset + 19], cipher)
        else:
            offsets = (0, 1) if len(payload) >= 20 else (0,)

            # 2. Test if raw packet is already unencrypted (offset 0 or 1)
            for off in offsets:
                block = payload[off : off + 19]
                if _probably_decoded_correctly(block):
                    self._active_gan_cipher = (False, off)
                    decrypted = block
                    print(f"[BLE] GAN cube verified as UNENCRYPTED at offset {off}")
                    break

            # 3. Test candidate AES ciphers
            if decrypted is None:
                for cipher in self._gan_ciphers:
                    for off in offsets:
                        block = payload[off : off + 19]
                        cand = _decrypt_gan_packet(block, cipher)
                        if _probably_decoded_correctly(cand):
                            self._active_gan_cipher = (cipher, off)
                            decrypted = cand
                            print(f"[BLE] GAN AES cipher LOCKED IN at offset {off}!")
                            break
                    if decrypted is not None:
                        break

        if not decrypted or not _probably_decoded_correctly(decrypted):
            return False

        # Byte 12: rolling move counter (0..255)
        counter = decrypted[12]

        # Initial packet sync: record starting counter without emitting moves
        if self._last_gan_counter == -1:
            self._last_gan_counter = counter
            print(f"[BLE] Initial state synchronized. Starting move counter: {counter}")
            return True

        # Compute delta of intervening moves (handles 8-bit counter overflow)
        delta = (counter - self._last_gan_counter) % 256
        if delta == 0:
            return True  # Heartbeat or status packet, no moves

        # Up to 6 recent moves are stored chronologically at decrypted[19 - num_moves : 19]
        num_moves = min(delta, 6)
        recent_moves = decrypted[19 - num_moves : 19]

        for m_code in recent_moves:
            if m_code in GAN_MOVE_MAP:
                move_str = GAN_MOVE_MAP[m_code]
                print(f"[BLE] >>> Physical Turn Detected: {move_str}")
                self.move_received.emit(move_str)

        self._last_gan_counter = counter
        return True

    # ── Testing & Simulation ─────────────────────────────────────────

    def inject_move(self, move_str: str) -> None:
        clean_move = move_str.strip().upper().replace("’", "'").replace("`", "'")
        if clean_move:
            self.move_received.emit(clean_move)

    def shutdown(self) -> None:
        if self._loop and self._loop.is_running():
            self._loop.call_soon_threadsafe(self._loop.stop)
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)
