# Drive CAR_Exterior along the closed ring: (re)attaches a Follow Path constraint to CITY_DrivePath and KEYS the
# path's eval_time (one key per frame, from production/timeline.json motionCues). Run after build_city/build_car
# (build_city recreates the car without the constraint); animate.py then reads these keys for wheels/steering.
# Distances are measured from the pickup stop (path start, x=5 y=-2, heading +X); eval_time is in centimetres.
#   frames 1..car_arrive_start     car rolls at the approach speed, out of shot behind the EST camera
#   car_arrive_start..car_stopped  constant deceleration to a stop at the curb (stops exactly at the path start)
#   car_stopped..drive_start       stands at the curb (the human gets in off screen)
#   drive_start..+ACCEL_S          speed follows a smoothstep 0 -> SPEED (no jump), then cruises at SPEED
import bpy, os
exec(open(os.path.join(os.path.dirname(bpy.data.filepath), "scripts", "_anim_util.py")).read())

SPEED = 8.5      # m/s (about 30 km/h)
APPROACH_M = 15  # the car stops 15 m after the point where the cut to the pickup shot happens
ACCEL_S = 3.5    # seconds to reach SPEED

car, path = bpy.data.objects["CAR_Exterior"], bpy.data.objects["CITY_DrivePath"]
L = path["length_m"]
cu = path.data; cu.use_path = True; cu.path_duration = round(L * 100)   # eval_time in centimetres
if cu.animation_data and cu.animation_data.drivers:
    for d in list(cu.animation_data.drivers): cu.animation_data.drivers.remove(d)   # old constant-speed driver
cu.eval_time = 0

for c in [c for c in car.constraints if c.type == "FOLLOW_PATH"]: car.constraints.remove(c)
car.location = (0, 0, 0); car.rotation_mode = "XYZ"; car.rotation_euler = (0, 0, 0)   # the path places it
con = car.constraints.new("FOLLOW_PATH"); con.name = "Drive"
con.target = path; con.use_curve_follow = True
con.forward_axis = "TRACK_NEGATIVE_Y"; con.up_axis = "UP_Z"   # the Kenney car faces its local -Y

act = new_action(cu, "CarPath")
dist = [travelled(f, APPROACH_M, SPEED, ACCEL_S) for f in FRAMES]
key(act, "eval_time", 0, FRAMES, [(L + s) * 100 for s in dist])   # negative s = behind the start (end of the closed loop)
bpy.context.scene.frame_set(1)
result = {"path_m": round(L, 1), "car_at_f1": [round(v, 2) for v in car.matrix_world.translation],
          "dist_m": {f: round(travelled(f, APPROACH_M, SPEED, ACCEL_S), 2) for f in (1, 181, 253, 277, 400, 1335)}}
