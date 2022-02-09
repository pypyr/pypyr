#!/bin/sh
err(){
    echo assert failed >&2
    exit 1
}

if [ "$1" != "one" ]; then err; fi
if [ "$2" != "two two" ]; then err; fi
if [ "$3" != three ]; then err; fi

