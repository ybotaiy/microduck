"""Head-mounted virtual camera and synchronized presentation; no vision control."""
import json
import math
from pathlib import Path

import mujoco
import numpy as np
from PIL import Image, ImageDraw, ImageFont

WIDTH, HEIGHT = 480, 288


def add_camera(scene):
    source = scene.camera('head_camera')
    source.parent.add_camera(name='robot_view', pos=source.pos.copy(), fovy=70)


def configure(model, data):
    """Calibrate a fixed local rotation at the runner's neutral initialization."""
    cid = model.camera('robot_view').id
    bid = int(model.cam_bodyid[cid])
    pitch = math.radians(25)
    # MuJoCo camera axes: +X image right, +Y image up, -Z viewing direction.
    world = np.array([[0, math.sin(pitch), -math.cos(pitch)],
                      [-1, 0, 0], [0, math.cos(pitch), math.sin(pitch)]])
    local = data.xmat[bid].reshape(3, 3).T @ world
    mujoco.mju_mat2Quat(model.cam_quat[cid], local.reshape(-1))
    model.geom('ball_geom').rgba[:] = [.95, .03, .75, 1]
    mujoco.mj_forward(model, data)
    return cid


def composite(third, robot, title, detail):
    frame = Image.new('RGB', (960, 384), (15, 22, 32))
    frame.paste(Image.fromarray(third), (0, 64))
    frame.paste(Image.fromarray(robot), (480, 64))
    draw = ImageDraw.Draw(frame)
    font = ImageFont.load_default(size=17)
    small = ImageFont.load_default(size=14)
    draw.text((14, 8), title, font=font, fill='white')
    draw.text((14, 39), 'THIRD PERSON', font=small, fill='#9ecaff')
    draw.text((494, 39), 'ROBOT VIEW | head mounted', font=small, fill='#9ecaff')
    draw.text((14, 361), detail, font=small, fill='white')
    return frame


class DualView:
    def __init__(self, model, out):
        self.model = model
        self.renderer = mujoco.Renderer(model, height=HEIGHT, width=WIDTH)
        self.out = Path(out)
        self.rows = []

    def render(self, data, camera, t, state, robot_frame=None, vision=False, search=False):
        self.renderer.update_scene(data, camera)
        third = self.renderer.render().copy()
        if robot_frame is None:
            self.renderer.update_scene(data, 'robot_view')
            robot = self.renderer.render().copy()
        else:
            robot = robot_frame
        cid = self.model.camera('robot_view').id
        self.rows.append(dict(t=t, position=data.cam_xpos[cid].tolist(),
                              rotation=data.cam_xmat[cid].tolist()))
        return composite(third, robot, f'{"IMAGE CONTROL" if vision else "CAMERA VALIDATION"} | t={t:05.2f}s | {state}',
                         '1x speed | XML simulation | RGB target + robot proprioception | bounded search' if search else
                         '1x speed | XML simulation | RGB-only steering / size stop / lost stop' if vision else
                         '1x speed | XML simulation | magenta ball | steering uses simulator coordinates')

    def close(self):
        self.renderer.close()
        (self.out/'camera-poses.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in self.rows))


def validate(model, data, qa, out):
    """Snapshot tests use imposed poses, separate from the physical rollout.

    Segmentation and projection are evaluation-only and never feed the policy.
    """
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    saved = data.qpos.copy()
    ball = model.body('ball').id
    saved_ball = model.body_pos[ball].copy()
    cid = model.camera('robot_view').id
    gid = model.geom('ball_geom').id
    camera = mujoco.MjvCamera()
    camera.azimuth, camera.elevation, camera.distance = 125, -25, 1.65
    camera.lookat[:] = [.25, 0, .1]
    renderer = mujoco.Renderer(model, height=HEIGHT, width=WIDTH)
    checks = []
    try:
        for yaw in (0, math.pi/2):
            for name, xy, expected in [('front',(.8,0),'center'),('left',(.8,.35),'left'),
                                       ('right',(.8,-.35),'right'),('outside-left',(0,.8),'hidden'),
                                       ('behind',(-.8,0),'hidden')]:
                data.qpos[:] = saved
                data.qpos[qa+3:qa+7] = [math.cos(yaw/2),0,0,math.sin(yaw/2)]
                rot = np.array([[math.cos(yaw),-math.sin(yaw)],[math.sin(yaw),math.cos(yaw)]])
                model.body_pos[ball,:2] = rot @ xy
                mujoco.mj_forward(model,data)
                renderer.update_scene(data,'robot_view')
                rgb = renderer.render().copy()
                renderer.enable_segmentation_rendering()
                renderer.update_scene(data,'robot_view')
                seg = renderer.render().copy()
                renderer.disable_segmentation_rendering()
                yy,xx = np.where((seg[:,:,0]==gid)&(seg[:,:,1]==int(mujoco.mjtObj.mjOBJ_GEOM)))
                center = [float(xx.mean()),float(yy.mean())] if len(xx) else None
                local = data.cam_xmat[cid].reshape(3,3).T @ (data.xpos[ball]-data.cam_xpos[cid])
                f = .5*HEIGHT/math.tan(math.radians(model.cam_fovy[cid])/2)
                predicted = [WIDTH/2+f*local[0]/(-local[2]), HEIGHT/2-f*local[1]/(-local[2])] if local[2]<0 else None
                passed = (center is None if expected=='hidden' else center is not None and
                          ((abs(center[0]-WIDTH/2)<5) if expected=='center' else
                           (center[0]<WIDTH/2-20 if expected=='left' else center[0]>WIDTH/2+20)))
                projection_error = float(np.linalg.norm(np.array(center)-predicted)) if center and predicted else None
                passed = passed and (projection_error is None or projection_error<3)
                forward = -data.cam_xmat[cid].reshape(3,3)[:,2]
                heading_error = math.atan2(math.sin(math.atan2(forward[1],forward[0])-yaw),math.cos(math.atan2(forward[1],forward[0])-yaw))
                passed = passed and abs(heading_error)<1e-6
                key=f'{name}-yaw-{round(math.degrees(yaw))}'
                checks.append(dict(case=key, expected=expected, visible_pixels=len(xx), centroid=center,
                                   projected_center=predicted, projection_error_px=projection_error,
                                   camera_heading_error_rad=heading_error, passed=bool(passed)))
                renderer.update_scene(data,camera)
                third=renderer.render().copy()
                composite(third,rgb,f'CAMERA CHECK | {key} | {"PASS" if passed else "FAIL"}',
                          'POSED SNAPSHOT | evaluation only | 70 deg vertical FOV | 25 deg downward neutral aim').save(out/f'{key}.png')
    finally:
        data.qpos[:] = saved
        model.body_pos[ball] = saved_ball
        mujoco.mj_forward(model,data)
        renderer.close()
    result=dict(camera='robot_view', mount='same position and parent as upstream head_camera',
                fovy_degrees=70, neutral_downward_degrees=25,
                local_quaternion=model.cam_quat[cid].tolist(),
                note='Idealized virtual optics; pose tests are not physical turns or image-only control.',
                passed=all(c['passed'] for c in checks),checks=checks)
    (out/'checks.json').write_text(json.dumps(result,indent=2)+'\n')
    if not result['passed']:
        raise AssertionError('Camera validation failed; inspect checks.json')
