import bpy, bmesh
o=bpy.data.objects["HUM_Body"]; rig=bpy.data.objects["RIG_Human"]
bm=bmesh.new(); bm.from_mesh(o.data); bm.verts.ensure_lookup_table()
W={s: rig.data.bones[f"hand.{s}"].head_local for s in "LR"}  # wrists
E={s: rig.data.bones[f"forearm.{s}"].head_local for s in "LR"}  # elbows
for R in (0.08,0.10,0.12,0.15):
    # local patch: verts within R of the hands' midpoint; plus never through elbows
    mid=(W["L"]+W["R"])/2 + (rig.data.bones["hand.L"].tail_local+rig.data.bones["hand.R"].tail_local)/2; mid/=2
    patch={v.index for v in bm.verts if (v.co-mid).length<R}
    def comp(seed):
        st=[seed]; seen={seed}
        while st:
            a=st.pop()
            for e in bm.verts[a].link_edges:
                b=e.other_vert(bm.verts[a]).index
                if b in patch and b not in seen: seen.add(b); st.append(b)
        return seen
    seeds={s: min(patch, key=lambda i:(bm.verts[i].co-W[s]).length) for s in "LR"}
    cl=comp(seeds["L"])
    print("INFO R=%.2f patch %d verts; L-wrist piece %d verts; contains R-wrist vertex: %s; dist seeds to wrists L %.3f R %.3f"%(R,len(patch),len(cl),seeds["R"] in cl,(bm.verts[seeds['L']].co-W['L']).length,(bm.verts[seeds['R']].co-W['R']).length))
