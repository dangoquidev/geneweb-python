import json
import pickle
from pathlib import Path

src = Path("data.json")
dst = Path("data.pkl")

if not src.exists():
    raise SystemExit("data.json introuvable dans le répertoire courant")

obj = json.load(src.open("r", encoding="utf-8"))
pickle.dump(obj, dst.open("wb"), protocol=pickle.HIGHEST_PROTOCOL)
print("OK:", dst.resolve())
