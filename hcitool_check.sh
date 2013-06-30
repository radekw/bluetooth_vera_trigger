#!/bin/bash

DEVICE=$(echo $1 |tr '[:lower:]' '[:upper:]')

for s in $(/usr/bin/hcitool con); do
    if [ "$s" == "$DEVICE" ]; then
        echo "$DEVICE connected already"
        exit 0
    fi
done

if [ -z "$(/usr/bin/hcitool cc $DEVICE 2>&1)" ]; then
    echo "$DEVICE connected"
    /usr/bin/hcitool rssi $DEVICE
    /usr/bin/hcitool dc $DEVICE
    exit 0
fi

echo "$DEVICE not available"
exit 1

