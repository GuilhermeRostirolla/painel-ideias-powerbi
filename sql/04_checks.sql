SET NOCOUNT ON;
WITH abertas AS (
    SELECT id_ideia, SUM(CASE WHEN data_saida IS NULL THEN 1 ELSE 0 END) AS n
    FROM dw.fato_movimentacao GROUP BY id_ideia),
faixas AS (
    SELECT DISTINCT CASE WHEN Dias_na_Etapa <= 15 THEN 1 WHEN Dias_na_Etapa <= 30 THEN 2
                         WHEN Dias_na_Etapa <= 60 THEN 3 ELSE 4 END AS f
    FROM bi.vw_Dim_SLA_Ideias)
SELECT 'ideias existem' AS check_nome, CASE WHEN (SELECT COUNT(*) FROM dw.fato_ideia) > 0 THEN 1 ELSE 0 END AS ok
UNION ALL SELECT '1 etapa aberta por ideia', CASE WHEN NOT EXISTS (SELECT 1 FROM abertas WHERE n <> 1) THEN 1 ELSE 0 END
UNION ALL SELECT 'sem entrada futura', CASE WHEN NOT EXISTS (SELECT 1 FROM dw.fato_movimentacao WHERE data_entrada > (SELECT MAX(data_referencia) FROM dw.meta_carga)) THEN 1 ELSE 0 END
UNION ALL SELECT '9 etapas com registro', CASE WHEN (SELECT COUNT(DISTINCT id_etapa) FROM dw.fato_movimentacao) = 9 THEN 1 ELSE 0 END
UNION ALL SELECT '4 faixas de dias', CASE WHEN (SELECT COUNT(*) FROM faixas) = 4 THEN 1 ELSE 0 END
UNION ALL SELECT '5 faixas de valor', CASE WHEN (SELECT COUNT(DISTINCT Faixa) FROM bi.vw_Dim_Valores) = 5 THEN 1 ELSE 0 END
UNION ALL SELECT 'movimento no mes atual', CASE WHEN EXISTS (SELECT 1 FROM dw.fato_movimentacao m CROSS JOIN dw.meta_carga r WHERE m.data_entrada >= DATEFROMPARTS(YEAR(r.data_referencia), MONTH(r.data_referencia), 1)) THEN 1 ELSE 0 END
UNION ALL SELECT 'vw_Fato_Ideias', CASE WHEN EXISTS (SELECT 1 FROM bi.vw_Fato_Ideias) THEN 1 ELSE 0 END
UNION ALL SELECT 'vw_Dim_Estado', CASE WHEN (SELECT COUNT(*) FROM bi.vw_Dim_Estado) = 9 THEN 1 ELSE 0 END
UNION ALL SELECT 'vw_Dim_Colaboradores', CASE WHEN EXISTS (SELECT 1 FROM bi.vw_Dim_Colaboradores) THEN 1 ELSE 0 END
UNION ALL SELECT 'vw_Dim_Elaborador 1:1', CASE WHEN (SELECT COUNT(*) FROM bi.vw_Dim_Elaborador) = (SELECT COUNT(*) FROM dw.fato_ideia) THEN 1 ELSE 0 END
UNION ALL SELECT 'vw_Dim_Data 1:1', CASE WHEN (SELECT COUNT(*) FROM bi.vw_Dim_Data) = (SELECT COUNT(*) FROM dw.fato_ideia) THEN 1 ELSE 0 END
UNION ALL SELECT 'vw_Dim_Valores 1:1', CASE WHEN (SELECT COUNT(*) FROM bi.vw_Dim_Valores) = (SELECT COUNT(*) FROM dw.fato_ideia) THEN 1 ELSE 0 END
UNION ALL SELECT 'vw_Dim_Ganhos_Indiretos', CASE WHEN EXISTS (SELECT 1 FROM bi.vw_Dim_Ganhos_Indiretos) THEN 1 ELSE 0 END
UNION ALL SELECT 'vw_Planilha', CASE WHEN EXISTS (SELECT 1 FROM bi.vw_Planilha) THEN 1 ELSE 0 END
UNION ALL SELECT 'vw_TabelaFuncionarios', CASE WHEN (SELECT COUNT(*) FROM bi.vw_TabelaFuncionarios) = 6 THEN 1 ELSE 0 END
UNION ALL SELECT 'vw_Dim_Empresa_Campanha', CASE WHEN (SELECT COUNT(*) FROM bi.vw_Dim_Empresa_Campanha) = 12 THEN 1 ELSE 0 END
UNION ALL SELECT 'vw_Referencia', CASE WHEN (SELECT COUNT(*) FROM bi.vw_Referencia WHERE Hoje IS NOT NULL) = 1 THEN 1 ELSE 0 END
UNION ALL SELECT 'vw_Dim_Tema', CASE WHEN (SELECT COUNT(*) FROM bi.vw_Dim_Tema) = 5 THEN 1 ELSE 0 END;
