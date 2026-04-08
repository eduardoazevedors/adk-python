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

"""Classificacao de movimentacoes com base nas Tabelas Processuais Unificadas (TPU/SGT) do CNJ.

As TPUs padronizam os codigos de movimentacao em todos os tribunais do Brasil.
Referencia: https://www.cnj.jus.br/sgt/consulta_publica_movimentos.php

Este modulo mapeia os codigos mais relevantes para niveis de urgencia
e associa o prazo processual aplicavel quando pertinente.
"""

from typing import Optional


# --- Movimentacoes que geram prazo (URGENTES) ---
# Formato: codigo_tpu -> {descricao, prazo_dias, tipo_prazo, referencia_legal}

MOVIMENTACOES_URGENTES = {
    # Intimacoes
    12: {
        "descricao": "Intimacao",
        "prazo_dias": None,  # Depende do conteudo
        "referencia": "Verificar conteudo da intimacao",
    },
    12054: {
        "descricao": "Intimacao para manifestacao",
        "prazo_dias": 15,
        "referencia": "CPC art. 218, §3",
    },
    12055: {
        "descricao": "Intimacao para cumprir decisao",
        "prazo_dias": 15,
        "referencia": "CPC art. 218, §3",
    },

    # Citacoes
    14: {
        "descricao": "Citacao",
        "prazo_dias": 15,
        "referencia": "CPC art. 335 (contestacao)",
    },

    # Sentencas e decisoes
    22: {
        "descricao": "Sentenca",
        "prazo_dias": 15,
        "referencia": "CPC art. 1.003, §5 (apelacao)",
    },
    193: {
        "descricao": "Decisao interlocutoria",
        "prazo_dias": 15,
        "referencia": "CPC art. 1.015 (agravo de instrumento)",
    },
    67: {
        "descricao": "Despacho",
        "prazo_dias": None,  # Depende do conteudo do despacho
        "referencia": "Verificar se contem prazo",
    },
    848: {
        "descricao": "Acordao",
        "prazo_dias": 15,
        "referencia": "CPC art. 1.029 (recurso especial/extraordinario)",
    },
    385: {
        "descricao": "Decisao monocratica",
        "prazo_dias": 15,
        "referencia": "CPC art. 1.021 (agravo interno)",
    },

    # Tutelas
    334: {
        "descricao": "Tutela de urgencia concedida",
        "prazo_dias": 5,
        "referencia": "CPC art. 1.023 (embargos de declaracao) ou cumprimento",
    },

    # Transito em julgado
    848: {
        "descricao": "Transito em julgado",
        "prazo_dias": None,
        "referencia": "Inicio da fase de cumprimento de sentenca",
    },

    # Penhora e bloqueio
    11372: {
        "descricao": "Penhora",
        "prazo_dias": 15,
        "referencia": "CPC art. 915 (embargos a execucao)",
    },
    11373: {
        "descricao": "Bloqueio de valores (SISBAJUD)",
        "prazo_dias": 5,
        "referencia": "Impugnacao / desbloqueio",
    },

    # Audiencias
    970: {
        "descricao": "Audiencia designada",
        "prazo_dias": None,
        "referencia": "Verificar data da audiencia",
    },
    11385: {
        "descricao": "Audiencia de conciliacao designada",
        "prazo_dias": None,
        "referencia": "CPC art. 334 (comparecimento obrigatorio)",
    },

    # Hasta publica / leilao
    11419: {
        "descricao": "Hasta publica / leilao designado",
        "prazo_dias": None,
        "referencia": "Verificar data do leilao",
    },
}

# --- Movimentacoes informativas ---
MOVIMENTACOES_INFORMATIVAS = {
    581: "Juntada de documento",
    85: "Juntada de peticao",
    51: "Conclusao ao juiz/relator",
    123: "Vista ao Ministerio Publico",
    11009: "Pericia designada",
    36: "Redistribuicao",
    22: "Remetido para publicacao",
    11010: "Conclusos para julgamento",
    11014: "Suspenso por acordo das partes",
    972: "Designacao de audiencia",
}

# --- Movimentacoes de rotina ---
MOVIMENTACOES_ROTINA = {
    60: "Remessa dos autos",
    61: "Retorno dos autos",
    580: "Certificacao",
    11001: "Numeracao de paginas",
    11002: "Atualizacao de sistema",
    1061: "Recebimento dos autos",
    11006: "Juntada de AR (aviso de recebimento)",
    132: "Arquivamento",
    246: "Desarquivamento",
    11008: "Carga / vista dos autos ao advogado",
}


def classificar_movimentacao(
    codigo: Optional[int] = None,
    nome: str = "",
) -> dict:
    """Classifica uma movimentacao processual por urgencia.

    Usa o codigo TPU quando disponivel, com fallback para analise textual.

    Args:
        codigo: Codigo TPU da movimentacao (quando disponivel).
        nome: Descricao textual da movimentacao.

    Returns:
        Dicionario com classificacao, prazo sugerido e referencia legal.
    """
    nome_lower = nome.lower()

    # 1. Tentar classificar pelo codigo TPU
    if codigo and codigo in MOVIMENTACOES_URGENTES:
        info = MOVIMENTACOES_URGENTES[codigo]
        return {
            "classificacao": "URGENTE",
            "descricao_tpu": info["descricao"],
            "prazo_dias": info.get("prazo_dias"),
            "referencia_legal": info.get("referencia", ""),
            "metodo": "codigo_tpu",
        }

    if codigo and codigo in MOVIMENTACOES_INFORMATIVAS:
        return {
            "classificacao": "INFORMATIVO",
            "descricao_tpu": MOVIMENTACOES_INFORMATIVAS[codigo],
            "prazo_dias": None,
            "referencia_legal": "",
            "metodo": "codigo_tpu",
        }

    if codigo and codigo in MOVIMENTACOES_ROTINA:
        return {
            "classificacao": "ROTINA",
            "descricao_tpu": MOVIMENTACOES_ROTINA[codigo],
            "prazo_dias": None,
            "referencia_legal": "",
            "metodo": "codigo_tpu",
        }

    # 2. Fallback: analise textual do nome da movimentacao
    # URGENTE - palavras-chave que indicam necessidade de acao
    palavras_urgentes = [
        "intimacao", "intimação", "citacao", "citação",
        "sentenca", "sentença", "acordao", "acórdão",
        "decisao interlocutoria", "decisão interlocutória",
        "tutela", "penhora", "bloqueio", "arresto",
        "hasta publica", "leilao", "leilão",
        "transito em julgado", "trânsito em julgado",
        "multa", "condenacao", "condenação",
        "despejo", "reintegracao", "reintegração",
        "mandado de prisao", "mandado de prisão",
    ]

    for palavra in palavras_urgentes:
        if palavra in nome_lower:
            # Tentar inferir prazo
            prazo = _inferir_prazo_por_texto(nome_lower)
            return {
                "classificacao": "URGENTE",
                "descricao_tpu": nome,
                "prazo_dias": prazo,
                "referencia_legal": "Classificado por analise textual - verificar manualmente",
                "metodo": "analise_textual",
            }

    # INFORMATIVO
    palavras_informativas = [
        "juntada", "conclus", "vista",
        "pericia", "perícia", "redistribui",
        "publicacao", "publicação", "audiencia designada",
        "suspens",
    ]

    for palavra in palavras_informativas:
        if palavra in nome_lower:
            return {
                "classificacao": "INFORMATIVO",
                "descricao_tpu": nome,
                "prazo_dias": None,
                "referencia_legal": "",
                "metodo": "analise_textual",
            }

    # ROTINA (default)
    return {
        "classificacao": "ROTINA",
        "descricao_tpu": nome,
        "prazo_dias": None,
        "referencia_legal": "",
        "metodo": "analise_textual",
    }


def _inferir_prazo_por_texto(nome: str) -> Optional[int]:
    """Tenta inferir o prazo processual a partir do texto da movimentacao."""
    if "contestacao" in nome or "contestação" in nome:
        return 15
    if "apelacao" in nome or "apelação" in nome:
        return 15
    if "agravo" in nome:
        return 15
    if "embargos de declaracao" in nome or "embargos de declaração" in nome:
        return 5
    if "sentenca" in nome or "sentença" in nome:
        return 15  # Prazo para apelar
    if "acordao" in nome or "acórdão" in nome:
        return 15  # Prazo para recurso especial/extraordinario
    if "intimacao" in nome or "intimação" in nome:
        return 15  # Prazo generico mais comum
    if "citacao" in nome or "citação" in nome:
        return 15  # Prazo para contestar
    return None
