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

"""Ferramentas para o agente de monitoramento processual."""

import json
import logging
import os
import smtplib
from datetime import datetime
from email.mime.text import MIMEText
from typing import Any

import requests

from monitor_processual.settings import DATAJUD_API_KEY
from monitor_processual.settings import DATAJUD_BASE_URL
from monitor_processual.settings import EMAIL_DESTINATARIO
from monitor_processual.settings import HISTORICO_PATH
from monitor_processual.settings import PROCESSOS_MONITORADOS
from monitor_processual.settings import SLACK_WEBHOOK_URL
from monitor_processual.settings import SMTP_HOST
from monitor_processual.settings import SMTP_PASSWORD
from monitor_processual.settings import SMTP_PORT
from monitor_processual.settings import SMTP_USER
from monitor_processual.settings import TRIBUNAIS

logger = logging.getLogger("google_adk." + __name__)


# --- Historico local ---


def _carregar_historico() -> dict:
    """Carrega o historico de movimentacoes ja vistas."""
    if os.path.exists(HISTORICO_PATH):
        with open(HISTORICO_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def _salvar_historico(historico: dict) -> None:
    """Salva o historico de movimentacoes."""
    with open(HISTORICO_PATH, "w", encoding="utf-8") as f:
        json.dump(historico, f, ensure_ascii=False, indent=2)


# --- Tools para o agente ---


def consultar_movimentacoes(numero_processo: str, tribunal: str) -> dict[str, Any]:
    """Consulta as movimentacoes de um processo na API DataJud do CNJ.

    Args:
        numero_processo: Numero unificado do processo (formato CNJ).
        tribunal: Sigla do tribunal (ex: TJSP, TRF3, STJ).

    Returns:
        Dicionario com as movimentacoes encontradas ou mensagem de erro.
    """
    endpoint = TRIBUNAIS.get(tribunal.upper())
    if not endpoint:
        return {
            "status": "erro",
            "mensagem": f"Tribunal '{tribunal}' nao suportado. "
            f"Tribunais disponiveis: {', '.join(TRIBUNAIS.keys())}",
        }

    # Numero limpo (apenas digitos)
    numero_limpo = numero_processo.replace("-", "").replace(".", "")

    url = f"{DATAJUD_BASE_URL}/{endpoint}/_search"
    headers = {
        "Authorization": f"APIKey {DATAJUD_API_KEY}",
        "Content-Type": "application/json",
    }
    body = {
        "query": {
            "match": {
                "numeroProcesso": numero_limpo,
            }
        },
        "size": 1,
    }

    try:
        response = requests.post(url, json=body, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Erro ao consultar DataJud para {numero_processo}: {e}")
        return {
            "status": "erro",
            "mensagem": f"Falha na consulta ao tribunal: {e}",
        }

    hits = data.get("hits", {}).get("hits", [])
    if not hits:
        return {
            "status": "sem_resultado",
            "mensagem": f"Processo {numero_processo} nao encontrado no {tribunal}.",
        }

    processo = hits[0].get("_source", {})
    movimentacoes = processo.get("movimentos", [])

    # Filtrar apenas movimentacoes novas (apos ultima verificacao)
    historico = _carregar_historico()
    ultima_verificacao = historico.get(numero_processo, {}).get(
        "ultima_verificacao", "1900-01-01T00:00:00"
    )

    novas = []
    for mov in movimentacoes:
        data_mov = mov.get("dataHora", "")
        if data_mov > ultima_verificacao:
            novas.append({
                "data": data_mov,
                "nome": mov.get("nome", "Sem descricao"),
                "codigo": mov.get("codigo", ""),
                "complemento": mov.get("complementosTabelados", []),
            })

    # Atualizar historico
    historico[numero_processo] = {
        "ultima_verificacao": datetime.now().isoformat(),
        "tribunal": tribunal,
        "total_movimentacoes": len(movimentacoes),
    }
    _salvar_historico(historico)

    # Dados basicos do processo
    info_processo = {
        "numero": numero_processo,
        "tribunal": tribunal,
        "classe": processo.get("classe", {}).get("nome", ""),
        "assunto": ", ".join(
            a.get("nome", "") for a in processo.get("assuntos", [])
        ),
        "orgao_julgador": processo.get("orgaoJulgador", {}).get("nome", ""),
    }

    return {
        "status": "sucesso",
        "processo": info_processo,
        "novas_movimentacoes": novas,
        "total_novas": len(novas),
        "total_movimentacoes": len(movimentacoes),
    }


def listar_processos_monitorados() -> dict[str, Any]:
    """Lista todos os processos da carteira que estao sendo monitorados.

    Returns:
        Dicionario com a lista de processos monitorados.
    """
    processos = []
    for p in PROCESSOS_MONITORADOS:
        processos.append({
            "numero": p["numero"],
            "tribunal": p["tribunal"],
            "responsavel": p.get("responsavel", "Nao definido"),
        })

    return {
        "status": "sucesso",
        "total": len(processos),
        "processos": processos,
    }


def registrar_movimentacao(
    numero_processo: str,
    data_movimentacao: str,
    descricao: str,
    classificacao: str,
) -> dict[str, Any]:
    """Registra uma movimentacao analisada no historico local.

    Args:
        numero_processo: Numero unificado do processo.
        data_movimentacao: Data da movimentacao.
        descricao: Descricao da movimentacao.
        classificacao: Classificacao: URGENTE, INFORMATIVO ou ROTINA.

    Returns:
        Confirmacao do registro.
    """
    historico = _carregar_historico()

    registro = historico.get(numero_processo, {})
    movimentacoes_registradas = registro.get("movimentacoes_registradas", [])
    movimentacoes_registradas.append({
        "data": data_movimentacao,
        "descricao": descricao,
        "classificacao": classificacao,
        "registrado_em": datetime.now().isoformat(),
    })

    registro["movimentacoes_registradas"] = movimentacoes_registradas
    historico[numero_processo] = registro
    _salvar_historico(historico)

    logger.info(
        f"Movimentacao registrada: {numero_processo} - "
        f"{classificacao} - {descricao[:80]}"
    )

    return {
        "status": "sucesso",
        "mensagem": f"Movimentacao registrada para {numero_processo}.",
        "classificacao": classificacao,
    }


def notificar_responsavel(
    numero_processo: str,
    responsavel: str,
    mensagem: str,
    canal: str = "email",
) -> dict[str, Any]:
    """Envia notificacao sobre movimentacao processual para o responsavel.

    Args:
        numero_processo: Numero do processo.
        responsavel: Nome do advogado responsavel.
        mensagem: Conteudo da notificacao com detalhes da movimentacao.
        canal: Canal de notificacao: 'email' ou 'slack'.

    Returns:
        Confirmacao do envio.
    """
    assunto = f"[Monitor Processual] Nova movimentacao - {numero_processo}"

    if canal == "slack" and SLACK_WEBHOOK_URL:
        try:
            payload = {
                "text": f"*{assunto}*\n\n{mensagem}",
            }
            resp = requests.post(
                SLACK_WEBHOOK_URL, json=payload, timeout=10
            )
            resp.raise_for_status()
            logger.info(f"Notificacao Slack enviada para {responsavel}.")
            return {
                "status": "sucesso",
                "mensagem": f"Notificacao enviada via Slack para {responsavel}.",
            }
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro ao enviar Slack: {e}")
            return {"status": "erro", "mensagem": f"Falha no envio Slack: {e}"}

    # Email
    if not SMTP_USER or not SMTP_PASSWORD:
        # Modo simulacao quando nao ha credenciais configuradas
        logger.info(
            f"[SIMULACAO] Email para {responsavel}: {assunto}\n{mensagem}"
        )
        return {
            "status": "sucesso",
            "mensagem": (
                f"[SIMULACAO] Notificacao registrada para {responsavel}. "
                "Configure SMTP_USER e SMTP_PASSWORD para envio real."
            ),
        }

    try:
        # Buscar email do responsavel na carteira
        email_dest = EMAIL_DESTINATARIO
        for p in PROCESSOS_MONITORADOS:
            if p["numero"] == numero_processo:
                email_dest = p.get("email_responsavel", EMAIL_DESTINATARIO)
                break

        msg = MIMEText(mensagem, "plain", "utf-8")
        msg["Subject"] = assunto
        msg["From"] = SMTP_USER
        msg["To"] = email_dest

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)

        logger.info(f"Email enviado para {responsavel} ({email_dest}).")
        return {
            "status": "sucesso",
            "mensagem": f"Email enviado para {responsavel} ({email_dest}).",
        }
    except Exception as e:
        logger.error(f"Erro ao enviar email: {e}")
        return {"status": "erro", "mensagem": f"Falha no envio de email: {e}"}
