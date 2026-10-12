# -*- coding: utf-8 -*-
"""Scouting only: how many CC0 / public-domain files do Commons categories hold?  METADATA only; no image is downloaded.

  WIKIQA_CONTACT=... python -m datasets.tools.probe_domains check      # do the root categories exist? (categoryinfo)
  WIKIQA_CONTACT=... python -m datasets.tools.probe_domains run        # traverse, sample, write manifests/domain_probe.{json,md}

Per root category: breadth-first over sub-categories (depth <= DEPTH, at most MAX_CATS categories listed), file titles listed
(<= LIST_CAP per category), then up to SAMPLE random files get imageinfo (50 per request) -> licence / size / mime.
Counts are ESTIMATES from the sample unless the whole tree was listed and sampled (``exact``).
"""
from __future__ import annotations

import json
import pathlib
import random
import re
import sys
import time
from collections import Counter

from datasets.fetch import commons, http

OUT = pathlib.Path(__file__).resolve().parents[1] / "manifests"
DEPTH, MAX_CATS, LIST_CAP, SAMPLE, LOW_PX = 2, 30, 1500, 500, 400
SKIP = re.compile(r"people|portrait|medical|x-ray|radiograph|\bMRI\b|\bCT\b|ultrasound|patient|surgery|faces|women|men\b|"
                  r"nude|sex|cadaver|autopsy|pathology|histolog|dental|clinical", re.I)
CC0 = re.compile(r"^(cc0|cc-zero|cc zero)", re.I)
PD = re.compile(r"^(public domain|pd\b|pd-|pd )", re.I)
NOLEVEL = re.compile(r"^(no known|no restrictions)", re.I)

ROOTS = {
    "1 business documents": ["Invoices", "Receipts", "Forms (documents)", "Business cards", "Certificates", "Ledgers", "Account books",
                             "Tickets", "Letters", "United States government forms", "Taxation forms of the United States", "Contracts",
                             "Purchase orders", "Bills", "Invoices from Austria-Hungary", "Receipts of Russia", "Payment systems"],
    "2 safety and quality": ["Safety signs", "Warning signs", "Personal protective equipment", "Hard hats", "Occupational Safety and Health Administration",
                             "Occupational safety and health", "Hazard symbols", "Hazard signs", "ISO 7010 safety signs", "ISO 7010 warning signs",
                             "Prohibition signs", "Safety symbols", "GHS pictograms", "Chemical hazard signs"],
    "3 maps, routes, drawings": ["Floor plans", "Blueprints", "Circuit diagrams", "Schematics", "Flowcharts", "Transit maps", "Metro maps",
                                 "Railway maps", "Site plans", "Technical drawings", "Wiring diagrams", "Subway maps", "Rail transport maps",
                                 "Tram maps", "Bus maps", "Public transport maps of London", "Schematic plans", "Flow charts", "Schematic drawings"],
    "4 science, astronomy, satellite": ["NASA images", "Images from NASA", "PD NASA", "Astronomical images", "Satellite images", "Satellite imagery",
                                        "NASA Earth Observatory images (review needed)", "Hubble Space Telescope", "Microscopy",
                                        "Anatomical plates and drawings in English", "Anatomography"],
    "5 old Japanese materials": ["Newspapers of Japan", "1910s newspapers of Japan", "1920s newspapers of Japan", "1930s newspapers of Japan",
                                 "Newspapers in Japanese", "Old maps of Japan", "Old maps of Tokyo", "Timetables of Japan",
                                 "Train timetables in Japan", "Public transport timetables of Japan", "Tickets of Japan", "Posters of Japan",
                                 "Japanese-language posters", "Advertisements in Japan by year", "Meiji era", "Meiji period"],
    "6 charts, graphs, tables, UI": ["Charts", "Graphs", "Tables", "Screenshots", "Diagrams", "Infographics", "Bar charts", "Line graphs",
                                     "Pie charts", "Computer screenshots", "Graphical user interface"],
}


def api(params):
    return http.api_json(commons.COMMONS, dict(action="query", **params), use_cache=True, post=True)


def cat_info(names):
    """name -> (exists, files, subcats)"""
    out = {}
    names = list(names)
    for i in range(0, len(names), 50):
        chunk = ["Category:" + n for n in names[i:i + 50]]
        q = api(dict(titles="|".join(chunk), prop="categoryinfo")).get("query", {})
        norm = {n["from"]: n["to"] for n in q.get("normalized", [])}
        redir = {}
        pages = {p["title"]: p for p in q.get("pages", {}).values()}
        for t in chunk:
            p = pages.get(norm.get(t, t))
            if p is None or "missing" in p:
                out[t[9:]] = (False, 0, 0)
            else:
                ci = p.get("categoryinfo", {})
                out[t[9:]] = (True, ci.get("files", 0), ci.get("subcats", 0))
    return out


def members(cat, types, cap):
    titles, cont = [], {}
    while len(titles) < cap:
        d = http.api_json(commons.COMMONS, dict(action="query", list="categorymembers", cmtitle="Category:" + cat, cmtype=types,
                                                cmlimit=500, **cont), use_cache=True, post=True)
        titles += [m["title"] for m in d.get("query", {}).get("categorymembers", [])]
        cont = d.get("continue")
        if not cont:
            break
    return titles


def traverse(root):
    """-> (cats listed [(name, depth, files, subcats)], file titles {title}, truncated?)"""
    seen = {root}
    queue = [(root, 0)]
    listed, files, trunc = [], set(), False
    info = cat_info([root])
    if not info[root][0]:
        return None
    meta = {root: info[root]}
    while queue and len(listed) < MAX_CATS:
        cat, depth = queue.pop(0)
        _, nf, ns = meta[cat]
        listed.append((cat, depth, nf, ns))
        if nf:
            ts = members(cat, "file", LIST_CAP)
            trunc |= nf > len(ts)
            files.update(ts)
        if ns and depth < DEPTH:
            subs = [t[9:] for t in members(cat, "subcat", 500) if not SKIP.search(t)]
            subs = [s for s in subs if s not in seen]
            seen.update(subs)
            si = cat_info(subs)
            meta.update(si)
            # biggest first (by files + subcats), empty ones dropped
            for s in sorted(subs, key=lambda s: -(si[s][1] + si[s][2])):
                if si[s][1] + si[s][2] > 0:
                    queue.append((s, depth + 1))
            queue.sort(key=lambda x: (x[1], -(meta[x[0]][1] + meta[x[0]][2])))
    return listed, files, trunc or bool(queue)


def classify(lic):
    if CC0.match(lic):
        return "cc0"
    if PD.match(lic):
        return "pd"
    return "other"


def sample_info(titles):
    out = []
    for i in range(0, len(titles), 50):
        chunk = titles[i:i + 50]
        q = api(dict(titles="|".join(chunk), prop="imageinfo", iiprop="size|mime|extmetadata",
                     iiextmetadatafilter="LicenseShortName", redirects=1)).get("query", {})
        for p in q.get("pages", {}).values():
            ii = (p.get("imageinfo") or [None])[0]
            if not ii:
                continue
            em = ii.get("extmetadata")
            if not isinstance(em, dict):      # the API returns [] when a file has no extended metadata
                em = {}
            lic = ((em.get("LicenseShortName") or {}).get("value", "") if isinstance(em.get("LicenseShortName"), dict) else "") or ""
            out.append(dict(title=p["title"], license=lic.strip(), mime=ii.get("mime"), w=ii.get("width") or 0, h=ii.get("height") or 0))
    return out


def probe(root, rng):
    t = traverse(root)
    if t is None:
        return dict(category=root, exists=False)
    listed, files, trunc = t
    titles = sorted(files)
    sample = titles if len(titles) <= SAMPLE else rng.sample(titles, SAMPLE)
    rows = sample_info(sample)
    n = len(rows) or 1
    cls = Counter(classify(r["license"]) for r in rows)
    lic = Counter(r["license"] or "(none)" for r in rows)
    mime = Counter((r["mime"] or "?").split("/")[-1] for r in rows)
    low = [r for r in rows if max(r["w"], r["h"]) < LOW_PX]
    ok = [r for r in rows if classify(r["license"]) != "other" and max(r["w"], r["h"]) >= LOW_PX]
    exact = len(titles) <= SAMPLE and not trunc
    scale = len(titles) / n
    return dict(
        category=root, exists=True, cats_listed=len(listed), sum_files_categoryinfo=sum(c[2] for c in listed),
        unique_files_listed=len(titles), listing_truncated=trunc, sampled=len(rows), exact=exact,
        cc0_n=cls["cc0"], pd_n=cls["pd"], other_n=cls["other"], low_res_n=len(low), usable_n=len(ok),
        est_unique=len(titles), est_cc0=round(cls["cc0"] * scale), est_pd=round(cls["pd"] * scale),
        est_other=round(cls["other"] * scale), est_low=round(len(low) * scale), est_usable=round(len(ok) * scale),
        licenses=lic.most_common(12), mimes=dict(mime), sub_categories=[c[0] for c in listed[1:8]],
        samples=dict(cc0_or_pd=[r["title"] for r in ok[:5]], other=[r["title"] for r in rows if classify(r["license"]) == "other"][:5]),
    )


def report():
    res = json.loads((OUT / "domain_probe.json").read_text(encoding="utf-8"))
    L = ["# domain_probe: CC0 / public-domain files per Commons category (metadata only, no image downloaded)", "",
         "Counts are scaled from a random sample (<= %d files per category tree) unless 'exact'. 'files' = unique files listed in the tree "
         "(depth <= %d, <= %d categories, <= %d titles per category); 'catinfo' = sum of the categories' own file counts (double counts "
         "files filed in several categories). low-res = longer side < %d px. usable = (CC0 or PD) and longer side >= %d px."
         % (SAMPLE, DEPTH, MAX_CATS, LIST_CAP, LOW_PX, LOW_PX)]
    cur = None
    for k, r in res["results"].items():
        if r["domain"] != cur:
            cur = r["domain"]
            L += ["", "## " + cur, "", "| category | files (listed) | catinfo | sampled | exact | CC0 | PD | other | low-res | usable | formats | top licences |",
                  "|---|---|---|---|---|---|---|---|---|---|---|---|"]
        if not r.get("exists"):
            L.append("| %s | (category does not exist) |||||||||||" % r["category"])
            continue
        f = lambda n: ("%d" % n) if r["exact"] else "~%d" % n         # noqa: E731
        L.append("| %s | %d%s | %d | %d | %s | %s | %s | %s | %s | %s | %s | %s |" % (
            r["category"], r["unique_files_listed"], "+" if r["listing_truncated"] else "", r["sum_files_categoryinfo"], r["sampled"],
            "yes" if r["exact"] else "no (estimate)", f(r["est_cc0"]), f(r["est_pd"]), f(r["est_other"]), f(r["est_low"]), f(r["est_usable"]),
            ", ".join("%s %d" % kv for kv in sorted(r["mimes"].items(), key=lambda kv: -kv[1])[:4]),
            "; ".join("%s %d" % tuple(kv) for kv in r["licenses"][:5])))
    L += ["", "## samples (file names, 5 each)", ""]
    for k, r in res["results"].items():
        if r.get("exists") and r["samples"]["cc0_or_pd"]:
            L.append("- **%s / %s**: %s" % (r["domain"][2:], r["category"], "; ".join(t[5:] for t in r["samples"]["cc0_or_pd"])))
    (OUT / "domain_probe.md").write_text("\n".join(L) + "\n", encoding="utf-8")


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "check"
    allroots = [(d, c) for d, cs in ROOTS.items() for c in cs]
    if mode == "check":
        info = cat_info([c for _, c in allroots])
        for d, c in allroots:
            print("%-32s %-55s %s" % (d, c, info[c]))
        return
    if mode == "report":
        return report()
    only = sys.argv[2:]
    rng = random.Random(20261011)
    t0 = time.time()
    resfile = OUT / "domain_probe.json"
    res = json.loads(resfile.read_text(encoding="utf-8")) if resfile.exists() else {"results": {}}
    for d, c in allroots:
        if only and d.split()[0] not in only:
            continue
        if f"{d}|{c}" in res["results"]:
            continue
        r = probe(c, rng)
        r["domain"] = d
        res["results"][f"{d}|{c}"] = r
        resfile.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
        print(d, "|", c, "->", {k: r.get(k) for k in ("exists", "unique_files_listed", "cc0_n", "pd_n", "other_n", "usable_n")}, flush=True)
    res["elapsed_s_this_run"] = round(time.time() - t0)
    resfile.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
