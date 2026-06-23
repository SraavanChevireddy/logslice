# VHS tape for logslice demo. Render with:  vhs demo/demo.tape
Output demo/demo.gif

Set Shell "bash"
Set FontSize 16
Set Width 1300
Set Height 760
Set Theme "Catppuccin Mocha"
Set Padding 20
Set TypingSpeed 45ms
Set LoopOffset 55%

Hide
Type "export PATH=/tmp/demoenv/bin:$PATH && clear" Enter
Show

Type "# logslice: follow one request across all your service logs" Sleep 1s Enter
Type "ls examples/" Sleep 500ms Enter
Sleep 2s

Type "# three services, three log formats, one trace id" Sleep 1s Enter
Type "logslice req-7f3a examples/*.log" Sleep 500ms Enter
Sleep 5s
