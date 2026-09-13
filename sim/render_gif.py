"""Create a small, normal-speed GIF excerpt from a reviewed simulation MP4."""
import argparse
from pathlib import Path

import imageio.v2 as imageio
from PIL import Image


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--start', type=float, default=0.)
    parser.add_argument('--duration', type=float, default=12.)
    parser.add_argument('--fps', type=float, default=10.)
    parser.add_argument('--width', type=int, default=720)
    args = parser.parse_args()
    reader = imageio.get_reader(args.input)
    source_fps = float(reader.get_meta_data()['fps'])
    start = round(args.start * source_fps)
    stop = round((args.start + args.duration) * source_fps)
    stride = max(1, round(source_fps / args.fps))
    frames = []
    for index, frame in enumerate(reader):
        if index < start:
            continue
        if index >= stop:
            break
        if (index - start) % stride == 0:
            image = Image.fromarray(frame)
            height = round(image.height * args.width / image.width)
            frames.append(image.resize((args.width, height), Image.Resampling.LANCZOS))
    reader.close()
    if not frames:
        raise ValueError('The requested excerpt contains no frames')
    args.output.parent.mkdir(parents=True, exist_ok=True)
    output_fps = source_fps / stride
    frames[0].save(args.output, save_all=True, append_images=frames[1:], duration=round(1000 / output_fps), loop=0,
                   optimize=False, disposal=2)
    print(f'{args.output}: {len(frames)} frames, {len(frames) / output_fps:.1f}s')


if __name__ == '__main__':
    main()
