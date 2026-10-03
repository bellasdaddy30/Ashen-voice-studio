"""Performance pass: add eleven_v3 audio tags and pause marks to every chapter.

    python3 tools/perform_elevenlabs.py

Tags come from the prose itself: a line only gets [whispers], [screams], [laughs]...
when the narration right next to it says so about THAT speaker (by name, by the
right pronoun, or in the line's own attribution, e.g. "she whispered.").
Character-level direction from the parse notes (City, Remainder, post-vision
Enhedu, failing Zik) is added too. Pauses go where the story goes silent.

Writes:
  book-data/elevenlabs/scripts/<chapter>.txt   readable performance script
  book-data/elevenlabs/scripts/THE_FIRST_CITY_FULL_SCRIPT.txt
  book-data/elevenlabs/<chapter>.json          (adds tags + pauseBefore per line)
"""
import json, os, re
from export_elevenlabs import BOOK, OUT, pronunciations, respell

FEMALE = {'Enhedu', 'Ninsun', "Zik's Mother"}
# (regex on the cue sentence, tag) — first match wins, most specific first.
CUES = [
    (r'\bscream', 'screams'), (r'\bcried out\b', 'screams'),
    (r'\bshout|\byell|\bbellow|\bcalled out\b|\broared\b', 'shouts'),
    (r'\bwhisper|under (?:his|her) breath|barely above a whisper|voice (?:was )?(?:very )?low|lowered (?:his|her) voice|kept (?:his|her) voice low|voice dropped', 'whispers'),
    (r'\bhissed\b', 'hissing'),
    (r'\bgasp', 'gasps'),
    (r'almost laugh|almost smil|despite himself|despite herself', 'amused'),
    (r'\blaugh(?!ter)|\bbarked a laugh|\bchuckl', 'laughs'),
    (r'\bsigh(?:s|ed|ing)?\b', 'sighs'),
    (r'\bsnort', 'snorts'),
    (r'\bmutter|\bgrumbl', 'mutters'),
    (r'\bgrowl', 'growls'),
    (r'\bsnapped\b', 'sharply'),
    (r'voice (?:had )?(?:gone )?flat|without (?:anger|humor)', 'flatly'),
    (r'voice (?:had )?(?:sharpened|hardened)|voice harden', 'sharply'),
    (r'voice (?:shook|trembled|broke|hitched|cracked)|trembl', 'trembling'),
    (r'\bquietly\b|\bsoftly\b|\bsoftened (?:his|her) voice\b|spoke softly', 'softly'),
    (r'\bswore\b|\bcursed\b', 'angrily'),
]
SILENCE = re.compile(r'^(No one (spoke|answered|moved|argued)|Nobody (spoke|moved|answered)|Silence|The silence|For a long moment|For several (breaths|seconds|moments)|Nothing (moved|happened)\.|The chamber went|The room went (quiet|still)|The words sat|The question hung)')
NOTE_TAG = [('The City', 'whispers'), ('The Statue', 'flatly'), ('The Remainder', 'exhausted'),
            ('Dead King', 'whispers')]

def sentences(t):
    return [s for s in re.split(r'(?<=[.!?…])\s+', t) if s]

def about(sentence, speaker):
    s = sentence.strip()
    if speaker.split()[-1] in s or speaker in s:
        return True
    first = s.split(' ', 1)[0].lower().strip(',')
    return (first == 'she' and speaker in FEMALE) or (first == 'he' and speaker not in FEMALE)

def cue_tag(text):
    if re.search(r'\b(?:was|were) (?:shouted|called|whispered)\b', text): return None
    for rx, tag in CUES:
        if re.search(rx, text, re.I):
            return tag
    return None

def tags_for(segs, i):
    s = segs[i]
    out = []
    note = s.get('note', '')
    for name, tag in NOTE_TAG:
        if s['speaker'] == name: out.append(tag)
    if 'Post-vision' in note: out.append('flatly')
    if 'physically failing' in note: out.append('weakly')
    if 'CITY MIMIC' in note: out.append('eerie')
    if 'Whispered' in note: out.append('whispers')
    if 'urgent and strained' in note: out.append('urgently')
    if 'sorrow' in note.lower(): out.append('sorrowful')
    # Attribution right after the line ("she whispered.") belongs to it.
    nxt = segs[i + 1] if i + 1 < len(segs) else None
    if nxt and nxt['speaker'] == 'Narrator' and nxt['pause'] <= 0.16 and about(sentences(nxt['text'])[0], s['speaker']):
        t = cue_tag(sentences(nxt['text'])[0])
        if t: out.append(t)
    # Action beat right before the line, only if it is about this speaker.
    prv = segs[i - 1] if i > 0 else None
    if prv and prv['speaker'] == 'Narrator' and not out:
        last = sentences(prv['text'])[-1:] or ['']
        if about(last[0], s['speaker']) and len(last[0].split()) <= 14:
            t = cue_tag(last[0])
            if t: out.append(t)
    if s['text'].rstrip().endswith('!') and not any(t in out for t in ('shouts', 'screams', 'whispers')):
        out.append('shouts' if len(s['text']) < 40 else 'urgently')
    seen = []
    for t in out:
        if t not in seen: seen.append(t)
    return seen[:2]

def pause_before(segs, i):
    s = segs[i]
    if i == 0: return 0
    if segs[i - 1]['text'].startswith('CHAPTER') and i == 1: return 1.0
    if i == 2: return 2.0                       # after the chapter title
    prev = segs[i - 1]
    if 'long beat' in prev.get('note', '').lower() or 'Leave a long beat' in prev.get('note', ''): return 2.0
    if prev.get('pause', 0) >= 0.6: return 1.5
    if s['speaker'] == 'Narrator' and SILENCE.match(s['text']): return 1.5
    return 0

def main():
    rules = pronunciations()
    manifest = json.load(open(os.path.join(BOOK, 'manifest.json'), encoding='utf-8'))
    sdir = os.path.join(OUT, 'scripts'); os.makedirs(sdir, exist_ok=True)
    full = ['THE FIRST CITY — C. R. ASHEN', 'ElevenLabs performance script (eleven_v3 audio tags)', '']
    stats = {}
    for key, cfg in manifest['chapters'].items():
        prod_path = os.path.join(BOOK, cfg['production'])
        prod = json.load(open(prod_path, encoding='utf-8'))
        folder = os.path.dirname(prod_path)
        segs = [x for f in prod['chapters'][0]['lineFiles']
                for x in json.load(open(os.path.join(folder, f), encoding='utf-8'))]
        lines, script = [], [cfg['title'].upper(), '']
        for i, s in enumerate(segs):
            tags = tags_for(segs, i) if s['speaker'] != 'Narrator' else []
            if s['speaker'] == 'Narrator' and 'Written text' in s.get('note', ''): tags = ['slowly']
            p = pause_before(segs, i)
            text = respell(s['text'], rules)
            entry = {'speaker': s['speaker'], 'text': text}
            if tags: entry['tags'] = tags; entry['tag'] = '] ['.join(tags)
            if p: entry['pauseBefore'] = p
            if s.get('note'): entry['note'] = s['note']
            lines.append(entry)
            if p: script.append(f'[pause {p:g}s]')
            tagtxt = ''.join(f'[{t}] ' for t in tags)
            script.append(f"{s['speaker']}: {tagtxt}{text}")
            for t in tags: stats[t] = stats.get(t, 0) + 1
            stats['pauses'] = stats.get('pauses', 0) + (1 if p else 0)
        script.append('[pause 3s]')
        chars = sum(len(l['text']) for l in lines)
        doc = {'book': 'The First City', 'chapterKey': key, 'title': cfg['title'], 'chars': chars,
               'speakers': sorted({l['speaker'] for l in lines}), 'lines': lines}
        json.dump(doc, open(os.path.join(OUT, key + '.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
        open(os.path.join(sdir, key + '.txt'), 'w', encoding='utf-8').write('\n'.join(script) + '\n')
        full += script + ['', '']
    open(os.path.join(sdir, 'THE_FIRST_CITY_FULL_SCRIPT.txt'), 'w', encoding='utf-8').write('\n'.join(full))
    print(sorted(stats.items(), key=lambda x: -x[1]))

if __name__ == '__main__':
    main()
