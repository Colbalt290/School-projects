"""
BinTimer Core Package
═════════════════════
Decoupled backend architecture for BinTimer smart cube integration.
"""

try:
    from bintimer.core.virtual_cube import VirtualCube
    from bintimer.core.ble_manager import BLEManager
    from bintimer.core.timer_state_machine import TimerStateMachine, TimerPhase
except ImportError:
    try:
        from core.virtual_cube import VirtualCube
        from core.ble_manager import BLEManager
        from core.timer_state_machine import TimerStateMachine, TimerPhase
    except ImportError:
        from .virtual_cube import VirtualCube
        from .ble_manager import BLEManager
        from .timer_state_machine import TimerStateMachine, TimerPhase

__all__ = [
    "VirtualCube",
    "BLEManager",
    "TimerStateMachine",
    "TimerPhase",
]
