#CubeSter by Jacob Morris
Original Author: Jacob Morris

Email Address: blendingjake@gmail.com

URL: www.blendingjacob.blogspot.com

CubeSter is an add-on for Blender 3D that takes an image and converts it into
a height-based mesh object. The mesh can either be composed of multiple cubes 
or of a single plane. The height of the mesh is based upon the pixel intensity 
and alpha value at that point. By default the RGBA channels are each contribute
25% of the height, but they can be manually adjusted or set to random. 

Image sequences can also be imported and used to animate the meshes' color and height
over time.

CubeSter can cause Blender to go unresponsive for a period of time, so an
approximate time to generate the mesh is listed in the panel. Also, generating
a plane object is faster then generating a cube based object.