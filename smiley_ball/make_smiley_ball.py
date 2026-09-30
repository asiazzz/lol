"""Build a yellow smiley-face ball in Blender.

Run from Blender's Text Editor (Alt+P), or headless:
    blender --background --python make_smiley_ball.py
    python make_smiley_ball.py            # with the `bpy` pip module

Writes smiley_ball.blend, smiley_ball.glb and smiley_ball.obj next to this script.
"""
import math
import os

import bpy

OUT_DIR = os.path.dirname(os.path.abspath(__file__))
RADIUS = 1.0


def surface_point(x, z, lift=0.0):
    """Point on the ball's front (-Y) face at screen-space (x, z), pushed out by `lift`."""
    y = -math.sqrt(max(RADIUS * RADIUS - x * x - z * z, 0.0))
    scale = (RADIUS + lift) / RADIUS
    return (x * scale, y * scale, z * scale)


def make_material(name, rgb, roughness):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (*rgb, 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    return mat


# Start from an empty scene.
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene

yellow = make_material("Smiley_Yellow", (0.80, 0.70, 0.0), 0.7)
black = make_material("Smiley_Black", (0.005, 0.005, 0.005), 0.9)

# Ball.
bpy.ops.mesh.primitive_uv_sphere_add(segments=64, ring_count=32, radius=RADIUS, location=(0, 0, 0))
ball = bpy.context.active_object
ball.name = "SmileyBall"
ball.data.materials.append(yellow)
bpy.ops.object.shade_smooth()

parts = []

# Eyes: small vertical ovals sitting on the surface.
for side in (-1, 1):
    x, z = 0.26 * side, 0.22
    bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=12, radius=1.0,
                                         location=surface_point(x, z))
    eye = bpy.context.active_object
    eye.name = "Eye_L" if side < 0 else "Eye_R"
    eye.scale = (0.065, 0.03, 0.105)
    # Tilt the eye so it lies flat against the curved surface.
    eye.rotation_euler = (math.asin(z), 0.0, math.asin(x))
    eye.data.materials.append(black)
    bpy.ops.object.shade_smooth()
    parts.append(eye)

# Smile: a thick curve following a wide "U" across the lower face,
# with small upturned hooks at each end like the reference image.
points = []
steps = 48
for i in range(steps + 1):
    t = -1.0 + 2.0 * i / steps
    x = 0.62 * t
    z = -0.40 + 0.26 * t * t
    points.append((x, z))
for side in (-1, 1):  # end hooks
    hook = [(0.62 * side + 0.03 * side, -0.14 + 0.07), (0.62 * side + 0.02 * side, -0.14 + 0.03)]
    if side < 0:
        points = list(reversed(hook)) + points
    else:
        points = points + hook

curve_data = bpy.data.curves.new("SmileCurve", type="CURVE")
curve_data.dimensions = "3D"
curve_data.bevel_depth = 0.028
curve_data.bevel_resolution = 4
curve_data.use_fill_caps = True
spline = curve_data.splines.new("POLY")
spline.points.add(len(points) - 1)
for p, (x, z) in zip(spline.points, points):
    p.co = (*surface_point(x, z, lift=0.005), 1.0)
smile = bpy.data.objects.new("Smile", curve_data)
scene.collection.objects.link(smile)
smile.data.materials.append(black)
bpy.context.view_layer.objects.active = smile
smile.select_set(True)
bpy.ops.object.convert(target="MESH")
bpy.ops.object.shade_smooth()
parts.append(smile)

# Parent face features to the ball so it moves as one object.
for part in parts:
    part.parent = ball
    part.matrix_parent_inverse = ball.matrix_world.inverted()

# Sit the ball on the ground.
ball.location.z = RADIUS

# Preview staging: ground, sun, camera.
bpy.ops.mesh.primitive_plane_add(size=20, location=(0, 0, 0))
ground = bpy.context.active_object
ground.name = "Ground"
ground.data.materials.append(make_material("Ground_Green", (0.08, 0.25, 0.04), 0.9))

bpy.ops.object.light_add(type="SUN", location=(2, -3, 6))
sun = bpy.context.active_object
sun.data.energy = 3.0
sun.rotation_euler = (math.radians(15), 0, math.radians(10))

world = bpy.data.worlds.new("World")
world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.6, 0.7, 0.9, 1.0)
world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.8
scene.world = world

bpy.ops.object.camera_add(location=(0, -7.0, 1.3), rotation=(math.radians(88), 0, 0))
scene.camera = bpy.context.active_object

# Save and export.
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT_DIR, "smiley_ball.blend"))

bpy.ops.object.select_all(action="DESELECT")
ball.select_set(True)
for part in parts:
    part.select_set(True)
bpy.ops.export_scene.gltf(filepath=os.path.join(OUT_DIR, "smiley_ball.glb"), use_selection=True)
bpy.ops.wm.obj_export(filepath=os.path.join(OUT_DIR, "smiley_ball.obj"), export_selected_objects=True)

print("Wrote smiley_ball.blend / .glb / .obj to", OUT_DIR)
