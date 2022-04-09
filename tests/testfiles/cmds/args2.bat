@ECHO OFF
IF not "%~1" == "four" goto error
IF not "%~2" == "five six" goto error
IF not "%~3" == "seven" goto error

goto :EOF

:error
echo assert2 failed 1>&2
exit /b 1
