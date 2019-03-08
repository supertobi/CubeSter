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
    "blender": (2, 78, 0),
    "location": "View 3D > Toolbar > CubeSter",
    "description": "Take an image, image sequence, or audio file and use it to generate a cube-based mesh.",
    "category": "Add Mesh"
    }
    
from bpy.types import Scene, PropertyGroup, Object
from bpy.props import PointerProperty
from bpy.utils import register_class, unregister_class
from bpy import app


class CSObjectProperties(PropertyGroup):
    pass


class CSSceneProperties(PropertyGroup):
    pass


classes = [
    CSObjectProperties,
    CSSceneProperties
]


def frame_handler(scene):
    pass


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