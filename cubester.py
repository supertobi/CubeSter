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
    
from bpy.types import Scene, PropertyGroup
from bpy.props import PointerProperty
from bpy.utils import register_class, unregister_class


class CSProperties(PropertyGroup):
    pass


classes = [
    CSProperties
]


def register():
    for cls in classes:
        register_class(cls)

    Scene.cs_properties = PointerProperty(
        name="cs_properties",
        type=CSProperties,
        description="All the properties needed for the add-on CubeSter"
    )


def unregister():
    del Scene.cs_properties

    for cls in classes:
        unregister_class(cls)


if __name__ == "__main__":
    register() 