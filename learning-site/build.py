"""カリキュラムと学習記録を静的サイト用データへ変換する。"""
import json
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = Path(__file__).resolve().parent

def build():
    curriculum = (ROOT / 'CURRICULUM_DAY31_100.md').read_text()
    progress = (ROOT / 'progress.md').read_text()
    records = {}
    for line in progress.splitlines():
        cells = [c.strip() for c in line.strip('|').split('|')]
        if len(cells) == 6 and cells[0].isdigit():
            records[int(cells[0])] = dict(zip(['status','questions','accuracy','cost','review'], cells[1:]))
    days = []
    for line in curriculum.splitlines():
        cells = [c.strip() for c in line.strip('|').split('|')]
        if len(cells) not in (3,4) or not cells[0].isdigit():
            continue
        day = int(cells[0])
        note = ROOT / 'notes' / f'day-{day:03}.md'
        days.append({'day':day,'title':cells[1], 'reuse':cells[2] if len(cells)==4 else '',
                     'goal':cells[3] if len(cells)==4 else '学習記録と確認問題を使い、仕組みと用途を説明する。',
                     'note':note.read_text() if note.exists() else '', **records.get(day,{})})
    data = {'days':days,'curriculum':curriculum,'updated':'2026-09-08',
            'sources':['CURRICULUM_DAY31_100.md','progress.md','notes/day-XXX.md']}
    (SITE/'data.js').write_text('window.COURSE = '+json.dumps(data,ensure_ascii=False)+';\n')
    print(f'Generated {len(days)} days, {sum(bool(d["note"]) for d in days)} notes')

if __name__ == '__main__':
    if '--package-only' not in sys.argv:
        build()
    # 公開する静的アセットだけを配布先へコピーする。元ノートや実行環境は含めない。
    output = SITE / 'dist'
    output.mkdir(exist_ok=True)
    for name in ('index.html', 'style.css', 'readability.css', 'app.js', 'data.js', 'quizzes.js'):
        shutil.copyfile(SITE / name, output / name)
