@echo off

set qtenv=%1
set vcvarsall=%2
set bits=%3
set tmp_path=%4
set prj_path=%5
set target=%6

echo %qtenv%
echo %vcvarsall% %bits%
echo %tmp_path%
echo %prj_path%
echo %target%

call %qtenv%
call %vcvarsall% %bits%

cd /D %tmp_path%
qmake %prj_path%
nmake %target%
