from src.preprocess.zones import xy_to_zone

print(xy_to_zone(0, 0))        # should be zone_0
print(xy_to_zone(120, 80))     # last zone
print(xy_to_zone(60, 40))      # middle