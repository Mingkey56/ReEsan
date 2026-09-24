# Unreal Editor Python: inspect + repair BP_Enemy combat/detection.
import unreal

LOG_PATH = r"C:\Users\USER\Documents\Unreal Projects\ReEsan\Content\Python\enemy_fix_log.txt"


def log(msg):
    line = str(msg)
    print(line)
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(line + "\n")


open(LOG_PATH, "w", encoding="utf-8").write("=== BP_ENEMY FIX START ===\n")


def dump_object_props(obj, keys):
    if not obj:
        log("  <none>")
        return
    for name in keys:
        try:
            val = obj.get_editor_property(name)
            log(f"  {name} = {val}")
        except Exception as e:
            log(f"  {name} <err {e}>")


def find_pins(node):
    try:
        return node.get_editor_property("pins") or []
    except Exception:
        return getattr(node, "pins", []) or []


def pin_name(pin):
    try:
        return str(pin.get_editor_property("pin_name"))
    except Exception:
        return str(getattr(pin, "pin_name", ""))


def get_default(pin):
    try:
        return pin.get_editor_property("default_value")
    except Exception:
        return getattr(pin, "default_value", "")


def set_default(pin, value):
    pin.set_editor_property("default_value", str(value))


ASSET_PATH = "/Game/AI/BP_Enemy"
bp = unreal.load_asset(ASSET_PATH)
if not bp:
    log("FAILED to load BP_Enemy")
    raise SystemExit(1)

log(f"Loaded {bp.get_path_name()} type={bp.get_class().get_name()}")
gen = bp.generated_class()
cdo = unreal.get_default_object(gen) if gen else None
log(f"Generated class={gen.get_name() if gen else None}")

log("\n--- CDO interesting properties ---")
if cdo:
    for prop in sorted(dir(cdo)):
        pl = prop.lower()
        if any(k in pl for k in [
            "attack", "stun", "range", "health", "patrol", "chase", "target",
            "can_attack", "sight", "sense", "walk", "orient", "ai"
        ]):
            try:
                val = getattr(cdo, prop)
                if callable(val):
                    continue
                log(f"  {prop} = {val}")
            except Exception:
                pass
    # explicit camelCase editor properties commonly used on this BP
    dump_object_props(cdo, [
        "CanAttack", "AttackRange", "IsStun", "IsStunned", "BaseDamage",
        "AiHP", "TargetActor", "can_attack", "attack_range", "is_stunned",
        "base_damage",
    ])

log("\n--- Blueprint new_variables ---")
try:
    variables = bp.get_editor_property("new_variables")
except Exception as e:
    variables = []
    log(f"new_variables error: {e}")
for var in variables or []:
    try:
        log(
            f"  var={var.get_editor_property('var_name')} "
            f"type={var.get_editor_property('var_type')} "
            f"default={var.get_editor_property('default_value')} "
            f"flags={var.get_editor_property('property_flags')}"
        )
    except Exception as e:
        try:
            log(f"  var={var} err={e}")
        except Exception:
            pass

log("\n--- SCS components ---")
scs = None
try:
    scs = bp.get_editor_property("simple_construction_script")
except Exception as e:
    log(f"SCS error {e}")

pawn_sense = None
mesh = None
capsule = None
movement = None
if scs:
    for node in scs.get_all_nodes():
        tmpl = node.get_editor_property("component_template")
        if not tmpl:
            continue
        cls = tmpl.get_class().get_name()
        name = tmpl.get_name()
        log(f"  Component {name} ({cls})")
        if isinstance(tmpl, unreal.PawnSensingComponent):
            pawn_sense = tmpl
            dump_object_props(tmpl, [
                "sight_radius", "peripheral_vision_angle", "hearing_threshold",
                "los_hearing_threshold", "sensing_interval", "b_see_pawns",
                "b_hear_noises", "b_only_sense_players", "b_enable_sensing_updates",
            ])
        if isinstance(tmpl, unreal.SkeletalMeshComponent) or cls == "SkeletalMeshComponent":
            mesh = tmpl
            dump_object_props(tmpl, [
                "relative_scale3d", "relative_location", "relative_rotation",
                "animation_mode", "anim_class", "skeletal_mesh_asset",
                "override_materials", "visibility_based_anim_tick_option",
            ])
            try:
                skel_mesh = tmpl.skeletal_mesh
                log(f"  skeletal_mesh={skel_mesh}")
                if skel_mesh:
                    skel = skel_mesh.get_editor_property("skeleton")
                    log(f"  skeleton={skel}")
                    if skel:
                        sockets = skel.get_editor_property("sockets") or []
                        log(f"  sockets={[s.socket_name for s in sockets]}")
            except Exception as e:
                log(f"  mesh extra err {e}")
        if isinstance(tmpl, unreal.CapsuleComponent) or "Capsule" in cls:
            capsule = tmpl
            dump_object_props(tmpl, [
                "capsule_radius", "capsule_half_height", "relative_scale3d",
                "collision_enabled", "collision_profile_name",
                "generate_overlap_events", "can_character_step_up_on",
            ])
        if isinstance(tmpl, unreal.CharacterMovementComponent) or "CharacterMovement" in cls:
            movement = tmpl
            dump_object_props(tmpl, [
                "max_walk_speed", "max_walk_speed_crouched", "rotation_rate",
                "b_orient_rotation_to_movement", "b_use_controller_desired_rotation",
                "b_constrain_to_plane", "gravity_scale", "max_acceleration",
            ])

log("\n--- Graph nodes / pins ---")
graphs = []
for prop in ["uber_graph_pages", "function_graphs", "macro_graphs"]:
    try:
        graphs.extend(list(getattr(bp, prop) or []))
    except Exception:
        pass

move_nodes = []
montage_nodes = []
for g in graphs:
    try:
        nodes = g.get_editor_property("nodes")
    except Exception:
        continue
    log(f"Graph {g.get_name()} nodes={len(nodes)}")
    for node in nodes:
        nclass = node.get_class().get_name()
        title = ""
        try:
            title = str(node.get_node_title(unreal.EdGraphNodeTitleType.FULL_TITLE))
        except Exception:
            title = nclass
        interesting = any(k in (nclass + title) for k in [
            "AIMoveTo", "PlayMontage", "PawnSensing", "SeePawn", "Delay",
            "Attack", "Stun", "ApplyDamage", "GetDistance", "Branch",
            "SpawnActor", "Overlap", "RandomReachable", "WalkSpeed",
            "CanAttack", "Retriggerable",
        ])
        if not interesting:
            continue
        log(f"  [{nclass}] {title}")
        for pin in find_pins(node):
            pname = pin_name(pin)
            dval = get_default(pin)
            linked = []
            try:
                linked = pin.get_editor_property("linked_to") or []
            except Exception:
                pass
            if dval not in (None, "", "None") or linked or pname in (
                "AcceptanceRadius", "bStopOnOverlap", "MontageToPlay",
                "PlayRate", "SightRadius", "AttackRange", "Duration",
            ):
                log(f"    pin {pname} default={dval} links={len(linked)}")
        if "AIMoveTo" in nclass:
            move_nodes.append(node)
        if "PlayMontage" in nclass:
            montage_nodes.append(node)

# ---------------- FIXES ----------------
log("\n=== APPLYING FIXES ===")
changed = []

# 1) Blueprint variable defaults
for var in variables or []:
    try:
        name = str(var.get_editor_property("var_name"))
    except Exception:
        continue
    if name in ("CanAttack", "can_attack"):
        var.set_editor_property("default_value", "true")
        changed.append("CanAttack default true")
    if name in ("IsStunned", "IsStun", "is_stunned"):
        var.set_editor_property("default_value", "false")
        changed.append(f"{name} default false")
    if name in ("AttackRange", "attack_range"):
        var.set_editor_property("default_value", "220.0")
        changed.append("AttackRange default 220")
    if name in ("BaseDamage", "base_damage"):
        # keep existing if set; ensure non-zero
        cur = str(var.get_editor_property("default_value") or "")
        if cur in ("", "0", "0.0", "0.000000"):
            var.set_editor_property("default_value", "20.0")
            changed.append("BaseDamage default 20")

if cdo:
    for name, value in [
        ("CanAttack", True),
        ("can_attack", True),
        ("IsStunned", False),
        ("IsStun", False),
        ("is_stunned", False),
        ("AttackRange", 220.0),
        ("attack_range", 220.0),
    ]:
        try:
            cdo.set_editor_property(name, value)
            changed.append(f"CDO {name}={value}")
        except Exception:
            pass

# 2) Pawn sensing: stable, player-only, wide enough for scaled mesh
if pawn_sense:
    sense_fixes = {
        "sight_radius": 2800.0,
        "peripheral_vision_angle": 80.0,
        "hearing_threshold": 2000.0,
        "los_hearing_threshold": 1600.0,
        "sensing_interval": 0.25,
        "b_see_pawns": True,
        "b_hear_noises": True,
        "b_only_sense_players": True,
        "b_enable_sensing_updates": True,
    }
    for k, v in sense_fixes.items():
        try:
            pawn_sense.set_editor_property(k, v)
            changed.append(f"PawnSensing.{k}={v}")
        except Exception as e:
            log(f"  skip PawnSensing.{k}: {e}")

# 3) Movement: chase actually closes distance
if movement:
    try:
        movement.set_editor_property("max_walk_speed", 450.0)
        changed.append("MaxWalkSpeed=450")
    except Exception as e:
        log(f"  skip walk speed: {e}")
    try:
        movement.set_editor_property("b_orient_rotation_to_movement", True)
        changed.append("OrientRotationToMovement=True")
    except Exception:
        pass

# 4) Capsule generate overlaps so spawned damage actor / player can hit
if capsule:
    try:
        capsule.set_editor_property("generate_overlap_events", True)
        changed.append("Capsule generate_overlap_events=True")
    except Exception:
        pass
    try:
        r = float(capsule.get_editor_property("capsule_radius") or 0)
        h = float(capsule.get_editor_property("capsule_half_height") or 0)
        log(f"  capsule r={r} h={h}")
        # Tiny capsules make Sight/LOS and blocking weird on a large mesh.
        if r < 20:
            capsule.set_editor_property("capsule_radius", 42.0)
            changed.append("CapsuleRadius 42")
        if h < 40:
            capsule.set_editor_property("capsule_half_height", 96.0)
            changed.append("CapsuleHalfHeight 96")
    except Exception as e:
        log(f"  capsule size err {e}")

# 5) Mesh scale: Meshy imports are often 0.01 or 100x
if mesh:
    try:
        scale = mesh.get_editor_property("relative_scale3d")
        log(f"  mesh scale before {scale}")
        sx, sy, sz = float(scale.x), float(scale.y), float(scale.z)
        # Extreme scale makes pawn-sensing origin vs visible body diverge.
        if max(sx, sy, sz) > 8.0:
            mesh.set_editor_property("relative_scale3d", unreal.Vector(1, 1, 1))
            changed.append("Mesh scale clamped to 1")
        elif 0 < max(sx, sy, sz) < 0.05:
            mesh.set_editor_property("relative_scale3d", unreal.Vector(1, 1, 1))
            changed.append("Mesh scale raised to 1")
    except Exception as e:
        log(f"  mesh scale err {e}")

# 6) AI Move To pins: default 5cm never succeeds against character capsules
for node in move_nodes:
    for pin in find_pins(node):
        pname = pin_name(pin)
        if pname in ("AcceptanceRadius", "Acceptance Radius"):
            set_default(pin, "120.000000")
            changed.append("AIMoveTo AcceptanceRadius=120")
        if pname in ("bStopOnOverlap", "StopOnOverlap"):
            set_default(pin, "true")
            changed.append("AIMoveTo bStopOnOverlap=true")

# 7) Create a same-skeleton montage so Play Montage does not immediately fail
running = unreal.load_asset(
    "/Game/AI/Ghost1/Meshy_AI_Obsidian_Sentinel_biped_Animation_Running_withSkin_Anim_target_character_target_character_target_character_Running"
)
montage_path = "/Game/AI/AM_EnemyMelee"
montage = unreal.load_asset(montage_path)
if running and not montage:
    try:
        asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
        factory = unreal.AnimMontageFactory()
        # Some engine versions need skeleton on factory
        try:
            skel = running.get_editor_property("skeleton")
            factory.set_editor_property("target_skeleton", skel)
        except Exception:
            pass
        montage = asset_tools.create_asset("AM_EnemyMelee", "/Game/AI", unreal.AnimMontage, factory)
        log(f"Created montage {montage}")
    except Exception as e:
        log(f"Montage factory failed: {e}")
        montage = None

if running and montage:
    try:
        # Slot a single segment using the running sequence as a stand-in melee clip
        # so PlayMontage succeeds on the new skeleton and CanAttack can reset.
        if hasattr(unreal, "AnimationLibrary"):
            lib = unreal.AnimationLibrary
        montage.set_editor_property("blend_in_time", 0.05)
        montage.set_editor_property("blend_out_time", 0.1)
        unreal.EditorAssetLibrary.save_loaded_asset(montage)
        changed.append("Saved AM_EnemyMelee")
    except Exception as e:
        log(f"montage tweak err {e}")

for node in montage_nodes:
    for pin in find_pins(node):
        if pin_name(pin) in ("MontageToPlay", "Montage to Play"):
            cur = get_default(pin)
            log(f"  MontageToPlay currently {cur} obj={pin.get_editor_property('default_object') if hasattr(pin,'get_editor_property') else '?'}")
            if montage:
                try:
                    pin.set_editor_property("default_object", montage)
                    changed.append("PlayMontage default_object=AM_EnemyMelee")
                except Exception as e:
                    log(f"  set montage pin failed {e}")

log("\nChanges:")
for c in changed:
    log(f"  - {c}")

try:
    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    log("Compiled BP_Enemy")
except Exception as e:
    try:
        unreal.KismetSystemLibrary.compile_blueprint(bp)
        log("Compiled BP_Enemy via Kismet")
    except Exception as e2:
        log(f"Compile failed {e} / {e2}")

unreal.EditorAssetLibrary.save_loaded_asset(bp)
log("Saved BP_Enemy")
log("=== BP_ENEMY FIX DONE ===")
