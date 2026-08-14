class DocumentAPI:
    def __init__(self):
        self.documents = {}
    def request(self, method, path, headers, body):
        raise NotImplementedError
