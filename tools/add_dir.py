import sys, re
p='performance_direction.py'; s=open(p).read()
new=open(sys.argv[1]).read().strip()
for m in re.finditer(r'^(\d+): """(.*?)"""', new, re.S|re.M):
    ch=m.group(1)
    if re.search(rf'^{ch}: """', s, re.M): s=re.sub(rf'^{ch}: """.*?""",\n', '', s, flags=re.S|re.M)
    s=s.replace('}\n\ndef parse(', f'{ch}: """{m.group(2)}""",\n}}\n\ndef parse(',1)
open(p,'w').write(s)
import importlib, performance_direction as d; importlib.reload(d); print({k:len(v) for k,v in d.parse().items()})
