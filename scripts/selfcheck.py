#!/usr/bin/env python3
"""Self-check for the ScreenPipe HyperFrames slideshow deck."""
import json, re, subprocess, sys, tempfile, os

ROOT = "/home/song/screenpipe-deck/slideshow"
COMP = ROOT + "/composition/index.html"
IDX  = ROOT + "/index.html"

html = open(COMP, encoding="utf-8").read()
idx_html = open(IDX, encoding="utf-8").read()
errors, warns = [], []

# ---- 1. Parse islands ----
def get_island(text, where):
    pat = re.compile(r'<script type="application/hyperframes-slideshow\+json">(.*?)</script>', re.S)
    blocks = pat.findall(text)
    if len(blocks) != 1:
        errors.append(f"{where}: expected exactly 1 JSON island, found {len(blocks)}")
        return None
    try:
        return json.loads(blocks[0])
    except Exception as e:
        errors.append(f"{where}: island JSON parse error: {e}")
        return None

island = get_island(html, "composition")
island2 = get_island(idx_html, "wrapper")
if island is not None and island2 is not None and island != island2:
    errors.append("island mismatch: composition and wrapper islands differ")

# ---- 2. Scene declarations ----
scene_pat = re.compile(
    r'<div[^>]*data-composition-id="([^"]+)"[^>]*data-start="(\d+)"[^>]*data-duration="(\d+)"', re.S)
scenes = {}
for m in scene_pat.finditer(html):
    cid, start, dur = m.group(1), int(m.group(2)), int(m.group(3))
    if cid in scenes:
        errors.append(f"duplicate composition-id: {cid}")
    scenes[cid] = {"start": start, "end": start + dur}
print(f"scenes declared: {len(scenes)} -> {list(scenes)}")

if island:
    slides = island.get("slides", [])
    seqs = island.get("slideSequences", [])
    seq_ids = {s.get("id") for s in seqs}
    main_ids = [s.get("sceneId") for s in slides]

    # every sceneId resolves
    for s in slides:
        sid = s.get("sceneId")
        if sid not in scenes:
            errors.append(f"main slide sceneId not found: {sid}")
    for q in seqs:
        for s in q.get("slides", []):
            sid = s.get("sceneId")
            if sid not in scenes:
                errors.append(f"branch slide sceneId not found: {sid} (seq {q.get('id')})")

    # no overlap between branch and main line
    branch_ids = [s.get("sceneId") for q in seqs for s in q.get("slides", [])]
    overlap = set(branch_ids) & set(main_ids)
    if overlap:
        errors.append(f"branch scenes also in main slides: {overlap}")

    # no time overlap among main-line slides
    ordered = []
    for s in slides:
        sid = s.get("sceneId")
        if sid in scenes:
            ordered.append((sid, scenes[sid]["start"], scenes[sid]["end"]))
    ordered.sort(key=lambda x: x[1])
    for a, b in zip(ordered, ordered[1:]):
        if a[2] > b[1]:
            errors.append(f"main slides overlap in time: {a} vs {b}")

    # fragments within [start, end] of their scene (inclusive)
    for s in slides:
        sid = s.get("sceneId")
        if sid not in scenes:
            continue
        lo, hi = scenes[sid]["start"], scenes[sid]["end"]
        for t in s.get("fragments", []):
            if t < lo or t > hi:
                errors.append(f"fragment {t} outside [{lo},{hi}] of {sid}")
    for q in seqs:
        for s in q.get("slides", []):
            sid = s.get("sceneId")
            if sid not in scenes:
                continue
            lo, hi = scenes[sid]["start"], scenes[sid]["end"]
            for t in s.get("fragments", []):
                if t < lo or t > hi:
                    errors.append(f"branch fragment {t} outside [{lo},{hi}] of {sid}")

    # hotspot targets reference defined sequences
    for s in slides:
        for h in s.get("hotspots", []):
            if h.get("target") not in seq_ids:
                errors.append(f"hotspot target not a sequence: {h}")

    # branch scene total duration fits inside root total
    total_needed = max(v["end"] for v in scenes.values())
    print(f"main slides: {len(slides)}, branch scenes: {len(branch_ids)}, timeline needs {total_needed}s")

# ---- 3. Fragment element ids referenced in the JS exist in DOM ----
frag_defs = re.findall(r'\{\s*t:\s*([\d.]+),\s*el:\s*"([^"]+)"\s*\}', html)
for t, el in frag_defs:
    if f'id="{el}"' not in html:
        errors.append(f"JS fragment element missing in DOM: {el}")

# ---- 4. JS fragment times match island fragments per scene ----
# (map: el->scene via container ids)
scene_of = {}
for sid in scenes:
    # find the div block for the scene and collect element ids inside it
    m = re.search(rf'<div id="{sid}"[^>]*>(.*?)\n</div>\n\n<!--', html, re.S)
    if not m:
        m = re.search(rf'<div id="{sid}"[^>]*>(.*)', html, re.S)
    body = m.group(1) if m else ""
    for el in re.findall(r'id="([^"]+)"', body):
        scene_of[el] = sid
js_by_scene = {}
for t, el in frag_defs:
    sid = scene_of.get(el)
    js_by_scene.setdefault(sid, []).append(float(t))
if island:
    for s in island.get("slides", []):
        sid = s.get("sceneId")
        want = sorted(s.get("fragments", []))
        got = sorted(js_by_scene.get(sid, []))
        if want != got:
            errors.append(f"fragment mismatch {sid}: island={want} js={got}")
print("js fragment times by scene:", js_by_scene)

# ---- 5. Extract inline <script> (non-JSON, non-src) and node --check ----
inline = []
for m in re.finditer(r'<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>', html, re.S):
    body = m.group(1)
    if 'application/hyperframes-slideshow+json' in m.group(0) or not body.strip():
        continue
    inline.append(body)
for m in re.finditer(r'<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>', idx_html, re.S):
    body = m.group(1)
    if 'application/hyperframes-slideshow+json' in m.group(0) or not body.strip():
        continue
    inline.append(body)
for i, body in enumerate(inline):
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as f:
        f.write(body)
        path = f.name
    r = subprocess.run(["node", "--check", path], capture_output=True, text=True)
    if r.returncode != 0:
        errors.append(f"inline script #{i} node --check failed:\n{r.stderr[:500]}")
    else:
        print(f"inline script #{i}: node --check OK ({len(body)} chars)")
    os.unlink(path)

# ---- 6. assets referenced exist ----
for src in re.findall(r'src="(\.\./assets/[^"]+)"', html):
    p = os.path.normpath(os.path.join(ROOT, "composition", src))
    if not os.path.exists(p):
        errors.append(f"missing asset: {src}")

# ---- 7. vendored bundles exist + wrapper references ----
for v in ["gsap.min.js", "hyperframes-player.global.js", "hyperframes-slideshow.global.js",
          "hyperframe.runtime.iife.js"]:
    if not os.path.exists(f"{ROOT}/vendor/{v}"):
        errors.append(f"missing vendor file: {v}")
for ref in ["vendor/gsap.min.js", "vendor/hyperframes-player.global.js",
            "vendor/hyperframes-slideshow.global.js", "composition/index.html"]:
    if ref not in idx_html:
        errors.append(f"wrapper missing reference: {ref}")

print()
if errors:
    print("SELF-CHECK FAILED:")
    for e in errors:
        print(" -", e)
    sys.exit(1)
print("SELF-CHECK PASSED ✓ (island schema, scene resolution, fragment ranges,")
print(" island↔JS fragment parity, node --check, assets, vendor bundles)")
