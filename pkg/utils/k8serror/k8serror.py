'''
    k8s package
'''


class K8serror(object):
    ''' K8serror class is handling kubernetes errors '''

    def __init__(self, err=None):
        self.err = err

    def IsNotFound(self, err):
        ''' IsNotFound returns true if the specified error was created by NewNotFound '''
        if err.reason == "Not Found":
            return True
        return False

    def IsAlreadyExists(self, err):
        ''' IsAlreadyExists determines if the err is an error which indicates that a specified resource already exists '''
        if err.reason == "Conflict":
            return True
        return False
