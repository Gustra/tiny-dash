import Queue
import os
from mock import patch
import unittest

import imp

tiny = imp.load_source('tinydash', os.path.join(os.path.dirname(__file__), '..', 'bin', 'tiny-dash.py'))

add_callback_called = False


class MockDeferred:
    def addCallback(self, cb):
        global add_callback_called
        add_callback_called = True


called_program = 'not called'


def getProcessValue(a, b, env):
    global called_program
    called_program = a
    return MockDeferred()


class TestSensorBase(unittest.TestCase):
    @patch('tinydash.SensorBase')
    @patch('tinydash.utils.getProcessValue', getProcessValue)
    def test_sensor(self, SensorBaseMock):
        queue = Queue.Queue()
        sensor = tiny.StatusSensor(queue, {'update-interval': 0.1, 'program': ['foobar']})
        sensor.run()
        self.assertEqual('foobar', called_program)
        self.assertTrue(add_callback_called)


if __name__ == '__main__':
    unittest.main()
