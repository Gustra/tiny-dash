#!/usr/bin/env bash

set -euo pipefail

for type in $(ls docs/shots/*.config); do
    bname=$(basename ${type%.config})
    name=$(basename ${bname%-*})
    geometry=$(basename ${bname##*-})
    ./bin/tiny-dash.py $type --geometry ${geometry}+0+0 &
    pid=$!
    sleep 3
    scrot -u docs/images/${name}.png
    kill $pid
done

