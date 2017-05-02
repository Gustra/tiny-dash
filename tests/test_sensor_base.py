import Queue
import os
import unittest
from mock import patch
import imp
from twisted.internet import reactor
import sys

tiny = imp.load_source('tinydash', os.path.join(os.path.dirname(__file__), '..', 'bin', 'tiny-dash.py'))


class EchoSensor(tiny.SensorBase):
    def run(self):
        self.update('foo')


nof_calls = 0


def callLater(a, b):
    global nof_calls
    nof_calls += 1
    return 'obj'


class TestSensorBase(unittest.TestCase):
    @patch('tinydash.reactor.callLater', callLater)
    def test_sensor(self, ):
        queue = Queue.Queue()
        sensor = EchoSensor(queue, 0.1)
        sensor.start()
        self.assertEqual(1, nof_calls)
        sensor.timeout_triggered()
        try:
            item = queue.get(True, 5)
        except Queue.Empty:
            self.fail('Queue not populated')
        self.assertEqual(item['result'], 'foo', 'Get value')
        self.assertEqual(2, nof_calls)


if __name__ == '__main__':
    unittest.main()
