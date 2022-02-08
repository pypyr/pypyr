@ECHO OFF
IF not "%~1" == "one" goto error
IF not "%~2" == "two two" goto error
IF not "%~3" == "three" goto error

goto :EOF

:error
echo assert failed 1>&2
exit /b 1
