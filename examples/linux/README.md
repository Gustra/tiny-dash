# Linux demo section

This is just a collection of silly programs and configuration which can
demo tiny-dash. To test the configurations here, first:

```
source env.sh
```

Then run the configs individually or all at once:

```
tiny-dash.py <file>.config
tiny-dash.py *.config
```

## Program descriptions

* `is-second`: exits 0 if current second is even, else exit 1
* `modulo-seconds`: seconds % argument (state change emulation)
* `off-sensor`: exits 1
* `print-minute-fill.py`: print seconds/60.0 (fraction of minute)
