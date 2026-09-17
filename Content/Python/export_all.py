import unreal
import os
import sys

output_dir = r"C:\Users\USER\.gemini\antigravity-ide\brain\c54d1529-2d52-47d2-877a-2c5cdc1f32a5\scratch"
log_file = os.path.join(output_dir, "ue_inspection.log")

with open(log_file, "w", encoding="utf-8") as out:
    def log(msg):
        print(msg)
        out.write(str(msg) + "\n")
        out.flush()

    log("=== STARTING BLUEPRINT INSPECTION ===")

    assets = [
        '/Game/AI/BP_Enemy',
        '/Game/AI/BP_NPC',
        '/Game/WeaponSystem/BP_Crosshair',
        '/Game/WeaponSystem/BP_Tailsman',
        '/Game/FirstPerson/Blueprints/BP_FirstPersonCharacterME',
        '/Game/Hud/PlayerHud',
        '/Game/MYDIALOUGE/W_Conversation',
        '/Game/PureDialogueSystem/DialogSystem/BP_DialogComponent',
        '/Game/PureDialogueSystem/SimpleInteractionSystem/BP_InteractionComponent'
    ]

    for p in assets:
        log("\n" + "="*80)
        log(f"ASSET: {p}")
        obj = unreal.load_asset(p)
        if not obj:
            log("FAILED TO LOAD")
            continue

        log(f"Class: {obj.get_class().get_name()}")

        # Try exporting to text
        asset_name = os.path.basename(p)
        txt_path = os.path.join(output_dir, f"{asset_name}.txt")
        task = unreal.AssetExportTask()
        task.object = obj
        task.filename = txt_path
        task.selected = False
        task.replace_identical = True
        task.prompt = False
        task.automated = True
        try:
            success = unreal.Exporter.run_asset_export_task(task)
            log(f"Export task success: {success}, size: {os.path.getsize(txt_path) if os.path.exists(txt_path) else 0}")
        except Exception as e:
            log(f"Export error: {e}")

        # If it has generated class, inspect CDO
        gen_class = None
        if hasattr(obj, 'generated_class'):
            gen_class = obj.generated_class()
        elif hasattr(obj, 'get_blueprint_class'):
            gen_class = obj.get_blueprint_class()

        if gen_class:
            log(f"Generated Class: {gen_class.get_name()}")
            cdo = unreal.get_default_object(gen_class)
            log("--- CDO Properties ---")
            for prop in dir(cdo):
                if prop.startswith('_'):
                    continue
                try:
                    val = getattr(cdo, prop)
                    # Check if custom property or interesting property
                    p_lower = prop.lower()
                    if any(k in p_lower for k in ['attack', 'stun', 'crosshair', 'hud', 'dialog', 'interact', 'health', 'range', 'talisman', 'tailsman', 'movement', 'patrol', 'chase', 'enemy', 'npc', 'widget']):
                        log(f"  {prop} = {val}")
                except Exception:
                    pass

        # Inspect graphs
        for graph_prop in ['uber_graph_pages', 'function_graphs', 'macro_graphs']:
            if hasattr(obj, graph_prop):
                try:
                    graphs = getattr(obj, graph_prop)
                    log(f"--- {graph_prop} ({len(graphs)}) ---")
                    for g in graphs:
                        log(f"  Graph: {g.get_name()}")
                        # Nodes
                        if hasattr(g, 'nodes'):
                            nodes = g.get_editor_property('nodes')
                            log(f"    Nodes count: {len(nodes)}")
                            for node in nodes:
                                title = ""
                                try:
                                    title = node.get_node_title(unreal.EdGraphNodeTitleType.FULL_TITLE)
                                except:
                                    pass
                                log(f"      [{node.get_class().get_name()}] {node.get_name()} : '{title}'")
                except Exception as e:
                    log(f"Error inspecting {graph_prop}: {e}")

    log("\n=== INSPECTION FINISHED ===")
