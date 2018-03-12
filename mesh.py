from ctypes import sizeof, c_float, c_void_p, c_uint

from PIL import Image

from OpenGL.GLUT import *
from OpenGL.GLU import *
from OpenGL.GL import *
import pickle
import numpy

from file_utils import get_image

# -----------------------------------------------------------------------------
#   Mesh construction
# -----------------------------------------------------------------------------

class Texture:

  @classmethod
  def new_from_file(cls, filename, path='', force_new=False):
    #TODO Cache the texture object

    try:
      image = get_image(filename, path)
      image_data = list(image.getdata())
      width, height = image.size

      byte_array = []
      for pixel in image_data:
        # Pad to RGBA
        pixel_rgba = [c for c in pixel]
        pixel_rgba += [255] * max(0, 4-len(pixel_rgba))
        for channel in pixel_rgba[:4]:
          byte_array.append(chr(channel))
      byte_array = b"".join(byte_array)

      return Texture(width, height, byte_array)
    except IOError, e:
      print "Error loading texture %s : %s" % (filename, str(e))
      return None

  def __init__(self, width, height, byte_array):
    self.width = width
    self.height = height
    self.byte_array = byte_array
    self.texture_id = -1

    self.prepared = False
    
  def prepare(self):
    if self.prepared:
      raise ValueError('Texture is already prepared')

    self.texture_id = glGenTextures(1)
    glEnable(GL_TEXTURE_2D)
    glBindTexture(GL_TEXTURE_2D, self.texture_id)
    glTexParameter(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    glTexParameter(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, self.width, self.height, 0,
                 GL_RGBA, GL_UNSIGNED_BYTE, self.byte_array)

    self.prepared = True

  def get_id(self):
    return self.texture_id

  def bind(self, channel=0):
    glBindTexture(GL_TEXTURE_2D, self.texture_id)

class Mesh:
  MATERIAL = 'material'
  VERTEX_BUFFER_DATA = 'vb_data'
  INDEX_BUFFER_DATA = 'ib_data'
  SIGNATURE = 'signature'

  VERTEX_BUFFER = 'vb'
  INDEX_BUFFER = 'ib'
  NUM_INDICES = 'num_indices'
  TEXTURE = 'texture'
  STRIDE = 'stride'
  POS_OFFSET = 'pos_offset'
  TEX_OFFSET = 'tex_offset'
  NOR_OFFSET = 'nor_offset'

  def __init__(self):
    self.components = []
    self.prepared = False
    self.prepared_components = []

  def add_component(self, material, vertex_buffer, index_buffer, signature, texture):
    if self.prepared:
      raise ValueError('Cannot add component after mesh is prepared')

    component = {
        Mesh.MATERIAL: material, 
        Mesh.VERTEX_BUFFER_DATA: vertex_buffer, 
        Mesh.INDEX_BUFFER_DATA: index_buffer,
        Mesh.TEXTURE: texture,
        Mesh.SIGNATURE: signature,
      }

    self.components.append(component)

  def prepare(self):
    """
    After all components have been added, create the vertex/index buffers
    """
    if self.prepared:
      raise ValueError('Mesh is already prepared')

    float_size = sizeof(c_float)
    for component in self.components:
      vb_id = glGenBuffers(1)
      ib_id = glGenBuffers(1)

      vb_data = component[Mesh.VERTEX_BUFFER_DATA]
      ib_data = component[Mesh.INDEX_BUFFER_DATA]
      num_indices = len(ib_data)
      material = component[Mesh.MATERIAL]
      texture = component[Mesh.TEXTURE]
      signature = component[Mesh.SIGNATURE]

      vb_data = (c_float*len(vb_data))(*vb_data)
      ib_data = (c_uint*len(ib_data))(*ib_data)

      glBindBuffer(GL_ARRAY_BUFFER, vb_id);
      glBufferData(GL_ARRAY_BUFFER, vb_data, GL_STATIC_DRAW);

      glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, ib_id)
      glBufferData(GL_ELEMENT_ARRAY_BUFFER, ib_data, GL_STATIC_DRAW)

      stride = 0 * float_size
      pos_offset = stride
      stride += (3 * float_size) if signature[0] else 0
      tex_offset = stride
      stride += (2 * float_size) if signature[1] else 0
      nor_offset = stride
      stride += (3 * float_size) if signature[2] else 0

      if texture is not None:
        texture.prepare()
      # Store as a prepared component
      prepared_component = {
          Mesh.VERTEX_BUFFER : vb_id,
          Mesh.INDEX_BUFFER : ib_id,
          Mesh.NUM_INDICES : num_indices,
          Mesh.TEXTURE : texture,
          Mesh.SIGNATURE : signature,
          Mesh.STRIDE : stride,
          Mesh.POS_OFFSET : pos_offset,
          Mesh.TEX_OFFSET : tex_offset,
          Mesh.NOR_OFFSET : nor_offset,
        }
      self.prepared_components.append(prepared_component)
    self.prepared = True

  def draw(self):
    """
    draw the mesh
    """
    if not self.prepared:
      raise ValueError('Mesh is not prepared yet')

    for component in self.prepared_components:
      vb = component[Mesh.VERTEX_BUFFER]
      ib = component[Mesh.INDEX_BUFFER]
      signature = component[Mesh.SIGNATURE]
      stride = component[Mesh.STRIDE]
      pos_offset = component[Mesh.POS_OFFSET]
      tex_offset = component[Mesh.TEX_OFFSET]
      nor_offset = component[Mesh.NOR_OFFSET]
      num_indices = component[Mesh.NUM_INDICES]
      texture = component[Mesh.TEXTURE]

      glBindBuffer(GL_ARRAY_BUFFER, vb)
      if signature[0]:
        glVertexPointer(3, GL_FLOAT, stride, c_void_p(pos_offset));
      if signature[1]:
        glTexCoordPointer(2, GL_FLOAT, stride, c_void_p(tex_offset))
      if signature[2]:
        glNormalPointer(GL_FLOAT, stride, c_void_p(nor_offset))
      glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, ib)

      if texture is not None:
        texture.bind()

      offset = 0
      glDrawElements(GL_TRIANGLES,
                     num_indices, GL_UNSIGNED_INT,
                     c_void_p(offset))
