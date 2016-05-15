__author__ = 'ilya'

'''
lstsq(a, b, cond=None, overwrite_a=False, overwrite_b=False, check_finite=True)
    Compute least-squares solution to equation Ax = b.

    Compute a vector x such that the 2-norm ``|b - A x|`` is minimized.
'''

import scipy
from scipy.linalg import lstsq
# b is our pnls
b  = scipy.matrix([[1,2,3,1,2,3,4]]).T
# x is our paramters
x  = scipy.matrix([[2,1,3,1,2,3,4],[1,2,3,4,5,6,7]]).T
r  = lstsq(a=x,b=b)
A  = r[0]
bb = x * A

from scipy.linalg import lstsq
import numpy
# b is our pnls
b  = numpy.array([[1,2,3,1,2,3,4]]).T
# x is our paramters
x  = numpy.array([[2,1,3,1,2,3,4],[1,2,3,4,5,6,7]]).T
r  = lstsq(a=x,b=b)
A  = r[0]
bb = numpy.dot(x, A)

print b
print bb