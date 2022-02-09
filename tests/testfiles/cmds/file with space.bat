@ECHO OFF
IF not "%~1" == "one two" goto error

goto :eof

:error
echo assert failed 1>&2
exit /b 1
