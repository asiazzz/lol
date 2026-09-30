"""Build a yellow smiley-face ball in Blender.

Run from Blender's Text Editor (Alt+P), or headless:
    blender --background --python make_smiley_ball.py
    python make_smiley_ball.py            # with the `bpy` pip module

Writes smiley_ball.blend, smiley_ball.glb and smiley_ball.obj next to this script.

The eyes and smile are thin "paint" layers: 2D outlines extruded toward the
ball and intersected with a shell a hair larger than the ball, so they sit
flush on the curved surface with crisp edges.
"""
import math
import os

import bpy
import bmesh  # must come after bpy

OUT_DIR = os.path.dirname(os.path.abspath(__file__))
RADIUS = 1.0
PAINT_RADIUS = RADIUS * 1.004  # how far the face "paint" sits above the ball

# Face layout in front-view units (x right, z up), ball radius = 1.
EYE_X, EYE_Z = 0.27, 0.22
EYE_W, EYE_H = 0.075, 0.125          # half-width / half-height of each eye
SMILE_HALF_WIDTH = 0.60              # smile spans x in [-0.60, 0.60]
SMILE_BOTTOM, SMILE_RISE = -0.36, 0.27
STROKE = 0.026                       # half-thickness of the smile line
TICK_LEN = 0.055                     # half-length of the end ticks


def make_material(name, rgb, roughness, specular=0.5):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (*rgb, 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Specular IOR Level"].default_value = specular
    return mat


def stroke_outline(centerline, half_width, cap_steps=10):
    """Closed 2D outline of a thick polyline with round caps."""
    def normal(i):
        a = centerline[max(i - 1, 0)]
        b = centerline[min(i + 1, len(centerline) - 1)]
        dx, dz = b[0] - a[0], b[1] - a[1]
        n = math.hypot(dx, dz)
        return (-dz / n, dx / n)

    left, right = [], []
    for i, (x, z) in enumerate(centerline):
        nx, nz = normal(i)
        left.append((x + nx * half_width, z + nz * half_width))
        right.append((x - nx * half_width, z - nz * half_width))

    def cap(center, start_normal):
        # Half circle from +normal round to -normal, bulging forward.
        ang0 = math.atan2(start_normal[1], start_normal[0])
        return [(center[0] + half_width * math.cos(ang0 - math.pi * k / cap_steps),
                 center[1] + half_width * math.sin(ang0 - math.pi * k / cap_steps))
                for k in range(1, cap_steps)]

    end_cap = cap(centerline[-1], normal(len(centerline) - 1))
    nx, nz = normal(0)
    start_cap = cap(centerline[0], (-nx, -nz))
    return left + end_cap + list(reversed(right)) + start_cap


def ellipse_outline(cx, cz, w, h, steps=48):
    return [(cx + w * math.cos(2 * math.pi * k / steps),
             cz + h * math.sin(2 * math.pi * k / steps)) for k in range(steps)]


def prism_from_outline(name, outline):
    """Extrude a 2D outline (x, z) along Y through the front of the ball."""
    mesh = bpy.data.meshes.new(name)
    bm = bmesh.new()
    front = [bm.verts.new((x, -2.0, z)) for x, z in outline]
    back = [bm.verts.new((x, -0.5, z)) for x, z in outline]
    bm.faces.new(front)
    bm.faces.new(list(reversed(back)))
    n = len(outline)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((front[i], front[j], back[j], back[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    return obj


def paint_on_ball(name, outline, shell, material):
    """Turn a 2D outline into a flush decal on the ball's surface."""
    obj = prism_from_outline(name, outline)
    mod = obj.modifiers.new("Paint", "BOOLEAN")
    mod.operation = "INTERSECT"
    mod.solver = "EXACT"
    mod.object = shell
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_apply(modifier=mod.name)
    obj.data.materials.append(material)
    obj.data.shade_smooth()
    return obj


# Start from an empty scene.
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene

yellow = make_material("Smiley_Yellow", (0.78, 0.62, 0.0), 0.45, specular=0.35)
black = make_material("Smiley_Black", (0.004, 0.004, 0.004), 0.55, specular=0.2)

# Ball.
bpy.ops.mesh.primitive_uv_sphere_add(segments=96, ring_count=48, radius=RADIUS)
ball = bpy.context.active_object
ball.name = "SmileyBall"
ball.data.materials.append(yellow)
ball.data.shade_smooth()

# Temporary shell the face features are cut from.
bpy.ops.mesh.primitive_uv_sphere_add(segments=192, ring_count=96, radius=PAINT_RADIUS)
shell = bpy.context.active_object
shell.name = "PaintShell"

parts = []

# Eyes: tall ovals.
for side, label in ((-1, "Eye_L"), (1, "Eye_R")):
    parts.append(paint_on_ball(label, ellipse_outline(EYE_X * side, EYE_Z, EYE_W, EYE_H),
                               shell, black))

# Smile: a wide parabola.
steps = 64
arc = []
for i in range(steps + 1):
    t = -1.0 + 2.0 * i / steps
    arc.append((SMILE_HALF_WIDTH * t, SMILE_BOTTOM + SMILE_RISE * t * t))
parts.append(paint_on_ball("Smile", stroke_outline(arc, STROKE), shell, black))

# Little crossbar ticks at each end of the smile, perpendicular to the curve.
for side, label in ((-1, "SmileTick_L"), (1, "SmileTick_R")):
    ex, ez = arc[0] if side < 0 else arc[-1]
    tx, tz = SMILE_HALF_WIDTH, 2 * SMILE_RISE * side  # d/dt of the arc at t = ±1
    n = math.hypot(tx, tz)
    px, pz = -tz / n, tx / n
    tick = [(ex - px * TICK_LEN, ez - pz * TICK_LEN), (ex + px * TICK_LEN, ez + pz * TICK_LEN)]
    parts.append(paint_on_ball(label, stroke_outline(tick, STROKE * 0.9), shell, black))

bpy.data.objects.remove(shell, do_unlink=True)

# Parent face features to the ball so it moves as one object, then sit it on the ground.
for part in parts:
    part.parent = ball
ball.location.z = RADIUS

# Preview staging: ground, sun, sky, camera.
bpy.ops.mesh.primitive_plane_add(size=40)
ground = bpy.context.active_object
ground.name = "Ground"
ground.data.materials.append(make_material("Ground_Green", (0.10, 0.30, 0.04), 0.9))

bpy.ops.object.light_add(type="SUN", location=(2, -3, 6))
sun = bpy.context.active_object
sun.data.energy = 3.5
sun.data.angle = math.radians(8)
sun.rotation_euler = (math.radians(20), 0, math.radians(20))

world = bpy.data.worlds.new("World")
world.use_nodes = True
bg = world.node_tree.nodes["Background"]
bg.inputs["Color"].default_value = (0.55, 0.70, 1.0, 1.0)
bg.inputs["Strength"].default_value = 0.7
scene.world = world

bpy.ops.object.camera_add(location=(0, -7.0, 1.4), rotation=(math.radians(88), 0, 0))
scene.camera = bpy.context.active_object

# Punchy, saturated colours like the reference (AgX desaturates bright yellow).
scene.view_settings.view_transform = "Standard"
scene.render.engine = "CYCLES"
scene.cycles.samples = 64

# Save and export.
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT_DIR, "smiley_ball.blend"))

bpy.ops.object.select_all(action="DESELECT")
ball.select_set(True)
for part in parts:
    part.select_set(True)
bpy.ops.export_scene.gltf(filepath=os.path.join(OUT_DIR, "smiley_ball.glb"), use_selection=True)
bpy.ops.wm.obj_export(filepath=os.path.join(OUT_DIR, "smiley_ball.obj"), export_selected_objects=True)

print("Wrote smiley_ball.blend / .glb / .obj to", OUT_DIR)
