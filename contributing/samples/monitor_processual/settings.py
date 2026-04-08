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

import json
import os

# Carrega .env se python-dotenv estiver instalado
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

# Diretorio raiz do projeto (onde esta o pyproject.toml)
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

# --- LLM ---
LLM_MODEL_NAME = os.environ.get("LLM_MODEL_NAME", "gemini-2.0-flash")

# --- DataJud API (CNJ) ---
# Chave de acesso da API DataJud do CNJ
# Solicite em: https://datajud-wiki.cnj.jus.br/
DATAJUD_API_KEY = os.environ.get("DATAJUD_API_KEY", "")
DATAJUD_BASE_URL = os.environ.get(
    "DATAJUD_BASE_URL",
    "https://api-publica.datajud.cnj.jus.br",
)

# --- Tribunais suportados (endpoints da API DataJud) ---
# Referencia: https://datajud-wiki.cnj.jus.br/api-publica/endpoints
TRIBUNAIS = {
    # Tribunais Superiores
    "STF": "api_publica_stf",
    "STJ": "api_publica_stj",
    "TST": "api_publica_tst",
    "TSE": "api_publica_tse",
    "STM": "api_publica_stm",
    # Tribunais Regionais Federais
    "TRF1": "api_publica_trf1",
    "TRF2": "api_publica_trf2",
    "TRF3": "api_publica_trf3",
    "TRF4": "api_publica_trf4",
    "TRF5": "api_publica_trf5",
    "TRF6": "api_publica_trf6",
    # Tribunais de Justica Estaduais
    "TJAC": "api_publica_tjac",
    "TJAL": "api_publica_tjal",
    "TJAM": "api_publica_tjam",
    "TJAP": "api_publica_tjap",
    "TJBA": "api_publica_tjba",
    "TJCE": "api_publica_tjce",
    "TJDF": "api_publica_tjdft",
    "TJES": "api_publica_tjes",
    "TJGO": "api_publica_tjgo",
    "TJMA": "api_publica_tjma",
    "TJMG": "api_publica_tjmg",
    "TJMS": "api_publica_tjms",
    "TJMT": "api_publica_tjmt",
    "TJPA": "api_publica_tjpa",
    "TJPB": "api_publica_tjpb",
    "TJPE": "api_publica_tjpe",
    "TJPI": "api_publica_tjpi",
    "TJPR": "api_publica_tjpr",
    "TJRJ": "api_publica_tjrj",
    "TJRN": "api_publica_tjrn",
    "TJRO": "api_publica_tjro",
    "TJRR": "api_publica_tjrr",
    "TJRS": "api_publica_tjrs",
    "TJSC": "api_publica_tjsc",
    "TJSE": "api_publica_tjse",
    "TJSP": "api_publica_tjsp",
    "TJTO": "api_publica_tjto",
    # Tribunais Regionais do Trabalho
    "TRT1": "api_publica_trt1",
    "TRT2": "api_publica_trt2",
    "TRT3": "api_publica_trt3",
    "TRT4": "api_publica_trt4",
    "TRT5": "api_publica_trt5",
    "TRT6": "api_publica_trt6",
    "TRT7": "api_publica_trt7",
    "TRT8": "api_publica_trt8",
    "TRT9": "api_publica_trt9",
    "TRT10": "api_publica_trt10",
    "TRT11": "api_publica_trt11",
    "TRT12": "api_publica_trt12",
    "TRT13": "api_publica_trt13",
    "TRT14": "api_publica_trt14",
    "TRT15": "api_publica_trt15",
    "TRT16": "api_publica_trt16",
    "TRT17": "api_publica_trt17",
    "TRT18": "api_publica_trt18",
    "TRT19": "api_publica_trt19",
    "TRT20": "api_publica_trt20",
    "TRT21": "api_publica_trt21",
    "TRT22": "api_publica_trt22",
    "TRT23": "api_publica_trt23",
    "TRT24": "api_publica_trt24",
    # Tribunais Regionais Eleitorais (endpoint usa hifen: api_publica_tre-uf)
    "TRE-AC": "api_publica_tre-ac",
    "TRE-AL": "api_publica_tre-al",
    "TRE-AM": "api_publica_tre-am",
    "TRE-AP": "api_publica_tre-ap",
    "TRE-BA": "api_publica_tre-ba",
    "TRE-CE": "api_publica_tre-ce",
    "TRE-DF": "api_publica_tre-df",
    "TRE-ES": "api_publica_tre-es",
    "TRE-GO": "api_publica_tre-go",
    "TRE-MA": "api_publica_tre-ma",
    "TRE-MG": "api_publica_tre-mg",
    "TRE-MS": "api_publica_tre-ms",
    "TRE-MT": "api_publica_tre-mt",
    "TRE-PA": "api_publica_tre-pa",
    "TRE-PB": "api_publica_tre-pb",
    "TRE-PE": "api_publica_tre-pe",
    "TRE-PI": "api_publica_tre-pi",
    "TRE-PR": "api_publica_tre-pr",
    "TRE-RJ": "api_publica_tre-rj",
    "TRE-RN": "api_publica_tre-rn",
    "TRE-RO": "api_publica_tre-ro",
    "TRE-RR": "api_publica_tre-rr",
    "TRE-RS": "api_publica_tre-rs",
    "TRE-SC": "api_publica_tre-sc",
    "TRE-SE": "api_publica_tre-se",
    "TRE-SP": "api_publica_tre-sp",
    "TRE-TO": "api_publica_tre-to",
    # Tribunais Militares Estaduais
    "TJMMG": "api_publica_tjmmg",
    "TJMRS": "api_publica_tjmrs",
    "TJMSP": "api_publica_tjmsp",
}
# NOTA: O STF nao possui endpoint publico na API DataJud (verificado em 2026).
# Para consultas ao STF, usar o portal: portal.stf.jus.br/servicos

# Mapeamento de tribunal para estado (para calculo de feriados estaduais)
TRIBUNAL_ESTADO = {
    "TJSP": "SP", "TRT2": "SP", "TRT15": "SP", "TRF3": "SP",
    "TJRJ": "RJ", "TRT1": "RJ", "TRF2": "RJ",
    "TJMG": "MG", "TRT3": "MG",
    "TJRS": "RS", "TRT4": "RS",
    "TJPR": "PR", "TRT9": "PR",
    "TJSC": "SC", "TRT12": "SC",
    "TJBA": "BA", "TRT5": "BA",
    "TJPE": "PE", "TRT6": "PE",
    "TJCE": "CE", "TRT7": "CE",
    "TJDF": "DF", "TRT10": "DF",
}

# --- Notificacoes ---
SMTP_HOST = os.environ.get("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USER = os.environ.get("SMTP_USER", "")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")
EMAIL_DESTINATARIO = os.environ.get("EMAIL_DESTINATARIO", "")

# Webhook do Slack (opcional)
SLACK_WEBHOOK_URL = os.environ.get("SLACK_WEBHOOK_URL", "")

# --- Carteira de processos ---
# Carrega de processos.json (ou caminho customizado via env)
PROCESSOS_PATH = os.environ.get(
    "PROCESSOS_PATH",
    os.path.join(PROJECT_ROOT, "processos.json"),
)

PROCESSOS_MONITORADOS = []
if os.path.exists(PROCESSOS_PATH):
    with open(PROCESSOS_PATH, "r", encoding="utf-8") as f:
        PROCESSOS_MONITORADOS = json.load(f)

# --- Armazenamento local ---
HISTORICO_PATH = os.environ.get(
    "HISTORICO_PATH",
    os.path.join(PROJECT_ROOT, "historico_movimentacoes.json"),
)
