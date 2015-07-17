from time import strftime


def golog(data):
    print '[' + strftime("%m/%d/%Y %H:%M:%S") + '] ' + str(data)
