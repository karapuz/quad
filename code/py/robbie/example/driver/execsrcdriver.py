import robbie.execution.execsrclink as execsrclink

if __name__ == '__main__':
    app, thread = execsrclink.init()
    print app
    while 1:
        print '.'
        import time
        time.sleep(1)