import time

def run():
    for ix,e in enumerate( xrange(1000000)):
        print ix,e, 'x' * 1000
        time.sleep(1)

if __name__ == '__main__':
    run()