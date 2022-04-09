$enc = [System.Text.Encoding]::Unicode
$out = $enc.GetBytes("one two three`r`n")
$stdout = [System.Console]::OpenStandardOutput();
$stdout.Write($out, 0, $out.Length)

$stderr = [System.Console]::OpenStandardError()
$err = $enc.GetBytes("four`r`n")
$stderr.Write($err, 0, $err.Length)