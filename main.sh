#!/bin/bash

#PATH=/usr/local/bin:/usr/bin/minizinc:/usr/share/minizinc:$PATH

PATH=$(realpath ./MiniZincIDE-2.7.6-bundle-linux-x86_64/bin):$(realpath ./MiniZincIDE-2.7.6-bundle-linux-x86_64/lib):$(realpath ./MiniZincIDE-2.7.6-bundle-linux-x86_64/share):$(realpath ./ampl.linux-intel64):$PATH
#LD_LIBRARY_PATH=$(realpath ./MiniZincIDE-2.7.6-bundle-linux-x86_64/lib):$LD_LIBRARY_PATH

python3 ./main.py
