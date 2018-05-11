#!/bin/bash

PATH_ROOT=$(cd "$(dirname "$0")/.."; pwd)

echo "compiling applescripts for OS X terminal..."

rm ${PATH_ROOT}/src/apple-scpt/Terminal.scpt
rm ${PATH_ROOT}/src/apple-scpt/iTerm2.scpt

osacompile -o ${PATH_ROOT}/src/apple-scpt/Terminal.scpt -x ${PATH_ROOT}/apple-scripts/scripts/Terminal.applescript
osacompile -o ${PATH_ROOT}/src/apple-scpt/iTerm2.scpt -x ${PATH_ROOT}/apple-scripts/scripts/iTerm2.applescript
