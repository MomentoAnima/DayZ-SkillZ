#!/usr/bin/env python3
"""DayZ Central Economy health check.

Usage:  python ce_validate.py <mission_dir>

Reads a mission folder (the one that holds cfgeconomycore.xml and db/) and reports
problems that make the CE silently skip things. Read-only: it never writes to the mission.

Severity:  ERROR = the game will ignore or choke on it    WARN = almost certainly a mistake
           INFO  = unusual, may be intended
"""
import collections
import os
import re
import sys
import xml.dom.minidom as minidom
from xml.parsers.expat import ExpatError

if len(sys.argv) != 2:
    sys.exit(__doc__)
ROOT = sys.argv[1].replace("\\", "/").rstrip("/") + "/"
findings = collections.defaultdict(list)          # (severity, title) -> [detail, ...]


def flag(sev, title, detail):
    findings[(sev, title)].append(detail)


def read(rel):
    p = ROOT + rel
    if not os.path.exists(p):
        return None
    return open(p, encoding="utf-8", errors="replace").read()


def strip_comments(text):
    return re.sub(r"<!--.*?-->", "", text, flags=re.S)


# ---- 1. byte-level checks on every XML/JSON file ------------------------------------------
files = []
for base, dirs, names in os.walk(ROOT):
    dirs[:] = [d for d in dirs if not d.lower().startswith("storage")]     # skip persistence
    for n in names:
        if n.lower().endswith((".xml", ".json")):
            files.append(os.path.join(base, n).replace("\\", "/"))
for p in files:
    rel = p[len(ROOT):]
    raw = open(p, "rb").read()
    if raw[:3] == b"\xef\xbb\xbf":
        flag("ERROR", "UTF-8 BOM (DayZ's XML/JSON parsers choke on it)", rel)
    try:
        raw.decode("utf-8")
    except UnicodeDecodeError as e:
        flag("ERROR", "not valid UTF-8", "%s (byte %d)" % (rel, e.start))
    if re.search(rb"[\x00-\x08\x0b\x0c\x0e-\x1f]", raw):
        flag("ERROR", "control characters in file", rel)
    crlf = raw.count(b"\r\n")
    lf = raw.count(b"\n") - crlf
    if crlf and lf:
        flag("INFO", "mixed CRLF/LF line endings (harmless to the parser, awkward for tools)", "%s (CRLF %d / LF %d)" % (rel, crlf, lf))
    if p.lower().endswith(".xml"):
        try:
            minidom.parseString(raw)
        except ExpatError as e:
            flag("ERROR", "XML does not parse", "%s: %s" % (rel, e))

# ---- 2. limits ------------------------------------------------------------------------------
lim = strip_comments(read("cfglimitsdefinition.xml") or "")
LIMITS = {k: set(re.findall(r'<%s name="([^"]+)"' % k, lim)) for k in ("usage", "value", "tag", "category")}
if len(LIMITS["usage"]) > 31:
    flag("WARN", "usage list has more than 31 names (DayZ stores usage as bit flags)", str(len(LIMITS["usage"])))
for k, v in collections.Counter(re.findall(r'<usage name="([^"]+)"', lim)).items():
    if v > 1:
        flag("WARN", "usage name listed twice in cfglimitsdefinition.xml", k)

# ---- 3. economy core registrations (comments are ignored) -----------------------------------
eco = strip_comments(read("cfgeconomycore.xml") or "")
registered = []                                   # (folder, file, type)
for folder, body in re.findall(r'<ce folder="([^"]+)">(.*?)</ce>', eco, re.S):
    for name, kind in re.findall(r'<file name="([^"]+)" type="([^"]+)"', body):
        registered.append((folder, name, kind))
        if not os.path.exists(ROOT + folder + "/" + name):
            flag("ERROR", "registered file is missing on disk", "%s/%s (%s)" % (folder, name, kind))
for k, v in collections.Counter((f, n) for f, n, _ in registered).items():
    if v > 1:
        flag("WARN", "file registered twice", "/".join(k))

# ---- 4. types -------------------------------------------------------------------------------
KNOWN = {"nominal", "lifetime", "restock", "min", "quantmin", "quantmax", "cost", "flags", "category", "usage", "value", "tag"}
FLAGS = {"count_in_cargo", "count_in_hoarder", "count_in_map", "count_in_player", "crafted", "deloot"}
types = {}
type_files = ["db/types.xml"] + [f + "/" + n for f, n, k in registered if k == "types"]
for rel in type_files:
    text = read(rel)
    if text is None:
        continue
    for name, body in re.findall(r'<type name="([^"]+)">(.*?)</type>', strip_comments(text), re.S):
        key = name.lower()                          # DayZ class names are case-insensitive
        if key in types:
            flag("WARN", "class defined twice (case-insensitive)", "%s in %s and %s" % (name, types[key], rel))
        types[key] = rel
        for tag in set(re.findall(r"<(\w+)[\s/>]", body)) - KNOWN:
            flag("INFO", "unknown element inside a type", "<%s> in %s: %s" % (tag, rel, name))
        num = {}
        for field in ("nominal", "min", "lifetime", "restock", "quantmin", "quantmax", "cost"):
            m = re.search(r"<%s>(.*?)</%s>" % (field, field), body, re.S)
            if m:
                if not re.fullmatch(r"\s*-?\d+\s*", m.group(1)):
                    flag("ERROR", "non-numeric value", "%s: %s <%s>%s" % (rel, name, field, m.group(1)[:20]))
                else:
                    num[field] = int(m.group(1))
        if "nominal" in num and "min" in num and num["min"] > num["nominal"]:
            flag("INFO", "min is higher than nominal", "%s: %s (%d > %d)" % (rel, name, num["min"], num["nominal"]))
        if num.get("nominal", 0) > 0 and num.get("lifetime", 1) <= 0:
            flag("WARN", "spawns (nominal>0) but lifetime is 0 or missing", "%s: %s" % (rel, name))
        for kind in ("usage", "value", "tag", "category"):
            seen = re.findall(r'<%s name="([^"]+)"' % kind, body)
            for item in seen:
                if item not in LIMITS[kind]:
                    flag("ERROR" if kind == "usage" else "WARN", "%s name is not in cfglimitsdefinition.xml (never matches)" % kind, "%s: %s -> %s" % (rel, name, item))
            for item, count in collections.Counter(seen).items():
                if count > 1:
                    flag("INFO", "same %s listed twice in one type" % kind, "%s: %s -> %s" % (rel, name, item))
        flag_tag = re.search(r"<flags([^>]*)/?>", body)
        if flag_tag:
            for attr in re.findall(r"(\w+)=", flag_tag.group(1)):
                if attr not in FLAGS:
                    flag("WARN", "unknown attribute in <flags> (typo?)", "%s: %s -> %s" % (rel, name, attr))

# ---- 5. events ------------------------------------------------------------------------------
events = {}
text = strip_comments(read("db/events.xml") or "")
for name, body in re.findall(r'<event name="([^"]+)">(.*?)</event>', text, re.S):
    if name in events:
        flag("WARN", "event defined twice in events.xml", name)
    events[name] = body
    for field in ("nominal", "min", "max", "active"):
        if not re.search(r"<%s>" % field, body):
            flag("WARN", "event is missing <%s>" % field, name)
    mn, mx = re.search(r"<min>(-?\d+)", body), re.search(r"<max>(-?\d+)", body)
    if mn and mx and int(mn.group(1)) > int(mx.group(1)):
        flag("WARN", "event min is greater than max", name)
    for child in re.findall(r'<child [^>]*type="([^"]+)"', body):
        if child.lower() not in types:
            flag("WARN", "event child has no types row (it cannot spawn)", "%s -> %s" % (name, child))

spawns = strip_comments(read("cfgeventspawns.xml") or "")
spawn_names = re.findall(r'<event name="([^"]+)"', spawns)
for n in spawn_names:
    if n not in events:
        flag("INFO", "cfgeventspawns.xml lists an event that events.xml does not define", n)
for n, c in collections.Counter(spawn_names).items():
    if c > 1:
        flag("WARN", "event listed twice in cfgeventspawns.xml", n)

# ---- 6. zombie territories <-> infected events ----------------------------------------------
zones = strip_comments(read("env/zombie_territories.xml") or "")
zone_names = collections.Counter(re.findall(r'<zone name="([^"]+)"', zones))
for n, c in zone_names.items():
    if n not in events:
        flag("WARN", "zombie zone name has no matching event (typo? it never spawns)", "%s (%d zones)" % (n, c))
for n, body in events.items():
    if n.startswith("Infected") and re.search(r"<active>1", body) and n not in zone_names:
        flag("INFO", "active Infected event has no zones in zombie_territories.xml", n)

# ---- 7. spawnable types ---------------------------------------------------------------------
sp_files = ["cfgspawnabletypes.xml"] + [f + "/" + n for f, n, k in registered if k == "spawnabletypes"]
for rel in sp_files:
    text = read(rel)
    if text is None:
        continue
    for cls in re.findall(r'<type name="([^"]+)"', strip_comments(text)):
        if cls.lower() not in types:
            flag("INFO", "spawnabletypes entry for a class with no types row", "%s: %s" % (rel, cls))

# ---- report ---------------------------------------------------------------------------------
print("mission: %s | %d types in %d files | %d events | %d zone names" % (ROOT, len(types), len(type_files), len(events), len(zone_names)))
order = {"ERROR": 0, "WARN": 1, "INFO": 2}
if not findings:
    print("no findings")
for (sev, title), details in sorted(findings.items(), key=lambda kv: (order[kv[0][0]], -len(kv[1]))):
    print("\n[%s] %s: %d" % (sev, title, len(details)))
    for d in details[:8]:
        print("    ", d)
    if len(details) > 8:
        print("     ... +%d more" % (len(details) - 8))
print("\nsummary: %s" % ", ".join("%s %d" % (s, sum(len(v) for (sv, _), v in findings.items() if sv == s)) for s in ("ERROR", "WARN", "INFO")))
