__author__ = 'ilya'

import robbie.util.mmap_array as utmmap

def run(shape):
    a = utmmap.newWrite(activity='a', shape=shape)
    b = utmmap.newWrite(activity='b', shape=shape)
    c = utmmap.newWrite(activity='c', shape=shape)
    d = utmmap.newWrite(activity='d', shape=shape)
    print a.shape

if __name__ == '__main__':
    shape = 100,1000000
    run(shape)
