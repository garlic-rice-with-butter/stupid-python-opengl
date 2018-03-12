"""
Wraps an instance of a mesh and its current position
"""
import mesh
import matrix

from OpenGL.GLUT import *
from OpenGL.GLU import *
from OpenGL.GL import *

# -----------------------------------------------------------------------------
#   Model class
# -----------------------------------------------------------------------------

class Model:
  def __init__(self, mesh):
    self.mesh = mesh
    self.pos = [0.0, 0.0, 0.0]
    self.rot = [0.0, 0.0, 0.0]
    self.scale = 1.0

  def set_pos(self, x, y, z):
    self.pos = [x, y, z]

  def move(self, x, y, z):
    for (idx, val) in [(0, x), (1, y), (2, z)]:
      self.pos[idx] += val

  def set_rot(self, x, y, z):
    self.rot = [x, y, z]

  def rotate(self, x, y, z):
    for (idx, val) in [(0, x), (1, y), (2, z)]:
      self.rot[idx] += val

  def set_scale(self, scale):
    self.scale = scale

  def resize(self, val):
    self.scale *= val

  def get_transform_matrix(self):
    p = matrix.translate(self.pos[0], self.pos[1], self.pos[2])
    rx = matrix.rotate_x(self.rot[0])
    ry = matrix.rotate_y(self.rot[1])
    rz = matrix.rotate_z(self.rot[2])
    s = matrix.scale(self.scale, self.scale, self.scale)
    rzs = matrix.multiply(rz, s)
    ryx = matrix.multiply(ry, rx)
    rs = matrix.multiply(ryx, rzs)
    return matrix.multiply(p, rs)

  def draw(self, view_matrix):
    # TODO start caching matrices if things are slow
    glMatrixMode(GL_MODELVIEW)
    t = self.get_transform_matrix()
    t = matrix.multiply(view_matrix, t)
    t.load()

    self.mesh.draw()


