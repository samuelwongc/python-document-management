import os

class LocalDocumentRepository:
    def __init__(self, directory):
        self.directory = directory

    def get(self, filename):
        fp = os.path.join(self.directory, filename)
        with open(fp, 'r') as f:
            return f.read()
    
    def put(self, filename, content):
        fp = os.path.join(self.directory, filename)
        with open(fp, 'w+') as f:
            f.write(content)