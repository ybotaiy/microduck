import unittest
from vision_follow import BallObservation
from vision_search import VisualSearch


class SearchTests(unittest.TestCase):
    def test_loss_settles_before_scanning(self):
        s=VisualSearch()
        for n in range(70):
            vx,wz,state,head=s.command(n*.02,n*.02,None,0)
            self.assertEqual((vx,wz,head),(0.,0.,0.))
        self.assertEqual(state,'SETTLE_LOST')
        self.assertEqual(s.command(1.6,1.6,None,0)[2],'HEAD_SEARCH')

    def test_requires_distinct_stable_frames(self):
        s=VisualSearch();s.command(0,0,None,0)
        s.command(1.6,1.6,None,0)
        obs=BallObservation(0,.1,100)
        for n in range(5):
            s.command(1.7+n*.01,1.7,obs,.5)
        self.assertEqual(s.reacquisitions,0)
        for n in range(1,6):
            s.command(1.7+n*.04,1.7+n*.04,obs,.5)
        self.assertEqual(s.reacquisitions,1)
        self.assertEqual(s.state,'ALIGN')

    def test_reappearance_does_not_skip_settling(self):
        s=VisualSearch();s.command(0,0,None,0)
        for n in range(30):
            cmd=s.command(.1+n*.04,.1+n*.04,BallObservation(0,.1,100),.5)
            self.assertEqual(cmd[:2],(0.,0.))
            self.assertEqual(cmd[2],'SETTLE_LOST')

    def test_search_limits_and_timeout(self):
        s=VisualSearch();head=0.;last=0.;body_times=[]
        for n in range(1200):
            t=n*.02
            vx,wz,state,head=s.command(t,t,None,head,(0.,0.,0.))
            self.assertEqual(vx,0.)
            self.assertLessEqual(abs(head),1.1+1e-8)
            if state=='HEAD_SEARCH':
                self.assertLessEqual(abs(head-last),.012+1e-8)
            if state=='BODY_SEARCH':body_times.append(t)
            last=head
        self.assertTrue(body_times)
        self.assertLessEqual(body_times[-1]-body_times[0],6.)
        self.assertEqual(s.state,'GAVE_UP')

    def test_no_approach_for_close_reacquired_ball(self):
        s=VisualSearch();s.command(0,0,None,0);s.command(1.6,1.6,None,0)
        for n in range(6):
            cmd=s.command(1.7+n*.04,1.7+n*.04,BallObservation(0,.2,100),.5)
        self.assertEqual(cmd[:2],(0.,0.))
        self.assertEqual(cmd[2],'ALIGN_NEAR')

if __name__=='__main__':unittest.main()
