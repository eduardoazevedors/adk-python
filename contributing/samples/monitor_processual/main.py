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

"""Ponto de entrada para o monitor de movimentacoes processuais.

Uso:
    # Instalar dependencias
    pip install -e ".[dev]"

    # Execucao automatica (verifica todos os processos)
    monitor-processual
    # ou: python -m monitor_processual.main

    # Modo interativo (consultas sob demanda)
    monitor-processual --interativo
    # ou: python -m monitor_processual.main --interativo

    # Via ADK CLI (UI web)
    adk web .

    # Agendar via crontab (diariamente as 8h)
    # 0 8 * * * cd /caminho/do/projeto && monitor-processual
"""

import asyncio
import logging
import sys

from google.adk.runners import InMemoryRunner
from google.genai import types

from .agent import root_agent
from .settings import PROCESSOS_MONITORADOS

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("monitor_processual")

APP_NAME = "monitor_processual"
USER_ID = "monitor_user"


async def executar_verificacao():
    """Executa a verificacao completa de todos os processos da carteira."""
    total = len(PROCESSOS_MONITORADOS)
    logger.info(f"--- Iniciando monitoramento de {total} processo(s) ---")

    if total == 0:
        logger.warning(
            "Nenhum processo configurado. "
            "Edite processos.json para adicionar processos."
        )
        return

    runner = InMemoryRunner(agent=root_agent, app_name=APP_NAME)
    session = await runner.session_service.create_session(
        user_id=USER_ID, app_name=APP_NAME
    )

    prompt = (
        "Verifique todas as movimentacoes dos processos da carteira. "
        "Para cada processo, consulte o tribunal, analise as movimentacoes "
        "novas, classifique por urgencia e notifique os responsaveis "
        "conforme as regras."
    )

    message = types.Content(
        role="user",
        parts=[types.Part(text=prompt)],
    )

    logger.info("Enviando tarefa para o pipeline de agentes...")

    async for event in runner.run_async(
        user_id=USER_ID,
        session_id=session.id,
        new_message=message,
    ):
        if (
            event.content
            and event.content.parts
            and hasattr(event.content.parts[0], "text")
        ):
            text = event.content.parts[0].text
            if text:
                agent_name = getattr(event, "author", "agente")
                logger.info(f"[{agent_name}] {text[:200]}")

    logger.info("--- Monitoramento concluido ---")


async def modo_interativo():
    """Modo interativo para consultas sob demanda."""
    runner = InMemoryRunner(agent=root_agent, app_name=APP_NAME)
    session = await runner.session_service.create_session(
        user_id=USER_ID, app_name=APP_NAME
    )

    print("\n=== Monitor Processual - Modo Interativo ===")
    print("Comandos:")
    print("  'verificar'    - Verificar todos os processos")
    print("  'consultar X'  - Consultar processo especifico")
    print("  'sair'         - Encerrar")
    print()

    while True:
        try:
            entrada = input(">> ").strip()
        except (EOFError, KeyboardInterrupt):
            break

        if not entrada:
            continue
        if entrada.lower() == "sair":
            break

        message = types.Content(
            role="user",
            parts=[types.Part(text=entrada)],
        )

        async for event in runner.run_async(
            user_id=USER_ID,
            session_id=session.id,
            new_message=message,
        ):
            if (
                event.content
                and event.content.parts
                and hasattr(event.content.parts[0], "text")
            ):
                text = event.content.parts[0].text
                if text:
                    print(text)

    print("Encerrando.")


def cli():
    """Ponto de entrada para o comando 'monitor-processual'."""
    if "--interativo" in sys.argv:
        asyncio.run(modo_interativo())
    else:
        asyncio.run(executar_verificacao())


if __name__ == "__main__":
    cli()
