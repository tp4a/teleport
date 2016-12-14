@echo off

sc stop "EOM Teleport Core Service" >nul
sc start "EOM Teleport Core Service" >nul

sc stop "EOM Teleport Web Service" >nul
sc start "EOM Teleport Web Service" >nul

