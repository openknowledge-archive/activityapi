#!/bin/bash

pip freeze --local >requirements.txt
echo 'newrelic' >>requirements.txt
