"""Bounded turn based on robot odometry; no target coordinates."""
import math


class BoundedTurn:
    def __init__(self,target=math.pi/2,speed=.3,max_time=10.,max_path=.7,max_displacement=.45):
        self.target,self.speed=target,speed
        self.max_time,self.max_path,self.max_displacement=max_time,max_path,max_displacement
        self.started=None;self.previous=None;self.origin=None
        self.angle=0.;self.path=0.;self.displacement=0.;self.reason=None;self.elapsed=0.

    def command(self,t,x,y,yaw):
        if self.started is None:
            self.started=t;self.previous=(x,y,yaw);self.origin=(x,y)
        px,py,pyaw=self.previous
        self.angle += math.atan2(math.sin(yaw-pyaw),math.cos(yaw-pyaw))
        self.path += math.hypot(x-px,y-py)
        self.displacement=math.hypot(x-self.origin[0],y-self.origin[1]);self.previous=(x,y,yaw)
        if self.reason is None:
            self.elapsed=t-self.started
            if abs(self.angle)>=abs(self.target) and self.angle*self.target>0:self.reason='ANGLE_REACHED'
            elif self.elapsed>=self.max_time:self.reason='TIME_LIMIT'
            elif self.path>=self.max_path or self.displacement>=self.max_displacement:self.reason='MOTION_LIMIT'
        if self.reason:return 0.,0.,self.reason
        return self.speed,math.copysign(1.2,self.target),'TURN'

    def metrics(self):
        return dict(reason=self.reason,angle_rad=self.angle,path_m=self.path,displacement_m=self.displacement,
                    command_duration_s=self.elapsed,target_rad=self.target,speed_command=self.speed,
                    max_time=self.max_time,max_path=self.max_path,max_displacement=self.max_displacement)
