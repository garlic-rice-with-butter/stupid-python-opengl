"""
Wraps matrix manipulation
"""
import math
import vec_utils

from ctypes import c_double

from OpenGL.GLUT import *
from OpenGL.GLU import *
from OpenGL.GL import *

# -----------------------------------------------------------------------------
#   Matrix class
# -----------------------------------------------------------------------------

def _idx(row, col):
  return (col * 4) + row

class Matrix:
  def __init__(self, data=None):
    if data is None:
      data = [1.0, 0.0, 0.0, 0.0,
              0.0, 1.0, 0.0, 0.0,
              0.0, 0.0, 1.0, 0.0,
              0.0, 0.0, 0.0, 1.0]
    self.data = data
    self.double_data = None

  def to_double(self):
    if self.double_data is None:
      self.double_data = (c_double*len(self.data))(*self.data)
    return self.double_data

  def load(self):
    glLoadMatrixd(self.to_double())

  def get(self, row, col):
    return self.data[_idx(row, col)]

  def set(self, row, col, val):
    self.data[_idx(row, col)] = val

# -----------------------------------------------------------------------------
#   Multiplication
# -----------------------------------------------------------------------------

def multiply(A, B):
  c = [0.0] * 16
  for row in range(4):
    for col in range(4):
      for i in range(4):
        c[_idx(row, col)] += A.get(row, i) * B.get(i, col)
  return Matrix(c)

def multiply_vec3(A, v):
  return [sum([
              v[j] * A.get(i, j) 
              for j in xrange(3)
              ]) + A.get(i, 3) 
          for i in xrange(3)]

# -----------------------------------------------------------------------------
#   Transforms
# -----------------------------------------------------------------------------

def _identity_array():
  return [1.0, 0.0, 0.0, 0.0,
          0.0, 1.0, 0.0, 0.0,
          0.0, 0.0, 1.0, 0.0,
          0.0, 0.0, 0.0, 1.0]

def _rotate_any(theta, j, k):
  c = _identity_array()
  c[_idx(j, j)] = math.cos(theta)
  c[_idx(j, k)] = -math.sin(theta)
  c[_idx(k, j)] = math.sin(theta)
  c[_idx(k, k)] = math.cos(theta)
  return Matrix(c)

def identity():
  return Matrix(_identity_array())

def rotate_x(theta):
  return _rotate_any(theta, 1, 2)

def rotate_y(theta):
  return _rotate_any(theta, 2, 0)

def rotate_z(theta):
  return _rotate_any(theta, 0, 1)

def translate(x, y, z):
  c = _identity_array()
  c[_idx(0, 3)] = x
  c[_idx(1, 3)] = y
  c[_idx(2, 3)] = z
  return Matrix(c)

def scale(x, y, z):
  c = _identity_array()
  c[_idx(0, 0)] = x
  c[_idx(1, 1)] = y
  c[_idx(2, 2)] = z
  return Matrix(c)

# -----------------------------------------------------------------------------
#   Basis-changing Transform
# -----------------------------------------------------------------------------

def basis_change_matrix(x_vec, y_vec, z_vec, origin):
  c = [0.0] * 16
  for i in range(3):
    c[_idx(i, 0)] = x_vec[i]
    c[_idx(i, 1)] = y_vec[i]
    c[_idx(i, 2)] = z_vec[i]
    c[_idx(i, 3)] = origin[i]
  c[_idx(3, 3)] = 1.0
  return Matrix(c)

# -----------------------------------------------------------------------------
#   Scene
# -----------------------------------------------------------------------------

def projection_matrix(near=0.1, far=100.0, width=None, height=None):
  fov = 45.0
  aspect = 1.0
  if width is not None and height is not None:
    aspect = float(width) / float(height) 
  glMatrixMode(GL_PROJECTION)
  glLoadIdentity()
  gluPerspective(fov,aspect,near, far)

def view_matrix_raw(eye_x, eye_y, eye_z, 
                    lookat_x, lookat_y, lookat_z, 
                    up_x, up_y, up_z):
  eye = [eye_x, eye_y, eye_z]
  lookat = [lookat_x, lookat_y, lookat_z]
  up = [up_x, up_y, up_z]
  return view_matrix(eye, lookat, up)

def view_matrix(eye, lookat, up):
  """
  Returns a matrix for the view matrix
  """
  forward = vec_utils.sub(lookat, eye)
  forward = vec_utils.normalize(forward)
  up = vec_utils.normalize(up)
  right = vec_utils.cross(forward, up)
  right = vec_utils.normalize(right)
  up = vec_utils.cross(right, forward)
  up = vec_utils.normalize(up)

  c = [0.0] * 16
  # Inverse of an orthogonal matrix is its transpose
  for i in range(3):
    c[_idx(0, i)] = right[i]
    c[_idx(1, i)] = up[i]
    c[_idx(2, i)] = forward[i]
  c[_idx(0, 3)] = -vec_utils.dot(eye, right)
  c[_idx(1, 3)] = -vec_utils.dot(eye, up)
  c[_idx(2, 3)] = -vec_utils.dot(eye, forward)
  c[_idx(3, 3)] = 1.0

  return Matrix(c)



