Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
scriptPath = fso.GetParentFolderName(WScript.ScriptFullName)
WshShell.CurrentDirectory = scriptPath
pythonPath = "C:\Users\ASUS\AppData\Local\Programs\Python\Python313\pythonw.exe"
WshShell.Run """" & pythonPath & """ """ & scriptPath & "\gui_launcher.py""", 0, False
