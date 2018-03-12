"""
Stuff to set up a window quickly

"""

import sys
import time
from collections import defaultdict

from OpenGL.GLUT import *
from OpenGL.GLU import *
from OpenGL.GL import *

# -----------------------------------------------------------------------------
#   Config and global state
#     Stored here so we only have to include window to get started and not
#     need to include a separate config file
# -----------------------------------------------------------------------------
DEFAULT_WINDOW_WIDTH = 800
DEFAULT_WINDOW_HEIGHT = 600

DEFAULT_FPS = 30

# -----------------------------------------------------------------------------
#   Classes to help store state
#   Other state as well
# -----------------------------------------------------------------------------

# Cannot store this in a class for some reason
_main_loop_callback = None
_resize_window_callback = None

class _WindowState:
  """ Stores global state about the window and setup """
  # State of the keyboard
  keys = defaultdict(bool)

  # Mouse
  mouse_x = None
  mouse_y = None
  mouse_moved_x = 0
  mouse_moved_y = 0
  mouse_buttons = defaultdict(bool)
  # Mouse calculation (for storing where the mouse is)
  mouse_raw_x = None
  mouse_raw_y = None
  mouse_updated = False
  infinite_mouse = False

  # Screen dimensions
  fullscreen = False
  width = None
  height = None

class _Timer:
  # Current fps
  fps = DEFAULT_FPS

  # Time of last frame
  last_frame_time = None

  @classmethod
  def start(cls):
    _Timer.last_frame_time = time.time()

  @classmethod
  def set_fps(cls, fps):
    _Timer.fps = fps

  @classmethod
  def next_frame(cls):
    """ 
    Returns seconds since last frame (double) if next frame is due
    otherwise returns null/None if too early
    """
    time_diff = time.time() - _Timer.last_frame_time
    if time_diff < (1.0 / _Timer.fps):
      return None
    _Timer.last_frame_time = time.time()
    return time_diff

# -----------------------------------------------------------------------------
#   Callbacks
# -----------------------------------------------------------------------------

def _resize_window(width, height):
  global _resize_window_callback
  fcn = _resize_window_callback
  if fcn is not None:
    fcn(width, height)
  pass

def _main_loop():
  global _main_loop_callback
  # Check time elapsed
  time_elapsed = _Timer.next_frame()
  if time_elapsed is None:
    return

  _update_mouse_handler()

  glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

  fcn = _main_loop_callback
  if fcn is not None:
    fcn(time_elapsed)

  # Error handling and frame cleanup
  error = glGetError()
  if error:
    print gluErrorString(error)

  glutSwapBuffers()

# -----------------------------------------------------------------------------
#   Keyboard/Mouse functions
# -----------------------------------------------------------------------------

"""
Keyboard handlers that set/unset keys so we can store the state of the keyboard
"""
def _keyboard_up_handler(c, x=None, y=None):
  """ Key was unpressed """
  _WindowState.keys[c.lower()] = False # Ignore caps/shift

def _keyboard_handler(c, x=None, y=None):
  """ Key was pressed """
  _WindowState.keys[c.lower()] = True # Ignore caps/shift

  # Quit if escape is pressed
  if c == '\x1b':
    exit()

def _keyboard_special_up_handler(c, x=None, y=None):
  """ Key was unpressed """
  _WindowState.keys[c] = False

def _keyboard_special_handler(c, x=None, y=None):
  """ Key was pressed """
  _WindowState.keys[c] = True

"""
Mouse handlers that set the position of the cursor and state of the buttons
"""
def _mouse_motion_handler(x, y):
  _WindowState.mouse_raw_x = x
  _WindowState.mouse_raw_y = y
  _WindowState.mouse_updated = True

def _update_mouse_handler():
  if _WindowState.mouse_updated:
    if _WindowState.mouse_x is None or _WindowState.mouse_y is None:
      _WindowState.mouse_x = _WindowState.mouse_raw_x
      _WindowState.mouse_y = _WindowState.mouse_raw_y

    _WindowState.mouse_moved_x = \
      _WindowState.mouse_raw_x - _WindowState.mouse_x
    _WindowState.mouse_moved_y = \
      _WindowState.mouse_raw_y - _WindowState.mouse_y
    _WindowState.mouse_x = _WindowState.mouse_raw_x
    _WindowState.mouse_y = _WindowState.mouse_raw_y
    _WindowState.mouse_updated = False
  else:
    # No update. Zero out the velocity
    _WindowState.mouse_moved_x = 0
    _WindowState.mouse_moved_y = 0

  # Warp mouse to middle of the screen 
  if _WindowState.infinite_mouse:
    glutWarpPointer(_WindowState.width / 2, _WindowState.height / 2)
    _WindowState.mouse_x = _WindowState.width / 2
    _WindowState.mouse_y = _WindowState.height / 2


# -----------------------------------------------------------------------------
#   GL
# -----------------------------------------------------------------------------

def _init_gl():
  """ Stuff that every GL window needs """
  glClearColor(0, 0, 0, 1)
  glEnable(GL_DEPTH_TEST)
  glDepthFunc(GL_LEQUAL)
  glEnable(GL_LIGHTING)
  glDisable(GL_LIGHTING)

  glEnableClientState(GL_VERTEX_ARRAY)
  glEnableClientState(GL_TEXTURE_COORD_ARRAY)
  #glEnableClientState(GL_NORMAL_ARRAY)
  #glEnableClientState(GL_COLOR_ARRAY)

# -----------------------------------------------------------------------------
#   Externally-accessible functions
# -----------------------------------------------------------------------------

""" Setup """
def create_window(Title, width=None, height=None, fullscreen=False, fps=None, 
    infinite_mouse=False):
  """ Creates a window with the specified parameters """
  
  # Initialize glut/window functions
  glutInit(sys.argv)
  glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGBA | GLUT_DEPTH)
  if width is None:
    width = DEFAULT_WINDOW_WIDTH
  if height is None:
    height = DEFAULT_WINDOW_HEIGHT
  glutInitWindowSize(width, height)
  if fullscreen:
    fullscreen_string = "%sx%s:32@60" % (width, height)
    glutGameModeString(fullscreen_string)
    glutEnterGameMode()
  else:
    glutCreateWindow(Title)
  if infinite_mouse:
    glutSetCursor(GLUT_CURSOR_NONE)
  _WindowState.fullscreen = fullscreen
  _WindowState.infinite_mouse = infinite_mouse
  _WindowState.width = width
  _WindowState.height = height

  glutDisplayFunc(_main_loop)
  glutIdleFunc(_main_loop)
  glutReshapeFunc(_resize_window)
  glutKeyboardFunc(_keyboard_handler)
  glutKeyboardUpFunc(_keyboard_up_handler)
  glutSpecialFunc(_keyboard_special_handler)
  glutSpecialUpFunc(_keyboard_special_up_handler)
  glutPassiveMotionFunc(_mouse_motion_handler)
  #glutReportErrors()

  _init_gl()

  if fps is None:
    fps = DEFAULT_FPS
  set_fps(fps)

def begin():
  _Timer.start()
  glutMainLoop()

def exit():
  glutLeaveGameMode()
  sys.exit()

""" Framerate """
def set_fps(fps):
  _Timer.set_fps(fps)

""" Keyboard """
def keydown(c):
  return _WindowState.keys[c]

""" Mouse """
def mouse_pos():
  if _WindowState.infinite_mouse:
    print "Warning, getting mouse position while infinite mouse"
  return _WindowState.mouse_x, _WindowState.mouse_y

def mouse_vel():
  return _WindowState.mouse_moved_x, _WindowState.mouse_moved_y

""" Callbacks """
def set_main_loop(fcn):
  global _main_loop_callback
  _main_loop_callback = fcn

def set_resize_callback(fcn):
  global _resize_window_callback
  _resize_window_callback = fcn

