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
TRIBUNAIS = {
    "TJSP": "api_publica_tjsp",
    "TJRJ": "api_publica_tjrj",
    "TJMG": "api_publica_tjmg",
    "TJRS": "api_publica_tjrs",
    "TJPR": "api_publica_tjpr",
    "TJSC": "api_publica_tjsc",
    "TJBA": "api_publica_tjba",
    "TJPE": "api_publica_tjpe",
    "TJCE": "api_publica_tjce",
    "TJDF": "api_publica_tjdf",
    "TRF1": "api_publica_trf1",
    "TRF2": "api_publica_trf2",
    "TRF3": "api_publica_trf3",
    "TRF4": "api_publica_trf4",
    "TRF5": "api_publica_trf5",
    "TRT1": "api_publica_trt1",
    "TRT2": "api_publica_trt2",
    "TRT15": "api_publica_trt15",
    "TST": "api_publica_tst",
    "STJ": "api_publica_stj",
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
