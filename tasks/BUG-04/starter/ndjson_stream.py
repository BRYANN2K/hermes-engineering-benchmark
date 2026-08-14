import json

class NDJSONDecoder:
    def __init__(self, max_line_bytes=65536):
        self.max_line_bytes = max_line_bytes
        self.line = 0
    def feed(self, chunk):
        results=[]
        for line in chunk.decode('utf-8').splitlines():
            self.line += 1
            if line.strip(): results.append(json.loads(line))
        return results
    def finish(self): return []
