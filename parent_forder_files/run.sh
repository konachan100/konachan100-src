#!/bin/bash
while true
do
    bash update.sh >> log.txt
    python trimlog.py
    sleep 300s
done

