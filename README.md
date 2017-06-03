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

_Note_: it has only been tested on Linux at the moment.

## Installation

Tiny dash is written in Python and uses [twisted][twi] for
asynchronous command execution and [Tkinter][tki] for presentation.

See the
[Tkinter wiki](https://tkinter.unpythonic.net/wiki/How_to_install_Tkinter)
for information on how to install Tkinter on your system.

Install twisted. Paste the following commands into a terminal window:

```
sudo pip install twisted
# Clone the tiny-dash repository:
git clone https://github.com/Gustra/tiny-dash.git
# To run, just do:
./tiny-dash/bin/tiny-dash.py <config file>
```

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
[documentation](https://github.com/Gustra/tiny-dash/wiki/User-guide) for
more information.


[tki]: https://wiki.python.org/moin/TkInter
[twi]: https://twistedmatrix.com/trac/
[yml]: http://yaml.org/
