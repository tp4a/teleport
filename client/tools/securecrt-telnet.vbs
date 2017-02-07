#$language = "VBScript"
#$interface = "1.0"
Sub main
  crt.Screen.Synchronous = True
  crt.Screen.Send "session:" & crt.Arguments(0) & VbCr
  crt.Screen.Synchronous = False
End Sub
