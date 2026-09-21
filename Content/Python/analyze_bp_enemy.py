#!/usr/bin/env python3
"""Offline binary analysis of BP_Enemy.uasset (and related)."""
import os
import re
import struct
from collections import Counter

ROOT = r"C:\Users\USER\Documents\Unreal Projects\ReEsan"
ASSETS = [
    os.path.join(ROOT, r"Content\AI\BP_Enemy.uasset"),
    os.path.join(ROOT, r"Content\AI\BP_Enemy1.uasset"),
    os.path.join(ROOT, r"Content\AI\BP_NPC.uasset"),
]

KEYWORDS = [
    b"Attack", b"CanAttack", b"Detect", b"Sight", b"Sense", b"Range",
    b"Radius", b"PawnSensing", b"AIPerception", b"Perception",
    b"Chase", b"Patrol", b"Stun", b"Damage", b"Montage", b"AIMoveTo",
    b"MoveTo", b"Player", b"Target", b"Overlap", b"Sphere", b"Capsule",
    b"Collision", b"Ignore", b"Block", b"Trace", b"LineOfSight",
    b"Hearing", b"FOV", b"Peripheral", b"MaxAge", b"Stimulus",
    b"Blackboard", b"Behavior", b"StateTree", b"EQS", b"CanSee",
    b"OnSeePawn", b"SeePawn", b"Heard", b"Team", b"Affiliation",
    b"Hostile", b"Enemy", b"AcceptableRadius", b"AcceptanceRadius",
    b"StopDistance", b"AttackRange", b"DetectionRange", b"Aggro",
    b"Idle", b"Combat", b"IsAttacking", b"PlayAnim", b"AnimMontage",
    b"ApplyDamage", b"TakeDamage", b"Health", b"Dead", b"IsDead",
    b"Timer", b"Delay", b"Branch", b"Sequence", b"SetTimer",
    b"GetPlayer", b"GetActorOfClass", b"GetAllActors",
    b"AddOnScreenDebug", b"PrintString", b"DrawDebug",
    b"GenerateOverlap", b"OnComponentBeginOverlap",
    b"OnComponentEndOverlap", b"SetCollision", b"CollisionEnabled",
    b"QueryOnly", b"NoCollision", b"Pawn", b"Visibility",
    b"WorldDynamic", b"CustomDepth", b"CanEverAffectNavigation",
    b"UseControllerRotation", b"OrientRotation", b"MaxWalkSpeed",
    b"SightRadius", b"LoseSight", b"DetectNeutral", b"DetectFriendlies",
    b"DetectEnemies", b"Affiliation", b"SenseConfig",
]

INTERESTING_FNAMES = re.compile(
    rb"(Attack|Detect|Sight|Sense|Range|Radius|Chase|Patrol|Stun|"
    rb"Perception|Overlap|Sphere|Target|Player|Health|Montage|"
    rb"AIMove|MoveTo|CanSee|SeePawn|Hearing|Aggro|Combat|Idle|"
    rb"Collision|Ignore|Trace|Damage|Dead|Timer|Blackboard|"
    rb"Behavior|StateTree|Acceptance|StopDistance|FOV|Peripheral)",
    re.I,
)


def printable_runs(data, min_len=3):
    return [(m.start(), m.group(0).decode("ascii", "ignore"))
            for m in re.finditer(rb"[\x20-\x7E]{%d,}" % min_len, data)]


def dump_keyword_contexts(data, path, out):
    out.append(f"\n===== FILE {os.path.basename(path)} size={len(data)} =====")
    found = {}
    for kw in KEYWORDS:
        idxs = []
        pos = 0
        while True:
            i = data.find(kw, pos)
            if i < 0:
                break
            idxs.append(i)
            pos = i + 1
            if len(idxs) >= 40:
                break
        if idxs:
            found[kw.decode()] = idxs
    out.append("Keyword hit counts:")
    for k, idxs in sorted(found.items(), key=lambda x: -len(x[1])):
        out.append(f"  {k}: {len(idxs)}")

    out.append("\n--- Keyword contexts ---")
    for k, idxs in sorted(found.items()):
        for i in idxs[:8]:
            chunk = data[max(0, i - 80): min(len(data), i + 160)]
            clean = "".join(chr(b) if 32 <= b <= 126 else "." for b in chunk)
            out.append(f"  [{k} @{i}] {clean}")


def dump_interesting_strings(data, out):
    strs = printable_runs(data, 4)
    interesting = []
    for pos, s in strs:
        if INTERESTING_FNAMES.search(s.encode("ascii", "ignore")):
            interesting.append((pos, s))
    out.append(f"\n--- Interesting strings ({len(interesting)}) ---")
    seen = set()
    for pos, s in interesting:
        if s in seen:
            continue
        seen.add(s)
        out.append(f"  @{pos}: {s}")


def dump_float_near_keywords(data, out):
    out.append("\n--- Float32 values near range/radius/sight keywords ---")
    keys = [b"Range", b"Radius", b"Sight", b"Detect", b"Acceptable",
            b"Sphere", b"Hearing", b"FOV", b"Peripheral", b"Speed",
            b"Health", b"Damage", b"Delay", b"Timer", b"Distance"]
    for kw in keys:
        pos = 0
        n = 0
        while n < 6:
            i = data.find(kw, pos)
            if i < 0:
                break
            window = data[i:i + 256]
            floats = []
            for off in range(0, len(window) - 4, 4):
                f = struct.unpack_from("<f", window, off)[0]
                if 0.01 <= abs(f) <= 100000 and abs(f) not in (1.0, 0.5, -1.0):
                    # skip nan/inf already handled by range
                    if abs(f) > 1e-3:
                        floats.append((off, f))
            # keep plausible gameplay numbers
            plausible = [f"{off}:{f:.4g}" for off, f in floats
                         if 0.05 <= abs(f) <= 20000]
            out.append(f"  {kw.decode()} @{i} floats={plausible[:12]}")
            pos = i + 1
            n += 1


def dump_k2_nodes(data, out):
    nodes = re.findall(rb"K2Node_[A-Za-z0-9_]+", data)
    c = Counter(n.decode() for n in nodes)
    out.append("\n--- K2Node type counts ---")
    for name, cnt in c.most_common():
        out.append(f"  {name}: {cnt}")


def dump_custom_events_and_funcs(data, out):
    out.append("\n--- CustomFunctionName nearby ---")
    for m in re.finditer(rb"CustomFunctionName", data):
        chunk = data[m.start(): m.start() + 180]
        names = [s.decode("ascii") for s in re.findall(rb"[\x20-\x7E]{3,}", chunk)]
        out.append("  " + " | ".join(names))
    out.append("\n--- MemberName nearby ---")
    seen = set()
    for m in re.finditer(rb"MemberName", data):
        chunk = data[m.start(): m.start() + 120]
        names = tuple(s.decode("ascii") for s in re.findall(rb"[\x20-\x7E]{3,}", chunk))
        if names not in seen:
            seen.add(names)
            out.append("  " + " | ".join(names))


def compare_assets(a, b, out):
    sa = set(s for _, s in printable_runs(a, 4))
    sb = set(s for _, s in printable_runs(b, 4))
    out.append("\n===== STRING DIFF BP_Enemy vs BP_Enemy1 =====")
    only_a = sorted(sa - sb)
    only_b = sorted(sb - sa)
    out.append(f"only Enemy ({len(only_a)}):")
    for s in only_a:
        if INTERESTING_FNAMES.search(s.encode("ascii", "ignore")) or True:
            if len(s) < 80:
                out.append("  - " + s)
    out.append(f"only Enemy1 ({len(only_b)}):")
    for s in only_b:
        if len(s) < 80:
            out.append("  + " + s)


def main():
    lines = []
    blobs = {}
    for p in ASSETS:
        if not os.path.exists(p):
            lines.append(f"MISSING {p}")
            continue
        with open(p, "rb") as f:
            data = f.read()
        blobs[os.path.basename(p)] = data
        dump_keyword_contexts(data, p, lines)
        dump_interesting_strings(data, lines)
        dump_float_near_keywords(data, lines)
        dump_k2_nodes(data, lines)
        dump_custom_events_and_funcs(data, lines)

    if "BP_Enemy.uasset" in blobs and "BP_Enemy1.uasset" in blobs:
        compare_assets(blobs["BP_Enemy.uasset"], blobs["BP_Enemy1.uasset"], lines)

    outp = os.path.join(ROOT, r"Content\Python\bp_enemy_analysis.txt")
    with open(outp, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print("Wrote", outp, "lines", len(lines))


if __name__ == "__main__":
    main()
