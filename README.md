#CubeSter by Jacob Morris
Original Author: Jacob Morris

Email Address: blendingjake@gmail.com

URL: www.blendingjacob.blogspot.com

CubeSter is an add-on for Blender 3D that takes an image and converts it into
a height-bases mesh object. The mesh can either be composed of cubes or a single, 
plane based mesh. The cube/mesh height is based upon the pixel intensity and alpha 
value at that point. By default the RGBA channel each are weighted to 25% of the height,
but they can be manually adjusted or set to random. 

CubeSter can cause Blender to go unresponsive for a period of time, so an
approximate time to generate the mesh is listed in the panel. Also, generating
a plane object is faster then generating a cube based object.