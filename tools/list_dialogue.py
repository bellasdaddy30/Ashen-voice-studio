import json, os, sys
sys.argv += []
from perform_elevenlabs import BOOK, tags_for
m = json.load(open(os.path.join(BOOK, 'manifest.json')))
AB = {'Zik':'Z','Balag':'B','Enhedu':'E','Ninsun':'N','Kurash':'K','The Collector':'C','Mardu':'M','Bel-iddin':'F','Dead King':'DK'}
for key, cfg in m['chapters'].items():
    ch = int(key[:2])
    if str(ch) not in sys.argv[1:]: continue
    pp = os.path.join(BOOK, cfg['production']); d = os.path.dirname(pp)
    segs = [x for f in json.load(open(pp))['chapters'][0]['lineFiles'] for x in json.load(open(os.path.join(d, f)))]
    print(f'## CH{ch}'); k = 0
    for i, s in enumerate(segs):
        if s['speaker'] == 'Narrator': continue
        t = tags_for(segs, i, ch)
        prev = segs[i-1]['text'] if segs[i-1]['speaker'] == 'Narrator' else ''
        print(f"{k}|{AB.get(s['speaker'], s['speaker'][:6])}|{','.join(t)}|{s['text'][:80]}" + (f"  <{prev[-55:]}" if prev else ''))
        k += 1
