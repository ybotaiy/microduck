import unittest
import numpy as np
from vision_follow import BallObservation, VisionFollower, detect_ball


def scene(cx=50, radius=8):
    rgb=np.zeros((80,100,3),dtype=np.uint8)
    yy,xx=np.ogrid[:80,:100]
    rgb[(xx-cx)**2+(yy-40)**2<=radius**2]=[240,10,190]
    return rgb


class VisionTests(unittest.TestCase):
    def test_color_position_and_size(self):
        a,b=detect_ball(scene(25)),detect_ball(scene(75,12))
        self.assertLess(a.horizontal,0)
        self.assertGreater(b.horizontal,0)
        self.assertGreater(b.diameter,a.diameter)
        self.assertIsNone(detect_ball(np.zeros((80,100,3),dtype=np.uint8)))

    def test_speckle_and_clipped_target(self):
        rgb=np.zeros((80,100,3),dtype=np.uint8);rgb[2,3]=[240,10,190]
        self.assertIsNone(detect_ball(rgb))
        self.assertIsNone(detect_ball(scene(0)))

    def test_steering_direction_and_lost_stop(self):
        c=VisionFollower()
        self.assertGreater(c.command(0,0,BallObservation(-.4,.1,50))[1],0)
        self.assertLess(c.command(.02,.02,BallObservation(.4,.1,50))[1],0)
        self.assertEqual(c.command(.04,.04,None),(0.,0.,'LOST'))
        self.assertEqual(c.command(1,0,BallObservation(0,.1,50)),(0.,0.,'LOST'))

    def test_stop_hysteresis(self):
        c=VisionFollower()
        self.assertEqual(c.command(0,0,BallObservation(0,.21,50))[2],'STOP')
        self.assertEqual(c.command(.1,.1,BallObservation(0,.14,50))[2],'STOP')
        self.assertEqual(c.command(1,1,BallObservation(0,.155,50))[2],'STOP')
        self.assertEqual(c.command(1.1,1.1,BallObservation(0,.14,50))[2],'APPROACH')
        self.assertEqual(c.command(1.12,1.12,BallObservation(0,.21,50))[2],'STOP')

if __name__=='__main__':
    unittest.main()
