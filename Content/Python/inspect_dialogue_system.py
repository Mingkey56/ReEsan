import unreal
import os

output_dir = r"C:\Users\USER\.gemini\antigravity-ide\brain\13100737-4d61-4662-b633-0a9832dc3777\scratch"
os.makedirs(output_dir, exist_ok=True)
log_file = os.path.join(output_dir, "dialogue_inspection.log")

with open(log_file, "w", encoding="utf-8") as out:
    def log(msg):
        print(msg)
        out.write(str(msg) + "\n")
        out.flush()

    log("=== DIALOGUE SYSTEM INSPECTION ===\n")

    # All dialogue-related assets to inspect
    dialogue_assets = [
        # AI folder - NPC and dialogue assets
        '/Game/AI/BP_NPC',
        '/Game/AI/BP_NPC1',
        '/Game/AI/BPI_Dialog',
        '/Game/AI/DT_Dialogue',
        '/Game/AI/F_Choice',
        '/Game/AI/F_Dialogue',
        '/Game/AI/NPCDatatable_Script_-_Untitled',

        # MYDIALOUGE folder - custom dialogue
        '/Game/MYDIALOUGE/W_Conversation',
        '/Game/MYDIALOUGE/W_ChoiceButton',

        # DialogueSystem folder
        '/Game/DialogueSystem/Blueprints/Core/BP_DialogueGameInstance',
        '/Game/DialogueSystem/Blueprints/Structs/ST_DialogueLine',
        '/Game/DialogueSystem/Blueprints/UI/WBP_Subtitles',
        '/Game/DialogueSystem/Blueprints/Enums/E_DialogueDisplayType',
        '/Game/DialogueSystem/Blueprints/Enums/E_DialogueState',
        '/Game/DialogueSystem/Blueprints/Enums/E_DialogueType',
        '/Game/DialogueSystem/Blueprints/Interfaces/BPI_DialogueConversation',
        '/Game/DialogueSystem/Blueprints/Interfaces/BPI_DialogueEvents',
        '/Game/DialogueSystem/Blueprints/Interfaces/BPI_DialogueWidget',
        '/Game/DialogueSystem/Data/Dialogue/Facility27_1',
        '/Game/DialogueSystem/Data/Dialogue/Facility27_2',

        # PureDialogueSystem folder
        '/Game/PureDialogueSystem/Blueprints/BPI_PlayerController',
        '/Game/PureDialogueSystem/Blueprints/BPI_SetCustomFocus',
        '/Game/PureDialogueSystem/Blueprints/BP_PureDialoguePlayerController',
        '/Game/PureDialogueSystem/DialogSystem/BP_DialogComponent',
        '/Game/PureDialogueSystem/DialogSystem/E_DialogTriggers',
        '/Game/PureDialogueSystem/DialogSystem/ST_Dialog',
        '/Game/PureDialogueSystem/DialogSystem/ST_PlayerResponse',
        '/Game/PureDialogueSystem/DialogSystem/WBP_DialogWidget',
        '/Game/PureDialogueSystem/DialogSystem/WBP_PlayerResponse',
        '/Game/PureDialogueSystem/ExampleNPC/BP_NPC1',
        '/Game/PureDialogueSystem/ExampleNPC/BP_NPC2',
        '/Game/PureDialogueSystem/SimpleInteractionSystem/BPI_Interactable',
        '/Game/PureDialogueSystem/SimpleInteractionSystem/BP_InteractionComponent',
        '/Game/PureDialogueSystem/SimpleInteractionSystem/WBP_InteractionWidget',

        # Interactive folder
        '/Game/Interactive/BPI_Interactable',
        '/Game/Interactive/BP_Interact',
        '/Game/Interactive/InteractBP',
        '/Game/Interactive/WBP_InteractPrompt',

        # Player character and controller
        '/Game/FirstPerson/Blueprints/BP_FirstPersonCharacterME',
        '/Game/FirstPerson/Blueprints/BP_FirstPersonPlayerController',
        '/Game/FirstPerson/Blueprints/BP_FirstPersonGameMode',

        # HUD
        '/Game/Hud/PlayerHud',
    ]

    for p in dialogue_assets:
        log("\n" + "=" * 80)
        log(f"ASSET: {p}")

        obj = unreal.load_asset(p)
        if not obj:
            log("*** FAILED TO LOAD ***")
            continue

        obj_class = obj.get_class().get_name()
        log(f"Class: {obj_class}")

        # DataTable inspection
        if isinstance(obj, unreal.DataTable):
            log("--- DataTable Rows ---")
            row_names = unreal.DataTableFunctionLibrary.get_data_table_column_as_string(obj, "")
            log(f"Row names attempt: {row_names}")
            # Try to get row struct
            try:
                row_struct = obj.get_editor_property('row_struct')
                log(f"Row Struct: {row_struct}")
            except:
                pass
            # Get all row names
            try:
                rows = obj.get_editor_property('row_map')
                log(f"Row map: {rows}")
            except:
                pass

        # UserDefinedStruct inspection
        if obj_class in ['UserDefinedStruct', 'ScriptStruct']:
            log("--- Struct Properties ---")
            for prop in dir(obj):
                if not prop.startswith('_'):
                    try:
                        val = getattr(obj, prop)
                        if not callable(val):
                            log(f"  {prop} = {val}")
                    except:
                        pass

        # Blueprint / WidgetBlueprint inspection
        if isinstance(obj, (unreal.Blueprint, unreal.WidgetBlueprint)):
            gen_class = None
            if hasattr(obj, 'generated_class'):
                gen_class = obj.generated_class()

            if gen_class:
                log(f"Generated Class: {gen_class.get_name()}")

                # Parent class
                try:
                    parent = gen_class.get_super_class()
                    log(f"Parent Class: {parent.get_name() if parent else 'None'}")
                    # Go up the chain
                    p = parent
                    chain = []
                    while p:
                        chain.append(p.get_name())
                        p = p.get_super_class()
                    log(f"Class Hierarchy: {' -> '.join(chain)}")
                except:
                    pass

                # CDO - ALL properties, not just filtered ones
                cdo = unreal.get_default_object(gen_class)
                log("--- CDO Properties (all custom) ---")
                builtin_props = set()
                # Get parent CDO props for comparison
                try:
                    parent_class = gen_class.get_super_class()
                    if parent_class:
                        parent_cdo = unreal.get_default_object(parent_class)
                        builtin_props = set(d for d in dir(parent_cdo) if not d.startswith('_'))
                except:
                    pass

                for prop in sorted(dir(cdo)):
                    if prop.startswith('_'):
                        continue
                    # Show properties that are NOT in the parent class (custom ones)
                    if prop not in builtin_props:
                        try:
                            val = getattr(cdo, prop)
                            log(f"  [CUSTOM] {prop} = {val}")
                        except Exception as e:
                            log(f"  [CUSTOM] {prop} = <error: {e}>")

                # Also show dialogue/interact/npc related even if inherited
                for prop in sorted(dir(cdo)):
                    if prop.startswith('_'):
                        continue
                    p_lower = prop.lower()
                    if any(k in p_lower for k in ['dialog', 'interact', 'npc', 'choice', 'convers', 'response', 'widget', 'hud', 'text', 'button']):
                        if prop in builtin_props:
                            try:
                                val = getattr(cdo, prop)
                                log(f"  [INHERITED-RELEVANT] {prop} = {val}")
                            except:
                                pass

            # Components
            log("--- Components in SCS ---")
            scs = obj.get_editor_property('simple_construction_script')
            if scs:
                for node in scs.get_all_nodes():
                    comp_template = node.get_editor_property('component_template')
                    if comp_template:
                        comp_name = comp_template.get_name()
                        comp_class = comp_template.get_class().get_name()
                        log(f"  Component: {comp_name} ({comp_class})")
                        # List all non-builtin props on components
                        for cp in dir(comp_template):
                            if not cp.startswith('_'):
                                cp_lower = cp.lower()
                                if any(k in cp_lower for k in ['dialog', 'interact', 'npc', 'choice', 'collision', 'sphere', 'box', 'overlap']):
                                    try:
                                        val = getattr(comp_template, cp)
                                        if not callable(val):
                                            log(f"    {cp} = {val}")
                                    except:
                                        pass

            # Implemented interfaces
            log("--- Implemented Interfaces ---")
            try:
                interfaces = obj.get_editor_property('implemented_interfaces')
                if interfaces:
                    for iface in interfaces:
                        iface_class = iface.get_editor_property('interface')
                        log(f"  Interface: {iface_class.get_name() if iface_class else 'None'}")
                else:
                    log("  (none)")
            except Exception as e:
                log(f"  Error reading interfaces: {e}")

            # Graph names for understanding logic flow
            log("--- Blueprint Graphs ---")
            for graph_prop in ['uber_graph_pages', 'function_graphs', 'macro_graphs', 'event_graphs']:
                if hasattr(obj, graph_prop):
                    try:
                        graphs = getattr(obj, graph_prop)
                        log(f"  {graph_prop} ({len(graphs)}):")
                        for g in graphs:
                            log(f"    Graph: {g.get_name()}")
                    except Exception as e:
                        log(f"  {graph_prop}: Error - {e}")

        # BlueprintGeneratedClass (for interfaces)
        if obj_class == 'BlueprintGeneratedClass':
            log("--- Interface Functions ---")
            for prop in dir(obj):
                if not prop.startswith('_'):
                    try:
                        val = getattr(obj, prop)
                        if callable(val):
                            log(f"  Function: {prop}")
                    except:
                        pass

    # Also check what GameMode is being used
    log("\n\n" + "=" * 80)
    log("=== GAME MODE & LEVEL CHECK ===")
    try:
        world = unreal.EditorLevelLibrary.get_editor_world()
        if world:
            log(f"Current World: {world.get_name()}")
            settings = world.get_world_settings()
            if settings:
                gm = settings.get_editor_property('default_game_mode')
                log(f"Default GameMode: {gm}")
    except Exception as e:
        log(f"Could not check game mode: {e}")

    # Check project settings for default maps
    log("\n=== PROJECT SETTINGS ===")
    try:
        default_map = unreal.SystemLibrary.get_project_content_directory()
        log(f"Content Dir: {default_map}")
    except:
        pass

    log("\n=== INSPECTION FINISHED ===")
