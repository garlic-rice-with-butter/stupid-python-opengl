# stupid-python-opengl
Whenever I need to make a new python program that has any 3d, it takes a lot of setup
I just wanted to skip all that and write it once here
In general, this isn't well done code, just that I don't want to keep rewriting it

The only things you need to care about are:
window.py
  - Use this to set up a window

obj.py
  - Loads .obj files

mesh.py
  - Communicates with OpenGL to draw stuff

model.py
  - Wraps around meshes, so all you have to do is change position when rendering

Might need to install pillow and python-opengl
