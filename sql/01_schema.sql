CREATE SCHEMA dw;
GO
CREATE SCHEMA bi;
GO

CREATE TABLE dw.dim_unidade (
    id_unidade       INT          NOT NULL,
    nome             NVARCHAR(60) NOT NULL,
    sigla            NVARCHAR(20) NOT NULL,
    qtd_funcionarios INT          NOT NULL,
    CONSTRAINT pk_dim_unidade PRIMARY KEY (id_unidade),
    CONSTRAINT uq_dim_unidade_nome UNIQUE (nome),
    CONSTRAINT uq_dim_unidade_sigla UNIQUE (sigla),
    CONSTRAINT ck_dim_unidade_qtd CHECK (qtd_funcionarios > 0));

CREATE TABLE dw.dim_pessoa (
    id_pessoa  INT           NOT NULL,
    nome       NVARCHAR(120) NOT NULL,
    id_unidade INT           NOT NULL,
    id_gestor  INT           NULL,
    eh_gestor  BIT           NOT NULL,
    CONSTRAINT pk_dim_pessoa PRIMARY KEY (id_pessoa),
    CONSTRAINT uq_dim_pessoa_nome UNIQUE (nome),
    CONSTRAINT fk_dim_pessoa_dim_unidade FOREIGN KEY (id_unidade) REFERENCES dw.dim_unidade (id_unidade),
    CONSTRAINT fk_dim_pessoa_dim_pessoa_gestor FOREIGN KEY (id_gestor) REFERENCES dw.dim_pessoa (id_pessoa),
    CONSTRAINT ck_dim_pessoa_gestor CHECK (eh_gestor = 1 OR id_gestor IS NOT NULL));

CREATE TABLE dw.dim_campanha (
    id_campanha INT          NOT NULL,
    nome        NVARCHAR(80) NOT NULL,
    tipo        NVARCHAR(40) NOT NULL,
    id_tipo     INT          NOT NULL,
    id_unidade  INT          NOT NULL,
    data_inicio DATE         NOT NULL,
    CONSTRAINT pk_dim_campanha PRIMARY KEY (id_campanha),
    CONSTRAINT fk_dim_campanha_dim_unidade FOREIGN KEY (id_unidade) REFERENCES dw.dim_unidade (id_unidade),
    CONSTRAINT ck_dim_campanha_tipo CHECK (id_tipo IN (1, 2)));

CREATE TABLE dw.dim_tema (
    id_tema INT          NOT NULL,
    nome    NVARCHAR(80) NOT NULL,
    CONSTRAINT pk_dim_tema PRIMARY KEY (id_tema),
    CONSTRAINT uq_dim_tema_nome UNIQUE (nome));

CREATE TABLE dw.dim_origem (
    id_origem INT          NOT NULL,
    nome      NVARCHAR(80) NOT NULL,
    CONSTRAINT pk_dim_origem PRIMARY KEY (id_origem),
    CONSTRAINT uq_dim_origem_nome UNIQUE (nome));

CREATE TABLE dw.dim_tipo_ganho (
    id_tipo_ganho INT          NOT NULL,
    nome          NVARCHAR(80) NOT NULL,
    CONSTRAINT pk_dim_tipo_ganho PRIMARY KEY (id_tipo_ganho),
    CONSTRAINT uq_dim_tipo_ganho_nome UNIQUE (nome));

CREATE TABLE dw.dim_motivo_reprovacao (
    id_motivo INT           NOT NULL,
    nome      NVARCHAR(120) NOT NULL,
    CONSTRAINT pk_dim_motivo_reprovacao PRIMARY KEY (id_motivo),
    CONSTRAINT uq_dim_motivo_reprovacao_nome UNIQUE (nome));

CREATE TABLE dw.dim_etapa (
    id_etapa INT          NOT NULL,
    estado   NVARCHAR(60) NOT NULL,
    resumo   NVARCHAR(60) NOT NULL,
    terminal BIT          NOT NULL,
    CONSTRAINT pk_dim_etapa PRIMARY KEY (id_etapa),
    CONSTRAINT uq_dim_etapa_estado UNIQUE (estado));
GO

CREATE TABLE dw.fato_ideia (
    id_ideia              INT            NOT NULL,
    titulo                NVARCHAR(200)  NOT NULL,
    descricao             NVARCHAR(400)  NOT NULL,
    id_autor              INT            NOT NULL,
    id_unidade            INT            NOT NULL,
    id_campanha           INT            NOT NULL,
    id_tema               INT            NOT NULL,
    id_origem             INT            NULL,
    data_criacao          DATE           NOT NULL,
    id_etapa_atual        INT            NOT NULL,
    data_ultima_mov       DATE           NOT NULL,
    data_aprovacao        DATE           NULL,
    data_inicio_impl      DATE           NULL,
    data_implantacao      DATE           NULL,
    data_reprovacao       DATE           NULL,
    id_motivo_reprovacao  INT            NULL,
    id_responsavel_impl   INT            NULL,
    data_inicio_previsto  DATE           NULL,
    data_termino_previsto DATE           NULL,
    investimento_previsto DECIMAL(18, 2) NULL,
    investimento_real     DECIMAL(18, 2) NULL,
    ganho_previsto_12m    DECIMAL(18, 2) NULL,
    CONSTRAINT pk_fato_ideia PRIMARY KEY (id_ideia),
    CONSTRAINT uq_fato_ideia_titulo UNIQUE (titulo),
    CONSTRAINT fk_fato_ideia_dim_pessoa_autor FOREIGN KEY (id_autor) REFERENCES dw.dim_pessoa (id_pessoa),
    CONSTRAINT fk_fato_ideia_dim_unidade FOREIGN KEY (id_unidade) REFERENCES dw.dim_unidade (id_unidade),
    CONSTRAINT fk_fato_ideia_dim_campanha FOREIGN KEY (id_campanha) REFERENCES dw.dim_campanha (id_campanha),
    CONSTRAINT fk_fato_ideia_dim_tema FOREIGN KEY (id_tema) REFERENCES dw.dim_tema (id_tema),
    CONSTRAINT fk_fato_ideia_dim_origem FOREIGN KEY (id_origem) REFERENCES dw.dim_origem (id_origem),
    CONSTRAINT fk_fato_ideia_dim_etapa FOREIGN KEY (id_etapa_atual) REFERENCES dw.dim_etapa (id_etapa),
    CONSTRAINT fk_fato_ideia_dim_motivo_reprovacao FOREIGN KEY (id_motivo_reprovacao)
        REFERENCES dw.dim_motivo_reprovacao (id_motivo),
    CONSTRAINT fk_fato_ideia_dim_pessoa_responsavel FOREIGN KEY (id_responsavel_impl)
        REFERENCES dw.dim_pessoa (id_pessoa),
    CONSTRAINT ck_fato_ideia_datas CHECK (data_ultima_mov >= data_criacao),
    CONSTRAINT ck_fato_ideia_previsto CHECK (data_termino_previsto >= data_inicio_previsto),
    CONSTRAINT ck_fato_ideia_valores CHECK (investimento_previsto >= 0 AND investimento_real >= 0
                                            AND ganho_previsto_12m >= 0),
    CONSTRAINT ck_fato_ideia_reprovacao CHECK (
        (id_etapa_atual = 8 AND id_motivo_reprovacao IS NOT NULL)
        OR (id_etapa_atual <> 8 AND id_motivo_reprovacao IS NULL)));

CREATE TABLE dw.fato_movimentacao (
    id_ideia     INT  NOT NULL,
    seq          INT  NOT NULL,
    id_etapa     INT  NOT NULL,
    data_entrada DATE NOT NULL,
    data_saida   DATE NULL,
    CONSTRAINT pk_fato_movimentacao PRIMARY KEY (id_ideia, seq),
    CONSTRAINT fk_fato_movimentacao_fato_ideia FOREIGN KEY (id_ideia) REFERENCES dw.fato_ideia (id_ideia),
    CONSTRAINT fk_fato_movimentacao_dim_etapa FOREIGN KEY (id_etapa) REFERENCES dw.dim_etapa (id_etapa),
    CONSTRAINT ck_fato_movimentacao_datas CHECK (data_saida > data_entrada),
    CONSTRAINT ck_fato_movimentacao_seq CHECK (seq >= 1));

CREATE TABLE dw.ponte_ideia_coautor (
    id_ideia  INT NOT NULL,
    id_pessoa INT NOT NULL,
    CONSTRAINT pk_ponte_ideia_coautor PRIMARY KEY (id_ideia, id_pessoa),
    CONSTRAINT fk_ponte_ideia_coautor_fato_ideia FOREIGN KEY (id_ideia) REFERENCES dw.fato_ideia (id_ideia),
    CONSTRAINT fk_ponte_ideia_coautor_dim_pessoa FOREIGN KEY (id_pessoa) REFERENCES dw.dim_pessoa (id_pessoa));

CREATE TABLE dw.ponte_ideia_ganho (
    id_ideia      INT NOT NULL,
    id_tipo_ganho INT NOT NULL,
    CONSTRAINT pk_ponte_ideia_ganho PRIMARY KEY (id_ideia, id_tipo_ganho),
    CONSTRAINT fk_ponte_ideia_ganho_fato_ideia FOREIGN KEY (id_ideia) REFERENCES dw.fato_ideia (id_ideia),
    CONSTRAINT fk_ponte_ideia_ganho_dim_tipo_ganho FOREIGN KEY (id_tipo_ganho)
        REFERENCES dw.dim_tipo_ganho (id_tipo_ganho));

CREATE TABLE dw.meta_carga (
    id_carga        INT    NOT NULL CONSTRAINT df_meta_carga_id DEFAULT 1,
    data_referencia DATE   NOT NULL,
    semente         BIGINT NOT NULL,
    CONSTRAINT pk_meta_carga PRIMARY KEY (id_carga),
    CONSTRAINT ck_meta_carga_unica CHECK (id_carga = 1));
GO

CREATE INDEX ix_dim_pessoa_id_unidade ON dw.dim_pessoa (id_unidade);
CREATE INDEX ix_dim_pessoa_id_gestor ON dw.dim_pessoa (id_gestor);
CREATE INDEX ix_dim_campanha_id_unidade ON dw.dim_campanha (id_unidade);
CREATE INDEX ix_fato_ideia_id_autor ON dw.fato_ideia (id_autor);
CREATE INDEX ix_fato_ideia_id_unidade ON dw.fato_ideia (id_unidade);
CREATE INDEX ix_fato_ideia_id_campanha ON dw.fato_ideia (id_campanha);
CREATE INDEX ix_fato_ideia_id_tema ON dw.fato_ideia (id_tema);
CREATE INDEX ix_fato_ideia_id_origem ON dw.fato_ideia (id_origem);
CREATE INDEX ix_fato_ideia_id_etapa_atual ON dw.fato_ideia (id_etapa_atual);
CREATE INDEX ix_fato_ideia_id_motivo_reprovacao ON dw.fato_ideia (id_motivo_reprovacao);
CREATE INDEX ix_fato_ideia_id_responsavel_impl ON dw.fato_ideia (id_responsavel_impl);
CREATE INDEX ix_fato_movimentacao_id_etapa ON dw.fato_movimentacao (id_etapa);
CREATE INDEX ix_ponte_ideia_coautor_id_pessoa ON dw.ponte_ideia_coautor (id_pessoa);
CREATE INDEX ix_ponte_ideia_ganho_id_tipo_ganho ON dw.ponte_ideia_ganho (id_tipo_ganho);
GO
