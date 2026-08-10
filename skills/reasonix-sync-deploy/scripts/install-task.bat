@echo off
rem ============================================================
rem  ReasonixSync task installer (wrapper -> install-tasks.ps1)
rem  Run once per machine (your normal user, NOT as administrator):
rem      install-task.bat            -> Push + Pull tasks
rem      install-task.bat organizer  -> ALSO the weekly Organize
rem                                     task (main machine only)
rem  All tasks have StartWhenAvailable: if the machine is off at
rem  the scheduled time, the task runs as soon as it boots.
rem  Machine name is auto-detected (COMPUTERNAME); no config needed.
rem ============================================================
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0install-tasks.ps1" %*
pause
