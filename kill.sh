#!/bin/bash
ps aux | grep runserver | grep -v grep | awk '{print $2}'| xargs kill -9
