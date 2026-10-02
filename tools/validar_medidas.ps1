param([int]$Porta = 0)
$ErrorActionPreference = 'Stop'
$bin = Split-Path (Get-Process msmdsrv | Select-Object -First 1).Path
Add-Type -Path (Join-Path $bin 'Microsoft.PowerBI.AdomdClient.dll')

function Abrir([int]$p) {
    $c = New-Object Microsoft.AnalysisServices.AdomdClient.AdomdConnection("Data Source=localhost:$p"); $c.Open(); $c
}
if ($Porta -eq 0) {
    $ids = @((Get-Process msmdsrv).Id)
    $portas = netstat -ano | Select-String 'LISTENING' | ForEach-Object {
        $f = @(($_.Line.Trim() -split '\s+'))
        if ($ids -contains [int]$f[-1] -and $f[1] -like '127.0.0.1:*') { [int]($f[1].Split(':')[-1]) }
    } | Sort-Object -Unique
    foreach ($p in $portas) {
        $achou = $false
        try {
            $c = Abrir $p; $cmd = $c.CreateCommand()
            $cmd.CommandText = "SELECT [Name] FROM `$SYSTEM.TMSCHEMA_TABLES WHERE [Name] = 'Fato_Ideias'"
            $r = $cmd.ExecuteReader(); $achou = $r.Read(); $r.Close(); $c.Close()
        } catch { }
        if ($achou) { $Porta = $p; break }
    }
    if ($Porta -eq 0) { throw 'Modelo PainelIdeias nao encontrado. Abra powerbi\PainelIdeias.pbip e atualize.' }
}
$c = Abrir $Porta
$cmd = $c.CreateCommand(); $cmd.CommandText = 'SELECT [Name] FROM $SYSTEM.TMSCHEMA_MEASURES'
$r = $cmd.ExecuteReader(); $medidas = @(); while ($r.Read()) { $medidas += [string]$r.GetValue(0) }; $r.Close()
$cmd.CommandText = 'EVALUATE ROW("n", COUNTROWS(Fato_Ideias))'
$r = $cmd.ExecuteReader(); $null = $r.Read(); $linhas = $r.GetValue(0); $r.Close()
if (-not $linhas) { throw 'Fato_Ideias vazia: atualize o modelo no Power BI Desktop.' }

$baseline = @()
$arqBase = Join-Path $env:LOCALAPPDATA 'PainelIdeias\baseline_medidas.json'
if (Test-Path $arqBase) { $baseline = @(Get-Content $arqBase -Raw -Encoding UTF8 | ConvertFrom-Json | ForEach-Object { $_ }) }
$novas = @()
foreach ($m in $medidas) {
    $x = $c.CreateCommand(); $x.CommandText = 'EVALUATE ROW("v", [' + $m.Replace(']', ']]') + '])'
    try { $rr = $x.ExecuteReader(); while ($rr.Read()) {}; $rr.Close() }
    catch {
        $msg = if ($_.Exception.InnerException) { $_.Exception.InnerException.Message } else { $_.Exception.Message }
        if ($baseline -notcontains $m) { $novas += "$m :: $msg" }
    }
}
$c.Close()
"Porta $Porta | Fato_Ideias: $linhas linhas | medidas: $($medidas.Count) | erros novos: $($novas.Count)"
if ($novas.Count) { $novas | ForEach-Object { "  $_" }; exit 1 }
