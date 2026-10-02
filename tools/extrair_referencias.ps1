param([Parameter(Mandatory = $true)][int]$Porta, [Parameter(Mandatory = $true)][string]$TabelaTitulos)
$ErrorActionPreference = 'Stop'
$raiz = Split-Path $PSScriptRoot -Parent
$py = Join-Path $raiz '.venv\Scripts\python.exe'
$pasta = Join-Path $env:LOCALAPPDATA 'PainelIdeias'
New-Item -ItemType Directory -Force $pasta | Out-Null

$bin = Split-Path (Get-Process msmdsrv | Select-Object -First 1).Path
Add-Type -Path (Join-Path $bin 'Microsoft.PowerBI.AdomdClient.dll')
$c = New-Object Microsoft.AnalysisServices.AdomdClient.AdomdConnection("Data Source=localhost:$Porta")
$c.Open()

function Valores([string]$dax) {
    $cmd = $c.CreateCommand(); $cmd.CommandText = $dax
    $r = $cmd.ExecuteReader()
    while ($r.Read()) { if (-not $r.IsDBNull(0)) { [string]$r.GetValue(0) } }
    $r.Close()
}
function Gravar([string[]]$textos, [string]$destino, [int]$minPalavras = 1) {
    $OutputEncoding = New-Object System.Text.UTF8Encoding($false)
    $textos | & $py (Join-Path $PSScriptRoot 'hashes.py') $destino --min-palavras $minPalavras
}

$a = [char]0x00E1; $c7 = [char]0x00E7; $a3 = [char]0x00E3
$funcionario = "Funcion${a}rio"
$unidadeCol = "Unidade de Presta${c7}${a3}o Servi${c7}o"
$abrev = "Abrevia${c7}${a3}o"

$pessoas = @()
$pessoas += Valores 'EVALUATE DISTINCT(Dim_Colaboradores[Nome_Colaborador])'
$pessoas += Valores 'EVALUATE DISTINCT(Dim_Elaborador[Nome_elaborador])'
$pessoas += Valores "EVALUATE DISTINCT(Planilha[$funcionario])"
$pessoas += Valores "EVALUATE DISTINCT(Planilha[Nome do Gestor])"
$pessoas += Valores "EVALUATE DISTINCT(Dim_Funcionarios[$funcionario])"
$pessoas += Valores 'EVALUATE DISTINCT(Dim_Implantacao_Responsavel[ID_Responsavel_Pela_Implantacao])'
$pessoas += Valores "EVALUATE DISTINCT('Dim_Reprovadas'[resultado.Elaborador.Name])"
$titulos = Valores "EVALUATE DISTINCT('$TabelaTitulos'[Titulo])"
Gravar ($pessoas + $titulos) (Join-Path $pasta 'blocklist.sha256')

$empresas = @()
$empresas += Valores 'EVALUATE DISTINCT(Dim_Empresa_Campanha[Empresa])'
$empresas += Valores "EVALUATE DISTINCT(Dim_Empresa_Campanha[$abrev])"
$empresas += Valores 'EVALUATE DISTINCT(TabelaFuncionarios[Empresa])'
$empresas += Valores "EVALUATE DISTINCT(Planilha[$unidadeCol])"
$empresas += ($empresas | ForEach-Object { $_ -split '\s+' } | Where-Object { $_.Length -ge 3 })
Gravar $empresas (Join-Path $pasta 'proibidos.sha256')

$tax = @()
$tax += Valores 'EVALUATE DISTINCT(Dim_Tema[Nome_tema])'
$tax += Valores 'EVALUATE DISTINCT(Dim_Ganhos_Indiretos[Ganhos_Indiretos])'
$tax += Valores 'EVALUATE DISTINCT(Dim_Surgimento[Surgimento_ideia])'
$tax += Valores "EVALUATE DISTINCT('Dim_Reprovadas'[resultado.MotivoReprovacao])"
Gravar $tax (Join-Path $pasta 'proibidos.sha256') 3

$cmd = $c.CreateCommand(); $cmd.CommandText = 'SELECT [Name] FROM $SYSTEM.TMSCHEMA_MEASURES'
$r = $cmd.ExecuteReader(); $medidas = @(); while ($r.Read()) { $medidas += [string]$r.GetValue(0) }; $r.Close()
$falhas = @()
foreach ($m in $medidas) {
    $q = 'EVALUATE ROW("v", [' + $m.Replace(']', ']]') + '])'
    try { $x = $c.CreateCommand(); $x.CommandText = $q; $rr = $x.ExecuteReader(); while ($rr.Read()) {}; $rr.Close() }
    catch { $falhas += $m }
}
$c.Close()
ConvertTo-Json @($falhas) | Out-File (Join-Path $pasta 'baseline_medidas.json') -Encoding utf8
"Medidas: $($medidas.Count); com erro no original: $($falhas.Count)"
