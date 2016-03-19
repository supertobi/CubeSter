#This program is free software: you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation, either version 3 of the License, or
#(at your option) any later version.
#
#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.
#
#You should have received a copy of the GNU General Public License
#along with this program.  If not, see <http://www.gnu.org/licenses/>.

#Original Author = Jacob Morris
#URL = blendingjacob.blogspot.com

bl_info = {
    "name" : "CubeSter",
    "author" : "Jacob Morris",
    "version" : (0, 1, 1),
    "blender" : (2, 76, 0),
    "location" : "View 3D > Toolbar > CubeSter",
    "description" : "Takes image and converts it into a height map based on pixel color and alpha values",
    "category" : "Add Mesh"
    }
    
import bpy
from bpy.props import BoolProperty, IntProperty, FloatProperty, StringProperty
import timeit 
from random import uniform

#load image if needed
def adjustSelectedImage(self, context):
    scene = context.scene
    try:
        image = bpy.data.images.load(scene.cubester_load_image)
        scene.cubester_image = image.name
    except:
        print("CubeSter: " + scene.cubester_load_image + " could not be loaded")

#scene properties
bpy.types.Scene.cubester_invert = BoolProperty(name = "Invert Height?", default = False)
bpy.types.Scene.cubester_skip_pixels = IntProperty(name = "Skip # Pixels", min = 0, max = 256, default = 64, description = "Skip this number of pixels before placing the next")
bpy.types.Scene.cubester_size_per_hundred_pixels = FloatProperty(name = "Size Per 100 Blocks", subtype =  "DISTANCE", min = 0.001, max = 2, default = 1)
bpy.types.Scene.cubester_height_scale = FloatProperty(name = "Height Scale", subtype = "DISTANCE", min = 0.1, max = 2, default = 0.2)
bpy.types.Scene.cubester_image = StringProperty(default = "", name = "") 
bpy.types.Scene.cubester_load_image = StringProperty(default = "", name = "Load Image", subtype = "FILE_PATH", update = adjustSelectedImage) 

#advanced
bpy.types.Scene.cubester_advanced = BoolProperty(name = "Advanved Options?")
bpy.types.Scene.cubester_random_weights = BoolProperty(name = "Random Weights?")
bpy.types.Scene.cubester_weight_r = FloatProperty(name = "Red", subtype = "FACTOR", min = 0, max = 1.0, default = 0.25)
bpy.types.Scene.cubester_weight_g = FloatProperty(name = "Green", subtype = "FACTOR", min = 0, max = 1.0, default = 0.25)
bpy.types.Scene.cubester_weight_b = FloatProperty(name = "Blue", subtype = "FACTOR", min = 0, max = 1.0, default = 0.25)
bpy.types.Scene.cubester_weight_a = FloatProperty(name = "Alpha", subtype = "FACTOR", min = 0, max = 1.0, default = 0.25)

class CubeSterPanel(bpy.types.Panel):
    bl_idname = "OBJECT_PT.cubester"
    bl_label = "CubeSter"
    bl_space_type = "VIEW_3D"
    bl_region_type = "TOOLS"
    bl_category = "Tools"      
    
    def draw(self, context):
        layout = self.layout 
        scene = bpy.context.scene
        layout.label("Image To Convert:")
        layout.prop_search(scene, "cubester_image", bpy.data, "images")
        layout.prop(scene, "cubester_load_image")
        layout.separator()
        
        layout.prop(scene, "cubester_skip_pixels")
        layout.prop(scene, "cubester_size_per_hundred_pixels")
        layout.prop(scene, "cubester_height_scale")
        layout.prop(scene, "cubester_invert", icon = "FILE_REFRESH")                 
        
        layout.separator()
        layout.operator("mesh.cubester", icon = "OBJECT_DATA")       
        
        if scene.cubester_image in bpy.data.images:
            rows = int(bpy.data.images[scene.cubester_image].size[1] / (scene.cubester_skip_pixels + 1))
            columns = int(bpy.data.images[scene.cubester_image].size[0] / (scene.cubester_skip_pixels + 1))            
            layout.label("Approximate Cube Count: " + str(rows * columns))
            
            time = rows * columns * 0.000062873 + 0.10637 #approximate time count
            time_mod = "s"
            if time > 60: #convert to minutes if needed
                time /= 60
                time_mod = "min"
            time = round(time, 3)
            layout.label("Expected Time: " + str(time) + " " + time_mod)
            
            #expected vert/face count
            layout.label("Expected # Verts/Faces: " + str(rows * columns * 8) + " / " + str(rows * columns * 6))
            
        #advanced
        layout.separator()
        layout.prop(scene, "cubester_advanced", icon = "TRIA_DOWN")    
        if bpy.context.scene.cubester_advanced:
            layout.prop(scene, "cubester_random_weights", icon = "RNDCURVE")
            layout.separator()
            
            if not bpy.context.scene.cubester_random_weights:
                box = layout.box()
                box.label("RGBA Channel Weights", icon = "COLOR")
                box.prop(scene, "cubester_weight_r")
                box.prop(scene, "cubester_weight_g")
                box.prop(scene, "cubester_weight_b")
                box.prop(scene, "cubester_weight_a")
    
class CubeSter(bpy.types.Operator):
    bl_idname = "mesh.cubester"
    bl_label = "Generate Mesh"
    bl_options = {"REGISTER", "UNDO"}  
    
    def execute(self, context): 
        scene = bpy.context.scene
        picture = bpy.data.images[scene.cubester_image]
        pixels = list(picture.pixels)
        
        x_pixels = picture.size[0] / (scene.cubester_skip_pixels + 1)
        y_pixels = picture.size[1] / (scene.cubester_skip_pixels + 1)

        width = x_pixels / 100 * scene.cubester_size_per_hundred_pixels
        height = y_pixels / 100 * scene.cubester_size_per_hundred_pixels

        step_x = width / x_pixels
        step_y = height / y_pixels
        hx = step_x / 2
        hy = step_y / 2

        y = -height / 2 + step_y / 2

        verts, faces = [], []
        vert_colors = []

        start = timeit.default_timer()                 

        #go through each row of pixels stepping by scene.cubester_skip_pixels + 1
        for row in range(0, picture.size[1], scene.cubester_skip_pixels + 1):           
            x = -width / 2 + step_x / 2 #reset to left edge of mesh
            #go through each column, step by appropriate amount
            for column in range(0, picture.size[0] * 4, 4 + scene.cubester_skip_pixels * 4):        
                i = (row * picture.size[0] * 4) + column #determin i position to start at based on row and column position             
                pixs = pixels[i:i+4]       
                r = pixs[0]
                g = pixs[1]
                b = pixs[2] 
                a = pixs[3]
                
                if a != 0: #if not completely transparent
                    vert_colors += [(r, g, b) for i in range(24)]
                    normalize = 1
                    
                    #channel weighting
                    if not scene.cubester_advanced:
                        composed = 0.25 * r + 0.25 * g + 0.25 * b + 0.25 * a
                        total = 1
                    else:
                        if not scene.cubester_random_weights:
                            composed = scene.cubester_weight_r * r + scene.cubester_weight_g * g + scene.cubester_weight_b * b + scene.cubester_weight_a * a
                            total = scene.cubester_weight_r + scene.cubester_weight_g + scene.cubester_weight_b + scene.cubester_weight_a
                            normalize = 1 / total
                        else:
                            weights = [uniform(0.0, 1.0) for i in range(4)]
                            composed = weights[0] * r + weights[1] * g + weights[2] * b + weights[3] * a
                            total = weights[0] + weights[1] + weights[2] + weights[3] 
                            normalize = 1 / total  
                            
                    if scene.cubester_invert:
                        h = (1 - composed) * scene.cubester_height_scale * normalize
                    else:
                        h = composed * scene.cubester_height_scale * normalize

                    p = len(verts)              
                    verts += [(x - hx, y - hy, 0.0), (x + hx, y - hy, 0.0), (x + hx, y + hy, 0.0), (x - hx, y + hy, 0.0)]  
                    verts += [(x - hx, y - hy, h), (x + hx, y - hy, h), (x + hx, y + hy, h), (x - hx, y + hy, h)]  
                    
                    faces += [(p, p+1, p+5, p+4), (p+1, p+2, p+6, p+5), (p+2, p+3, p+7, p+6), (p, p+4, p+7, p+3), (p+4, p+5, p+6, p+7),
                        (p, p+3, p+2, p+1)]
                    
                x += step_x
                
            y += step_y
                  
        mesh = bpy.data.meshes.new("cubed")
        mesh.from_pydata(verts, [], faces)
        ob = bpy.data.objects.new("cubed", mesh)  
        bpy.context.scene.objects.link(ob) 
        bpy.context.scene.objects.active = ob        
        ob.select = True
        
        #material
        if context.scene.render.engine == "CYCLES":
            if "CubeSter" in bpy.data.materials:
                ob.data.materials.append(bpy.data.materials["CubeSter"])
            else:
                mat = bpy.data.materials.new("CubeSter")
                mat.use_nodes = True
                nodes = mat.node_tree.nodes            
                att = nodes.new("ShaderNodeAttribute")
                att.attribute_name = "Col"
                att.location = (-200, 300)
                mat.node_tree.links.new(nodes["Attribute"].outputs[0], nodes["Diffuse BSDF"].inputs[0])
                ob.data.materials.append(mat)

        #vertex colors
        bpy.ops.mesh.vertex_color_add()        
        i = 0
        for c in ob.data.vertex_colors[0].data:
            c.color = vert_colors[i]
            i += 1

        stop = timeit.default_timer() 
        print(str(int(len(verts) / 8)) + " in " + str(stop - start))               
        return {"FINISHED"}               
        
def register():
    bpy.utils.register_module(__name__)   
    
def unregister():
    bpy.utils.unregister_module(__name__)
    
if __name__ == "__main__":
    register() 