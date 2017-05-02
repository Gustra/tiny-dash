# tiny-dash User Guide

## Introduction

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
  update-interval: 2.0
```

The content of the `name` attribute is displayed in the status bar at
the bottom of the window when moving the mouse over the indicator. Very
useful if there are a lot of indicators on the dashboard.

A very important setting is `update-interval` which determines the
polling interval in seconds for the sensors, e.g. "8.4". A sensor will
wait for a return value before waiting again, so there is no risk for
calling the same sensor in parallel.

## Sensors

### Status sensor

Calls `program` and senses the exit status:

| Status | Setting |
|:-------|:--------|
| = 0    | On  (on-color) |
| > 0    | Off (off-color) |
| < 0    | Broken (broken-color) |

Example: program which tests whether Foo server thinks it is running:

```
#!/usr/bin/env bash
test -f /var/run/foo.pid || exit 1
exec ps -o pid= -p $(cat /var/run/foo.pid) > /dev/null
```

### State sensor

Calls `program` which prints the state on stdout, e.g. `stopped`,
`running`, `success` etc. This example prints the process state:

```
#!/usr/bin/env bash
set -euo pipefail
ps -o state= $(cat /var/run/foo.pid)
```

### Fraction sensor

Calls `program` which prints a fraction 0.0-1.0 on stdout. Here is a
program which prints seconds as a fraction of a minute:

```
#!/usr/bin/env python

import time
import sys

print float(int(time.time())%60)/60.0
sys.exit(0)
```

### Configuration summary

Some of the options only makes sense for certain sensors and indicators.
Configurations for both the sensor and the indicator are stored in the
same entry, and any unrecognized setting is ignored, of course. The
minimal configurations are `type`, `sensor` and `program`.

|  Configuration  |  Description  |  Default  |
|:----------------|:--------------|:----------|
|`broken-color`   | Color to show when the sensor is "broken" | black |
|`default-color`  | Color to show for unknown states          | `broken-color` |
|`defaults`       | Reset and change default values           | |
|`defaults+`      | Add to default values                     | |
|`height`         | Height of the indicator                   | 40 |
|`max-angle`      | Ending angle relative to start-angle for meters | 360.0 |
|`max-color`      | Color for fraction 0.0                    | red |
|`min-color`      | Color for fraction 1.0                    | green |
|`name`           | Text to display in status bar on mouse over | |
|`off-color`      | Color representing "off"                  | red |
|`on-color`       | Color representing "on"                   | green |
|`program`        | Program to run for sensors as a list      | |
|`sensor`         | Sensor to use, e.g `State`, `Status`, `Fraction` | |
|`shape`          | Indicator shape, e.g. `round`, `square`   | round |
|`start-angle`    | Angle where the meter arc starts          | 360.0 |
|`state-colors`   | A dict with state as key, and color as value | |
|`thickness`      | Thickness of a meter arc, 0.0 (none) to 1.0 (filled) | 0.5 |
|`type`           | indicator to use, e.g `Lamp`, `Meter`, `Broken` | |
|`update-interval` | How often to pull the sensor in seconds, e.g. 1.6 | 5.0 |
|`width`          | Width of the indicator                    | 40 |


## Defaults

The `defaults` key resets default values to default, and updates with
the given values. `defaults+` adds to the current default values,
overriding any current values. Any setting can be part of the defaults,
so to make a lot of lamps of the same type, just do this:

```
- defaults:
    type: Lamp
    sensor: Status
    on-color: yellow
    off-color: blue
- program: ['is-alive', 'foo']
- program: ['is-alive', 'bar']
- defaults+:
    shape: square
    on-color: green
- program: ['is-alive', 'zoq']
- program: ['is-alive', 'pik']
```

Any other keys in the entry are ignored:

```
- type: Lamp    # Ignored, no indicator is added to the dashboard
  defaults+:
    width: 80
```


To default all default values to default default values, give it an
empty default:

```
- defaults:
# This works too:
- defaults+:
```

## Indicators

### Lamps

Lamps can show values of type status, state and fraction, and can accept
values of these types in any order, but it can only show one at a time:

```
- defaults:
    type: Lamp
    on-color: green
    off-color: red
    state-colors:
        stopped: purple
        running: blue
        zombie: gangreen
    min-color: '#000000'
    max-color: '#ffffff'
    sensor: Status
    program: ['test', '-e', '/']
- sensor: State
  program: ['/bin/echo', 'stopped']
- sensor: State
  program: ['/bin/echo', 'running']
- sensor: Fraction
  program: ['echo', '0.01']
- sensor: Fraction
  program: ['echo', '0.5']
- sensor: Fraction
  program: ['echo', '0.99']
```

[![Colored lamp](images/lamp-colors.png)](shots/lamp-colors-250x80.config)

It can have one of two `shape`s: `round` (default) or `square`:

```
- defaults:
    type: Lamp
    sensor: Status
- shape: round
  program: ['test', '-e', '/']
- shape: square
  program: ['test', '-f', '/']
```

[![Lamp shapes](images/lamp-shapes.png)](shots/lamp-shapes-84x80.config)

### Meter

Meters show a fraction, e.g. som kind of progress or level, as an arc:

```
- type: Meter
  sensor: Fraction
  program: ['echo', '0.75']
```

[![Simple meter](images/meter-simple.png)](shots/meter-simple-44x80.config)

It can start at any angle and move clockwise or counter-clockwise:

```
- defaults:
    program: ['echo', '0.99']
    sensor: Fraction
- type: Meter
  start-angle: 0.0
  max-angle: -90.0
- type: Meter
  start-angle: 180.0
  max-angle: 180.0
```

[![Meter angles](images/meter-angles.png)](shots/meter-angles-84x80.config)

The `thickness` of the arc can be set to a value between 0.0 and 1.0:

```
- defaults:
    program: ['echo', '0.4']
    sensor: Fraction
- type: Meter
  thickness: 0.2
- type: Meter
  thickness: 1.0
```

[![Meter thickness](images/meter-thickness.png)](shots/meter-thickness-84x80.config)

The meter can change color based on the fraction:

```
- defaults:
    sensor: Fraction
- type: Meter
  program: ['echo', '0.3']
  min-color: yellow
  max-color: blue
- type: Meter
  program: ['echo', '0.83']
  thickness: 1.0
  min-color: blue
  max-color: magenta
  max-angle: -180.0
```

[![Lamp shapes](images/meter-color.png)](shots/meter-color-84x80.config)


## Layout

Nope, none, sorry. The dashboard will simply put as many indicators as
fits on a line from left to right, and then continue on a new line.
Overflowing indicators will be outside the window, and there is no
scrollbar...just to be annoying.

All hope is not lost though. By using clever sizes and dividers, some
resemblance of order can be created:

[![Layout example](images/layout-example.png)](shots/layout-example-168x200.config)

### Divider

This is just an empty indicator which creates some space in the
dashboard. Just create a meter with zero value:

```
- type: Meter
  sensor: Fraction
  program: ['echo', '0.0']
  width: 20
  height: 20
  # Update the sensor at the start, and never again
  update-interval: 9999999999999999999.0
```


## References

[pyt]: https://www.python.org/
[tki]: https://wiki.python.org/moin/TkInter
[twi]: https://twistedmatrix.com/trac/
[yml]: http://yaml.org/
