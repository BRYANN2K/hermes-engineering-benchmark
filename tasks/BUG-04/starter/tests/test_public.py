import unittest
from ndjson_stream import NDJSONDecoder

class PublicTests(unittest.TestCase):
    def test_lines_may_span_chunks_and_finish_handles_tail(self):
        d=NDJSONDecoder()
        self.assertEqual(d.feed(b'{"a":'), [])
        self.assertEqual(d.feed(b'1}\n{"b":2}'), [{'a':1}])
        self.assertEqual(d.finish(), [{'b':2}])
        self.assertEqual(d.finish(), [])
    def test_blank_lines_and_crlf(self):
        d=NDJSONDecoder(); self.assertEqual(d.feed(b' \r\n{"x":1}\r\n'), [{'x':1}])

if __name__ == '__main__': unittest.main()
