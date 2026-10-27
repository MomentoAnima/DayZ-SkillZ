---
name: dayz-ce-health-check
description: Audit a DayZ server mission folder's Central Economy files (types, events, spawn positions, limits, zombie territories, spawnable types) for silent-failure problems such as BOMs, unregistered or missing files, typos in usage names, orphaned event children and misnamed zombie zones. Use when loot, vehicles, animals or zombies are not spawning, after merging mod types files, or before pushing economy changes to a live server.
---

# DayZ Central Economy health check

The DayZ CE fails silently. A typo in a usage name, a types file that is not registered, or a BOM at the
start of an XML file makes items stop spawning with no error in the log. This skill runs a read-only audit
of a mission folder and explains how to read the result.

## When to use

- Loot, vehicles, animals, events or zombies are missing or fewer than expected.
- You merged or edited a mod's types, events or spawn files.
- Before copying economy files to a live server (run on the staged copy, then on the live copy after).

## How to run

```
python scripts/ce_validate.py <mission_dir>
```

`<mission_dir>` is the folder that contains `cfgeconomycore.xml`, `cfglimitsdefinition.xml`, `db/`,
`cfgeventspawns.xml` and `env/`. The script only reads. Always run it against a copy or a read-only view
of a live server, never edit live files as part of the check.

## What it checks

| Severity | Check |
|---|---|
| ERROR | UTF-8 BOM, invalid UTF-8, control characters, XML that does not parse |
| ERROR | A file registered in `cfgeconomycore.xml` that does not exist on disk |
| ERROR | A `<usage>` name that is not in `cfglimitsdefinition.xml` (the type never matches any location) |
| ERROR | Non-numeric values in nominal, min, lifetime, restock, quantmin, quantmax or cost |
| WARN | Same class defined twice (compared case-insensitively, as the game does) |
| WARN | `value`, `tag` or `category` names not in the limits file |
| WARN | A type with nominal above 0 but lifetime 0 or missing |
| WARN | Unknown attributes on `<flags>` (typo such as `count_in_hoarm1er`) |
| WARN | Event missing nominal/min/max/active, event min above max, event defined twice |
| WARN | Event child class with no types row (the child cannot spawn) |
| WARN | Zombie zone name with no matching event in `events.xml` (typo, the zone never spawns) |
| WARN | More than 31 usage names in the limits file (usage is stored as bit flags) |
| WARN | A file registered twice in `cfgeconomycore.xml` |
| INFO | Mixed CRLF and LF line endings inside one file |
| INFO | min above nominal, unknown elements in a type, duplicate usage/value/tag inside one type |
| INFO | `cfgeventspawns.xml` lists an event that `events.xml` does not define |
| INFO | Active `Infected*` event with no zones in `zombie_territories.xml` |
| INFO | `cfgspawnabletypes` entry for a class with no types row |

Comments are stripped before checking, so a commented-out registration is correctly treated as absent.

## Reading the result

1. Fix every ERROR first. Each one means the game ignores or chokes on something.
2. WARN items are almost always mistakes; read each before changing it.
3. INFO items are often intended. Vanilla itself reports a few hundred (types with min above a nominal of
   0, events without zones). Judge INFO against what you meant to do, not against zero.

## Rules of thumb when fixing

- Write XML and JSON without a BOM. Keep each file's existing line endings.
- Class names are case-insensitive in the game. Compare them case-insensitively.
- A types file is only read if its folder is registered with a `<ce folder="...">` block in
  `cfgeconomycore.xml`.
- Do not "fix" vanilla quirks you did not cause. Types with nominal 0 and min above 0 and events without
  zones exist in the stock mission.
- Change the file, re-run the check, and confirm the result on the target file itself. A note saying a fix
  was applied is not proof that it was.
- Never guess at a field's meaning. If unsure, find a working example or the mod's documentation first.

## Limits of this check

It validates structure and cross-references. It does not judge balance (nominal and min values), whether
spawn positions sit on valid ground, or whether a mod's scripts read the file. Regex based parsing is used
on purpose so that slightly malformed files still produce a report instead of stopping at the first error.
