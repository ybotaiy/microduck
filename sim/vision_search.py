"""Bounded visual search using camera observations and a head-joint encoder."""
import math
from vision_follow import VisionFollower
from bounded_turn import BoundedTurn


class VisualSearch:
    settle_time = 1.5
    head_limit = 1.1
    head_rate = .6
    stable_frames = 6
    body_scan_time = 6.

    def __init__(self):
        self.follower = VisionFollower()
        self.state = 'TRACK'
        self.entered = 0.
        self.head_target = 0.
        self.last_time = None
        self.last_frame = None
        self.seen_count = 0
        self.events = []
        self.scan_index = 0
        self.scan_targets = [1.1,-1.1,0.]
        self.reacquisitions = 0
        self.body_turn = None
        self.loss_started = None
        self.loss_origin = None
        self.search_limit = 28.
        self.search_displacement_limit = .5

    def transition(self, state, now):
        if state != self.state:
            self.events.append(dict(t=now,previous=self.state,state=state))
            self.state, self.entered = state, now

    def command(self, now, frame_time, observation, head_encoder, body_pose=None):
        dt = .02 if self.last_time is None else max(0.,min(.04,now-self.last_time))
        self.last_time = now
        if self.state == 'GAVE_UP':
            return 0.,0.,self.state,self.head_target
        fresh = observation is not None and 0 <= now-frame_time <= .12
        if not fresh:
            self.seen_count = 0
        elif frame_time != self.last_frame:
            self.seen_count += 1
        self.last_frame = frame_time
        if self.state == 'TRACK':
            if not fresh:
                self.transition('SETTLE_LOST',now)
                self.scan_index = 0
                self.body_turn = None
                self.loss_started = now
                self.loss_origin = body_pose[:2] if body_pose is not None else None
            else:
                vx,wz,state = self.follower.command(now,frame_time,observation)
                self.head_target = max(-self.head_limit,min(self.head_limit,self.head_target))
                self.head_target += max(-dt*self.head_rate,min(dt*self.head_rate,-self.head_target))
                return vx,wz,state,self.head_target
        if self.loss_started is not None and self.state not in ('TRACK','GAVE_UP'):
            moved = math.hypot(body_pose[0]-self.loss_origin[0],body_pose[1]-self.loss_origin[1]) if body_pose is not None and self.loss_origin is not None else 0.
            if now-self.loss_started >= self.search_limit or moved >= self.search_displacement_limit:
                self.transition('GAVE_UP',now)
                return 0.,0.,self.state,self.head_target
        if self.state == 'SETTLE_LOST':
            if now-self.entered >= self.settle_time:
                self.transition('HEAD_SEARCH',now)
        if self.state in ('HEAD_SEARCH','BODY_SEARCH','GAVE_UP','SETTLE_LOST'):
            if fresh and self.seen_count >= self.stable_frames and (self.state != 'SETTLE_LOST' or now-self.entered >= self.settle_time):
                self.reacquisitions += 1
                self.transition('ALIGN',now)
            elif self.state == 'HEAD_SEARCH':
                if not fresh:
                    target = self.scan_targets[self.scan_index]
                    self.head_target += max(-dt*self.head_rate,min(dt*self.head_rate,target-self.head_target))
                    if abs(self.head_target-target)<.001 and abs(head_encoder-target)<.15:
                        self.scan_index += 1
                        if self.scan_index == len(self.scan_targets):
                            self.transition('BODY_SEARCH',now)
                if now-self.entered > 12 and self.state == 'HEAD_SEARCH':
                    self.transition('BODY_SEARCH',now)
            elif self.state == 'BODY_SEARCH':
                self.head_target = 0.
                if body_pose is None:
                    self.transition('GAVE_UP',now)
                else:
                    if self.body_turn is None:
                        self.body_turn = BoundedTurn(target=math.pi,speed=0.,max_time=self.body_scan_time,max_displacement=.15)
                    vx,wz,reason = self.body_turn.command(now,*body_pose)
                    if self.body_turn.reason:
                        self.transition('GAVE_UP',now)
                    else:
                        return vx,wz,self.state,self.head_target
        if self.state == 'ALIGN':
            if not fresh:
                self.transition('SETTLE_LOST',now)
                self.scan_index = 0
                return 0.,0.,self.state,self.head_target
            image_bearing = -math.atan(observation.horizontal*(480/288)*math.tan(math.radians(70)/2))
            bearing = head_encoder + image_bearing
            self.head_target = max(-self.head_limit,min(self.head_limit,self.head_target + image_bearing*1.4*dt))
            if abs(head_encoder)<.15 and abs(observation.horizontal)<.18:
                self.head_target=0.
                self.transition('TRACK',now)
                return (*self.follower.command(now,frame_time,observation)[:2], self.follower.state, self.head_target)
            if observation.diameter >= self.follower.stop_size:
                # Do not walk toward a close target just to align the body.
                return 0.,0.,'ALIGN_NEAR',self.head_target
            if now-self.entered>10:
                self.transition('GAVE_UP',now)
                return 0.,0.,self.state,self.head_target
            return .3,max(-1.2,min(1.2,2*bearing)),self.state,self.head_target
        return 0.,0.,self.state,self.head_target
