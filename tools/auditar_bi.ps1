param([Parameter(Mandatory = $true)][int]$Porta, [Parameter(Mandatory = $true)][string]$Saida)
$ErrorActionPreference = 'Stop'
$bin = Split-Path (Get-Process msmdsrv | Select-Object -First 1).Path
Add-Type -Path (Join-Path $bin 'Microsoft.PowerBI.AdomdClient.dll')
$c = New-Object Microsoft.AnalysisServices.AdomdClient.AdomdConnection("Data Source=localhost:$Porta"); $c.Open()

function Tabela([string]$dax) {
    $cmd = $c.CreateCommand(); $cmd.CommandText = $dax; $r = $cmd.ExecuteReader(); $linhas = @()
    while ($r.Read()) { $v = @(); for ($i = 0; $i -lt $r.FieldCount; $i++) { $v += "$($r.GetValue($i))" }; $linhas += ($v -join ' | ') }
    $r.Close(); $linhas
}
$out = New-Object System.Collections.Generic.List[string]
$cmd = $c.CreateCommand(); $cmd.CommandText = 'SELECT [Name], [FormatString], [DisplayFolder] FROM $SYSTEM.TMSCHEMA_MEASURES'
$r = $cmd.ExecuteReader(); $medidas = @(); while ($r.Read()) { $medidas += , @("$($r.GetValue(0))", "$($r.GetValue(1))", "$($r.GetValue(2))") }; $r.Close()
$out.Add('## MEDIDAS (contexto total)')
foreach ($m in $medidas) {
    $q = 'EVALUATE ROW("v", [' + $m[0].Replace(']', ']]') + '])'
    try { $v = (Tabela $q) -join '' } catch { $v = '<ERRO>' }
    $out.Add("$($m[0]) [fmt=$($m[1])] = $v")
}
$out.Add('## FINANCEIRO POR EMPRESA (Prev/Inv/Ganho em R$ mi)')
$out.AddRange([string[]](Tabela 'EVALUATE SUMMARIZECOLUMNS(Fato_Ideias[Empresa_Sigla], "prev", [Prev Mil], "inv", [Inv Mil], "ganho", [Ganho Mil])'))
$out.Add('## ONDE ESTA O VALOR PREVISTO (por etapa)')
$out.AddRange([string[]](Tabela 'EVALUATE SUMMARIZECOLUMNS(Fato_Ideias[Etapa_Atual], "txt", [Txt Onde Valor], "ideias", [Txt Onde Ideias])'))
$out.Add('## TABELA DE INVESTIMENTO: vazios por coluna (ideias com investimento)')
$out.AddRange([string[]](Tabela 'EVALUATE ROW("ideias", COUNTROWS(FILTER(Fato_Ideias, Fato_Ideias[Previsto_Idea] > 0)), "prev_vazio", COUNTROWS(FILTER(Fato_Ideias, Fato_Ideias[Previsto_Idea] > 0 && ISBLANK(Fato_Ideias[Ganho_Idea]))), "inv_zero", COUNTROWS(FILTER(Fato_Ideias, Fato_Ideias[Previsto_Idea] > 0 && Fato_Ideias[Investido_Idea] = 0)))'))
$out.Add('## ETAPAS (qtde de ideias por etapa atual)')
$out.AddRange([string[]](Tabela 'EVALUATE SUMMARIZECOLUMNS(Fato_Ideias[Etapa_Atual], "n", COUNTROWS(Fato_Ideias))'))
$out.Add('## ENGAJAMENTO POR EMPRESA')
$out.AddRange([string[]](Tabela 'EVALUATE SUMMARIZECOLUMNS(Dim_Empresa_Campanha[Empresa_Sigla], "eng", [Taxa_Engajamento (%)])'))
$c.Close()
$out | Out-File $Saida -Encoding utf8
"linhas: $($out.Count) -> $Saida"
