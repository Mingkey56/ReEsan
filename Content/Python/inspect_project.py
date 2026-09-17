import unreal

def inspect_asset(path):
    print("=" * 70)
    print(f"INSPECTING ASSET: {path}")
    asset = unreal.load_asset(path)
    if not asset:
        print(f"FAILED TO LOAD: {path}")
        return
    print(f"Asset Type: {type(asset).__name__}")
    
    # If Blueprint
    if isinstance(asset, unreal.Blueprint):
        gen_class = asset.generated_class()
        print(f"Generated Class: {gen_class.get_name() if gen_class else 'None'}")
        if gen_class:
            cdo = unreal.get_default_object(gen_class)
            print("CDO Properties:")
            for prop in dir(cdo):
                if not prop.startswith('_'):
                    try:
                        val = getattr(cdo, prop)
                        # Filter standard engine props
                        if any(k in prop.lower() for k in ['attack', 'stun', 'crosshair', 'hud', 'dialog', 'interact', 'health', 'range', 'talisman', 'tailsman', 'movement']):
                            print(f"  {prop} = {val}")
                    except Exception:
                        pass

        # Inspect components
        print("Components in SCS:")
        scs = asset.get_editor_property('simple_construction_script')
        if scs:
            for node in scs.get_all_nodes():
                comp_template = node.get_editor_property('component_template')
                if comp_template:
                    print(f"  Component: {comp_template.get_name()} ({comp_template.get_class().get_name()})")

    # Let's also check if we can inspect widget blueprint
    elif isinstance(asset, unreal.WidgetBlueprint):
        print(f"Widget Blueprint: {asset.get_name()}")

print("--- STARTING REESAN ASSET INSPECTION ---")
inspect_asset('/Game/AI/BP_Enemy')
inspect_asset('/Game/AI/BP_NPC')
inspect_asset('/Game/WeaponSystem/BP_Crosshair')
inspect_asset('/Game/WeaponSystem/BP_Tailsman')
inspect_asset('/Game/FirstPerson/Blueprints/BP_FirstPersonCharacterME')
inspect_asset('/Game/Hud/PlayerHud')
print("--- FINISHED REESAN ASSET INSPECTION ---")
