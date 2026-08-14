from collections import OrderedDict

class TTLCache:
    def __init__(self, capacity, clock):
        self.capacity = capacity
        self.clock = clock
        self._data = OrderedDict()

    def set(self, key, value, ttl):
        if key in self._data:
            del self._data[key]
        self._data[key] = (value, self.clock() + ttl)
        while len(self._data) > self.capacity:
            self._data.popitem(last=False)

    def get(self, key, default=None):
        item = self._data.get(key)
        if item is None:
            return default
        value, deadline = item
        if deadline < self.clock():
            del self._data[key]
            return default
        self._data.move_to_end(key)
        return value

    def __len__(self):
        return len(self._data)

    def keys(self):
        return list(self._data)
