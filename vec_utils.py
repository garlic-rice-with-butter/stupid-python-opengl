import math
# -----------------------------------------------------------------------------
#   Vector manipulation
# -----------------------------------------------------------------------------
def sub(A, B):
  if len(A) != len(B):
    raise ValueError("%s and %s do not have the same dim" % (A, B))
  return [A[i] - B[i] for i in xrange(len(A))]

def add(A, B):
  if len(A) != len(B):
    raise ValueError("%s and %s do not have the same dim" % (A, B))
  return [A[i] + B[i] for i in xrange(len(A))]

def lerp(A, B, s):
  if len(A) != len(B):
    raise ValueError("%s and %s do not have the same dim" % (A, B))
  return [(A[i] * (1.0 - s)) + (B[i] * s) for i in xrange(len(A))]

def dot(A, B):
  if len(A) != len(B):
    raise ValueError("%s and %s do not have the same dim" % (A, B))
  return sum([A[i] * B[i] for i in xrange(len(A))])

def scale(s, A):
  return [s * c for c in A]

def length(A):
  return math.sqrt(dot(A, A))

# -----------------------------------------------------------------------------
#   Slightly more complex
# -----------------------------------------------------------------------------

def normalize(A):
  denom = length(A)
  if denom == 0.0:
    return [x for x in A] # Copy
  return [x / denom for x in A]

def cross(A, B):
  if len(A) != 3 or len(B) != 3:
    err = "Can only get cross product of 3-dim vectors, not %s x %s" % (A, B)
    raise ValueError(err)
  C = [0.0, 0.0, 0.0]
  for i in xrange(3):
    j, k = (i + 1) % 3, (i + 2) % 3
    C[i] = (A[j]*B[k])-(A[k]*B[j])
  return C

def triangle_normal(A, B, C):
  """ Returns a normal to the plane defined by ABC """
  AB = normalize(sub(B, A))
  BC = normalize(sub(C, B))
  return normalize(cross(AB, BC))

