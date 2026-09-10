"""CPU experiments using the unmodified official runner (Apache-2.0).

The first version uses XML position actuators, not the default BAM model.
Robot motion comes from MuJoCo and the official policies. In follow mode only,
the target ball follows an explicitly scripted mocap trajectory.
"""
import argparse
import contextlib
import hashlib
import importlib.util
import io
import json
import math
import subprocess
from pathlib import Path

import imageio.v2 as imageio
import mujoco
import numpy as np
from PIL import Image, ImageDraw
from follow import FollowController, target_at, analyze_follow, KEYFRAMES


def steer(x, y, yaw, bx, by, stopped):
    distance = math.hypot(bx - x, by - y)
    error = math.atan2(math.sin(math.atan2(by-y, bx-x)-yaw),
                       math.cos(math.atan2(by-y, bx-x)-yaw))
    if stopped or distance <= 0.24:
        return 0.0, 0.0, True, distance, error
    yaw_rate = float(np.clip(2.0 * error, -1.2, 1.2))
    # This shipped policy did not sustain in-place turning in the XML model.
    # Use a walking turn; measure the actual path rather than assuming yaw obedience.
    forward = 0.3
    return forward, yaw_rate, False, distance, error


def run(args):
    lab = args.lab.resolve()
    runner = lab / 'microduck_rl/scripts/infer_policy.py'
    spec = importlib.util.spec_from_file_location('official_infer', runner)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    scene = lab / 'microduck_rl/src/mjlab_microduck/robot/microduck/scene_ball.xml'
    scene_spec = mujoco.MjSpec.from_file(str(scene))
    # The ball is fixed for static modes, or mocap-scripted for follow mode.
    ball_joint = scene_spec.joint('ball_free')
    ball_body = ball_joint.parent
    scene_spec.delete(ball_joint)
    if args.mode == 'follow':
        ball_body.mocap = True
    ball_body.pos = [args.ball[0], args.ball[1], 0.035]
    model = scene_spec.compile()
    model.vis.global_.offwidth = 800
    model.vis.global_.offheight = 480
    model.opt.timestep = 0.005
    data = mujoco.MjData(model)
    quiet = io.StringIO()
    with contextlib.redirect_stdout(quiet):
        policy = module.PolicyInference(
            model, data, walking_onnx_path=str(lab / 'policies/alpha_walking.onnx'),
            standing_onnx_path=str(lab / 'policies/alpha_stand.onnx'),
            new_cmd_obs=True, use_projected_gravity=True)
        policy.set_vel_cmd(0, 0, 0)
    jid = model.joint('trunk_base_freejoint').id
    qa, va = int(model.jnt_qposadr[jid]), int(model.jnt_dofadr[jid])
    data.qpos[qa:qa+7] = [0, 0, 0.125, 1, 0, 0, 0]
    data.qpos[policy.joint_qpos_indices] = policy.default_pose
    policy.set_position_targets(policy.default_pose)
    mujoco.mj_forward(model, data)
    assert policy.get_observations().shape == (61,)
    camera = mujoco.MjvCamera()
    camera.azimuth, camera.elevation, camera.distance = 125, -25, 1.65
    camera.lookat[:] = [0.25, 0, 0.10]
    renderer = mujoco.Renderer(model, height=480, width=800) if args.video else None
    args.out.mkdir(parents=True, exist_ok=True)
    writer = imageio.get_writer(args.out / 'rollout.mp4', fps=25) if renderer else None
    ball_bid = model.body(ball_body.name).id
    mocap_id = int(model.body_mocapid[ball_bid])
    follower = FollowController()
    ball_geoms = set(np.flatnonzero(model.geom_bodyid == ball_bid).tolist())
    rows, stopped, fell, pushed, touched_ball = [], False, False, False, False
    try:
        for step in range(round(args.seconds * 50)):
            t = step / 50
            target_vx,target_vy=0.,0.
            if args.mode == 'follow':
                bx,by,target_vx,target_vy=target_at(t,args.ball)
                data.mocap_pos[mocap_id] = [bx,by,.035]
                mujoco.mj_forward(model,data)
            pos = data.qpos[qa:qa+3].copy()
            w,x,y,z = data.qpos[qa+3:qa+7]
            yaw = math.atan2(2*(w*z+x*y), 1-2*(y*y+z*z))
            tilt = math.acos(float(np.clip(1-2*(x*x+y*y), -1, 1)))
            fell = fell or tilt > math.radians(60) or pos[2] < 0.055
            bx, by = data.xpos[ball_bid,:2]
            distance = math.hypot(bx-pos[0], by-pos[1])
            error, vx, wz = 0.0, 0.0, 0.0
            state = 'SETTLE'
            if t >= 2.0 and args.mode in ('ball','follow') and not fell:
                if args.mode == 'follow':
                    vx,wz,stopped,distance,error=follower.command(t,*pos[:2],yaw,bx,by)
                else:
                    vx, wz, stopped, distance, error = steer(*pos[:2], yaw, bx, by, stopped)
                state = 'STOP' if stopped else ('APPROACH' if abs(error) < 0.3 else 'WALKING TURN')
            elif t >= 2.0:
                state = 'HOLD'
            if args.mode == 'push' and step == 150:
                data.qvel[va:va+2] = [args.push, 0.0]
                pushed = True
            if fell:
                state, vx, wz = 'FALL', 0.0, 0.0
            with contextlib.redirect_stdout(quiet):
                policy.set_vel_cmd(vx, 0.0, wz)
            action = policy.infer()
            if not np.isfinite(action).all():
                raise ValueError('Non-finite policy action')
            policy.apply_action(action)
            rows.append(dict(t=t, x=float(pos[0]), y=float(pos[1]), z=float(pos[2]),
                             yaw=yaw, tilt_deg=math.degrees(tilt), distance=distance,
                             speed=float(np.linalg.norm(data.qvel[va:va+2])),
                             ball_x=float(bx),ball_y=float(by),target_vx=target_vx,target_vy=target_vy,
                             heading_error=error, vx_cmd=vx, wz_cmd=wz, state=state))
            if renderer and step % 2 == 0:
                camera.lookat[:] = [(pos[0]+bx)/2, (pos[1]+by)/2, 0.09]
                renderer.update_scene(data, camera)
                frame = Image.fromarray(renderer.render())
                draw = ImageDraw.Draw(frame)
                draw.rectangle((0,0,800,64), fill=(15,22,32))
                label = f'{args.mode.upper()} | t={t:4.1f}s | {state} | XML actuators / simulation only'
                draw.text((14,10), label, fill='white')
                draw.text((14,34), f'distance {distance:.3f} m | tilt {math.degrees(tilt):.1f} deg | push applied: {pushed}', fill='white')
                if args.mode == 'follow':
                    target_state='MOVING' if math.hypot(target_vx,target_vy)>0 else 'PAUSED'
                    draw.rectangle((0,32,800,64),fill=(15,22,32))
                    draw.text((14,34),f'SCRIPTED BALL: {target_state} | distance {distance:.3f}m | resumes {sum(e["event"]=="resume" for e in follower.events)} | NO VISION',fill='white')
                writer.append_data(np.array(frame))
                if step in (0, 150, 200, round(args.seconds*50)-2) or (args.mode=='follow' and step%200==0):
                    frame.save(args.out / f'frame-{step:04d}.png')
            for _ in range(4):
                mujoco.mj_step(model, data)
                for contact in data.contact:
                    g1, g2 = int(contact.geom1), int(contact.geom2)
                    if (g1 in ball_geoms) != (g2 in ball_geoms):
                        other = g2 if g1 in ball_geoms else g1
                        if model.geom_bodyid[other] != 0:
                            touched_ball = True
    finally:
        if writer:
            writer.close()
        if renderer:
            renderer.close()
    tail = rows[-50:]
    summary = dict(mode=args.mode, actuator_model='XML position (no BAM)',
                   seconds=args.seconds, ball=args.ball, push_velocity=args.push if pushed else None,
                   fell=bool(fell), stopped=bool(stopped), final_distance=rows[-1]['distance'],
                   mean_final_speed=float(np.mean([r['speed'] for r in tail])),
                   max_tilt_deg=max(r['tilt_deg'] for r in rows),
                   final_position=[rows[-1]['x'], rows[-1]['y']],
                   touched_ball=touched_ball,
                   final_heading_error=rows[-1]['heading_error'],
                   script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                   runner_commit=subprocess.check_output(['git','-C',str(lab/'microduck_rl'),'rev-parse','HEAD'], text=True).strip(),
                   versions={'mujoco':mujoco.__version__, 'numpy':np.__version__, 'onnxruntime':module.ort.__version__},
                   policy_sha256={p.name:hashlib.sha256(p.read_bytes()).hexdigest()
                                  for p in (lab/'policies').glob('*.onnx')})
    summary['success'] = bool(not fell and not touched_ball and
        (args.mode != 'ball' or (stopped and 0.18 <= summary['final_distance'] <= 0.28
          and summary['mean_final_speed'] < 0.01 and abs(summary['final_heading_error']) < 0.35)))
    if args.mode == 'follow':
        summary['target_model']='scripted mocap; no contact dynamics or vision estimation'
        summary['keyframes']=KEYFRAMES
        summary['controller']={k:getattr(follower,k) for k in ('stop_distance','resume_distance','min_dwell')}
        summary['follow_source_sha256']=hashlib.sha256((Path(__file__).parent/'follow.py').read_bytes()).hexdigest()
        summary['follow']=analyze_follow(rows,follower)
        f=summary['follow']
        summary['success']=bool(not fell and not touched_ball and not f['tracking_lost']
            and all(f['resumed_after_each_departure']) and all(p['held_stop'] for p in f['pause_checks'])
            and f['final_held_stop'] and summary['mean_final_speed']<.01
            and .18<=summary['final_distance']<=.40)
    (args.out / 'summary.json').write_text(json.dumps(summary, indent=2)+'\n')
    (args.out / 'trajectory.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in rows))
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--lab', type=Path, default=Path('microduck-lab'))
    parser.add_argument('--mode', choices=['baseline', 'push', 'ball','follow'], default='baseline')
    parser.add_argument('--seconds', type=float, default=8)
    parser.add_argument('--ball', type=float, nargs=2, default=[0.8,0.35])
    parser.add_argument('--push', type=float, default=0.4)
    parser.add_argument('--video', action='store_true')
    parser.add_argument('--out', type=Path, required=True)
    run(parser.parse_args())
