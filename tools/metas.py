SLA_GERAL_DIAS = 60
SLA_ETAPA_DIAS = {"Avaliação": 15, "Proposta de Solução": 45, "Aprovada": 30,
                  "Em Implantação": 90, "Validação": 20}
META_ENGAJAMENTO = 0.50
META_CONVERSAO = 0.15


def pct(x: float) -> str:
    return f"{x:.0%}"
