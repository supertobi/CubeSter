# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

# Original Author = Jacob Morris
# URL = github.com/BlendingJake

bl_info = {
    "name": "CubeSter",
    "author": "Jacob Morris",
    "version": (1, 0, 0),
    "blender": (2, 80, 0),
    "location": "View 3D > Toolbar > CubeSter",
    "description": "Take an image, image sequence, or audio file and use it to generate a cube-based mesh.",
    "category": "Add Mesh"
}

from bpy.types import Scene, PropertyGroup, Object, Panel, Image, Operator
from bpy.props import PointerProperty, EnumProperty, BoolProperty, StringProperty, CollectionProperty, IntProperty, \
    FloatProperty
from bpy.utils import register_class, unregister_class
from bpy import app
from os import walk
from bpy.path import abspath
from pathlib import Path
from typing import List
import bpy
import bmesh


def build_block_mesh_from_heights(context, props, heights: List[list]):
    bpy.ops.mesh.primitive_cube_add()
    bm = bmesh.new()
    bs = props.grid_size
    y = -(len(heights)*bs) / 2

    verts, faces = [], []
    for row in heights:
        x = -(len(heights[0])*bs) / 2

        for height in row:
            p = len(verts)

            verts += [
                (x, y, 0), (x+bs, y, 0), (x+bs, y+bs, 0), (x, y+bs, 0),
                (x, y, height), (x+bs, y, height), (x+bs, y+bs, height), (x, y+bs, height)
            ]

            faces += [
                (p, p+4, p+5, p+1), (p, p+3, p+7, p+4), (p+3, p+2, p+6, p+7), (p+2, p+1, p+5, p+6),
                (p+4, p+7, p+6, p+5), (p, p+1, p+2, p+3)
            ]

            x += bs
        y += bs

    for vert in verts:
        bm.verts.new(vert)
    bm.verts.ensure_lookup_table()

    for face in faces:
        bm.faces.new([bm.verts[i] for i in face])
    bm.faces.ensure_lookup_table()

    bm.to_mesh(context.object.data)
    bm.free()


def build_plane_mesh_from_heights(context, props, heights: List[list]):
    bpy.ops.mesh.primitive_cube_add()
    bm = bmesh.new()
    bs = props.grid_size
    y = -(len(heights)*bs)/2

    verts, faces = [], []
    for row in heights:
        x = -(len(heights[0])*bs)/2

        for height in row:
            verts.append((x, y, height))

            x += bs
        y += bs

    rl = len(heights[0])
    for i in range(len(heights) - 1):
        for j in range(len(heights[0]) - 1):
            pos = (i * rl) + j
            faces.append((pos, pos + 1, pos + 1 + rl, pos + rl))

    for vert in verts:
        bm.verts.new(vert)
    bm.verts.ensure_lookup_table()

    for face in faces:
        bm.faces.new([bm.verts[i] for i in face])
    bm.faces.ensure_lookup_table()

    bm.to_mesh(context.object.data)
    bm.free()


def create_vertex_material():
    mat = bpy.data.materials.new("CubeSter")
    mat.use_nodes = True

    nodes = mat.node_tree.nodes

    att = nodes.new("ShaderNodeAttribute")
    att.location = (-275, 275)
    att.attribute_name = "Col"

    mat.node_tree.links.new(att.outputs[0], nodes["Principled BSDF"].inputs[0])


def color_block_mesh(context, props, colors: List[list]):
    bpy.ops.mesh.vertex_color_add()
    layer = context.object.data.vertex_colors[0].data

    i = 0
    for row in colors:
        for color in row:
            for _ in range(24):  # 6 faces, 4 vertices each
                layer[i].color = color
                i += 1


def color_plane_mesh(context, props, colors: List[list]):
    bpy.ops.mesh.vertex_color_add()
    layer = context.object.data.vertex_colors[0].data

    i = 0
    # there is one less row and column of faces then the number of rows and columns of vertices, so stop one short
    for r in range(len(colors) - 1):
        for c in range(len(colors[0]) - 1):
            for _ in range(4):
                layer[i].color = colors[r][c]
                i += 1


def frame_handler(scene):
    pass


def image_update(_, context):
    props = context.scene.cs_properties

    if "." in props.image.name:
        name = props.image.name[0:props.image.name.rindex(".")]
    else:
        name = props.image.name

    props.image_base_name = name


class CSImageProperties(PropertyGroup):
    filepath: StringProperty()


class CSObjectProperties(PropertyGroup):
    cs_type: EnumProperty(
        name="CubeSter type",
        items=(("none", "None", ""), ("single", "Single", ""), ("sequence", "Sequence", "")),
        default="none"
    )


class CSSceneProperties(PropertyGroup):
    image: PointerProperty(
        name="Image",
        type=Image,
        update=image_update
    )

    is_image_sequence: BoolProperty(
        name="Image Sequence?", default=False
    )

    image_base_name: StringProperty(
        name="Base Image Name"
    )

    image_sequence: CollectionProperty(
        type=CSImageProperties, name="Image Sequence"
    )

    skip_pixels: IntProperty(
        name="Skip Pixels",
        min=0, default=64,
        description="Skip this many pixels in each row and column"
    )

    height: FloatProperty(
        name="Height",
        unit="LENGTH", min=0, default=0.5,
        description="The height of pure white"
    )

    grid_size: FloatProperty(
        name="Grid Size",
        unit="LENGTH", min=0, default=0.01,
        description="The length and width of each block, or the spacing between vertices in the plane"
    )

    invert: BoolProperty(
        name="Invert Heights?", default=False, description="Make black the highest value, not white"
    )

    mesh_type: EnumProperty(
        name="Mesh Type",
        items=(("blocks", "Blocks", ""), ("plane", "Plane", "")),
        description="Whether the mesh is a plane or composed of many blocks"
    )


class CSPanel(Panel):
    bl_idname = "OBJECT_PT_cs_panel"
    bl_label = "CubeSter"
    bl_space_type = "VIEW_3D"
    bl_region_type = "TOOLS"

    def draw(self, context):
        layout = self.layout
        props = context.scene.cs_properties

        layout.template_ID(props, "image", open="image.open")

        layout.separator()
        layout.prop(props, "is_image_sequence", icon="RENDER_RESULT")
        if props.is_image_sequence:
            layout.prop(props, "image_base_name")
            layout.operator("object.cs_load_image_sequence")

        layout.separator()
        box = layout.box()
        box.prop(props, "skip_pixels")
        box.prop(props, "height")
        box.prop(props, "grid_size")

        layout.separator()
        layout.prop(props, "invert")

        layout.separator()
        layout.prop(props, "mesh_type")

        layout.separator()
        layout.operator("object.cs_create_object")


class CSLoadImageSequence(Operator):
    bl_idname = "object.cs_load_image_sequence"
    bl_label = "Load Image Sequence"
    bl_description = "Load CubeSter Image Sequence"

    def execute(self, context):
        props = context.scene.cs_properties
        dir_path = Path(abspath(props.image.filepath)).parent
        props.image_sequence.clear()

        image_files = []
        for _, _, files in walk(dir_path):
            for file in files:
                if file.startswith(props.image_base_name):
                    image_files.append(file)

            break  # only get top-level

        image_files.sort()

        for file in image_files:
            img = props.image_sequence.add()
            img.filepath = str(dir_path / file)

        return {"FINISHED"}


class CSCreateObject(Operator):
    bl_idname = "object.cs_create_object"
    bl_label = "Create Object"
    bl_description = "Create CubeSter Object"

    def execute(self, context):
        props = context.scene.cs_properties

        if not props.is_image_sequence:
            w, h = props.image.size
            channels = props.image.channels
            pixels = list(props.image.pixels)  # 0 = bottom-left corner of image
            sp = props.skip_pixels
            height_factor = props.height / channels

            heights = []
            colors = []
            for r in range(0, h, sp):
                heights.append([])
                colors.append([])
                for c in range(0, w, sp):
                    pos = ((r * w) + c) * channels
                    total = 0

                    for i in range(channels):
                        total += pixels[pos + i]

                    colors[-1].append(pixels[pos:pos+channels])

                    if props.invert:
                        heights[-1].append((channels-total) * height_factor)
                    else:
                        heights[-1].append(total * height_factor)

            if props.mesh_type == "blocks":
                build_block_mesh_from_heights(context, props, heights)
                color_block_mesh(context, props, colors)
            else:
                build_plane_mesh_from_heights(context, props, heights)
                color_plane_mesh(context, props, colors)

            if "CubeSter" not in bpy.data.materials:
                create_vertex_material()

            context.object.cs_properties.cs_type = "single"
            context.object.data.materials.append(bpy.data.materials["CubeSter"])

        return {"FINISHED"}


classes = [
    CSImageProperties,
    CSObjectProperties,
    CSSceneProperties,
    CSPanel, 
    CSLoadImageSequence,
    CSCreateObject
]


def register():
    for cls in classes:
        register_class(cls)

    Scene.cs_properties = PointerProperty(
        name="cs_properties",
        type=CSSceneProperties,
        description="All the scene properties needed for the add-on CubeSter"
    )

    Object.cs_properties = PointerProperty(
        name="cs_properties",
        type=CSObjectProperties,
        description="All the object properties needed for the add-on CubeSter"
    )

    app.handlers.frame_change_pre.append(frame_handler)


def unregister():
    del Scene.cs_properties
    del Object.cs_properties

    for cls in classes:
        unregister_class(cls)

    app.handlers.frame_change_pre.remove(frame_handler)


if __name__ == "__main__":
    register() 