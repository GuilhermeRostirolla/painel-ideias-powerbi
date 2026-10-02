param(
    [Parameter(Mandatory = $true)][string]$Saida,
    [double[]]$Regiao = @(0.1209, 0.1587, 0.8640, 0.8938)
)
Add-Type -AssemblyName System.Drawing, System.Windows.Forms
Add-Type -Namespace Win -Name Dpi -MemberDefinition '[DllImport("user32.dll")] public static extern bool SetProcessDPIAware();'
[Win.Dpi]::SetProcessDPIAware() | Out-Null
$tela = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds
$x = [int]($tela.Width * $Regiao[0]); $y = [int]($tela.Height * $Regiao[1])
$w = [int]($tela.Width * ($Regiao[2] - $Regiao[0])); $h = [int]($tela.Height * ($Regiao[3] - $Regiao[1]))
$bmp = New-Object System.Drawing.Bitmap $w, $h
$g = [System.Drawing.Graphics]::FromImage($bmp)
$g.CopyFromScreen($tela.X + $x, $tela.Y + $y, 0, 0, $bmp.Size)
$bmp.Save($Saida, [System.Drawing.Imaging.ImageFormat]::Png)
$g.Dispose(); $bmp.Dispose()
"$Saida ($w x $h)"
