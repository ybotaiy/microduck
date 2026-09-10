"""Scripted simulation target and distance-hysteresis follower; no perception."""
import math

# t [s], x/y offset [m] relative to --ball. Piecewise linear and repeatable.
KEYFRAMES = ((0.,0.,0.), (8.,0.,0.), (16.,.40,.18),
             (23.,.40,.18), (31.,.77,-.12), (42.,.77,-.12))


def target_at(t, origin):
    for a,b in zip(KEYFRAMES,KEYFRAMES[1:]):
        if t <= b[0]:
            u = max(0.,(t-a[0])/(b[0]-a[0]))
            vx,vy = (b[1]-a[1])/(b[0]-a[0]), (b[2]-a[2])/(b[0]-a[0])
            return (origin[0]+a[1]+u*(b[1]-a[1]),
                    origin[1]+a[2]+u*(b[2]-a[2]), vx,vy)
    return origin[0]+KEYFRAMES[-1][1],origin[1]+KEYFRAMES[-1][2],0.,0.


class FollowController:
    stop_distance = .26
    resume_distance = .38
    min_dwell = .8

    def __init__(self):
        self.stopped = False
        self.last_change = -math.inf
        self.events = []

    def command(self,t,x,y,yaw,bx,by):
        distance = math.hypot(bx-x,by-y)
        bearing = math.atan2(by-y,bx-x)
        error = math.atan2(math.sin(bearing-yaw),math.cos(bearing-yaw))
        change = None
        if self.stopped and distance >= self.resume_distance and t-self.last_change >= self.min_dwell:
            self.stopped,change = False,'resume'
        elif not self.stopped and distance <= self.stop_distance:
            # Stop immediately even inside dwell: never delay a proximity stop.
            self.stopped,change = True,'stop'
        if change:
            self.last_change = t
            self.events.append(dict(t=t,event=change,distance=distance))
        vx,wz = (0.,0.) if self.stopped else (.3,max(-1.2,min(1.2,2.*error)))
        return vx,wz,self.stopped,distance,error


def analyze_follow(rows,controller):
    events=controller.events
    first_stop=next((e['t'] for e in events if e['event']=='stop'),None)
    gaps=[b['t']-a['t'] for a,b in zip(events,events[1:])]
    tail=rows[-50:]
    pauses=[]
    for start,end in ((0.,8.),(16.,23.),(31.,42.)):
        sample=[r for r in rows if end-1. <= r['t'] < end]
        pauses.append(dict(start=start,end=end,observed=bool(sample),
            held_stop=bool(sample) and all(r['state']=='STOP' for r in sample),
            mean_speed=sum(r['speed'] for r in sample)/len(sample) if sample else None))
    # Ground truth is always available; this detects sustained excessive distance,
    # not camera/perception loss. An initial approach is excluded until first stop.
    far_duration,max_far=0.,0.
    for r in rows:
        far_duration=far_duration+.02 if first_stop is not None and r['t']>=first_stop and r['distance']>1. else 0.
        max_far=max(max_far,far_duration)
    resumed_legs=[any(e['event']=='resume' and start<=e['t']<end for e in events)
                  for start,end in ((8.,16.),(23.,31.))]
    return dict(events=events,stop_count=sum(e['event']=='stop' for e in events),
        resume_count=sum(e['event']=='resume' for e in events),
        resumed_after_each_departure=resumed_legs,
        min_transition_interval=min(gaps) if gaps else None,
        pause_checks=pauses,tracking_lost=max_far>=2.,max_far_duration=max_far,
        max_distance=max(r['distance'] for r in rows),
        max_distance_after_first_stop=max((r['distance'] for r in rows if first_stop is not None and r['t']>=first_stop),default=None),
        min_distance=min(r['distance'] for r in rows),
        final_held_stop=all(r['state']=='STOP' for r in tail))
