"""Replay image observations, then evaluate physical outcomes independently."""
import argparse
import json
from pathlib import Path
from vision_follow import BallObservation, VisionFollower
from vision_search import VisualSearch


def check_run(directory):
    directory = Path(directory)
    summary = json.loads((directory/'summary.json').read_text())
    rows = [json.loads(line) for line in (directory/'trajectory.jsonl').read_text().splitlines()]
    controller = VisionFollower()
    if summary.get('vision_controller', 'rules') != 'rules':
        raise ValueError('Command replay currently supports only the deterministic rules controller')
    controller.stop_size = summary['image_thresholds']['stop_size']
    controller.resume_size = summary['image_thresholds']['resume_size']
    search = VisualSearch() if summary.get("search") else None
    mismatches = []
    for row in rows:
        if row['t'] < 2:
            continue
        observation = None if row['image_horizontal'] is None else BallObservation(
            row['image_horizontal'], row['image_diameter'], row['image_pixels'])
        # Replay intentionally selects only image-derived fields and timestamps.
        if search:
            vx,wz,state,head = search.command(row['t'],row['frame_time'],observation,row['head_encoder'],(row['x'],row['y'],row['yaw']))
        else:
            vx, wz, state = controller.command(row['t'], row['frame_time'], observation)
        if (vx,wz,state) != (row['vx_cmd'],row['wz_cmd'],row['state']):
            mismatches.append(row['t'])
    result = dict(command_replay_mismatches=mismatches,
                  lost_command_stop_pass=(summary['search']['head_search_body_commands_zero'] and summary['search']['body_search_forward_commands_zero']) if search else summary['lost_commands_zero'],
                  approach_success=summary['success'],fell=summary['fell'],
                  touched_ball=summary['touched_ball'])
    (directory/'replay-check.json').write_text(json.dumps(result,indent=2)+'\n')
    if mismatches or not result['lost_command_stop_pass']:
        raise AssertionError(result)
    return result


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory',type=Path)
    args=parser.parse_args()
    print(json.dumps(check_run(args.directory),indent=2))
