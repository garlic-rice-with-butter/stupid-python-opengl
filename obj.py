import os
import mesh
from collections import defaultdict
from file_utils import get_file_contents

import vec_utils

# -----------------------------------------------------------------------------
#   MTL reading
# -----------------------------------------------------------------------------

class Material:
  SPECULAR_EXPONENT = 'Ns'
  AMBIENT_COLOR = 'Ka'
  DIFFUSE_COLOR = 'Kd'
  SPECULAR_COLOR = 'Ks'
  TRANSPARENCY = 'd'
  ILLUMINATION_MODEL = 'illum'

  def __init__(self, value_map):
    self.values = value_map

  def get_specular_exponent(self):
    return self.values.get(SPECULAR_EXPONENT, 1.0)

def read_mtllib(filename, path=''):
  file_contents = get_file_contents(filename, path)

  # Materials. Key is material name. Value is dict of the material
  # material dict is key-value of property-value
  materials = {}

  # Parse
  current_material = None
  for line in file_contents.splitlines():
    components = line.split()
    if len(components) == 0:
      continue
    key = components[0].lower()
    remaining = line.split(None, 1)[-1] # So it wont crash
    if key == '#': #comment
      continue
    elif key == 'newmtl':
      material_name = remaining
      current_material = material_name
      materials[material_name] = {} # Erase if exists
    elif key == 'Ns'.lower(): #Specular exponent
      materials[current_material][key] = float(components[1])
    elif key == 'Ka'.lower(): #Ambient color
      color = (float(components[1]), float(components[2]), float(components[3]))
      materials[current_material][key] = color
    elif key == 'Kd'.lower(): #Diffuse color
      color = (float(components[1]), float(components[2]), float(components[3]))
      materials[current_material][key] = color
    elif key == 'Ks'.lower(): #Specular color
      color = (float(components[1]), float(components[2]), float(components[3]))
      materials[current_material][key] = color
    elif key == 'd': #Transparency
      materials[current_material][key] = float(components[1])
    elif key == 'illum': #illumination model (enum)
      illum_model = int(components[1])
      if illum_model != 2:
        raise ValueError("Illum model is not 2! Anything else not supported")
      materials[current_material][key] = illum_model
    elif key == 'Ni'.lower(): #optical density (refraction index)
      materials[current_material][key] = float(components[1])
    elif key == 'map_Ka'.lower(): #ambient texture
      map_filename = remaining
      materials[current_material][key] = map_filename
    elif key == 'map_Kd'.lower(): #diffuse texture
      map_filename = remaining
      materials[current_material][key] = map_filename
    elif key == 'map_Ks'.lower(): #specular texture
      map_filename = remaining
      materials[current_material][key] = map_filename
  return materials

# -----------------------------------------------------------------------------
#   OBJ reading
# -----------------------------------------------------------------------------

# vertex dedupe
def make_key(v, vt, vn):
  return '%s:%s:%s' % (v, vt, vn)

def read_obj(filename, path=''):
  file_contents = get_file_contents(filename, path)

  # OBJ-wide state

  # Raw data read in by the OBJ parser
  v_pos_raw = []
  v_tex_raw = []
  v_nor_raw = []
  mesh_faces = defaultdict(list) # Key is material, value is array of faces
  mesh_smoothing = defaultdict(bool) # Key is material, value is smoothing
  # Vertex data is split by material. That means that we will have a separate
  # vertex buffer and index buffer for each material. If optimization is
  # necessary, then we can combine them into one big vb+ib and have multiple
  # draw calls that do not change vb/ibs
  # These are keyed by material
  vertex_data = defaultdict(list)
  vertex_data_map = defaultdict(dict)
  face_tris = defaultdict(list)
  # Materials
  materials = defaultdict(dict)

  # Convenience function to make vertices
  def make_or_get_vert_index(material, vp, vt, vn):
    key = make_key(vp, vt, vn)
    if key in vertex_data_map[material]:
      return vertex_data_map[material][key]
    pos = v_pos_raw[vp-1] if vp is not None else None
    tex = v_tex_raw[vt-1] if vt is not None else None
    nor = v_nor_raw[vn-1] if vn is not None else None
  
    # Should be done later, but filled in now to save space
    i = len(vertex_data[material])
    vertex = []
    for vec in [pos, tex, nor]:
      if vec is not None:
        vertex.extend(vec)
    vertex_data[material].append(vertex)
    vertex_data_map[material][key] = i
    return i

  # Convenience function for parsing
  def to_tuple(vals, cast, dim):
    return tuple([cast(x) for x in vals[:dim]])

  # Parse the lines in the OBJ file
  current_material = None
  for line in file_contents.splitlines():
    components = line.split()
    if len(components) == 0:
      continue
    line_type = components[0]
    if line_type == '#':
      continue

    remaining = components[1:]
    if line_type == 'v':
      v_pos_raw.append(to_tuple(remaining, float, 3))
    elif line_type == 'vt':
      # Tex coords need swizzling to work
      raw_tex = to_tuple(remaining, float, 2)
      v_tex_raw.append((raw_tex[0], 1.0-raw_tex[1]))
    elif line_type == 'vn':
      v_nor_raw.append(to_tuple(remaining, float, 3))
    elif line_type == 'f':
      def int_or_none(s):
        if s:
          return int(s)
        return None
      face = []
      for v_idx_data in remaining:
        idxs = v_idx_data.split('/')
        v_idx = [int_or_none(idx) for idx in idxs]
        v_idx += [None] * max(0, 3-len(idxs))
        face.append(tuple(v_idx))
      mesh_faces[current_material].append(face)
    elif components[0] == 's':
      mesh_smoothing[current_material] = (components[1] == 'on')
    elif components[0] == 'usemtl':
      current_material = components[1]
    elif components[0] == 'mtllib':
      mtl_filename = line.split(None, 1)[-1] # So it wont crash
      materials = read_mtllib(mtl_filename, path=path)

  # For each material
  for material, faces in mesh_faces.iteritems():
    # For each face, make vertex and index
    for face in faces:
      face_indices = []
      for vp, vt, vn in face:
        index = make_or_get_vert_index(material, vp, vt, vn)
        face_indices.append(index)
      # Triangulate
      a = face_indices[0]
      for i in xrange(len(face_indices)-2):
        b = face_indices[i+1]
        c = face_indices[i+2]
        face_tris[material].extend([a, b, c])

  # Flatten the index and vertex buffers
  vertex_buffers = defaultdict(list)
  index_buffers = defaultdict(list)
  for material, indices in face_tris.iteritems():
    index_buffers[material] = indices
    for vert in vertex_data[material]:
      vertex_buffers[material].extend(vert)

  # Vertex signature
  # Whether or not each channel was provided
  signature = [len(vec) > 0 for vec in [v_pos_raw, v_tex_raw, v_nor_raw]]

  return materials, vertex_buffers, index_buffers, signature

# -----------------------------------------------------------------------------
#   Mesh construction
# -----------------------------------------------------------------------------

def read_obj_to_mesh(filename):
  path, basename = os.path.split(filename)
  materials, vertex_buffers, index_buffers, signature = read_obj(basename, path=path)

  m = mesh.Mesh()
  for material, vb in vertex_buffers.iteritems():
    ib = index_buffers[material]
    material = materials[material]
    texture_filename = material.get('map_Kd'.lower(), None)
    if texture_filename is not None:
      texture = mesh.Texture.new_from_file(texture_filename, path=path)
    else:
      texture = None
    m.add_component(material, vb, ib, signature, texture)

  return m

