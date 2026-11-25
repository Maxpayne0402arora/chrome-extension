"""Local web app: `python -m radar serve`, then open http://localhost:8765

Uses only the Python standard library (no Flask needed). Data collection has to
happen server-side because browsers can't fetch Play Store / Reddit pages
directly (CORS), so this is a small local server rather than a static page.
"""
from __future__ import annotations

import json
import os
import tempfile
import threading
import traceback
import uuid
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from . import llm
from . import pipeline as P
from . import taxonomy as T
from . import topic as TP

WEB = os.path.join(os.path.dirname(__file__), "web")
JOBS: dict[str, dict] = {}
RUN_LOCK = threading.Lock()          # one collection at a time (sources share a logger)
CACHE: dict[str, tuple] = {}         # slug -> (mtime, df, summary, meta)
TOPICS_FILE = lambda: os.path.join(P.OUT, "saved_topics.json")  # noqa: E731


def _load(slug):
    path = os.path.join(P.OUT, slug, "feedback.pkl")
    mtime = os.path.getmtime(path)
    hit = CACHE.get(slug)
    if not hit or hit[0] != mtime:
        df, summary, meta = P.load(slug)
        CACHE[slug] = hit = (mtime, df, summary, meta)
    return hit[1], hit[2], hit[3]


def _saved_topics():
    try:
        with open(TOPICS_FILE()) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def _run_job(job_id, params):
    job = JOBS[job_id]

    def log(msg):
        job["log"].append(str(msg))

    with RUN_LOCK:
        try:
            job["status"] = "collecting"
            log(f"Analysing {params['brand']} (sources: {params['sources']}, country: {params['country']})")
            recs = P.collect(params, log=log)
            if not recs:
                raise RuntimeError("No feedback collected. Check the brand name, app IDs or your network, "
                                   "or upload a CSV of reviews.")
            job["status"] = "analysing"
            log(f"Scoring sentiment and tagging {len(recs)} items ...")
            df, summary = P.build(recs, params)
            P.save(df, summary, params)
            job.update(status="done", slug=P.slug(params["brand"]))
            log(f"Done: {summary['n']} items kept after cleaning.")
        except BaseException as e:  # noqa: BLE001 - SystemExit from analyse layer too
            job.update(status="error", error=str(e) or e.__class__.__name__)
            log("ERROR: " + (str(e) or traceback.format_exc()))
        finally:
            for f in params.get("csv") or []:
                try:
                    os.remove(f)
                except OSError:
                    pass


class Handler(BaseHTTPRequestHandler):
    server_version = "PainPointRadar/1.0"

    def log_message(self, fmt, *args):  # quieter console
        if "/api/jobs/" not in (args[0] if args else ""):
            super().log_message(fmt, *args)

    # ---------------------------------------------------------------- helpers
    def _send(self, code, body, ctype="application/json"):
        data = body if isinstance(body, bytes) else (
            json.dumps(body, default=str, ensure_ascii=False).encode() if ctype == "application/json" else body.encode())
        self.send_response(code)
        self.send_header("Content-Type", ctype + "; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def _json(self):
        n = int(self.headers.get("Content-Length") or 0)
        return json.loads(self.rfile.read(n) or b"{}") if n else {}

    def _err(self, code, msg):
        self._send(code, {"error": msg})

    # ---------------------------------------------------------------- routes
    def do_GET(self):  # noqa: N802
        u = urlparse(self.path)
        parts = [p for p in u.path.split("/") if p]
        q = {k: v[0] for k, v in parse_qs(u.query).items()}
        try:
            if not parts:
                with open(os.path.join(WEB, "index.html"), encoding="utf-8") as f:
                    return self._send(200, f.read(), "text/html")
            if parts == ["api", "config"]:
                return self._send(200, {
                    "presets": P.PRESETS, "defaults": P.DEFAULTS, "sectors": list(T.SECTOR_PACKS),
                    "topics": sorted(set(T.CORE) | {a for pk in T.SECTOR_PACKS.values() for a in pk}),
                    "subtopics": {k: list(v) for k, v in T.SUBTOPICS.items()},
                    "claude": llm.available(), "saved_topics": _saved_topics()})
            if parts == ["api", "brands"]:
                return self._send(200, P.list_brands())
            if parts[:2] == ["api", "jobs"] and len(parts) == 3:
                job = JOBS.get(parts[2])
                return self._send(200, job) if job else self._err(404, "no such job")
            if parts[:2] == ["api", "brand"] and len(parts) == 4 and parts[3] == "summary":
                df, summary, meta = _load(parts[2])
                return self._send(200, {"summary": summary, "meta": meta,
                                        "sources": sorted(df["source"].unique().tolist())})
            if parts[0] == "report" and len(parts) == 2:
                path = os.path.join(P.OUT, os.path.basename(parts[1]), "report.html")
                with open(path, encoding="utf-8") as f:
                    return self._send(200, f.read(), "text/html")
            if parts == ["api", "compare"]:
                slugs = [s for s in q.get("slugs", "").split(",") if s]
                return self._send(200, [_load(s)[1] for s in slugs])
            return self._err(404, "not found")
        except FileNotFoundError:
            return self._err(404, "not analysed yet")
        except Exception as e:  # noqa: BLE001
            traceback.print_exc()
            return self._err(500, str(e))

    def do_POST(self):  # noqa: N802
        parts = [p for p in urlparse(self.path).path.split("/") if p]
        try:
            body = self._json()
            if parts == ["api", "analyze"]:
                brand = (body.get("brand") or "").strip()
                if not brand:
                    return self._err(400, "brand is required")
                csvs = []
                for f in body.get("csv_files") or []:
                    fd, path = tempfile.mkstemp(suffix=".csv")
                    with os.fdopen(fd, "w", encoding="utf-8") as h:
                        h.write(f.get("content", ""))
                    csvs.append(path)
                params = P.params_for(brand, **{k: body.get(k) for k in (
                    "sources", "play_id", "appstore_id", "country", "max_reviews", "sector", "competitors",
                    "subreddits", "query")}, csv=csvs)
                if body.get("sources") == "":
                    params["sources"] = ""
                job_id = uuid.uuid4().hex[:10]
                JOBS[job_id] = {"id": job_id, "brand": brand, "status": "queued", "log": [], "params": params}
                threading.Thread(target=_run_job, args=(job_id, params), daemon=True).start()
                return self._send(200, {"job": job_id})

            if parts == ["api", "topics"]:  # save / delete a custom topic definition
                topics = [t for t in _saved_topics() if t["name"] != body.get("name")]
                if not body.get("delete"):
                    topics.append({"name": body["name"], "keywords": body.get("keywords") or [],
                                   "subthemes": body.get("subthemes") or {}})
                os.makedirs(P.OUT, exist_ok=True)
                with open(TOPICS_FILE(), "w") as f:
                    json.dump(topics, f, indent=2)
                return self._send(200, topics)

            if parts[:2] == ["api", "brand"] and len(parts) >= 4:
                df, summary, meta = _load(parts[2])
                kw = body.get("keywords") or None
                if parts[3] == "topic" and len(parts) == 4:
                    return self._send(200, TP.deep_dive(df, summary["company"], body.get("topic"), kw,
                                                        body.get("subthemes"), int(meta.get("recent_days", 30))))
                if parts[3] == "feedback":
                    return self._send(200, TP.filter_feedback(
                        df, body.get("topic"), kw, body.get("subtheme"), body.get("subthemes"), body.get("phrase"),
                        body.get("q"), body.get("sentiment"), body.get("source"), body.get("sort", "helpful"),
                        int(body.get("limit", 30)), int(body.get("offset", 0))))
                if parts[3] == "topic" and len(parts) == 5 and parts[4] == "claude":
                    res = TP.filter_feedback(df, body.get("topic"), kw, body.get("subtheme"), body.get("subthemes"),
                                             body.get("phrase"), None, "negative", None, "helpful", 60)
                    texts = [i["text"] for i in res["items"]]
                    if len(texts) < 5:
                        return self._err(400, "Need at least 5 negative comments for Claude to analyse.")
                    label = body.get("topic") + (f" / {body['subtheme']}" if body.get("subtheme") else "")
                    try:
                        return self._send(200, llm.analyse_texts(summary["company"], label, texts))
                    except llm.LLMError as e:
                        return self._err(502, str(e))
            return self._err(404, "not found")
        except FileNotFoundError:
            return self._err(404, "not analysed yet")
        except Exception as e:  # noqa: BLE001
            traceback.print_exc()
            return self._err(500, str(e))


def serve(port=8765, open_browser=True):
    httpd = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    url = f"http://localhost:{port}"
    print(f"Pain-Point Radar running at {url}  (Ctrl+C to stop)")
    if open_browser:
        threading.Timer(0.8, lambda: webbrowser.open(url)).start()
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
