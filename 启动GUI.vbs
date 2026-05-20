Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
scriptPath = fso.GetParentFolderName(WScript.ScriptFullName)
WshShell.CurrentDirectory = scriptPath

' 1. 优先使用虚拟环境中的 Python
venvPython = scriptPath & "\venv\Scripts\pythonw.exe"
If fso.FileExists(venvPython) Then
    WshShell.Run """" & venvPython & """ """ & scriptPath & "\gui_launcher.py""", 0, False
    WScript.Quit 0
End If

' 2. 从 PATH 中查找 pythonw
Set env = WshShell.Environment("PROCESS")
pythonwPath = env("PATH")
paths = Split(pythonwPath, ";")
found = False
For Each path In paths
    If Right(path, 1) <> "\" Then path = path & "\"
    candidate = path & "pythonw.exe"
    If fso.FileExists(candidate) Then
        WshShell.Run """" & candidate & """ """ & scriptPath & "\gui_launcher.py""", 0, False
        found = True
        Exit For
    End If
Next

' 3. 尝试 python.exe
If Not found Then
    For Each path In paths
        If Right(path, 1) <> "\" Then path = path & "\"
        candidate = path & "python.exe"
        If fso.FileExists(candidate) Then
            WshShell.Run """" & candidate & """ """ & scriptPath & "\gui_launcher.py""", 0, False
            found = True
            Exit For
        End If
    Next
End If

' 4. 全部失败
If Not found Then
    MsgBox "找不到 Python 环境。" & vbCrLf & vbCrLf & "请运行 install.bat 完成安装，或手动安装 Python 3.9+。", vbExclamation, "PDF 笔记生成器"
End If
