"""Write the JSON files the hosted (claude.ai) version needs:
taxonomy.json (keywords, shared with the Python tool) and example.json
(SYNTHETIC demo data from make_fixture.py, labelled as such in the page)."""
import csv, io, json, os, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from radar import taxonomy as T, analyze as A, sources as S

out = sys.argv[1] if len(sys.argv) > 1 else "web-artifact"
json.dump({"core": T.CORE, "sectors": T.SECTOR_PACKS, "subtopics": T.SUBTOPICS,
           "churn": T.CHURN, "feature_request": T.FEATURE_REQUEST},
          open(os.path.join(out, "taxonomy.json"), "w"), indent=0)

raw = subprocess.run([sys.executable, os.path.join(os.path.dirname(__file__), "make_fixture.py"), "7", "Purplle"],
                     capture_output=True, text=True, check=True).stdout
tmp = os.path.join(out, "_fx.csv"); open(tmp, "w").write(raw)
df = A.score_sentiment(A.prepare(S.from_csv(tmp, "example"), "Example"))
os.remove(tmp)
rows = [{"text": r.text, "source": r.source.replace("csv:", ""), "date": r.date.date().isoformat() if r.date == r.date else None,
         "rating": None if r.rating != r.rating else int(r.rating), "likes": int(r.likes), "sentiment": float(r.sentiment)}
        for r in df.itertuples()]
json.dump({"name": "Example brand (made-up data)", "sector": "beauty,ecommerce", "competitors": "Purplle", "rows": rows},
          open(os.path.join(out, "example.json"), "w"))
print(len(rows), "example rows")
