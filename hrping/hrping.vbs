Dim WshShell, strCommand, WshShellExec
Const WshFinished = 1
Const WshFailed = 2

If WScript.Arguments.Count = 0 Then
  WScript.Echo "hrping.vbs IP_ADDRESS"
  WScript.Quit
End If

strCommand = "c:\project\hrping\hrping.exe -q " + WScript.Arguments.Item(0)


Set WshShell = CreateObject("WScript.Shell")
wshShell.RegWrite "HKCU\Software\cFos\hrPING\5.07\LicenseAccepted", 1, "REG_DWORD"
Set WshShellExec = WshShell.Exec(strCommand)

While WshShellExec.Status = WshRunning
    WScript.Sleep 50
Wend

Select Case WshShellExec.Status
   Case WshFinished
       strOutput = WshShellExec.StdOut.ReadAll
   Case WshFailed
       strOutput = WshShellExec.StdErr.ReadAll
End Select

If InStr(1, strOutput, "RTT", vbTextCompare) > 0 then
   Dim MString, RTTString, MAXtime

   MString = split(strOutput, vbCrLf)
   RTTString = MString(8)
   Alltime = split(RTTString, "/")
   MAXTime = Alltime(5)
   WScript.Echo Trim(MAXTime)
   
Else
  WScript.Echo 0
End If

