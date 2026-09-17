import unreal

bp = unreal.load_asset('/Game/AI/BP_Enemy')
print("DIR BP:")
for d in dir(bp):
    if not d.startswith('_'):
        print(d)
