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
    # Emotion the prose shows rather than names.
    (r'\bcough', 'coughs'),
    (r'\bgrunt', 'grunts'),
    (r'went pale|face had gone pale|lost colou?r|\bafraid\b|\bfrighten|\bterrif|\bpanic', 'scared'),
    (r'\bhesitat|\bswallowed\b', 'hesitant'),
    (r'jaw tightened|mouth tightened|expression hardened|face hardened|\bglared\b|turned on (?:him|her)|stiffened', 'tense'),
    (r'\bangr|\bfurious|\brage\b', 'angrily'),
    (r'\bimpatien', 'impatiently'),
    (r'(?:spoke|read|said|asked|placed each word) carefully', 'carefully'),
    (r'\bcalm(?:ly)?\b', 'calmly'),
    (r'\bexcit|\beager', 'excited'),
    (r'\bweary|\btired\b', 'tired'),
    (r'\bspat\b', 'disgusted'),
    (r'\bdryly\b|\bwryly\b', 'dryly'),
    (r'\bcoldly\b', 'coldly'),
    (r'\boffended\b', 'offended'),
    (r'\bshrug', 'casually'),
    (r'\bfrown', 'skeptical'),
]

# Hand-placed direction for key moments: (chapter number, speaker, line start) -> tags.
HAND = {
 (1, 'Kurash', 'Why?'): ['curious'], (1, 'Kurash', 'Maybe they died.'): ['dismissively'],
 (1, 'Zik', 'Then the trap is still here.'): ['flatly'], (1, 'Enhedu', 'Then they chose the wrong door.'): ['confidently'],
 (1, 'Zik', "Don't touch the gold"): ['shaken'], (1, 'Balag', 'You think?'): ['bitterly'],
 (1, 'Balag', 'Zik,'): ['warning'], (1, 'Zik', 'Well,'): ['shakily'], (1, 'Zik', "that's new."): ['deadpan'],
 (2, 'Enhedu', 'He died before he turned twenty.'): ['quietly'], (2, 'Enhedu', "No. It's supposed to make it true."): ['flatly'],
 (2, 'Balag', 'Someone always does.'): ['gruffly'], (2, 'Balag', 'Still don’t like'): ['quietly'],
 (3, 'Balag', 'Same fucking math again.'): ['bitterly'],
 (5, 'The Collector', 'Zikir.'): ['softly'], (5, 'The Collector', 'Where did you get that?'): ['curious'],
 (5, 'Zik', "I'm not him."): ['quietly'], (5, "Zik's Mother", 'No,'): ['softly'],
 (5, "Zik's Mother", 'That’s not the same as being brave'): ['coughs'], (5, "Zik's Mother", "That's not the same as being brave"): ['coughs'],
 (6, 'Ninsun', 'Desperate,'): ['quietly'], (6, 'Ninsun', 'I care about the tablets'): ['intense'],
 (7, 'Ninsun', 'My sister—'): ['desperate'], (7, 'Balag', 'No.'): ['firmly'],
 (9, 'Ninsun', 'I saw her.'): ['shaky'], (9, 'Ninsun', 'My sister.'): ['breathless'], (9, 'Ninsun', 'She never had that.'): ['horrified'],
 (9, 'Ninsun', 'Ammaru,'): ['defiantly'], (9, 'Ninsun', 'They’re crossing it out'): ['panicked'], (9, 'Ninsun', "They're crossing it out"): ['panicked'],
 (13, 'Balag', 'I know we almost didn'): ['calmly'], (14, 'Balag', 'I fucking hate that man.'): ['annoyed'],
 (16, 'Mardu', 'I am old. Everything takes too long.'): ['dryly'], (16, 'Mardu', 'Many have.'): ['dryly'],
 (16, 'Ninsun', 'Do not drag me.'): ['sharply'], (16, 'Archive Guard', 'Mardu?'): ['shouts'],
 (17, 'Ninsun', 'A human one.'): ['shaken'], (17, 'Zik', '…is still waiting below.'): ['quietly'],
 (18, 'False Scribe', 'Some doors are sealed'): ['ominous'], (18, 'False Scribe', 'Some are sealed'): ['ominous'],
 (19, 'Inn Cook', 'Out.'): ['shouts'],
 (20, 'The Collector', 'You,'): ['softly'], (20, 'Balag', 'I dislike him more than before.'): ['dryly'],
 (21, 'Balag', 'His name.'): ['gravely'], (21, 'Ninsun', 'My name is Ninsun Etana.'): ['shaky'], (21, 'Zik', 'Zikir Ashur.'): ['firmly'],
 (23, 'Zik', 'An invitation,'): ['quietly'],
 (24, 'Bel-iddin', 'You shouldn'): ['sorrowful'], (25, 'Enhedu', 'A kingdom.'): ['hungrily'], (25, 'Zik', "I don't think we did."): ['quietly'],
 (27, 'The Man Who Refused', 'Don’t give it your name.'): ['hoarse'], (27, 'The Man Who Refused', "Don't give it your name."): ['hoarse'],
 (27, 'The Man Who Refused', 'I can still see her face'): ['sadly'],
 (28, 'The Man Who Refused', 'Because it may hear you.'): ['whispers'],
 (29, 'Zik', 'Enhedu?'): ['concerned'],
 (31, 'Balag', 'Who?'): ['confused'], (32, 'Balag', 'I don'): ['coldly'],
 (33, 'Zik', 'Her name is Ninsun.'): ['firmly'], (35, 'Ninsun', 'You lied,'): ['flatly'], (35, 'Zik', 'It says the left path is safe.'): ['evenly'],
 (36, 'Balag', 'I objected internally.'): ['dryly'],
 (37, 'The Remainder', 'Do you remember the key?'): ['whispers'],
 (38, 'The Remainder', 'Take the damned key, Zik.'): ['impatiently'], (38, 'The Remainder', 'Don’t make me wait here again.'): ['pleading'],
 (38, 'The Remainder', "Don't make me wait here again."): ['pleading'],
 (39, 'Zik', 'But I was looking for him.'): ['quietly'],
 (40, 'Zik', 'Enhedu hated being carried.'): ['fondly'], (40, 'Ninsun', 'You can tell her yourself.'): ['tearfully'],
 (40, 'Zik', 'Go.'): ['urgently'], (40, 'Ninsun', 'I will come back,'): ['determined'], (40, 'Zik', 'Then don'): ['gently'],
 (40, 'Ninsun', 'Zik.'): ['whispers'], (40, 'Zik', "I can't remember what it felt like."): ['hollow'],
}
HAND_USED = set()

def hand_tags(ch, s):
    for (c, spk, start), tags in HAND.items():
        if c == ch and s['speaker'] == spk and s['text'].replace('’', "'").startswith(start.replace('’', "'")):
            HAND_USED.add((c, spk, start)); return tags
    return []
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

def tags_for(segs, i, ch=0):
    s = segs[i]
    out = list(hand_tags(ch, s))
    if ch == 40 and s['speaker'] == 'Ninsun' and s['text'] == 'Zik.' and \
            any(x['speaker'] == 'Ninsun' and x['text'] == 'Zik.' for x in segs[i + 1:]):
        out = []  # only the final "Zik." at the sealed stone is whispered
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
        for sent in reversed(sentences(prv['text'])[-2:]):
            if about(sent, s['speaker']) and len(sent.split()) <= 16:
                t = cue_tag(sent)
                if t: out.append(t); break
    if s['text'].rstrip().endswith('!') and not any(t in out for t in ('shouts', 'screams', 'whispers')):
        out.append('shouts' if len(s['text']) < 40 else 'urgently')
    seen = []
    for t in out:
        if t not in seen: seen.append(t)
    return seen[:2]

TIMEJUMP = re.compile(r'^(That night|That was when|By (mid-?morning|late afternoon|the time|sunset|nightfall|dusk|the second turn)|Toward morning|Late afternoon|Near midday|At (sunset|dawn|last)|They (left|broke camp|slept|started walking|moved on|went on|dug until|spent the better part|rested|met|crossed|descended|reached|found|did not return|took|finished)|The (first|second|third|fourth|fifth) (three days|day|dawn|night)|The next|Three days|Two days|Hours later|When they finally|Later,|Halfway|Sometime after|It took until|The east-side walls|The rain had|The old lime kilns|Uruk had emptied)')
BEATS = {'Once.', 'Twice.', 'Then twice.', 'Three times.', 'Then four.', 'Then another.', 'Pause.', 'Scrape.', 'Thump.', 'Then a fourth.', 'A pause.', 'Nothing.'}

def pause_before(segs, i):
    s = segs[i]
    if i == 0: return 0
    if i == len(segs) - 1 and s['speaker'] == 'Narrator': return 1.2
    if segs[i - 1]['text'].startswith('CHAPTER') and i == 1: return 1.0
    if i == 2: return 2.0                       # after the chapter title
    prev = segs[i - 1]
    if 'long beat' in prev.get('note', '').lower() or 'Leave a long beat' in prev.get('note', ''): return 2.0
    if prev.get('pause', 0) >= 0.6: return 1.5
    if s['speaker'] == 'Narrator' and SILENCE.match(s['text']): return 1.5
    if s['speaker'] == 'Narrator' and TIMEJUMP.match(s['text']) and prev['speaker'] != 'Narrator' or \
       s['speaker'] == 'Narrator' and TIMEJUMP.match(s['text']) and len(prev['text']) > 0 and i > 3 and s['pause'] >= 0.38: return 1.5
    if s['speaker'] == 'Narrator' and s['text'] in BEATS: return 0.6
    if s['speaker'] == 'Narrator' and len(s['text'].split()) <= 3 and s['text'].endswith('.') and prev['speaker'] == 'Narrator': return 0.5
    return 0

def main():
    from performance_direction import parse
    direction = parse()
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
        ch = int(key[:2]); dk = -1
        for i, s in enumerate(segs):
            tags = tags_for(segs, i, ch) if s['speaker'] != 'Narrator' else []
            if s['speaker'] != 'Narrator':
                dk += 1
                if dk in direction.get(ch, {}):
                    keep = [t for t in tags if t in ('weakly', 'flatly', 'exhausted', 'eerie') and t not in direction[ch][dk]]
                    tags = (keep + direction[ch][dk])[:2] if direction[ch][dk] else []
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
    unused = set(HAND) - HAND_USED
    print('hand tags not matched:', sorted({(c, sp, st) for c, sp, st in unused if not any(u[0]==c and u[1]==sp and u[2].replace('’',"'")==st.replace('’',"'") for u in HAND_USED)}))

if __name__ == '__main__':
    main()
