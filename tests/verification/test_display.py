"""Native key delivery requires focus on the harness's own process window.

These checks exercise the refusal path without connecting to a desktop. Real
window journeys separately verify delivery through Xwayland and winit.
"""
from __future__ import annotations

import ctypes as c
import unittest
from unittest.mock import Mock

from tests.verification.viewer_display import X11


class KeyFocusTests(unittest.TestCase):
    def harness(self, focused: int) -> X11:
        x = X11.__new__(X11)
        x.lib = Mock()
        x.display, x.root = 1, 2

        def get_focus(display, window, revert):
            c.cast(window, c.POINTER(c.c_ulong))[0] = focused

        x.lib.XGetInputFocus.side_effect = get_focus
        x.lib.XKeysymToKeycode.return_value = 57
        x.lib.XSendEvent.return_value = 1
        return x

    def test_unfocused_window_refuses_key_delivery(self):
        x = self.harness(99)
        with self.assertRaisesRegex(RuntimeError, "did not acquire keyboard focus"):
            x.key(42, "n")
        x.lib.XSendEvent.assert_not_called()

    def test_focused_window_delivers_one_press_and_release(self):
        x = self.harness(42)
        x.key(42, "n")
        events = x.lib.XSendEvent.call_args_list
        self.assertEqual(len(events), 2)
        self.assertEqual([args[0][1] for args in events], [42, 42])
        self.assertEqual([args[0][3] for args in events], [1, 2])


if __name__ == "__main__":
    unittest.main()
