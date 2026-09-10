import math
import unittest
from follow import FollowController, target_at, KEYFRAMES


class FollowTests(unittest.TestCase):
    def test_noise_inside_hysteresis_band_does_not_restart(self):
        c=FollowController()
        self.assertTrue(c.command(2.,0,0,0,.25,0)[2])
        for n,d in enumerate((.261,.30,.259,.379,.27)):
            self.assertTrue(c.command(3.+n,0,0,0,d,0)[2])
        self.assertEqual([e['event'] for e in c.events],['stop'])
        self.assertFalse(c.command(9.,0,0,0,.381,0)[2])
        self.assertEqual([e['event'] for e in c.events],['stop','resume'])

    def test_resume_dwell_but_immediate_proximity_stop(self):
        c=FollowController()
        c.command(2.,0,0,0,.25,0)
        self.assertTrue(c.command(2.1,0,0,0,.5,0)[2])
        self.assertFalse(c.command(3.,0,0,0,.5,0)[2])
        self.assertTrue(c.command(3.1,0,0,0,.24,0)[2])

    def test_yaw_wraparound_uses_short_turn(self):
        c=FollowController()
        self.assertGreater(c.command(2.,0,0,math.pi-.01,-1,-.01)[1],0)
        self.assertLess(c.command(2.,0,0,-math.pi+.01,-1,.01)[1],0)

    def test_target_continuity_and_pauses(self):
        origin=(.6,.05)
        for t,dx,dy in KEYFRAMES:
            p=target_at(t,origin)
            self.assertAlmostEqual(p[0],origin[0]+dx)
            self.assertAlmostEqual(p[1],origin[1]+dy)
            left,right=target_at(t-1e-6,origin),target_at(t+1e-6,origin)
            self.assertLess(math.dist(left[:2],right[:2]),1e-6)
        for t in (4.,20.,36.):
            self.assertEqual(target_at(t,origin)[2:],(0.,0.))


if __name__=='__main__':
    unittest.main()
