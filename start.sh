#!/bin/bash

echo "$@"
nearup "$@" && while true; do sleep 1; done
