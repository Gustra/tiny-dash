#!/usr/bin/env python
import Queue
import argparse
import json
import os
import traceback
import yaml
from Tkinter import *
from twisted.internet import protocol, utils, task, tksupport, reactor
from twisted.python import failure
from cStringIO import StringIO

import urllib2
# from datetime import datetime
# from urllib import urlencode

import logging

from copy import deepcopy


class ColorShade(object):
    """
    Handle color shading.
    """

    def __init__(self, min_rgb, max_rgb):
        """
        Constructor.
        
        :param min_rgb: color at 0.0 as (R, G, B)
        :param max_rgb: color at 1.0 as (R, G, B)
        """
        logging.debug('Min colors: {}'.format(min_rgb))
        logging.debug('Max colors: {}'.format(max_rgb))
        self.min_rgb = min_rgb
        self.max_rgb = max_rgb
        self.r_diff = self.max_rgb[0] - self.min_rgb[0]
        self.g_diff = self.max_rgb[1] - self.min_rgb[1]
        self.b_diff = self.max_rgb[2] - self.min_rgb[2]
        logging.debug('color diff: {},{},{}'.format(self.r_diff, self.g_diff, self.b_diff))

    def shade(self, fraction):
        return '#{:04x}{:04x}{:04x}'.format(int(self.min_rgb[0] + (self.r_diff * fraction)),
                                            int(self.min_rgb[1] + (self.g_diff * fraction)),
                                            int(self.min_rgb[2] + (self.b_diff * fraction)))


class SensorBase(object):
    """
    Base class for sensors executing external processes.
    """
    STATUS = ':status'
    FRACTION = ':fraction'
    STATE = ':state'

    def __init__(self, queue, update_interval=10.0):
        """
        Constructor. This will create the sensor, but not start updates. Call the start()
        method to start sensor updates.
        
        :param queue: the queue which this sensor shall put data in.
        :param update_interval: time in seconds (float) between sensor updates
        """
        self.queue = queue
        self.update_interval = update_interval if update_interval else 5.0
        self.timer = None
        self.value_type = None

    def start(self):
        """
        Start updating the sensor. The method timeout_triggered() will be called when an
        update is requested,
        
        :return: 
        """
        logging.debug('Sleeping for %f seconds', self.update_interval)
        self.timer = reactor.callLater(0.0, self.timeout_triggered)

    def timeout_triggered(self):
        """
        Called when timer fires. Calls the run() method.
        :return: 
        """
        logging.debug('Sensor awoke')
        self.run()

    def update(self, result, value_type=None):
        """
        Put a result in the queue and start update timer. Sub-classes must ensure that this
        method is called at some point for each update, otherwise the timer will not be restarted.
        
        :param result: data to send to emitter.
        :param value_type: type of value. Default is self.value_type.
        :return: 
        """
        logging.debug('Sensor result: %s', str(result))
        self.queue.put({'value-type': value_type if value_type else self.value_type, 'result': result})
        self.timer = reactor.callLater(self.update_interval, self.timeout_triggered)


class StatusSensor(SensorBase):
    """
    Run a program and return the exit status during update.
    """

    def __init__(self, queue, config):
        """
        Constructor.

        :param queue: the queue to put data in
        :param config: the sensor configuration dict
        """
        super(StatusSensor, self).__init__(queue, config['update-interval'] if 'update-interval' in config else None)
        self.program = config['program'] if 'program' in config else None
        self.value_type = self.STATUS

    def run(self):
        """
        Run the configured program and call the update() method with the exit status.
        """
        if not self.program:
            self.update(-1)
            return
        use_shell = not (isinstance(self.program, (list, tuple)))
        logging.debug('Calling %s',
                      self.program if use_shell else ' '.join(self.program))
        d = utils.getProcessValue(self.program[0], self.program[1:] if len(self.program) > 1 else [],
                                  env=os.environ)
        d.addCallback(self.update)


class StateSensor(SensorBase):
    """
    Run a program and return the first line of output.
    """

    def __init__(self, queue, config):
        """
        Constructor.

        :param queue: the queue to put data in
        :param config: the sensor configuration dict
        """
        super(StateSensor, self).__init__(queue, config['update-interval'] if 'update-interval' in config else None)
        self.program = config['program'] if 'program' in config else None
        self.value_type = self.STATE

    def run(self):
        """
        Run the configured program and call the update() method with the first line printed by the program.
        """
        if not self.program:
            self.update(-1)
            return
        use_shell = not (isinstance(self.program, (list, tuple)))
        logging.debug('Calling %s',
                      self.program if use_shell else ' '.join(self.program))
        d = utils.getProcessOutput(self.program[0], self.program[1:] if len(self.program) > 1 else [],
                                   env=os.environ)
        d.addCallbacks(self.got_output, self.no_output)

    def no_output(self, err):
        logging.debug("Got %s", err)
        self.update(-1)

    def got_output(self, output):
        result = output.split("\n")[0] if output else ''
        logging.debug("Got %s --> %s", output, result)
        self.update(result)


class FractionSensor(SensorBase):
    """
    Run a program which is expected to print a float value in the range 0.0..1.0.
    """

    def __init__(self, queue, config):
        """
        Constructor.
        
        :param queue: queue to put data in
        :param config: the sensor configuration dict
        """
        super(FractionSensor, self).__init__(queue, config['update-interval'] if 'update-interval' in config else None)
        self.program = config['program'] if 'program' in config else None
        self.value_type = self.FRACTION

    def run(self):
        """
        Run the configured program and expect a value in range 0.0..1.0. A negative value
        represents a broken sensor.
        """
        if not self.program:
            logging.debug("No program configured")
            self.update(-1.0)
            return
        use_shell = not (isinstance(self.program, (list, tuple)))
        logging.debug('Calling %s', self.program if use_shell else ' '.join(self.program))
        d = utils.getProcessOutput(self.program[0], self.program[1:] if len(self.program) > 1 else [])
        d.addCallbacks(self.got_output, self.no_output)

    def no_output(self, err):
        logging.debug("Got %s", err)
        self.update(-1.0)

    def got_output(self, output):
        result_float = float(output)
        logging.debug("Got %s --> %f", output, result_float)
        self.update(result_float)


class JenkinsJobStateSensor(SensorBase):
    """
    Monitors status of Jenkins jobs.
    """

    def __init__(self, queue, config):
        super(JenkinsJobStateSensor, self).__init__(queue,
                                                    config['update-interval'] if 'update-interval' in config else None)
        self.url = config['url'] if 'url' in config else None
        self.value_type = self.STATE

    def run(self):
        if self.url:
            try:
                logging.debug('Fetching Jenkins data from URL: %s/lastBuild/api/json', self.url)
                data = json.loads(urllib2.urlopen('{}/lastBuild/api/json'.format(self.url)).read())
                state = 'BUILDING' if data['building'] else data['result']
            except:
                state = -1
        else:
            state = -1
        self.update(state)


class Lamp(object):
    def __init__(self, parent, queue, config):
        self.queue = queue
        self.width = config['width'] if 'width' in config else 100
        self.height = config['height'] if 'height' in config else 100
        self.on_color = config['on-color'] if 'on-color' in config else '#80ff80'
        self.off_color = config['off-color'] if 'off-color' in config else '#ff0000'
        self.min_color = config['min-color'] if 'min-color' in config else 'green'
        self.max_color = config['max-color'] if 'max-color' in config else 'red'
        self.broken_color = config['broken-color'] if 'broken-color' in config else '#000000'
        self.default_color = config['default-color'] if 'default-color' in config else self.broken_color
        self.state_colors = config['state-colors'] if 'state-colors' in config else {}
        self.shape = config['shape'] if 'shape' in config else 'round'
        self.widget = Canvas(parent, height=self.height, width=self.width)

        self.shader = ColorShade(parent.winfo_rgb(self.min_color), parent.winfo_rgb(self.max_color))

    def update(self):
        try:
            data = self.queue.get(0)
        except Queue.Empty:
            return
        logging.debug('Got sensor data %s', str(data['result']))

        if data['value-type'] == SensorBase.FRACTION:
            fraction = data['result']
            if fraction < 0.0:
                logging.debug('Light is broken: %d => %s', fraction, self.broken_color)
                color = self.broken_color
            else:
                if fraction > 1.0:
                    fraction = 1.0
                logging.debug('Light is on by: %f', fraction)
                color = self.shader.shade(fraction)
        elif data['value-type'] == SensorBase.STATE:
            state = str(data['result'])
            if state not in self.state_colors:
                logging.debug('Unknown light state: %s => %s', state, self.default_color)
                color = self.broken_color
            else:
                logging.debug('Light is on: %s => %s', state, self.state_colors[state])
                color = self.state_colors[state]
        else:
            status = data['result']
            if int(status) < 0:
                logging.debug('Light is broken: %d => %s', status, self.broken_color)
                color = self.broken_color
            elif int(status) > 0:
                logging.debug('Light is off: %d', status)
                color = self.off_color
            else:
                logging.debug('Light is on: %d', status)
                color = self.on_color

        self.draw(color)

    def draw(self, color):
        self.widget.delete('all')
        if self.shape == 'square':
            self.widget.create_rectangle(0, 0, self.width, self.height, fill=color)
        else:
            self.widget.create_oval(0, 0, self.width, self.height, fill=color)


class Meter(object):
    """
    A meter type emitter which can be configured as a pie or arc and change color.
    """

    def __init__(self, parent, queue, config):
        self.queue = queue
        self.width = config['width'] if 'width' in config else 100
        self.height = config['height'] if 'height' in config else 100
        self.min_color = config['min-color'] if 'min-color' in config else '#00ff00'
        self.max_color = config['max-color'] if 'max-color' in config else '#ff0000'
        self.broken_color = config['broken-color'] if 'broken-color' in config else '#000000'
        self.start_angle = config['start-angle'] if 'start-angle' in config else 270.0
        self.max_angle = config['end-angle'] if 'end-angle' in config else 360.0
        self.max_angle = config['max-angle'] if 'max-angle' in config else 360.0
        self.thickness = config['thickness'] if 'thickness' in config else 0.5

        self.widget = Canvas(parent, height=self.height, width=self.width)

        # Maintain a color diff list to make calculation easier

        self.shader = ColorShade(parent.winfo_rgb(self.min_color), parent.winfo_rgb(self.max_color))

    def update(self):
        try:
            data = self.queue.get(0)
            status = float(data['result'])
        except Queue.Empty:
            return
        logging.debug('Got sensor data %f', status)
        if status < 0.0:
            logging.debug('Sensor is broken: %f => %s', status, self.broken_color)
            color = self.broken_color
            status = 0.5
        else:
            if status > 1.0:
                status = 1.0
            color = self.shader.shade(status)
        start_angle = self.start_angle
        end_angle = -self.max_angle * status
        logging.debug('Meter settings: %s, %f, %f', color, start_angle, end_angle)
        edgesize = self.width * self.thickness * 0.5
        margin = 1 + edgesize / 2
        self.widget.delete('all')
        self.widget.create_arc(margin, margin, self.width - margin, self.height - margin, start=start_angle,
                               extent=end_angle, outline=color, style="arc", width=edgesize)


class Broken(object):
    def __init__(self, parent, queue, config):
        self.queue = queue
        self.width = config['width'] if 'width' in config else 100
        self.height = config['height'] if 'height' in config else 100
        self.widget = Canvas(parent, height=self.height, width=self.width)
        self.draw()

    def update(self):
        try:
            data = self.queue.get(0)
        except Queue.Empty:
            return
        logging.debug('Got sensor data %s', str(data['result']))

    def draw(self):
        self.widget.delete('all')
        x0 = int(0.1 * float(self.width))
        w = self.width - int(0.1 * float(self.width))
        y0 = int(0.1 * float(self.height))
        h = self.height - int(0.1 * float(self.height))
        self.widget.create_line(x0, y0, w, h, fill='red', width=4)
        self.widget.create_line(w, y0, x0, h, fill='red', width=4)


class TinyDashApp:
    """
    Tiny dash application class.
     
    Reads config files, creates sensors and emitters, and triggers updates of
    emitters.
    """

    def __init__(self, parent, args):
        """
        Constructor. Reads configuration files and creates the dashboard.
        :param parent: Tkinter widget
        :param args: parsed command-line arguments in "argparse" format
        """
        self.parent = parent
        self.dash_frame = Frame(parent)
        self.dash_frame.pack(fill=BOTH, expand=1)
        self.status_text = StringVar()
        self.status_label = Label(parent, textvariable=self.status_text)
        self.status_label.pack(side=BOTTOM, fill=X, expand=0, anchor='w')

        self.args = args

        # Delay thread starts until after all emitters have been created
        self.sensors = []
        self.emitters = []

        # Default settings, also if defaults are reset
        default_defaults = {'height': 40,
                            'width': 40,
                            'update-interval': 5.0, }

        # Current default settings, which can be updated by config files
        defaults = default_defaults

        for config_file in args.configfiles:
            logging.debug('Reading configuration from %s', config_file)
            with open(config_file) as fp:
                config = yaml.load(fp)

            logging.debug('%s', config)

            for raw_item in config:
                if 'defaults+' in raw_item:
                    if not raw_item['defaults+']:
                        defaults = default_defaults
                        logging.debug('Defaults resetted: %s', defaults)
                    else:
                        defaults.update(raw_item['defaults+'])
                        logging.debug('Defaults updated: %s', defaults)
                    continue
                if 'defaults' in raw_item:
                    defaults = default_defaults
                    if not raw_item['defaults']:
                        continue
                    defaults.update(raw_item['defaults'])
                    logging.debug('Defaults set: %s', defaults)
                    continue

                item = deepcopy(defaults)
                item.update(raw_item)

                queue = Queue.Queue()
                thing = None
                if item['sensor'] == 'Status':
                    logging.debug("Found {}".format(item['sensor']))
                    thing = StatusSensor(queue, item)
                elif item['sensor'] == 'State':
                    logging.debug("Found {}".format(item['sensor']))
                    thing = StateSensor(queue, item)
                elif item['sensor'] == 'Fraction':
                    logging.debug("Found {}".format(item['sensor']))
                    thing = FractionSensor(queue, item)
                elif item['sensor'] == 'JenkinsJobState':
                    logging.debug("Found {}".format(item['sensor']))
                    thing = JenkinsJobStateSensor(queue, item)
                if not thing:
                    print "Error: {} is an unknown sensor type".format(item["sensor"])
                    continue
                self.sensors.append(thing)
                if 'type' in item:
                    try:
                        class_ = getattr(sys.modules[__name__], item['type'])
                        indicator = class_(self.dash_frame, queue, item)
                        self.emitters.append(indicator)
                        if 'name' in item:
                            indicator.widget.bind('<Enter>',
                                                  lambda event, name=item['name']: self.status_text.set(name))
                            indicator.widget.bind('<Leave>', lambda event: self.status_text.set(''))

                    except Exception as e:
                        logging.error(e.message)
                        indicator = Broken(self.dash_frame, queue, item)
                        self.emitters.append(indicator)
                        status_text = ''
                        if 'name' in item:
                            status_text = item['name'] + ': '
                        status_text += 'Error: ' + e.message
                        indicator.widget.bind('<Enter>',
                                              lambda event, name=status_text: self.status_text.set(name))
                        indicator.widget.bind('<Leave>', lambda event: self.status_text.set(''))

                else:
                    logging.warning('Sensor %s not connected to an indicator.')
                    indicator = Broken(self.dash_frame, queue, item)
                    self.emitters.append(indicator)
                    status_text = ''
                    if 'name' in item:
                        status_text = item['name'] + ': '
                    status_text += 'Error: not connected to an indicator'
                    indicator.widget.bind('<Enter>',
                                          lambda event, name=status_text: self.status_text.set(name))
                    indicator.widget.bind('<Leave>', lambda event: self.status_text.set(''))

        logging.debug("Laying out dashboard")

        if self.args.geometry:
            geometry = self.args.geometry
        else:
            geometry = self.load_saved_geometry()
        if geometry:
            self.parent.geometry(geometry)
        self.parent.update()
        self.layout()

        logging.debug("Starting sensors")

        # Start sensors
        for s in self.sensors:
            s.start()

        # And go with updates
        self.timer = parent.after(100, self.refresh)

    def layout(self, *args):
        logging.debug('Window width: %d', self.parent.winfo_width())
        max_x = self.parent.winfo_width() if self.parent.winfo_width() > 1 else 600
        x = 0
        y = 0
        delta_y = 0
        for emitter in self.emitters:
            if emitter.width + x > max_x:
                y = y + delta_y
                x = 0
                delta_y = 0
            emitter.widget.place(x=x, y=y)
            x += emitter.width
            if emitter.height > delta_y:
                delta_y = emitter.height

    def refresh(self):
        self.timer = self.parent.after(100, self.refresh)

        for emitter in self.emitters:
            emitter.update()

    def load_saved_geometry(self):
        geometry_file = os.path.join(self.args.config_dir, 'geometry')
        if not os.path.exists(geometry_file):
            return None
        logging.debug('Loading geometry from %s', geometry_file)
        with open(geometry_file) as fp:
            return fp.read()

    def save_geometry(self):
        if not self.args.geometry:
            # Only save geometry if started without the argument
            geometry_file = os.path.join(self.args.config_dir, 'geometry')
            if not os.path.exists(self.args.config_dir):
                os.makedirs(self.args.config_dir)
            logging.debug('Saving geometry %s in %s', self.parent.geometry(), geometry_file)
            with open(geometry_file, 'w') as fp:
                fp.write(self.parent.geometry())

    def on_closing(self, *args):
        self.save_geometry()
        self.parent.destroy()
        reactor.stop()


def parse_args():
    parser = argparse.ArgumentParser(description='Simple dashboard application')
    parser.add_argument('configfiles',
                        nargs='*',
                        default=os.path.join(os.path.expanduser('~'), '.tiny-dash', 'config'),
                        help='Dashboard configuration files to read.')
    parser.add_argument('--config-dir',
                        default=os.path.join(os.path.expanduser('~'), '.tiny-dash'),
                        help='Dashboard configuration files to read.')
    parser.add_argument('--geometry',
                        help='Size and position of the window')
    parser.add_argument('--debug',
                        action='store_true',
                        help='Emit debugging information')
    args = parser.parse_args()

    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
        logging.debug('Parsed arguments: %s', args)

    return args


if __name__ == '__main__':
    root = Tk()
    tksupport.install(root)
    tiny = TinyDashApp(root, parse_args())
    root.protocol("WM_DELETE_WINDOW", tiny.on_closing)


    def reconfigure(event):
        tiny.layout()


    root.bind('<Configure>', tiny.layout)
    root.bind('<Control-q>', tiny.on_closing)

    reactor.run()
