#!/usr/bin/env python3
"""Sample local video by presentation time and build evidence contact sheets."""
import argparse
import json
import math
from pathlib import Path

import av
from PIL import Image, ImageDraw, ImageFont


def label(seconds):
    ms = round(seconds * 1000)
    hours, ms = divmod(ms, 3600000)
    minutes, ms = divmod(ms, 60000)
    seconds, ms = divmod(ms, 1000)
    return f'{hours:02d}:{minutes:02d}:{seconds:02d}.{ms:03d}'


def get_font():
    for candidate in ['/System/Library/Fonts/Supplemental/Arial.ttf',
                      '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf']:
        if Path(candidate).is_file():
            return ImageFont.truetype(candidate, 18)
    return ImageFont.load_default(size=18)


def sample(args):
    if not args.input.is_file():
        raise ValueError('Input must be an existing local video')
    if args.output_dir.exists() and (not args.output_dir.is_dir() or any(args.output_dir.iterdir())):
        raise ValueError('Use a new or empty output directory; existing evidence is not overwritten')
    if not math.isfinite(args.start) or args.start < 0 or not 3 <= args.max_frames <= 500:
        raise ValueError('start must be nonnegative; max-frames must be between 3 and 500')
    with av.open(str(args.input)) as container:
        if not container.streams.video:
            raise ValueError('Input contains no video stream')
        stream = container.streams.video[0]
        origin = float((stream.start_time or 0) * stream.time_base)
        duration = float(stream.duration * stream.time_base) if stream.duration else None
        if duration is None and container.duration:
            duration = float(container.duration / av.time_base)
        if args.end is not None and (not math.isfinite(args.end) or args.end <= args.start):
            raise ValueError('end must be finite and later than start')
        end = args.end if args.end is not None else duration
        if end is None or end <= args.start:
            raise ValueError('A finite, nonempty sampling interval is required; supply --end if duration is unknown')
        span = end - args.start
        interval = args.interval if args.interval is not None else max(.5, span / max(1, args.max_frames - 2))
        if not math.isfinite(interval) or interval <= 0:
            raise ValueError('interval must be a positive finite number')
        if math.floor(span / interval) + 2 > args.max_frames:
            raise ValueError('Sampling would exceed max-frames; increase interval or max-frames')
        frames_dir = args.output_dir / 'frames'
        frames_dir.mkdir(parents=True, exist_ok=True)
        records = []

        def save(frame, seconds):
            if len(records) >= args.max_frames:
                raise ValueError('Decoded video exceeds the estimated frame budget; use a larger interval in a new output directory')
            path = frames_dir / f'frame-{len(records)+1:04d}.jpg'
            frame.to_image().save(path, quality=94)
            records.append({'index':len(records)+1, 'seconds':round(seconds,6),
                            'timestamp':label(seconds), 'path':str(path.resolve())})

        if args.start > 0:
            container.seek(int((args.start + origin) / stream.time_base), stream=stream, backward=True)
        next_time = args.start
        last_frame, last_time = None, None
        for frame in container.decode(stream):
            if frame.time is None:
                continue
            seconds = float(frame.time) - origin
            if seconds < args.start - 1e-6:
                continue
            if args.end is not None and seconds > end + 1e-6:
                break
            last_frame, last_time = frame, seconds
            if seconds + 1e-6 >= next_time:
                save(frame, seconds)
                next_time = args.start + (math.floor((seconds-args.start+1e-6)/interval)+1)*interval
        if last_frame is not None and records and last_time > records[-1]['seconds'] + 1e-5:
            save(last_frame, last_time)
        if not records:
            raise ValueError('No frames decoded in requested interval')
        width, height = stream.width, stream.height
        boards = []
        tile_w, tile_h = (240,426) if height > width else (384,216)
        font = get_font()
        for page, offset in enumerate(range(0, len(records), 12), 1):
            group = records[offset:offset+12]
            rows = math.ceil(len(group)/3)
            board = Image.new('RGB', (tile_w*3, (tile_h+28)*rows), (18,20,24))
            draw = ImageDraw.Draw(board)
            for index, record in enumerate(group):
                x, y = index%3*tile_w, index//3*(tile_h+28)
                with Image.open(record['path']) as im:
                    im.thumbnail((tile_w,tile_h), Image.Resampling.LANCZOS)
                    board.paste(im, (x+(tile_w-im.width)//2, y+28+(tile_h-im.height)//2))
                draw.text((x+8,y+4),record['timestamp'],font=font,fill='white')
            target = args.output_dir/f'contact-{page:02d}.jpg'
            board.save(target, quality=92)
            boards.append(str(target.resolve()))
        manifest = {'source':str(args.input.resolve()), 'width':width, 'height':height,
                    'duration_seconds':duration, 'requested_start':args.start, 'requested_end':args.end,
                    'last_decoded_frame_seconds':last_time,
                    'sampling_interval_seconds':interval,
                    'timestamp_basis':'decoded frame PTS relative to video stream start',
                    'frames':records, 'contact_sheets':boards,
                    'limitations':'Sampling does not prove cuts, continuity, camera hardware or author intent.'}
        path = args.output_dir/'manifest.json'
        path.write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
        return {'frames':len(records),'manifest':str(path.resolve()),'contact_sheets':boards}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('input',type=Path)
    p.add_argument('--output-dir',type=Path,required=True)
    p.add_argument('--start',type=float,default=0)
    p.add_argument('--end',type=float)
    p.add_argument('--interval',type=float)
    p.add_argument('--max-frames',type=int,default=72)
    args = p.parse_args()
    try:
        result = sample(args)
    except ValueError as error:
        p.error(str(error))
    print(json.dumps(result,ensure_ascii=False))


if __name__ == '__main__':
    main()
