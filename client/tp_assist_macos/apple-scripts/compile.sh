#!/bin/bash

PATH_ROOT=$(cd "$(dirname "$0")/.."; pwd)

echo "compiling applescripts for OS X terminal..."

rm ${PATH_ROOT}/src/apple-scpt/terminal.scpt
rm ${PATH_ROOT}/src/apple-scpt/iterm2.scpt

osacompile -o ${PATH_ROOT}/src/apple-scpt/terminal.scpt -x ${PATH_ROOT}/apple-scripts/scripts/terminal.applescript
osacompile -o ${PATH_ROOT}/src/apple-scpt/iterm2.scpt -x ${PATH_ROOT}/apple-scripts/scripts/iterm2.applescript
