import math
import unittest
from bounded_turn import BoundedTurn
from vision_search import VisualSearch


class TurnTests(unittest.TestCase):
    def test_angle_wrap_and_stop(self):
        b=BoundedTurn(target=.2,speed=0)
        self.assertEqual(b.command(0,0,0,3.1)[0],0)
        self.assertEqual(b.command(.2,0,0,-2.9)[:2],(0.,0.))
        self.assertEqual(b.reason,'ANGLE_REACHED')

    def test_budget_limits_and_latch(self):
        for pose,reason in [((1.,0.,0.),'MOTION_LIMIT'),((0.,0.,0.),'TIME_LIMIT')]:
            b=BoundedTurn(max_time=1.)
            b.command(0,0,0,0)
            self.assertEqual(b.command(1,*pose)[:2],(0.,0.))
            self.assertIn(b.reason,['TIME_LIMIT','MOTION_LIMIT'])
            self.assertEqual(b.command(2,0,0,0)[:2],(0.,0.))

    def test_zero_forward_scan_and_missing_odometry_stop(self):
        s=VisualSearch();s.state='BODY_SEARCH';s.entered=0
        self.assertEqual(s.command(0,0,None,0)[2],'GAVE_UP')
        s=VisualSearch();s.state='BODY_SEARCH';s.entered=0
        cmd=s.command(0,0,None,0,(0,0,0))
        self.assertEqual(cmd[:2],(0.,1.2))

    def test_terminal_timeout_cannot_chatter(self):
        from vision_follow import BallObservation
        s=VisualSearch();s.state='GAVE_UP'
        for n in range(20):
            self.assertEqual(s.command(n*.04,n*.04,BallObservation(0,.1,100),0,(0,0,0))[2],'GAVE_UP')

if __name__=='__main__':unittest.main()
