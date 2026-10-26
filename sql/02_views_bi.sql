CREATE VIEW bi.vw_Fato_Ideias AS
SELECT CAST(i.id_ideia AS NVARCHAR(20)) AS Chave_Primaria, i.titulo AS Titulo,
       CAST(i.id_etapa_atual AS BIGINT) AS ID_Estado,
       CAST(i.id_campanha AS BIGINT) AS ID_Campanha,
       CAST(i.id_tema AS BIGINT) AS ID_Tema,
       CAST(i.data_criacao AS DATETIME2(0)) AS [resultado.CriadoEm]
FROM dw.fato_ideia i;
GO
CREATE VIEW bi.vw_Dim_Estado AS
SELECT CAST(id_etapa AS NVARCHAR(10)) AS Id_Estado, estado AS Estados
FROM dw.dim_etapa;
GO
CREATE VIEW bi.vw_Dim_Tema AS
SELECT CAST(id_tema AS NVARCHAR(10)) AS ID_Tema, nome AS Nome_tema FROM dw.dim_tema;
GO
CREATE VIEW bi.vw_Dim_Colaboradores AS
SELECT CAST(i.id_ideia AS NVARCHAR(20)) AS Chave_Primaria, p.nome AS Nome_Colaborador
FROM dw.fato_ideia i JOIN dw.dim_pessoa p ON p.id_pessoa = i.id_autor
UNION ALL
SELECT CAST(c.id_ideia AS NVARCHAR(20)), p.nome
FROM dw.ponte_ideia_coautor c JOIN dw.dim_pessoa p ON p.id_pessoa = c.id_pessoa;
GO
CREATE VIEW bi.vw_Dim_Elaborador AS
SELECT CAST(i.id_ideia AS BIGINT) AS Chave_Primaria, p.nome AS Nome_elaborador
FROM dw.fato_ideia i JOIN dw.dim_pessoa p ON p.id_pessoa = i.id_autor;
GO
CREATE VIEW bi.vw_Dim_SLA_Ideias AS
SELECT CAST(m.id_ideia AS NVARCHAR(20)) AS Chave_Primaria,
       CAST(m.data_entrada AS DATETIME2(0)) AS Data_de_Entrada,
       CAST(m.data_saida AS DATETIME2(0)) AS Data_de_Saida,
       e.estado AS Andamento_Etapa,
       CAST(DATEDIFF(DAY, m.data_entrada, COALESCE(m.data_saida, (SELECT MAX(data_referencia) FROM dw.meta_carga))) AS BIGINT)
           AS Dias_na_Etapa
FROM dw.fato_movimentacao m JOIN dw.dim_etapa e ON e.id_etapa = m.id_etapa;
GO
CREATE VIEW bi.vw_Dim_Valores AS
SELECT CAST(id_ideia AS NVARCHAR(20)) AS Chave_Primaria,
       CAST(investimento_real AS FLOAT) AS [Valor investido (R$):],
       CAST(investimento_previsto AS DECIMAL(18,2)) AS [Qual investimento previsto para implementar?],
       CAST(ganho_previsto_12m AS FLOAT) AS [Qual a previsão de ganho (R$) em 12 meses?],
       CASE WHEN ganho_previsto_12m IS NULL OR ganho_previsto_12m <= 0 THEN N'0-Sem valor'
            WHEN ganho_previsto_12m <= 50000 THEN N'1-Até 50K'
            WHEN ganho_previsto_12m <= 100000 THEN N'2-50K até 100K'
            WHEN ganho_previsto_12m <= 500000 THEN N'3-100K até 500K'
            ELSE N'4-500K até 1M' END AS Faixa
FROM dw.fato_ideia;
GO
CREATE VIEW bi.vw_Dim_Data AS
SELECT CAST(i.id_ideia AS NVARCHAR(20)) AS [resultado.Id],
       CAST(COALESCE(i.data_aprovacao, i.data_reprovacao) AS DATETIME2(0)) AS Data_Aprovaca_Final,
       CAST(i.data_criacao AS DATETIME2(0)) AS Data_de_Criacao
FROM dw.fato_ideia i;
GO
CREATE VIEW bi.vw_Dim_Empresa_Campanha AS
SELECT u.nome AS Empresa, c.tipo AS Tipo_Campanha, CAST(c.id_campanha AS BIGINT) AS ID_Campanha,
       u.sigla AS [Abreviação]
FROM dw.dim_campanha c JOIN dw.dim_unidade u ON u.id_unidade = c.id_unidade;
GO
CREATE VIEW bi.vw_Dim_Ganhos_Indiretos AS
SELECT CAST(g.id_ideia AS NVARCHAR(20)) AS Primaria_Key, t.nome AS Ganhos_Indiretos
FROM dw.ponte_ideia_ganho g JOIN dw.dim_tipo_ganho t ON t.id_tipo_ganho = g.id_tipo_ganho;
GO
CREATE VIEW bi.vw_Planilha AS
SELECT u.nome AS [Unidade de Prestação Serviço], p.nome AS [Funcionário]
FROM dw.dim_pessoa p JOIN dw.dim_unidade u ON u.id_unidade = p.id_unidade;
GO
CREATE VIEW bi.vw_TabelaFuncionarios AS
SELECT sigla AS Empresa, CAST(qtd_funcionarios AS BIGINT) AS Funcionarios FROM dw.dim_unidade;
GO
CREATE VIEW bi.vw_Referencia AS
SELECT CAST(MAX(data_referencia) AS DATETIME2(0)) AS Hoje FROM dw.meta_carga;
GO
