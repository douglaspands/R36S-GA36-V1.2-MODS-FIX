import re
from pathlib import Path

src = Path("README.md").read_text(encoding="utf-8")
dst = Path("docs/DESENVOLVIMENTO.md")
dst.parent.mkdir(exist_ok=True)
out = src.replace("7 anos", "6 anos")
print("7 anos ocorrencias:", src.count("7 anos"))
# links relativos markdown
links = re.findall(r"\]\(([^)#]+)(?:#[^)]*)?\)", out)
rel = [l for l in links if not re.match(r"[a-z]+:", l)]
print("links relativos:", sorted(set(rel)))
for i, l in enumerate(out.splitlines(), 1):
    if "](" in l and any(("](" + r) in l for r in rel):
        print(i, l[:160])
dst.write_text(out, encoding="utf-8")
print("## titulos:", len(re.findall(r"^## ", src, re.M)), len(re.findall(r"^## ", out, re.M)))
