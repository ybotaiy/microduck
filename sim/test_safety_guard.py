import unittest

from safety_guard import MotionGuard


class MotionGuardTests(unittest.TestCase):
    def test_normal_command_passes(self):
        self.assertEqual(MotionGuard().command(.3, -.2), (.3, -.2, None))

    def test_terminal_events_latch_zero_commands(self):
        for event in ({'manual_stop': True}, {'fell': True},
                      {'stale_camera': True}, {'finite': False}):
            guard = MotionGuard()
            self.assertEqual(guard.command(.3, .2, **event)[:2], (0.0, 0.0))
            self.assertEqual(guard.command(.3, .2)[:2], (0.0, 0.0))


if __name__ == '__main__':
    unittest.main()
