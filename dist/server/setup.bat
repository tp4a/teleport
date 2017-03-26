@echo off

pushd %~dp0
set TPINST_ROOT=%cd%
popd

:: Check admin permission by create a temp file in system32 folder.
set TempFile=%SystemRoot%\System32\6A5D77DDFCFB40CEB26A8444EEC5757E%Random%.tmp
(echo "check" >%TempFile%) 1>nul 2>nul

if not exist %TempFile% goto NOT_ADMIN
del %TempFile% 1>nul 2>nul

"%TPINST_ROOT%\data\bin\tp_web.exe" --py "%TPINST_ROOT%\script\main.py"
goto END

:NOT_ADMIN
	echo.
	echo Teleport Server Setup requires administrator rights!
	echo.

	goto END

:END
	echo.
	echo.
	echo press any key to exit...
	pause >nul
