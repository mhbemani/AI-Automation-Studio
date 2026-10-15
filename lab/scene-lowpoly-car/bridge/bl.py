#!/usr/bin/env python3
"""Client for studio_bridge.py.
  bl.py exec 'print(len(bpy.data.objects))'      run code in the open Blender
  bl.py file script.py                            run a script file
  bl.py snap out.png [Camera] [--render]          preview image (default: fast viewport render)
Prints stdout / result; exits 1 on error."""
import socket, json, sys, os
here = os.path.dirname(os.path.abspath(__file__))
tok = open(os.path.join(here, ".token")).read().strip()
a = sys.argv[1:]
if a[0] == "exec": req = {"cmd": "exec", "code": a[1]}
elif a[0] == "file": req = {"cmd": "exec", "code": open(a[1]).read(), "note": os.path.basename(a[1])}
elif a[0] == "snap":
    req = {"cmd": "snap", "out": os.path.abspath(a[1]), "mode": "render" if "--render" in a else "gl"}
    cams = [x for x in a[2:] if not x.startswith("--")]
    if cams: req["camera"] = cams[0]
else: sys.exit(__doc__)
req["token"] = tok
s = socket.create_connection(("127.0.0.1", int(os.environ.get("BRIDGE_PORT", 9876))), timeout=330)
s.sendall((json.dumps(req) + "\n").encode())
r = json.loads(s.makefile().readline())
if not r["ok"]: sys.exit(r["error"])
print(r.get("stdout", "") + (f"result: {r['result']}" if r.get("result") is not None else r.get("out", "")))
