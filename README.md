# Tiny Dash

Tiny dash is a simple desktop dashboard application, which connects
"indicators" to "sensors". A sensor executes a command and sets the
dashboard indicator based on the exit status or output of the command.
Three types of sensors are currently supported: status, state, and
fraction, and two types of indicators: lamp and meter.

The purpose of tiny-dash is to be able to present a lot of indicators in
a tiny area on the desktop, quite the opposite of most web-based
dashboards which aim for the huge radiator screens.

It is in early stage of development, but it is already usable, please
visit the [wiki](https://github.com/Gustra/tiny-dash/wiki) to read the
[documentation](https://github.com/Gustra/tiny-dash/wiki/User-guide).

It has been verified to run on Linux and Windows 8, but it should work
on any platform supported by Tkinter and twisted, since it has no
special dependencies.

## Installation

Tiny dash is written in Python and uses [twisted][twi] for
asynchronous command execution and [Tkinter][tki] for presentation.

* Install [Python2](pyt) on your system (Python 3 untested)
* Install
[Tkinter](https://tkinter.unpythonic.net/wiki/How_to_install_Tkinter)
* On Windows: install [pywin32](https://pypi.python.org/pypi/pywin32)
* Install [twisted][twi]. Paste the following commands into a terminal
  window:
    * Linux: `sudo pip install twisted`
    * Windows: `pip install twisted`
* Download
  [`tiny-dash.py`](https://raw.githubusercontent.com/Gustra/tiny-dash/0.1.0-p1/bin/tiny-dash.py)
  and store it somewhere.
* On Linux: make it executable: `chmod +x tiny-dash.py`

To run, just do:

* Linux: `./tiny-dash.py` _config-file_
* Windows: `python.exe tiny-dash.py` _config-file_

To exit the program, close the window or type Ctrl-Q.

## Brief introduction

Dashboard configurations are written in [YAML][yml], and are given as
arguments to the program, or stored in the user's home directory as
`.tiny-dash/config`. All configurations contains a list of dicts. Sample
configuration:

```
- name: Friday
  type: Lamp
  sensor: Status
  program: ['/usr/bin/is-it-friday']
- name: Load
  type: Meter
  sensor: Fraction
  program: ['/usr/bin/cpu-load']
  update-interval: 5.0
```

The content of the `name` attribute is displayed in the status bar at
the bottom of the window when moving the mouse over the indicator. Very
useful if there are a lot of indicators on the dashboard.

A very important setting is `update-interval` which determines the
polling interval for the sensors, e.g. "8.4". A sensor will wait for a
return value before waiting again, so there is no risk for calling the
same sensor in parallel.

Please read the
[User Guide](https://github.com/Gustra/tiny-dash/wiki/User-guide) for
more information.

## Demo configurations

* Linux: [examples/linux](examples/linux)
* Windows: [examples/windows](examples/windows)


[pyt]: https://www.python.org/
[tki]: https://wiki.python.org/moin/TkInter
[twi]: https://twistedmatrix.com/trac/
[yml]: http://yaml.org/
