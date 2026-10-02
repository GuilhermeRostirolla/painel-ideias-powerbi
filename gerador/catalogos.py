from dataclasses import dataclass
from itertools import product

import numpy as np

from gerador.blocklist import bloqueado


@dataclass(frozen=True)
class Etapa:
    id: int
    estado: str
    resumo: str
    terminal: bool


ETAPAS = (
    Etapa(1, "ETAPA 1: AVALIAÇÃO", "Avaliação", False),
    Etapa(2, "ETAPA 2: PROPOSTA DE SOLUÇÃO", "Proposta de Solução", False),
    Etapa(3, "Aprovada", "Aprovada", False),
    Etapa(4, "Em Implantação", "Em Implantação", False),
    Etapa(5, "Validação da Implantação", "Validação da Implantação", False),
    Etapa(6, "Implantada", "Implantada", True),
    Etapa(7, "BANCO DE IDEIAS", "Banco de Ideias", False),
    Etapa(8, "Reprovada", "Reprovada", True),
    Etapa(9, "Cancelada", "Cancelada", True),
)

N_EMPRESAS = 6
_RADICAIS = ("Horizonte", "Aurora", "Atlântica", "Primavera", "Cristal", "Pioneira",
             "Estrela", "Litoral", "Planalto", "Girassol", "Alvorada", "Ventura",
             "Jatobá", "Cerrado")
_SEGMENTOS = ("Embalagens", "Metalúrgica", "Tecnologia", "Serviços", "Plásticos",
              "Engenharia", "Distribuição", "Alimentos", "Têxtil", "Química")


def gerar_empresas(rng: np.random.Generator, bloqueio: frozenset[str]) -> list[tuple[str, str]]:
    radicais = [_RADICAIS[i] for i in rng.permutation(len(_RADICAIS))]
    segmentos = [_SEGMENTOS[i] for i in rng.permutation(len(_SEGMENTOS))]
    empresas: list[tuple[str, str]] = []
    for radical in radicais:
        nome = f"{radical} {segmentos[len(empresas)]}"
        sigla = radical
        if any(bloqueado(t, bloqueio) for t in (nome, radical)):
            continue
        empresas.append((nome, sigla))
        if len(empresas) == N_EMPRESAS:
            return empresas
    raise ValueError("radicais insuficientes para gerar empresas")

TIPOS_CAMPANHA = ((1, "EXCELÊNCIA OPERACIONAL", "Excelência Operacional"),
                  (2, "INOVAÇÃO", "Inovação"))

TEMAS = ("Eficiência e Qualidade", "Segurança e Saúde", "Tecnologia e Processos",
         "Cultura e Comunicação", "Experiência do Cliente")

ORIGENS = ("Rotina de trabalho", "Análise de indicadores", "Conversa com a equipe",
           "Estudo de concorrentes", "Visita técnica", "Evento do setor",
           "Sugestão de cliente", "Pesquisa externa", "Contato com fornecedor",
           "Treinamento interno", "Comunidade online", "Viagem de trabalho",
           "Auditoria interna")

TIPOS_GANHO = ("Em Etapas Anteriores", "Menos retrabalho", "Mais segurança",
               "Menos energia", "Ciclo mais curto", "Mais ergonomia",
               "Menos desperdício", "Disponibilidade", "Satisf. clientes",
               "Equipe engajada", "Novas receitas", "Menos riscos",
               "Rastreabilidade", "Padronização", "Estoque reduzido")

MOTIVOS_REPROVACAO = ("Custo acima do benefício", "Já existe solução em andamento",
                      "Fora do escopo da campanha", "Inviável tecnicamente",
                      "Retorno não comprovado", "Depende de outra área",
                      "Proposta incompleta", "Prioridade baixa no momento")

FAIXAS_DIAS = ("0–15 d", "16–30 d", "31–60 d", "+60 d")
FAIXAS_VALOR = ("0-Sem valor", "1-Até 50K", "2-50K até 100K", "3-100K até 500K", "4-500K até 1M")


def faixa_valor(ganho: float | None) -> str:
    if ganho is None or ganho != ganho or ganho <= 0:
        return FAIXAS_VALOR[0]
    if ganho <= 50_000:
        return FAIXAS_VALOR[1]
    if ganho <= 100_000:
        return FAIXAS_VALOR[2]
    if ganho <= 500_000:
        return FAIXAS_VALOR[3]
    return FAIXAS_VALOR[4]


def faixa_dias(dias: int) -> str:
    if dias <= 15:
        return FAIXAS_DIAS[0]
    if dias <= 30:
        return FAIXAS_DIAS[1]
    if dias <= 60:
        return FAIXAS_DIAS[2]
    return FAIXAS_DIAS[3]


_VERBOS = ("Automatizar", "Padronizar", "Digitalizar", "Simplificar", "Reorganizar",
           "Monitorar", "Reduzir o tempo de", "Criar checklist para", "Agilizar",
           "Otimizar", "Revisar", "Centralizar", "Treinar a equipe em")
_DOMINIOS = (
    (("na expedição", "no almoxarifado", "na logística", "no pátio", "no centro de distribuição"),
     ("a conferência de lotes", "a separação de pedidos", "o recebimento de materiais",
      "o carregamento de caminhões", "a movimentação de paletes", "a gestão de estoque mínimo",
      "o agendamento de coletas", "o inventário de peças", "a rotulagem de embalagens",
      "a checagem de notas fiscais")),
    (("na produção", "na manutenção", "na qualidade", "no laboratório", "na linha de montagem"),
     ("o controle de ferramentas", "o registro de paradas", "a troca de turnos",
      "a limpeza de equipamentos", "a inspeção de qualidade", "a programação de manutenção",
      "o consumo de energia", "o uso de EPIs", "o abastecimento de linhas",
      "a calibração de instrumentos", "o controle de temperatura", "o descarte de resíduos",
      "o reaproveitamento de sobras", "o fluxo de amostras")),
    (("no escritório", "no RH", "no financeiro", "no setor de compras", "no atendimento"),
     ("a comunicação entre áreas", "o atendimento de chamados", "o arquivo de documentos",
      "a aprovação de compras", "o acompanhamento de indicadores",
      "a integração de novos colaboradores", "o controle de reembolsos")),
)


_CONTRACOES = (("de a ", "da "), ("de o ", "do "), ("em a ", "na "), ("em o ", "no "))


def _contrair(texto: str) -> str:
    for de, para in _CONTRACOES:
        texto = texto.replace(de, para)
    return texto


def gerar_titulos(rng: np.random.Generator, n: int, bloqueio: frozenset[str]) -> list[str]:
    combos = [_contrair(f"{v} {o} {a}")
              for areas, objetos in _DOMINIOS
              for v, o, a in product(_VERBOS, objetos, areas)]
    titulos: list[str] = []
    for i in rng.permutation(len(combos)):
        t = combos[i]
        if not bloqueado(t, bloqueio):
            titulos.append(t)
            if len(titulos) == n:
                return titulos
    raise ValueError(f"combinações insuficientes para {n} títulos")


_BENEFICIOS = ("reduzir retrabalho", "ganhar tempo na rotina", "aumentar a segurança",
               "evitar perdas de material", "melhorar a comunicação",
               "diminuir custos operacionais")


def gerar_descricao(rng: np.random.Generator, titulo: str) -> str:
    beneficio = _BENEFICIOS[int(rng.integers(len(_BENEFICIOS)))]
    return f"Proposta para {titulo[0].lower() + titulo[1:]}, com objetivo de {beneficio}."
