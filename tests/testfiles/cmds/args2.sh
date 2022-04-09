#!/bin/sh
err(){
    echo assert2 failed >&2
    exit 1
}

if [ "$1" != "four" ]; then err; fi
if [ "$2" != "five six" ]; then err; fi
if [ "$3" != seven ]; then err; fi

