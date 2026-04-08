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
from datetime import date, datetime
from email.mime.text import MIMEText
from typing import Any

import requests

from . import settings
from .classificacao import classificar_movimentacao
from .prazos import calcular_prazo_publicacao_dje
from .prazos import PRAZOS_COMUNS

logger = logging.getLogger("monitor_processual." + __name__)


# --- Historico local ---


def _carregar_historico() -> dict:
    """Carrega o historico de movimentacoes ja vistas."""
    if os.path.exists(settings.HISTORICO_PATH):
        with open(settings.HISTORICO_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def _salvar_historico(historico: dict) -> None:
    """Salva o historico de movimentacoes."""
    with open(settings.HISTORICO_PATH, "w", encoding="utf-8") as f:
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
    endpoint = settings.TRIBUNAIS.get(tribunal.upper())
    if not endpoint:
        return {
            "status": "erro",
            "mensagem": f"Tribunal '{tribunal}' nao suportado. "
            f"Tribunais disponiveis: {', '.join(settings.TRIBUNAIS.keys())}",
        }

    numero_limpo = numero_processo.replace("-", "").replace(".", "")

    url = f"{settings.DATAJUD_BASE_URL}/{endpoint}/_search"
    headers = {
        "Authorization": f"APIKey {settings.DATAJUD_API_KEY}",
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
    for p in settings.PROCESSOS_MONITORADOS:
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

    if canal == "slack" and settings.SLACK_WEBHOOK_URL:
        try:
            payload = {
                "text": f"*{assunto}*\n\n{mensagem}",
            }
            resp = requests.post(
                settings.SLACK_WEBHOOK_URL, json=payload, timeout=10
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

    if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
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
        email_dest = settings.EMAIL_DESTINATARIO
        for p in settings.PROCESSOS_MONITORADOS:
            if p["numero"] == numero_processo:
                email_dest = p.get("email_responsavel", settings.EMAIL_DESTINATARIO)
                break

        msg = MIMEText(mensagem, "plain", "utf-8")
        msg["Subject"] = assunto
        msg["From"] = settings.SMTP_USER
        msg["To"] = email_dest

        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.send_message(msg)

        logger.info(f"Email enviado para {responsavel} ({email_dest}).")
        return {
            "status": "sucesso",
            "mensagem": f"Email enviado para {responsavel} ({email_dest}).",
        }
    except Exception as e:
        logger.error(f"Erro ao enviar email: {e}")
        return {"status": "erro", "mensagem": f"Falha no envio de email: {e}"}


def calcular_prazo_processual(
    data_publicacao: str,
    tipo_prazo: str,
    tribunal: str = "",
    fazenda_publica: bool = False,
) -> dict[str, Any]:
    """Calcula o prazo processual a partir da data de publicacao no DJe.

    Aplica as regras do CPC 2015:
    - Art. 219: Contagem em dias uteis.
    - Art. 224: Exclui o dia do inicio, inclui o dia do vencimento.
    - Lei 11.419/2006: Intimacao no 1o dia util apos publicacao no DJe.
    - Art. 183/186: Prazo em dobro para Fazenda/Defensoria Publica.

    Args:
        data_publicacao: Data da publicacao no DJe (formato YYYY-MM-DD).
        tipo_prazo: Tipo do prazo (ex: 'contestacao', 'apelacao', 'embargos_declaracao').
            Tipos disponiveis: contestacao, replica, apelacao, contrarrazoes_apelacao,
            agravo_instrumento, embargos_declaracao, recurso_especial,
            recurso_extraordinario, embargos_execucao, impugnacao_cumprimento_sentenca,
            manifestacao_generica_5, manifestacao_generica_15, agravo_interno.
        tribunal: Sigla do tribunal para considerar feriados estaduais.
        fazenda_publica: Se a parte contraria e Fazenda ou Defensoria Publica.

    Returns:
        Dicionario com datas de intimacao, inicio e vencimento do prazo.
    """
    prazo_info = PRAZOS_COMUNS.get(tipo_prazo)
    if not prazo_info:
        tipos_disponiveis = ", ".join(sorted(PRAZOS_COMUNS.keys()))
        return {
            "status": "erro",
            "mensagem": f"Tipo de prazo '{tipo_prazo}' nao encontrado. "
            f"Tipos disponiveis: {tipos_disponiveis}",
        }

    try:
        data = date.fromisoformat(data_publicacao)
    except ValueError:
        return {
            "status": "erro",
            "mensagem": f"Data invalida: {data_publicacao}. Use formato YYYY-MM-DD.",
        }

    # Obter estado do tribunal para feriados
    estado = settings.TRIBUNAL_ESTADO.get(tribunal.upper())

    resultado = calcular_prazo_publicacao_dje(
        data_publicacao=data,
        dias=prazo_info["dias"],
        estado=estado,
        prazo_em_dobro=fazenda_publica,
    )

    resultado["tipo_prazo"] = tipo_prazo
    resultado["referencia_legal"] = prazo_info["referencia"]
    resultado["status"] = "sucesso"

    return resultado


def classificar_movimentacao_processual(
    nome_movimentacao: str,
    codigo_movimentacao: int = 0,
) -> dict[str, Any]:
    """Classifica uma movimentacao processual por nivel de urgencia.

    Usa os codigos das Tabelas Processuais Unificadas (TPU) do CNJ quando
    disponiveis, com fallback para analise textual.

    Classificacoes:
    - URGENTE: Intimacoes, citacoes, sentencas, decisoes, penhoras, audiencias.
    - INFORMATIVO: Juntadas, conclusoes, redistribuicoes.
    - ROTINA: Movimentacoes de cartorio, certificacoes, remessas.

    Args:
        nome_movimentacao: Descricao textual da movimentacao.
        codigo_movimentacao: Codigo TPU da movimentacao (0 se desconhecido).

    Returns:
        Dicionario com classificacao, prazo sugerido e referencia legal.
    """
    resultado = classificar_movimentacao(
        codigo=codigo_movimentacao if codigo_movimentacao else None,
        nome=nome_movimentacao,
    )
    resultado["status"] = "sucesso"
    return resultado


def gerar_relatorio_carteira() -> dict[str, Any]:
    """Gera um relatorio consolidado da carteira de processos monitorados.

    Retorna estatisticas da carteira: total por area, fase, tribunal,
    responsavel e prioridade. Util para visao gerencial.

    Returns:
        Dicionario com estatisticas consolidadas da carteira.
    """
    processos = settings.PROCESSOS_MONITORADOS

    if not processos:
        return {
            "status": "sucesso",
            "total": 0,
            "mensagem": "Nenhum processo na carteira.",
        }

    # Contadores
    por_area = {}
    por_fase = {}
    por_tribunal = {}
    por_responsavel = {}
    por_prioridade = {}
    valor_total = 0.0

    for p in processos:
        area = p.get("area", "nao_classificado")
        fase = p.get("fase", "nao_classificado")
        tribunal = p.get("tribunal", "desconhecido")
        resp = p.get("responsavel", "nao_atribuido")
        prio = p.get("prioridade", "normal")
        valor = p.get("valor_causa", 0.0)

        por_area[area] = por_area.get(area, 0) + 1
        por_fase[fase] = por_fase.get(fase, 0) + 1
        por_tribunal[tribunal] = por_tribunal.get(tribunal, 0) + 1
        por_responsavel[resp] = por_responsavel.get(resp, 0) + 1
        por_prioridade[prio] = por_prioridade.get(prio, 0) + 1
        valor_total += valor

    # Historico de movimentacoes recentes
    historico = _carregar_historico()
    processos_com_movimentacao = sum(
        1 for p in processos
        if p["numero"] in historico
        and historico[p["numero"]].get("movimentacoes_registradas")
    )

    return {
        "status": "sucesso",
        "total_processos": len(processos),
        "valor_total_carteira": valor_total,
        "por_area": por_area,
        "por_fase": por_fase,
        "por_tribunal": por_tribunal,
        "por_responsavel": por_responsavel,
        "por_prioridade": por_prioridade,
        "processos_com_movimentacao_recente": processos_com_movimentacao,
    }
