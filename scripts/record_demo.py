#!/usr/bin/env python3
"""Record a real CLI run into an asciicast, then render the same frames to GIF/MP4."""
import argparse
import codecs
import fcntl
import json
import os
import pty
import select
import shlex
import struct
import subprocess
import sys
import termios
import time
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
import pyte

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / 'docs/assets'


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--render-only', action='store_true')
    p.add_argument('--output', type=Path, default=Path('experiments/runs/demo'), help='Use a fresh run directory for a new recording')
    args = p.parse_args()
    ASSETS.mkdir(parents=True, exist_ok=True)
    cast = ASSETS / 'demo.cast'
    if not args.render_only:
        command = [sys.executable, '-m', 'simple_evals', '--eval', 'mmlu', '--examples', '2',
                   '--offline', '--max-tokens', '512', '--output', str(args.output)]
        master, slave = pty.openpty()
        fcntl.ioctl(slave, termios.TIOCSWINSZ, struct.pack('HHHH', 29, 112, 0, 0))
        env = dict(os.environ, TERM='xterm-256color', PYTHONUNBUFFERED='1', TOKENIZERS_PARALLELISM='false')
        child = subprocess.Popen(command, stdout=slave, stderr=slave, stdin=subprocess.DEVNULL, cwd=ROOT, env=env)
        os.close(slave)
        start = time.monotonic()
        events = [[0, 'o', '$ python -m simple_evals --eval mmlu --examples 2 --offline\r\n']]
        decoder = codecs.getincrementaldecoder('utf-8')('replace')
        while True:
            if select.select([master], [], [], 0.1)[0]:
                try: chunk = os.read(master, 65536)
                except OSError: break
                if not chunk: break
                events.append([round(time.monotonic() - start, 4), 'o', decoder.decode(chunk)])
            elif child.poll() is not None:
                break
        os.close(master)
        status = child.wait()
        if status: raise SystemExit(status)
        events.append([round(time.monotonic() - start + 0.5, 4), 'o', f'\r\n$ cat {args.output}/summary.csv\r\n' + (ROOT / args.output / 'summary.csv').read_text().replace('\n', '\r\n')])
        with cast.open('w') as f:
            f.write(json.dumps({'version': 2, 'width': 112, 'height': 29, 'timestamp': int(time.time()), 'title': 'Real MLX evaluation on Apple M1 Pro', 'env': {'TERM': 'xterm-256color'}}) + '\n')
            for event in events: f.write(json.dumps(event) + '\n')
    rows = [json.loads(line) for line in cast.read_text().splitlines()]
    events = rows[1:]
    screen = pyte.Screen(112, 29)
    stream = pyte.Stream(screen)
    font_path = '/System/Library/Fonts/Menlo.ttc'
    font = ImageFont.truetype(font_path, 16)
    heading = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf', 27)
    subheading = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf', 15)
    duration = events[-1][0] + 5
    fps = 8
    frames = []
    idx = 0
    ffmpeg = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24',
                               '-s', '1280x800', '-r', str(fps), '-i', '-', '-an', '-c:v', 'libx264',
                               '-pix_fmt', 'yuv420p', '-movflags', '+faststart', str(ASSETS / 'demo.mp4')], stdin=subprocess.PIPE)
    for step in range(int(duration * fps)):
        now = step / fps
        while idx < len(events) and events[idx][0] <= now:
            stream.feed(events[idx][2]); idx += 1
        frame = Image.new('RGB', (1280, 800), '#0b1120')
        draw = ImageDraw.Draw(frame)
        draw.text((48, 27), 'SIMPLE EVALS / LOCAL RUN', font=heading, fill='#f1f5f9')
        draw.text((48, 66), 'Apple M1 Pro  ·  MLX / Metal  ·  Open weights  ·  No API key', font=subheading, fill='#94a3b8')
        draw.rounded_rectangle((35, 105, 1245, 735), radius=14, fill='#111d30', outline='#2c3a50')
        for x, color in [(60,'#fb7185'),(84,'#fbbf24'),(108,'#34d399')]:
            draw.ellipse((x, 120, x+11, 131), fill=color)
        draw.text((150, 117), 'Actual terminal capture · deterministic 2-example MMLU subset', font=subheading, fill='#94a3b8')
        for line_no, text in enumerate(screen.display):
            draw.text((56, 154 + line_no*19), text, font=font, fill='#dbeafe')
        draw.text((48, 759), f'{now:04.1f}s / {duration:04.1f}s  ·  Real model output; this demo is not a full benchmark result.', font=subheading, fill='#7dd3fc')
        ffmpeg.stdin.write(frame.tobytes())
        frames.append(frame.resize((960, 600)).convert('P', palette=Image.Palette.ADAPTIVE, colors=96))
    ffmpeg.stdin.close()
    if ffmpeg.wait(): raise RuntimeError('ffmpeg encoding failed')
    frames[-1].save(ASSETS / 'demo-poster.png')
    frames[0].save(ASSETS / 'demo.gif', save_all=True, append_images=frames[1:], duration=1000//fps, loop=0, optimize=True)
    (ASSETS / 'demo.json').write_text(json.dumps({'source': 'demo.cast', 'duration_seconds': duration,
      'fps': fps, 'dimensions': [1280,800], 'recorded_command': ' '.join(shlex.quote(x) for x in command) if not args.render_only else 'see demo.cast',
      'note': 'Video/GIF are rendered from actual timestamped PTY output, without fabricated results.'}, indent=2)+'\n')
    print('Created demo.cast, demo.gif, demo.mp4 and demo-poster.png')


if __name__ == '__main__': main()
