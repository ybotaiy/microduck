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
import time
from bounded_turn import BoundedTurn
from pathlib import Path

import imageio.v2 as imageio
import mujoco
import numpy as np
from PIL import Image, ImageDraw
from follow import FollowController, target_at, analyze_follow, KEYFRAMES
import camera_view
from vision_follow import VisionFollower, detect_ball
from vision_search import VisualSearch
from safety_guard import MotionGuard
from learned_controller import LearnedVisionController


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
    run_started = time.perf_counter()
    timings = {}
    def measure(key, fn):
        started = time.perf_counter()
        result = fn()
        timings[key] = timings.get(key, 0.) + time.perf_counter()-started
        return result
    lab = args.lab.resolve()
    # Earlier runs stored the two official policies in an ignored `policies/`
    # directory.  The official runtime checkout also carries the identical
    # pinned files, which makes a fresh local checkout usable without copying
    # models into the public repository.
    policy_dir = lab / 'policies'
    if not (policy_dir / 'alpha_walking.onnx').is_file():
        policy_dir = lab / 'microduck' / 'policies'
    if not (policy_dir / 'alpha_walking.onnx').is_file():
        raise FileNotFoundError('Expected alpha_walking.onnx in the local policies or runtime checkout')
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
    if args.mode == 'follow' or args.search_scenario:
        ball_body.mocap = True
    ball_body.pos = [args.ball[0], args.ball[1], 0.035]
    if args.dual_view or args.vision:
        camera_view.add_camera(scene_spec)
    if args.search_scenario == 'occluder':
        wall = scene_spec.worldbody.add_body(name='visual_occluder',mocap=True,pos=[.5,2.,.25])
        wall.add_geom(name='occluder_geom',type=mujoco.mjtGeom.mjGEOM_BOX,size=[.02,.25,.25],rgba=[.3,.35,.4,1])
    model = scene_spec.compile()
    model.vis.global_.offwidth = 800
    model.vis.global_.offheight = 480
    model.opt.timestep = 0.005
    data = mujoco.MjData(model)
    quiet = io.StringIO()
    with contextlib.redirect_stdout(quiet):
        policy = module.PolicyInference(
            model, data, walking_onnx_path=str(policy_dir / 'alpha_walking.onnx'),
            standing_onnx_path=str(policy_dir / 'alpha_stand.onnx'),
            new_cmd_obs=True, use_projected_gravity=True)
        policy.set_vel_cmd(0, 0, 0)
    jid = model.joint('trunk_base_freejoint').id
    qa, va = int(model.jnt_qposadr[jid]), int(model.jnt_dofadr[jid])
    data.qpos[qa:qa+7] = [0, 0, 0.125, 1, 0, 0, 0]
    data.qpos[policy.joint_qpos_indices] = policy.default_pose
    policy.set_position_targets(policy.default_pose)
    mujoco.mj_forward(model, data)
    assert policy.get_observations().shape == (61,)
    if args.dual_view or args.vision:
        camera_view.configure(model, data)
        if args.camera_check:
            if args.mode == 'follow':
                raise ValueError('Run camera snapshots with a static ball mode')
            camera_view.validate(model, data, qa, args.out / 'checks')
    camera = mujoco.MjvCamera()
    camera.azimuth, camera.elevation, camera.distance = 125, -25, 1.65
    camera.lookat[:] = [0.25, 0, 0.10]
    renderer = mujoco.Renderer(model, height=480, width=800) if args.video else None
    args.out.mkdir(parents=True, exist_ok=True)
    writer = imageio.get_writer(args.out / 'rollout.mp4', fps=25) if renderer else None
    dual = camera_view.DualView(model, args.out) if args.dual_view or args.vision else None
    ball_bid = model.body(ball_body.name).id
    mocap_id = int(model.body_mocapid[ball_bid])
    follower = FollowController()
    vision = (LearnedVisionController(args.controller_model)
              if args.vision_controller == 'learned' else VisionFollower())
    search = VisualSearch()
    if args.vision_controller == 'learned':
        search.follower = vision
    guard = MotionGuard()
    turn = BoundedTurn(target=args.turn_angle, speed=args.turn_speed)
    head_qa = int(model.jnt_qposadr[model.joint('head_yaw').id])
    observation, frame_time, robot_frame = None, -math.inf, None
    perception_checks = []
    ball_geoms = set(np.flatnonzero(model.geom_bodyid == ball_bid).tolist())
    rows, stopped, fell, pushed, touched_ball = [], False, False, False, False
    touched_occluder = False
    repeat_segment = None
    repeat_geometry = None
    try:
        for step in range(round(args.seconds * 50)):
            t = step / 50
            target_vx,target_vy=0.,0.
            if args.mode == 'follow':
                bx,by,target_vx,target_vy=target_at(t,args.ball)
                data.mocap_pos[mocap_id] = [bx,by,.035]
                mujoco.mj_forward(model,data)
            if args.search_scenario:
                # Scenario generation belongs to the environment, not the visual controller.
                if args.search_scenario in ('left','right','behind'):
                    final_angle = {'left':math.pi/2,'right':-math.pi/2,'behind':math.pi}[args.search_scenario]
                    angle = final_angle*float(np.clip((t-4)/args.search_move_seconds,0,1))
                    data.mocap_pos[mocap_id] = [.8*math.cos(angle),.8*math.sin(angle),.035]
                elif args.search_scenario == 'repeat':
                    schedule = [(4.,1),(24.,-1),(44.,1),(64.,-1)]
                    active = next(((start,side) for start,side in reversed(schedule) if t>=start),None)
                    if active is not None:
                        start,side=active
                        if repeat_segment != start:
                            center=data.qpos[qa:qa+2].copy()
                            qw,qx,qy,qz=data.qpos[qa+3:qa+7]
                            body_heading=math.atan2(2*(qw*qz+qx*qy),1-2*(qy*qy+qz*qz))
                            delta=data.mocap_pos[mocap_id,:2]-center
                            initial_angle=math.atan2(delta[1],delta[0]);goal_angle=body_heading+side*math.pi/2
                            sweep=math.atan2(math.sin(goal_angle-initial_angle),math.cos(goal_angle-initial_angle))
                            repeat_geometry=(center,initial_angle,sweep,float(np.linalg.norm(delta)))
                            repeat_segment=start
                        center,initial_angle,sweep,initial_radius=repeat_geometry
                        u=float(np.clip((t-start)/.4,0,1));angle=initial_angle+u*sweep;radius=initial_radius+u*(.8-initial_radius)
                        data.mocap_pos[mocap_id]=[center[0]+radius*math.cos(angle),center[1]+radius*math.sin(angle),.035]
                elif args.search_scenario == 'occluder':
                    data.mocap_pos[mocap_id] = [.8,0,.035]
                    wall_mid = int(model.body_mocapid[model.body('visual_occluder').id])
                    data.mocap_pos[wall_mid] = [.5,0 if 4<=t<10 else 2.,.25]
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
            if args.mode == 'turn' and t >= 2:
                vx,wz,state = turn.command(t,*pos[:2],yaw)
            if args.vision:
                if step % 2 == 0:
                    dual.renderer.update_scene(data, 'robot_view')
                    robot_frame = measure('robot_rgb_render',lambda:dual.renderer.render().copy())
                    if args.vision_blackout and args.vision_blackout[0] <= t < args.vision_blackout[1]:
                        robot_frame[:] = 0
                    observation = measure('detection',lambda:detect_ball(robot_frame))
                    if any(abs(t-st)<.01 for st in args.snapshot_times):
                        args.out.mkdir(parents=True,exist_ok=True)
                        Image.fromarray(robot_frame).save(args.out/f'robot-{t:.2f}.png')
                    frame_time = t
                    if step % 10 == 0:
                        # Evaluator only: this result is logged, never passed to vision.command.
                        dual.renderer.enable_segmentation_rendering()
                        dual.renderer.update_scene(data, 'robot_view')
                        seg = measure('segmentation_render',lambda:dual.renderer.render().copy())
                        dual.renderer.disable_segmentation_rendering()
                        yy, xx = np.where((seg[:,:,0] == model.geom('ball_geom').id) &
                                          (seg[:,:,1] == int(mujoco.mjtObj.mjOBJ_GEOM)))
                        expected_visible = len(xx) >= 12
                        injected = bool(args.vision_blackout and args.vision_blackout[0] <= t < args.vision_blackout[1])
                        error_px = abs((observation.horizontal+1)*(camera_view.WIDTH-1)/2 - xx.mean()) if observation and len(xx) else None
                        perception_checks.append(dict(t=t, ground_truth_visible_pixels=len(xx),
                            detected=observation is not None, injected_blackout=injected,
                            missed_visible_ball=bool(expected_visible and observation is None and not injected),
                            detection_without_visible_ball=bool(not expected_visible and observation is not None),
                            horizontal_error_px=float(error_px) if error_px is not None else None))
                if t >= 2.0:
                    if args.search:
                        vx, wz, state, head_target = search.command(t,frame_time,observation,float(data.qpos[head_qa]),(*pos[:2],yaw))
                        policy.head_offset[2] = head_target
                    else:
                        vx, wz, state = vision.command(t, frame_time, observation)
                    stopped = state == 'STOP'
                error = math.atan2(math.sin(math.atan2(by-pos[1],bx-pos[0])-yaw),
                                   math.cos(math.atan2(by-pos[1],bx-pos[0])-yaw))
            elif t >= 2.0 and args.mode in ('ball','follow') and not fell:
                if args.mode == 'follow':
                    vx,wz,stopped,distance,error=follower.command(t,*pos[:2],yaw,bx,by)
                else:
                    vx, wz, stopped, distance, error = steer(*pos[:2], yaw, bx, by, stopped)
                state = 'STOP' if stopped else ('APPROACH' if abs(error) < 0.3 else 'WALKING TURN')
            elif t >= 2.0 and args.mode != 'turn':
                state = 'HOLD'
            if args.mode == 'push' and step == 150:
                data.qvel[va:va+2] = [args.push, 0.0]
                pushed = True
            # This guard applies to coordinate and RGB control alike.  A
            # camera-control rollout must never keep walking after the same
            # simulated fall condition that stops the coordinate controller.
            stale_stream = bool(args.vision and t >= 2.0 and t-frame_time > .12)
            vx, wz, guard_reason = guard.command(vx, wz, fell=fell,
                                                  stale_camera=stale_stream)
            if guard_reason:
                state = 'FALL' if guard_reason == 'FALL' else guard_reason
            with contextlib.redirect_stdout(quiet):
                policy.set_vel_cmd(vx, 0.0, wz)
            action = measure('onnx_inference',policy.infer)
            if not np.isfinite(action).all():
                raise ValueError('Non-finite policy action')
            policy.apply_action(action)
            rows.append(dict(t=t, x=float(pos[0]), y=float(pos[1]), z=float(pos[2]),
                             yaw=yaw, tilt_deg=math.degrees(tilt), distance=distance,
                             speed=float(np.linalg.norm(data.qvel[va:va+2])),
                             ball_x=float(bx),ball_y=float(by),target_vx=target_vx,target_vy=target_vy,
                             heading_error=error, vx_cmd=vx, wz_cmd=wz, state=state))
            if args.vision:
                rows[-1].update(image_horizontal=observation.horizontal if observation else None,
                                image_diameter=observation.diameter if observation else None,
                                image_pixels=observation.pixels if observation else 0,
                                frame_time=frame_time, head_encoder=float(data.qpos[head_qa]),
                                head_command=float(policy.head_offset[2]))
            if renderer and step % 2 == 0:
                camera.lookat[:] = [(pos[0]+bx)/2, (pos[1]+by)/2, 0.09]
                if not dual:
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
                if dual:
                    frame = measure('presentation_render',lambda:dual.render(
                        data, camera, t, state, robot_frame if args.vision else None,
                        args.vision, args.search, args.vision_controller))
                measure('video_encode_write',lambda:writer.append_data(np.array(frame)))
                if step in (0, 150, 200, round(args.seconds*50)-2) or (args.mode=='follow' and step%200==0):
                    frame.save(args.out / f'frame-{step:04d}.png')
            for _ in range(4):
                measure('physics',lambda:mujoco.mj_step(model,data))
                for contact in data.contact:
                    g1, g2 = int(contact.geom1), int(contact.geom2)
                    if args.search_scenario == 'occluder':
                        wall_gid = model.geom('occluder_geom').id
                        if g1 == wall_gid or g2 == wall_gid:
                            other = g2 if g1 == wall_gid else g1
                            if model.geom_bodyid[other] not in (0, ball_bid):
                                touched_occluder = True
                    if (g1 in ball_geoms) != (g2 in ball_geoms):
                        other = g2 if g1 in ball_geoms else g1
                        if model.geom_bodyid[other] != 0:
                            touched_ball = True
    finally:
        if dual:
            dual.close()
        if writer:
            measure('video_flush',writer.close)
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
                   guard_reason=guard.reason,
                   final_heading_error=rows[-1]['heading_error'],
                   script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                   runner_commit=subprocess.check_output(['git','-C',str(lab/'microduck_rl'),'rev-parse','HEAD'], text=True).strip(),
                   versions={'mujoco':mujoco.__version__, 'numpy':np.__version__, 'onnxruntime':module.ort.__version__},
                   policy_sha256={p.name:hashlib.sha256(p.read_bytes()).hexdigest()
                                  for p in policy_dir.glob('*.onnx')})
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
    if args.vision:
        controlled = [r for r in rows if r['t'] >= 2]
        summary['control'] = 'RGB magenta component horizontal offset and apparent diameter only'
        summary['vision_source_sha256'] = hashlib.sha256((Path(__file__).parent/'vision_follow.py').read_bytes()).hexdigest()
        evaluated_follower = search.follower if args.search else vision
        summary['vision_events'] = evaluated_follower.events
        summary['image_thresholds'] = ({'stop_size':vision.stop_size,'resume_size':vision.resume_size,'dwell':vision.resume_dwell}
                                       if args.vision_controller == 'rules' else None)
        summary['vision_controller'] = args.vision_controller
        if args.vision_controller == 'learned':
            summary['controller_model_sha256'] = hashlib.sha256(Path(args.controller_model).read_bytes()).hexdigest()
        summary['lost_samples'] = sum(r['state']=='LOST' for r in controlled)
        summary['lost_commands_zero'] = all(r['vx_cmd']==0 and r['wz_cmd']==0 for r in controlled if r['state']=='LOST')
        summary['blackout'] = args.vision_blackout
        summary['perception_evaluation'] = dict(samples=len(perception_checks),
            missed_visible_ball=sum(c['missed_visible_ball'] for c in perception_checks),
            detection_without_visible_ball=sum(c['detection_without_visible_ball'] for c in perception_checks),
            max_horizontal_error_px=max((c['horizontal_error_px'] for c in perception_checks if c['horizontal_error_px'] is not None),default=None))
        (args.out / 'perception-checks.json').write_text(json.dumps(perception_checks,indent=2)+'\n')
        summary['success'] = bool(not fell and not touched_ball and stopped and
                                  .18 <= summary['final_distance'] <= .40 and summary['mean_final_speed'] < .01)
        if args.mode == 'follow':
            # Reuse only the evaluator's event format, never its coordinate controller.
            follower.events = [dict(t=e['t'],event='stop' if e['state']=='STOP' else 'resume')
                               for e in evaluated_follower.events if e['state']=='STOP' or (e['previous']=='STOP' and e['state']=='APPROACH')]
            summary['follow'] = analyze_follow(rows, follower)
            f = summary['follow']
            summary['success'] = summary['success'] and all(f['resumed_after_each_departure']) and all(p['held_stop'] for p in f['pause_checks']) and not f['tracking_lost']
            summary.pop('controller',None)
            summary['target_model'] = 'scripted mocap; camera RGB control; coordinates used only by evaluator'
    if args.search:
        summary['search'] = dict(scenario=args.search_scenario,touched_occluder=touched_occluder,move_seconds=args.search_move_seconds,events=search.events,
            reacquisitions=search.reacquisitions,final_internal_state=search.state,
            head_command_limit=search.head_limit,body_scan_time_limit=search.body_scan_time,
            max_abs_head_encoder=max(abs(r['head_encoder']) for r in rows),
            max_abs_head_command=max(abs(r['head_command']) for r in rows),
            head_search_body_commands_zero=all(r['vx_cmd']==0 and r['wz_cmd']==0 for r in rows if r['state'] in ('SETTLE_LOST','HEAD_SEARCH','GAVE_UP')),
            body_turn_metrics=search.body_turn.metrics() if search.body_turn else None,
            search_time_limit=search.search_limit,search_displacement_limit=search.search_displacement_limit,
            body_search_forward_commands_zero=all(r['vx_cmd']==0 for r in rows if r['state']=='BODY_SEARCH'))
        summary['search_source_sha256'] = hashlib.sha256((Path(__file__).parent/'vision_search.py').read_bytes()).hexdigest()
        summary['success'] = bool(not fell and not touched_ball and not touched_occluder and stopped and .18 <= summary['final_distance'] <= .4 and summary['mean_final_speed'] < .01)
        if args.mode == 'follow':
            f = summary['follow']
            summary['success'] = summary['success'] and all(f['resumed_after_each_departure']) and all(p['held_stop'] for p in f['pause_checks']) and not f['tracking_lost']
    summary['timing'] = dict(wall_seconds=time.perf_counter()-run_started,seconds_by_stage=timings,
        note='Stage timers exclude uninstrumented setup, observation construction, policy command updates, contacts and Python overhead.')
    if args.mode == 'turn':
        summary['turn'] = turn.metrics()
        summary['success'] = bool(not fell and turn.reason == 'ANGLE_REACHED' and summary['mean_final_speed']<.01)
    (args.out / 'summary.json').write_text(json.dumps(summary, indent=2)+'\n')
    (args.out / 'trajectory.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in rows))
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--lab', type=Path, default=Path('microduck-lab'))
    parser.add_argument('--mode', choices=['baseline','push','ball','follow','turn'], default='baseline')
    parser.add_argument('--seconds', type=float, default=8)
    parser.add_argument('--ball', type=float, nargs=2, default=[0.8,0.35])
    parser.add_argument('--push', type=float, default=0.4)
    parser.add_argument('--video', action='store_true')
    parser.add_argument('--turn-speed',type=float,default=.3)
    parser.add_argument('--turn-angle',type=float,default=1.5707963267948966)
    parser.add_argument('--snapshot-times',type=float,nargs='*',default=[])
    parser.add_argument('--search', action='store_true', help='Enable bounded active head/body search after lost sight')
    parser.add_argument('--search-move-seconds', type=float, default=2., help='Scripted target transition duration')
    parser.add_argument('--search-scenario', choices=['left','right','behind','occluder','repeat'])
    parser.add_argument('--vision', action='store_true', help='Control using only robot-view RGB observations')
    parser.add_argument('--vision-controller', choices=['rules', 'learned'], default='rules')
    parser.add_argument('--controller-model', type=Path, help='ONNX learned visual controller; required for --vision-controller learned')
    parser.add_argument('--vision-blackout', type=float, nargs=2, help='Inject black sensor frames during this time interval')
    parser.add_argument('--dual-view', action='store_true', help='Record head-mounted and third-person views together')
    parser.add_argument('--camera-check', action='store_true', help='Evaluate camera poses before rollout; requires --dual-view')
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    if args.search_move_seconds <= 0:
        parser.error('--search-move-seconds must be positive')
    if args.search and not args.vision:
        parser.error('--search requires --vision')
    if args.search_scenario and not args.search:
        parser.error('--search-scenario requires --search')
    if args.vision and args.mode not in ('ball','follow'):
        parser.error('--vision requires ball/follow mode')
    if args.vision_controller == 'learned' and not args.vision:
        parser.error('--vision-controller learned requires --vision')
    if args.vision_controller == 'learned' and not args.controller_model:
        parser.error('--controller-model is required for --vision-controller learned')
    if args.vision_blackout and not args.vision:
        parser.error('--vision-blackout requires --vision')
    if args.camera_check and not args.dual_view:
        parser.error('--camera-check requires --dual-view')
    if args.dual_view and not args.video:
        parser.error('--dual-view requires --video')
    run(args)
