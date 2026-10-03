"""Export every chapter as an ElevenLabs-ready script.

    python3 tools/export_elevenlabs.py

Writes book-data/elevenlabs/<chapter>.json (load it in SmartAss AI -> Audiobook)
and <chapter>.txt (a readable "Speaker: line" script for ElevenLabs Studio).
Canon pronunciations from book-data/global/pronunciations.txt are respelled into
the text sent to ElevenLabs; the manuscript itself is never changed.
"""
import json, os, re

BOOK = os.path.join(os.path.dirname(__file__), '..', 'book-data')
OUT = os.path.join(BOOK, 'elevenlabs')

def pronunciations():
    rules = []
    period = os.path.join(OUT, 'pronunciations-period.txt')
    src = period if os.path.exists(period) else os.path.join(BOOK, 'global', 'pronunciations.txt')
    for line in open(src, encoding='utf-8'):
        if '->' in line and not line.lstrip().startswith('#'):
            a, b = [x.strip() for x in line.split('->', 1)]
            rules.append((a, b))
    rules.sort(key=lambda r: -len(r[0]))  # "Zikir" before "Zik"
    return rules

def respell(text, rules):
    for a, b in rules:
        text = re.sub(r'\b' + re.escape(a) + r'\b', b[0].upper() + b[1:], text)
    return text

def tag_for(line):
    """Optional eleven_v3 audio tag. Kept to a small, conservative set."""
    note = line.get('note', '')
    if 'Whispered' in note or line['speaker'] == 'The City':
        return 'whispers'
    if 'physically failing' in note or line['speaker'] == 'The Remainder':
        return 'exhausted'
    if 'Post-vision' in note:
        return 'flatly'
    return None

def main():
    rules = pronunciations()
    manifest = json.load(open(os.path.join(BOOK, 'manifest.json'), encoding='utf-8'))
    os.makedirs(OUT, exist_ok=True)
    total = 0
    for key, cfg in manifest['chapters'].items():
        prod_path = os.path.join(BOOK, cfg['production'])
        prod = json.load(open(prod_path, encoding='utf-8'))
        folder = os.path.dirname(prod_path)
        segs = [x for f in prod['chapters'][0]['lineFiles']
                for x in json.load(open(os.path.join(folder, f), encoding='utf-8'))]
        lines = []
        for s in segs:
            entry = {'speaker': s['speaker'], 'text': respell(s['text'], rules)}
            t = tag_for(s)
            if t: entry['tag'] = t
            if s.get('note'): entry['note'] = s['note']
            lines.append(entry)
        chars = sum(len(l['text']) for l in lines)
        total += chars
        speakers = sorted({l['speaker'] for l in lines})
        doc = {'book': 'The First City', 'chapterKey': key, 'title': cfg['title'],
               'chars': chars, 'speakers': speakers, 'lines': lines}
        with open(os.path.join(OUT, key + '.json'), 'w', encoding='utf-8') as f:
            json.dump(doc, f, ensure_ascii=False, indent=0)
        with open(os.path.join(OUT, key + '.txt'), 'w', encoding='utf-8') as f:
            f.write(f"{cfg['title']}\n\n")
            for l in lines:
                tag = f"[{l['tag']}] " if l.get('tag') else ''
                f.write(f"{l['speaker']}: {tag}{l['text']}\n")
        print(f"{key}: {len(lines)} lines, {chars:,} chars")
    print(f"TOTAL {total:,} characters")

if __name__ == '__main__':
    main()
