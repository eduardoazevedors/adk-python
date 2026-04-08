# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Calculo de prazos processuais conforme CPC 2015 (Lei 13.105/2015).

Regras principais:
- Art. 219: Prazos em dias contam apenas dias uteis.
- Art. 224, §1: Exclui o dia do comeco e inclui o dia do vencimento.
- Art. 224, §2: Se o vencimento cair em dia sem expediente, prorroga para
  o proximo dia util.
- Art. 220: Recesso forense de 20/dez a 20/jan (prazos suspensos).
- Juizados Especiais (Lei 9.099/95): Prazos em dias corridos.
- Processo Penal (CPP): Prazos em dias corridos.
- Fazenda Publica (art. 183): Prazo em dobro.
- Defensoria Publica (art. 186): Prazo em dobro.
"""

from datetime import date, timedelta
from typing import Optional


# --- Feriados nacionais fixos ---
FERIADOS_NACIONAIS_FIXOS = [
    (1, 1),    # Confraternizacao Universal
    (4, 21),   # Tiradentes
    (5, 1),    # Dia do Trabalhador
    (9, 7),    # Independencia
    (10, 12),  # Nossa Senhora Aparecida
    (11, 2),   # Finados
    (11, 15),  # Proclamacao da Republica
    (12, 25),  # Natal
]

# Feriados forenses nacionais (alem dos feriados civis)
FERIADOS_FORENSES_FIXOS = [
    (8, 11),   # Dia do Advogado (ponto facultativo, mas muitos tribunais suspendem)
    (10, 28),  # Dia do Servidor Publico
    (12, 8),   # Dia da Justica
]

# --- Feriados estaduais comuns (adicionar conforme necessidade) ---
# Formato: {sigla_estado: [(mes, dia), ...]}
FERIADOS_ESTADUAIS = {
    "SP": [(1, 25), (7, 9)],           # Aniversario de SP, Rev. Constitucionalista
    "RJ": [(4, 23), (11, 20)],          # Sao Jorge, Consciencia Negra
    "MG": [(4, 21),],                   # Tiradentes (ja e nacional, mas Inconfidencia)
    "RS": [(9, 20),],                   # Revolucao Farroupilha
    "PR": [(12, 19),],                  # Emancipacao do Parana
    "BA": [(7, 2),],                    # Independencia da Bahia
    "PE": [(3, 6),],                    # Revolucao Pernambucana
    "CE": [(3, 25),],                   # Data Magna do Ceara
    "DF": [(4, 21), (11, 30)],          # Fundacao de Brasilia, Dia do Evangelico
}


def _calcular_pascoa(ano: int) -> date:
    """Calcula a data da Pascoa pelo algoritmo de Gauss/Meeus."""
    a = ano % 19
    b = ano // 100
    c = ano % 100
    d = b // 4
    e = b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i = c // 4
    k = c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    mes = (h + l - 7 * m + 114) // 31
    dia = ((h + l - 7 * m + 114) % 31) + 1
    return date(ano, mes, dia)


def feriados_moveis(ano: int) -> list[date]:
    """Retorna feriados moveis baseados na Pascoa."""
    pascoa = _calcular_pascoa(ano)
    return [
        pascoa - timedelta(days=48),   # Segunda-feira de Carnaval
        pascoa - timedelta(days=47),   # Terca-feira de Carnaval
        pascoa - timedelta(days=2),    # Sexta-feira Santa
        pascoa,                         # Pascoa
        pascoa + timedelta(days=60),   # Corpus Christi
    ]


def feriados_do_ano(ano: int, estado: Optional[str] = None) -> set[date]:
    """Retorna todos os feriados de um ano (nacionais + forenses + estaduais).

    Args:
        ano: Ano para calcular feriados.
        estado: Sigla do estado (ex: 'SP') para incluir feriados estaduais.

    Returns:
        Conjunto de datas de feriados.
    """
    datas = set()

    # Feriados nacionais fixos
    for mes, dia in FERIADOS_NACIONAIS_FIXOS:
        datas.add(date(ano, mes, dia))

    # Feriados forenses fixos
    for mes, dia in FERIADOS_FORENSES_FIXOS:
        datas.add(date(ano, mes, dia))

    # Feriados moveis
    for d in feriados_moveis(ano):
        datas.add(d)

    # Feriados estaduais
    if estado and estado.upper() in FERIADOS_ESTADUAIS:
        for mes, dia in FERIADOS_ESTADUAIS[estado.upper()]:
            datas.add(date(ano, mes, dia))

    return datas


def em_recesso_forense(data: date) -> bool:
    """Verifica se a data esta no recesso forense (20/dez a 20/jan).

    CPC 2015, art. 220: Suspende-se o curso do prazo processual nos dias
    compreendidos entre 20 de dezembro e 20 de janeiro, inclusive.
    """
    if data.month == 12 and data.day >= 20:
        return True
    if data.month == 1 and data.day <= 20:
        return True
    return False


def eh_dia_util(data: date, estado: Optional[str] = None) -> bool:
    """Verifica se uma data e dia util forense.

    Nao e dia util se:
    - Sabado ou domingo
    - Feriado (nacional, forense ou estadual)
    - Recesso forense (20/dez a 20/jan)
    """
    # Fim de semana
    if data.weekday() >= 5:  # 5=sabado, 6=domingo
        return False

    # Recesso forense
    if em_recesso_forense(data):
        return False

    # Feriados
    todos_feriados = feriados_do_ano(data.year, estado)
    if data in todos_feriados:
        return False

    return True


def proximo_dia_util(data: date, estado: Optional[str] = None) -> date:
    """Retorna o proximo dia util a partir da data (inclusive)."""
    while not eh_dia_util(data, estado):
        data += timedelta(days=1)
    return data


def calcular_prazo(
    data_intimacao: date,
    dias: int,
    estado: Optional[str] = None,
    dias_corridos: bool = False,
    prazo_em_dobro: bool = False,
) -> date:
    """Calcula a data final de um prazo processual.

    Regras do CPC 2015:
    - Art. 224, §1: Exclui o dia do comeco, inclui o dia do vencimento.
    - Art. 219: Conta apenas dias uteis (salvo excecoes).
    - Art. 224, §2: Se o vencimento cair em dia sem expediente, prorroga.

    Args:
        data_intimacao: Data da intimacao (publicacao no DJe + 1 dia util).
        dias: Quantidade de dias do prazo.
        estado: Sigla do estado para feriados estaduais.
        dias_corridos: True para Juizados Especiais / processo penal.
        prazo_em_dobro: True para Fazenda Publica / Defensoria Publica.

    Returns:
        Data do vencimento do prazo.
    """
    if prazo_em_dobro:
        dias *= 2

    # Inicio da contagem: primeiro dia util APOS a intimacao
    data_atual = data_intimacao + timedelta(days=1)

    if dias_corridos:
        # Dias corridos: conta todos os dias
        data_vencimento = data_atual + timedelta(days=dias - 1)
        # Mas o vencimento deve cair em dia util
        return proximo_dia_util(data_vencimento, estado)

    # Dias uteis: conta apenas dias com expediente
    dias_contados = 0
    while dias_contados < dias:
        if eh_dia_util(data_atual, estado):
            dias_contados += 1
            if dias_contados == dias:
                return data_atual
        data_atual += timedelta(days=1)

    return data_atual


def calcular_prazo_publicacao_dje(
    data_publicacao: date,
    dias: int,
    estado: Optional[str] = None,
    dias_corridos: bool = False,
    prazo_em_dobro: bool = False,
) -> dict:
    """Calcula prazo a partir da publicacao no DJe.

    Lei 11.419/2006, art. 4, §3 e §4:
    - Intimacao considera-se realizada no 1o dia util seguinte a publicacao.
    - Prazo comeca a correr no 1o dia util seguinte a intimacao.

    Args:
        data_publicacao: Data da publicacao no DJe.
        dias: Quantidade de dias do prazo.
        estado: Sigla do estado.
        dias_corridos: True para dias corridos.
        prazo_em_dobro: True para prazo em dobro.

    Returns:
        Dicionario com datas relevantes.
    """
    # Data da intimacao: 1o dia util apos publicacao
    data_intimacao = proximo_dia_util(
        data_publicacao + timedelta(days=1), estado
    )

    # Data de inicio da contagem: 1o dia util apos intimacao
    data_inicio = proximo_dia_util(
        data_intimacao + timedelta(days=1), estado
    )

    # Data do vencimento
    data_vencimento = calcular_prazo(
        data_intimacao, dias, estado, dias_corridos, prazo_em_dobro
    )

    return {
        "data_publicacao": data_publicacao.isoformat(),
        "data_intimacao": data_intimacao.isoformat(),
        "data_inicio_contagem": data_inicio.isoformat(),
        "data_vencimento": data_vencimento.isoformat(),
        "dias_prazo": dias * (2 if prazo_em_dobro else 1),
        "tipo": "dias_corridos" if dias_corridos else "dias_uteis",
        "prazo_em_dobro": prazo_em_dobro,
    }


# --- Tabela de prazos comuns (CPC 2015) ---
PRAZOS_COMUNS = {
    "contestacao": {"dias": 15, "referencia": "CPC art. 335"},
    "replica": {"dias": 15, "referencia": "CPC art. 351"},
    "apelacao": {"dias": 15, "referencia": "CPC art. 1.003, §5"},
    "contrarrazoes_apelacao": {"dias": 15, "referencia": "CPC art. 1.010, §1"},
    "agravo_instrumento": {"dias": 15, "referencia": "CPC art. 1.015"},
    "embargos_declaracao": {"dias": 5, "referencia": "CPC art. 1.023"},
    "recurso_especial": {"dias": 15, "referencia": "CPC art. 1.029"},
    "recurso_extraordinario": {"dias": 15, "referencia": "CPC art. 1.029"},
    "contrarrazoes_recurso_especial": {"dias": 15, "referencia": "CPC art. 1.030"},
    "embargos_execucao": {"dias": 15, "referencia": "CPC art. 915"},
    "impugnacao_cumprimento_sentenca": {"dias": 15, "referencia": "CPC art. 525"},
    "manifestacao_generica_5": {"dias": 5, "referencia": "CPC art. 218, §3"},
    "manifestacao_generica_15": {"dias": 15, "referencia": "CPC art. 218, §3"},
    "recurso_ordinario": {"dias": 15, "referencia": "CPC art. 1.027"},
    "agravo_interno": {"dias": 15, "referencia": "CPC art. 1.021"},
    "reclamacao": {"dias": 15, "referencia": "CPC art. 988"},
}
