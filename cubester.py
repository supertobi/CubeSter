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
    "version" : (0, 4),
    "blender" : (2, 76, 0),
    "location" : "View 3D > Toolbar > CubeSter",
    "description" : "Takes image or image sequence and converts it into a height map based on pixel color and alpha values",
    "category" : "Add Mesh"
    }
    
import bpy
from bpy.props import BoolProperty, IntProperty, FloatProperty, StringProperty, EnumProperty
import timeit 
from random import uniform
import bmesh
import os
from bpy import path

#load image if possible
def adjustSelectedImage(self, context):
    scene = context.scene
    try:
        image = bpy.data.images.load(scene.cubester_load_image)
        scene.cubester_image = image.name
    except:
        print("CubeSter: " + scene.cubester_load_image + " could not be loaded")

#load color image if possible        
def adjustSelectedColorImage(self, context):
    scene = context.scene
    try:
        image = bpy.data.images.load(scene.cubester_load_color_image)
        scene.cubester_color_image = image.name
    except:
        print("CubeSter: " + scene.cubester_load_color_image + " could not be loaded")        
        
#if already loaded return image, else load and return
def fetchImage(name, load_path):
    if name in bpy.data.images:
        return bpy.data.images[name]
    else:
        try:
            image = bpy.data.images.load(load_path)
            return image
        except:
            print("CubeSter: " + load_path + " could not be loaded")
            return None            

#crate block at center position x, y with block width 2*hx and 2*hy and height of h    
def createBlock(x, y, hx, hy, h, verts, faces):
    p = len(verts)              
    verts += [(x - hx, y - hy, 0.0), (x + hx, y - hy, 0.0), (x + hx, y + hy, 0.0), (x - hx, y + hy, 0.0)]  
    verts += [(x - hx, y - hy, h), (x + hx, y - hy, h), (x + hx, y + hy, h), (x - hx, y + hy, h)]  
    
    faces += [(p, p+1, p+5, p+4), (p+1, p+2, p+6, p+5), (p+2, p+3, p+7, p+6), (p, p+4, p+7, p+3), (p+4, p+5, p+6, p+7),
        (p, p+3, p+2, p+1)]
 
#generate uv map for object       
def createUVMap(context, rows, columns):
    mesh = context.object.data
    mesh.uv_textures.new("cubester")
    bm = bmesh.new()
    bm.from_mesh(mesh)
    
    uv_layer = bm.loops.layers.uv[0]
    bm.faces.ensure_lookup_table()
    
    x_scale = 1 / columns
    y_scale = 1 / rows
    
    y_pos = 0.0
    x_pos = 0.0
    count = columns - 1 #hold current count to compare to if need to go to next row
    
    #if blocks
    if context.scene.cubester_mesh_style == "blocks":              
        for fa in range(int(len(bm.faces) / 6)):        
            for i in range(6):
                pos = (fa * 6) + i
                bm.faces[pos].loops[0][uv_layer].uv = (x_pos, y_pos)
                bm.faces[pos].loops[1][uv_layer].uv = (x_pos + x_scale, y_pos)                    
                bm.faces[pos].loops[2][uv_layer].uv = (x_pos + x_scale, y_pos + y_scale)
                bm.faces[pos].loops[3][uv_layer].uv = (x_pos, y_pos + y_scale)
                        
            x_pos += x_scale
            
            if fa >= count:            
                y_pos += y_scale
                x_pos = 0.0
                count += columns
    
    #if planes
    else:
        for fa in range(len(bm.faces)):
            bm.faces[fa].loops[0][uv_layer].uv = (x_pos, y_pos)
            bm.faces[fa].loops[1][uv_layer].uv = (x_pos + x_scale, y_pos)                    
            bm.faces[fa].loops[2][uv_layer].uv = (x_pos + x_scale, y_pos + y_scale)
            bm.faces[fa].loops[3][uv_layer].uv = (x_pos, y_pos + y_scale) 
            
            x_pos += x_scale 
            
            if fa >= count:            
                y_pos += y_scale
                x_pos = 0.0
                count += columns  
                    
    bm.to_mesh(mesh) 
    
#find all images that would belong to sequence
def findSequenceImages(context):
    scene = context.scene
    images = [[], []]
    
    if scene.cubester_image in bpy.data.images:
        image = bpy.data.images[scene.cubester_image]
        main = image.name.split(".")[0]
        exstention = image.name.split(".")[1]
        
        #first part of name to check against other files
        length = len(main)
        keep_going = True
        for i in range(len(main) - 1, -1, -1):
            if main[i].isdigit() and keep_going:
                length -= 1
            else:
                keep_going = not keep_going
        name = main[0:length]
        
        dir_name = os.path.dirname(path.abspath(image.filepath))
        for file in os.listdir(dir_name):
            if os.path.isfile(os.path.join(dir_name, file)) and file.startswith(name):
                images[0].append(os.path.join(dir_name, file))
                images[1].append(file)
        
    return images

#find height for point
def findPointHeight(r, g, b, a, scene):        
    if a != 0: #if not completely transparent                    
        normalize = 1
        
        #channel weighting
        if not scene.cubester_advanced:
            composed = 0.25 * r + 0.25 * g + 0.25 * b + 0.25 * a
            total = 1
        else:
            #user defined weighting
            if not scene.cubester_random_weights:
                composed = scene.cubester_weight_r * r + scene.cubester_weight_g * g + scene.cubester_weight_b * b + scene.cubester_weight_a * a
                total = scene.cubester_weight_r + scene.cubester_weight_g + scene.cubester_weight_b + scene.cubester_weight_a
                normalize = 1 / total
            #random weighting
            else:                           
                composed = weights[0] * r + weights[1] * g + weights[2] * b + weights[3] * a
                total = weights[0] + weights[1] + weights[2] + weights[3] 
                normalize = 1 / total  
                
        if scene.cubester_invert:
            h = (1 - composed) * scene.cubester_height_scale * normalize
        else:
            h = composed * scene.cubester_height_scale * normalize
    
        return h
    
    else:
        return -1
    
#get the RGBA values from pixel
def getPixelValues(picture, pixels, row, column):
    i = (row * picture.size[0] * 4) + column #determin i position to start at based on row and column position             
    pixs = pixels[i:i+4]       
    r = pixs[0]
    g = pixs[1]
    b = pixs[2] 
    a = pixs[3]
    
    return r, g, b, a   

#frame change handler for materials
def materialFrameHandler(scene):
    frame = scene.frame_current
    
    for ob in bpy.data.objects:
        if ob.type == "MESH" and ob.name in scene.cubester_vertex_colors:
            object = scene.cubester_vertex_colors[ob.name]
            colors = object["frames"]
            skip_frames = object["frame_skip"]
            max = object["total_images"]            
                                   
            if frame % skip_frames == 0 and frame < max * skip_frames:
                use_frame = int(frame / skip_frames)
                color = colors[use_frame]                                                
                
                i = 0
                for c in ob.data.vertex_colors[0].data:
                    c.color = color[i]
                    i += 1

#main properties
#image
bpy.types.Scene.cubester_load_type = EnumProperty(name = "Input Type", items = (("single", "Single Image", ""), ("multiple", "Image Sequence", "")))
bpy.types.Scene.cubester_image = StringProperty(default = "", name = "") 
bpy.types.Scene.cubester_load_image = StringProperty(default = "", name = "Load Image", subtype = "FILE_PATH", update = adjustSelectedImage) 
bpy.types.Scene.cubester_skip_images = IntProperty(name = "Skip # Images", min = 0, max = 30, default = 0, description = "Skip this number of images before using one")
bpy.types.Scene.cubester_max_images = IntProperty(name = "Max Number Of Images", min = 2, max = 100, default = 10, description = "Maximum number of images to be used")
bpy.types.Scene.cubester_frame_step = IntProperty(name = "Frame Step Size", min = 1, max = 10, default = 4, description = "The number of frames each picture is used")
#look adjustments
bpy.types.Scene.cubester_invert = BoolProperty(name = "Invert Height?", default = False)
bpy.types.Scene.cubester_skip_pixels = IntProperty(name = "Skip # Pixels", min = 0, max = 256, default = 64, description = "Skip this number of pixels before placing the next")
bpy.types.Scene.cubester_size_per_hundred_pixels = FloatProperty(name = "Size Per 100 Blocks/Points", subtype =  "DISTANCE", min = 0.001, max = 5, default = 1)
bpy.types.Scene.cubester_height_scale = FloatProperty(name = "Height Scale", subtype = "DISTANCE", min = 0.1, max = 2, default = 0.2)
bpy.types.Scene.cubester_mesh_style = EnumProperty(name = "Mesh Type", items = (("blocks", "Blocks", ""), ("plane", "Plane", "")), description = "Compose mesh of multiple blocks or of a single plane")
#material based stuff
bpy.types.Scene.cubester_materials = EnumProperty(name = "Material", items = (("vertex", "Vertex Colors", ""), ("image", "Image", "")), description = "Color on a block by block basis with vertex colors, or uv unwrap and use an image")
bpy.types.Scene.cubester_use_image_color = BoolProperty(name = "Use Original Image Colors'?", default = True, description = "Use the original image for colors, otherwise specify an image to use for the colors")
bpy.types.Scene.cubester_color_image = StringProperty(default = "", name = "") 
bpy.types.Scene.cubester_load_color_image = StringProperty(default = "", name = "Load Color Image", subtype = "FILE_PATH", update = adjustSelectedColorImage) 
bpy.types.Scene.cubester_vertex_colors = {}
#advanced
bpy.types.Scene.cubester_advanced = BoolProperty(name = "Advanced Options?")
bpy.types.Scene.cubester_random_weights = BoolProperty(name = "Random Weights?")
bpy.types.Scene.cubester_weight_r = FloatProperty(name = "Red", subtype = "FACTOR", min = 0.01, max = 1.0, default = 0.25)
bpy.types.Scene.cubester_weight_g = FloatProperty(name = "Green", subtype = "FACTOR", min = 0.01, max = 1.0, default = 0.25)
bpy.types.Scene.cubester_weight_b = FloatProperty(name = "Blue", subtype = "FACTOR", min = 0.01, max = 1.0, default = 0.25)
bpy.types.Scene.cubester_weight_a = FloatProperty(name = "Alpha", subtype = "FACTOR", min = 0.01, max = 1.0, default = 0.25)

class CubeSterPanel(bpy.types.Panel):
    bl_idname = "OBJECT_PT.cubester"
    bl_label = "CubeSter"
    bl_space_type = "VIEW_3D"
    bl_region_type = "TOOLS"
    bl_category = "Tools"      
    
    def draw(self, context):
        layout = self.layout.box() 
        scene = bpy.context.scene
        
        box = layout.box()
        box.prop(scene, "cubester_load_type")        
        box.label("Image To Convert:")
        box.prop_search(scene, "cubester_image", bpy.data, "images")
        box.prop(scene, "cubester_load_image")
        layout.separator()
        
        #find number of approriate images if sequence
        if scene.cubester_load_type == "multiple":
            box = layout.box()
            #display number of images found there            
            images = findSequenceImages(context)
            if len(images[0]) > 0:
                box.label(str(len(images[0])) + " Images Found", icon = "PACKAGE")
            box.prop(scene, "cubester_max_images")
            box.prop(scene, "cubester_skip_images")
            box.prop(scene, "cubester_frame_step")
                
            layout.separator()
        
        box = layout.box()
        box.prop(scene, "cubester_skip_pixels")
        box.prop(scene, "cubester_size_per_hundred_pixels")
        box.prop(scene, "cubester_height_scale")
        box.prop(scene, "cubester_invert", icon = "FILE_REFRESH")                 
        
        layout.separator()
        box = layout.box()
        box.prop(scene, "cubester_mesh_style", icon = "MESH_GRID")        
        box.prop(scene, "cubester_materials", icon = "MATERIAL")
        
        #if using uvs for image, then give option to use different image for color
        if scene.cubester_materials == "image":
            box.separator()
            box.prop(scene, "cubester_use_image_color", icon = "COLOR")
            
            if not scene.cubester_use_image_color:
                box.label("Image To Use For Colors:")
                box.prop_search(scene, "cubester_color_image", bpy.data, "images")
                box.prop(scene, "cubester_load_color_image")   
        
        layout.separator()
        layout.operator("mesh.cubester", icon = "OBJECT_DATA")       
        
        if scene.cubester_image in bpy.data.images:
            layout.separator()
            box = layout.box()
            rows = int(bpy.data.images[scene.cubester_image].size[1] / (scene.cubester_skip_pixels + 1))
            columns = int(bpy.data.images[scene.cubester_image].size[0] / (scene.cubester_skip_pixels + 1))
            
            if scene.cubester_mesh_style == "blocks":           
                box.label("Approximate Cube Count: " + str(rows * columns))
            else:
                box.label("Approximate Point Count: " + str(rows * columns))
            
            #blocks and plane time values
            if scene.cubester_mesh_style == "blocks":
                slope = 0.0000876958
                intercept = 0.02501
            else:
                slope = 0.000017753
                intercept = 0.04201
            
            time = rows * columns * slope + intercept #approximate time count for mesh
                
            time_mod = "s"
            if time > 60: #convert to minutes if needed
                time /= 60
                time_mod = "min"
            time = round(time, 3)
            box.label("Expected Time: " + str(time) + " " + time_mod)
            
            #expected vert/face count
            if scene.cubester_mesh_style == "blocks":           
                box.label("Expected # Verts/Faces: " + str(rows * columns * 8) + " / " + str(rows * columns * 6))
            else:
                box.label("Expected # Verts/Faces: " + str(rows * columns) + " / " + str(rows * (columns - 1)))           
            
        #advanced
        layout.separator()
        box = layout.box()
        box.prop(scene, "cubester_advanced", icon = "TRIA_DOWN")    
        if bpy.context.scene.cubester_advanced:
            box.prop(scene, "cubester_random_weights", icon = "RNDCURVE")
            box.separator()
            
            if not bpy.context.scene.cubester_random_weights:                
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
        weights = [uniform(0.0, 1.0) for i in range(4)] #random weights  
        rows = 0             

        #go through each row of pixels stepping by scene.cubester_skip_pixels + 1
        for row in range(0, picture.size[1], scene.cubester_skip_pixels + 1): 
            rows += 1          
            x = -width / 2 + step_x / 2 #reset to left edge of mesh
            #go through each column, step by appropriate amount
            for column in range(0, picture.size[0] * 4, 4 + scene.cubester_skip_pixels * 4):                        
                r, g, b, a = getPixelValues(picture, pixels, row, column)
                h = findPointHeight(r, g, b, a, scene)
                
                #if not transparent
                if h != -1:                   
                    if scene.cubester_mesh_style == "blocks":
                        createBlock(x, y, hx, hy, h, verts, faces)
                        vert_colors += [(r, g, b) for i in range(24)]
                    else:                            
                        verts += [(x, y, h)]                                 
                        vert_colors += [(r, g, b) for i in range(4)]
                        
                x += step_x                
            y += step_y
            
            #if creating plane not blocks, then remove last 4 items from vertex_colors as the faces have already wrapped around
            if scene.cubester_mesh_style == "plane":
                del vert_colors[len(vert_colors) - 4:len(vert_colors)]                        
            
        #create faces if plane based and not block based
        if scene.cubester_mesh_style == "plane":
            off = int(len(verts) / rows)
            for r in range(rows - 1):
                for c in range(off - 1):
                    faces += [(r * off + c, r * off + c + 1, (r + 1) * off + c + 1, (r + 1) * off + c)]                
                  
        mesh = bpy.data.meshes.new("cubed")
        mesh.from_pydata(verts, [], faces)
        ob = bpy.data.objects.new("cubed", mesh)  
        bpy.context.scene.objects.link(ob) 
        bpy.context.scene.objects.active = ob        
        ob.select = True
        
        #uv unwrap
        if scene.cubester_mesh_style == "blocks":
            createUVMap(context, rows, int(len(faces) / 6 / rows))
        else:
            createUVMap(context, rows - 1, int(len(faces) / (rows - 1)))
        
        #material
        if scene.render.engine == "CYCLES":
            #determine name and if already created
            if scene.cubester_materials == "vertex": #vertex color
                image_name = "Vertex"             
            elif not scene.cubester_use_image_color and scene.cubester_color_image in bpy.data.images and scene.cubester_materials == "image": #replaced image
                image_name = scene.cubester_color_image
            else: #normal image
                image_name = scene.cubester_image
             
            #either add material or create   
            if ("CubeSter_" + image_name)  in bpy.data.materials:
                ob.data.materials.append(bpy.data.materials["CubeSter_" + image_name])
            
            #create material
            else:
                #add all nodes, only link ones needed
                mat = bpy.data.materials.new("CubeSter_" + image_name)
                mat.use_nodes = True
                nodes = mat.node_tree.nodes 
                           
                att = nodes.new("ShaderNodeAttribute")
                att.attribute_name = "Col"
                att.location = (-200, 300)
                
                att = nodes.new("ShaderNodeTexImage")
                if not scene.cubester_use_image_color and scene.cubester_color_image in bpy.data.images:
                    att.image = bpy.data.images[scene.cubester_color_image]
                else:
                    att.image = bpy.data.images[scene.cubester_image]
                att.location = (-200, 600)                
                
                att = nodes.new("ShaderNodeTexCoord")
                att.location = (-450, 600)
                
                if scene.cubester_materials == "image":
                    mat.node_tree.links.new(nodes["Image Texture"].outputs[0], nodes["Diffuse BSDF"].inputs[0])                
                    mat.node_tree.links.new(nodes["Texture Coordinate"].outputs[2], nodes["Image Texture"].inputs[0])
                else:
                    mat.node_tree.links.new(nodes["Attribute"].outputs[0], nodes["Diffuse BSDF"].inputs[0])
                
                ob.data.materials.append(mat)                
                      
        #vertex colors
        bpy.ops.mesh.vertex_color_add()        
        i = 0
        for c in ob.data.vertex_colors[0].data:
            c.color = vert_colors[i]
            i += 1

        stop = timeit.default_timer()
        
        #print time to generate mesh and handle materials
        if scene.cubester_mesh_style == "blocks":
            print("CubeSter: " + str(int(len(verts) / 8)) + " blocks in " + str(stop - start)) 
        else:
            print("CubeSter: " + str(len(verts)) + " points in " + str(stop - start))   
            
        #image squence handling
        if scene.cubester_load_type == "multiple":
            image_start = timeit.default_timer() #########TIMER
            
            images = findSequenceImages(context)
            
            frames = []
            frames_vert_colors = []
            
            if len(images[0]) >= scene.cubester_max_images:
                max = scene.cubester_max_images
            else:
                max = len(images[0])
            max *= scene.cubester_skip_images + 1
            
            #goes through and for each image for each block finds new height
            for image_index in range(0, max, scene.cubester_skip_images + 1):
                filepath = images[0][image_index]
                name = images[1][image_index]                                
                picture = fetchImage(name, filepath)
                pixels = list(picture.pixels)
                
                frame_heights = []
                frame_colors = []               
                
                for row in range(0, picture.size[1], scene.cubester_skip_pixels + 1):        
                    for column in range(0, picture.size[0] * 4, 4 + scene.cubester_skip_pixels * 4): 
                        r, g, b, a = getPixelValues(picture, pixels, row, column)                        
                        h = findPointHeight(r, g, b, a, scene)
                        
                        if h != -1:
                            frame_heights.append(h)
                            if scene.cubester_mesh_style == "blocks":
                                frame_colors += [(r, g, b) for i in range(24)]
                            else:                                                            
                                frame_colors += [(r, g, b) for i in range(4)]
                            
                if scene.cubester_mesh_style == "plane":
                    del vert_colors[len(vert_colors) - 4:len(vert_colors)]   
                                            
                frames.append(frame_heights)
                frames_vert_colors.append(frame_colors)
                
            scene.cubester_vertex_colors[ob.name] = {"frames" : frames_vert_colors, "frame_skip" : scene.cubester_frame_step, "total_images" : max}
            
            print(str(len(frames)) + " frames each with " + str(int(len(verts) / 8)) + " points in " + str(timeit.default_timer() - image_start))
            
            #use data to animate mesh                    
            action = bpy.data.actions.new("CubeSterAnimation")

            mesh.animation_data_create()
            mesh.animation_data.action = action

            data_path = "vertices[%d].co" 
            
            if scene.cubester_mesh_style == "blocks":   
                vert_index = 4 #index of first vert
            else:
                vert_index = 0                  
            
            #loop for every face height value            
            for frame_start_vert in range(len(frames[0])): 
                #only go once if plane, otherwise do all four vertices that are in top plane if blocks   
                if scene.cubester_mesh_style == "blocks":   
                    end_point = frame_start_vert + 4
                else:
                    end_point = frame_start_vert + 1
                    
                #loop through to get the four vertices that compose the face                                
                for frame_vert in range(frame_start_vert, end_point):
                    fcurves = [action.fcurves.new(data_path % vert_index, i) for i in range(3)] #fcurves for x, y, z
                    frame_counter = 1 #go through each frame and add position                   
                    temp_v = mesh.vertices[vert_index].co                 
                    
                    #loop through frames
                    for frame in frames:
                        vals = [temp_v[0], temp_v[1], frame[frame_start_vert]] #new x, y, z positions
                        for i in range(3): #for each x, y, z set each corresponding fcurve                                                        
                            fcurves[i].keyframe_points.insert(frame_counter, vals[i], {'FAST'})   
                        
                        frame_counter += scene.cubester_frame_step #skip frames for smoother animation   
                    
                    vert_index += 1
                    
                #only skip vertices if made of blocks
                if scene.cubester_mesh_style == "blocks":
                    vert_index += 4
        
        return {"FINISHED"}               
        
def register():
    bpy.utils.register_module(__name__)   
    bpy.app.handlers.frame_change_pre.append(materialFrameHandler)
    
def unregister():
    bpy.utils.unregister_module(__name__)
    f_change = bpy.app.handlers.frame_change_pre
    del f_change[0:len(f_change)]
    
if __name__ == "__main__":
    register() 