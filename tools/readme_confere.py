import re
from pathlib import Path

arqs = ["README.md", "README.pt-BR.md", "README.es.md"]
contagens = {}
for a in arqs:
    t = Path(a).read_text(encoding="utf-8")
    contagens[a] = (len(re.findall(r"^## ", t, re.M)), t.count("!["))
    for m in re.findall(r"\]\(([^)]+)\)", t):
        if re.match(r"[a-z]+:", m):
            continue
        if not Path(m).exists():
            print("QUEBRADO", a, m)
    for termo in ("7 anos", "7 years", "7 años"):
        if termo in t:
            print("IDADE", a, termo)
    print(a, "6 anos/years/años:", bool(re.search(r"6[ -](anos|years?|años)", t)),
          "ilustrativ:", bool(re.search(r"ilustrativ|illustrative", t, re.I)))
print(contagens)

for pasta in ["CLAUDE.md", "GEMINI.md", "tests", "tools", "openspec", "build.sh", "flash.sh", "config"]:
    p = Path(pasta)
    files = [p] if p.is_file() else [f for f in p.rglob("*") if f.is_file()] if p.exists() else []
    for f in files:
        if "readme-trilingue" in str(f) or "archive" in f.parts and False:
            continue
        try:
            for i, l in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
                if "README" in l or "7 anos" in l:
                    print(f"{f}:{i}: {l[:150]}")
        except Exception:
            pass
