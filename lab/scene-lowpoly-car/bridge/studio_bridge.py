"""Live bridge: run inside Blender's GUI (blender --python studio_bridge.py).
Lets a local script (bl.py) run Python in the open Blender session and take
preview snapshots, so the creator watches the scene change and can edit it too.
Localhost only + shared token. Every exec is an undo step (Ctrl+Z in Blender)."""
import bpy, socket, threading, json, io, contextlib, traceback, queue, os

HOST, PORT, TOKEN = "127.0.0.1", int(os.environ.get("BRIDGE_PORT", 9876)), os.environ["BRIDGE_TOKEN"]
jobs, ns = queue.Queue(), {"bpy": bpy}


def do_exec(req):
    bpy.ops.ed.undo_push(message="agent: " + req.get("note", "exec"))
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        exec(req["code"], ns)
    return {"stdout": out.getvalue(), "result": ns.pop("result", None)}


def do_snap(req):
    sc, r = bpy.context.scene, bpy.context.scene.render
    keep = (sc.camera, r.resolution_x, r.resolution_y, r.resolution_percentage, r.filepath)
    try:
        if req.get("camera"): sc.camera = bpy.data.objects[req["camera"]]
        r.resolution_percentage = 100
        r.resolution_x, r.resolution_y = req.get("w", 960), req.get("h", 540)
        r.filepath = req["out"]
        if req.get("mode", "gl") == "render":
            bpy.ops.render.render(write_still=True)
        else:  # fast viewport-style render from the camera
            area = next(a for w in bpy.context.window_manager.windows for a in w.screen.areas if a.type == "VIEW_3D")
            with bpy.context.temp_override(window=bpy.context.window_manager.windows[0], area=area,
                                           region=next(g for g in area.regions if g.type == "WINDOW")):
                bpy.ops.render.opengl(write_still=True, view_context=False)
    finally:
        sc.camera, r.resolution_x, r.resolution_y, r.resolution_percentage, r.filepath = keep
    return {"out": req["out"]}


def pump():  # main-thread timer: the only place bpy is touched
    while not jobs.empty():
        req, box, done = jobs.get()
        try:
            box["r"] = {"ok": True, **{"exec": do_exec, "snap": do_snap}[req["cmd"]](req)}
        except Exception:
            box["r"] = {"ok": False, "error": traceback.format_exc()}
        done.set()
    return 0.1


def serve():
    s = socket.socket(); s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((HOST, PORT)); s.listen(4)
    while True:
        c, _ = s.accept()
        try:
            req = json.loads(c.makefile().readline())
            if req.get("token") != TOKEN: raise PermissionError("bad token")
            box, done = {}, threading.Event()
            jobs.put((req, box, done)); done.wait(300)
            reply = box.get("r", {"ok": False, "error": "timeout"})
        except Exception as e:
            reply = {"ok": False, "error": repr(e)}
        c.sendall((json.dumps(reply, default=str) + "\n").encode()); c.close()


threading.Thread(target=serve, daemon=True).start()
bpy.app.timers.register(pump, persistent=True)
print(f"[studio_bridge] listening on {HOST}:{PORT}")
