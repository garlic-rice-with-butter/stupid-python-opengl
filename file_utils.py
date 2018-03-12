import os
from PIL import Image

# -----------------------------------------------------------------------------
#   File reading
# -----------------------------------------------------------------------------

def _get_file_location(filename, path=''):
  file_to_open = filename
  # Try base filename, and then try adding the path
  if os.path.isfile(filename):
    file_to_open = filename
  elif os.path.isfile(os.path.join(path, filename)):
    file_to_open = os.path.join(path, filename)
  else:
    raise ValueError('File not found: %s' % filename)
  return file_to_open

def get_file_contents(filename, path=''):
  file_to_open = _get_file_location(filename, path)
  with open(file_to_open, 'r') as f:
    file_contents = f.read()
  return file_contents

def get_image(filename, path=''):
  file_to_open = _get_file_location(filename, path)
  return Image.open(file_to_open)

