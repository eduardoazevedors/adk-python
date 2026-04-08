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

"""Agente de monitoramento de movimentacoes processuais."""

from google.adk.agents import SequentialAgent
from google.adk.agents.llm_agent import Agent

from monitor_processual.settings import LLM_MODEL_NAME
from monitor_processual.tools import consultar_movimentacoes
from monitor_processual.tools import listar_processos_monitorados
from monitor_processual.tools import notificar_responsavel
from monitor_processual.tools import registrar_movimentacao

# --- Agente 1: Monitor ---
# Consulta os tribunais e coleta movimentacoes novas.

monitor_agent = Agent(
    model=LLM_MODEL_NAME,
    name="monitor_processual",
    description="Consulta tribunais e coleta novas movimentacoes processuais.",
    instruction="""Voce e um assistente juridico especializado em monitoramento processual.

Sua tarefa:
1. Use a ferramenta 'listar_processos_monitorados' para obter a carteira de processos.
2. Para CADA processo da lista, use 'consultar_movimentacoes' passando o numero e o tribunal.
3. Retorne um resumo consolidado com:
   - Processos consultados
   - Novas movimentacoes encontradas (com data e descricao)
   - Processos sem novidades

Formato do resumo:
PROCESSO: [numero] ([tribunal])
NOVAS MOVIMENTACOES: [quantidade]
- [data] - [descricao da movimentacao]

Se nao houver movimentacoes novas para um processo, informe: "Sem novidades."
""",
    tools=[consultar_movimentacoes, listar_processos_monitorados],
)

# --- Agente 2: Analista ---
# Classifica cada movimentacao por urgencia.

analista_agent = Agent(
    model=LLM_MODEL_NAME,
    name="analista_processual",
    description="Analisa e classifica movimentacoes processuais por urgencia.",
    instruction="""Voce e um analista juridico especializado em classificacao de movimentacoes.

Analise cada movimentacao processual recebida e classifique como:

**URGENTE** - Requer acao imediata:
- Intimacao (qualquer tipo)
- Citacao
- Sentenca ou acordao
- Decisao interlocutoria
- Despacho com prazo
- Trânsito em julgado
- Penhora ou bloqueio
- Hasta publica / leilao
- Tutela de urgencia

**INFORMATIVO** - Importante mas sem prazo imediato:
- Juntada de documento
- Conclusao ao juiz
- Vista ao Ministerio Publico
- Pericia designada
- Audiencia designada
- Redistribuicao

**ROTINA** - Apenas registro:
- Movimentacao de cartorio
- Remessa / retorno de autos
- Certificacao
- Numeracao de paginas
- Atualizacao de sistema

Para cada movimentacao, use a ferramenta 'registrar_movimentacao' com a classificacao.

Retorne um relatorio organizado por classificacao:

## URGENTES (requer acao imediata)
- [processo] - [data] - [movimentacao] - [acao recomendada]

## INFORMATIVOS
- [processo] - [data] - [movimentacao]

## ROTINA
- [processo] - [data] - [movimentacao]
""",
    tools=[registrar_movimentacao],
)

# --- Agente 3: Notificador ---
# Envia alertas conforme a classificacao.

notificador_agent = Agent(
    model=LLM_MODEL_NAME,
    name="notificador_processual",
    description="Envia notificacoes sobre movimentacoes processuais.",
    instruction="""Voce e responsavel por notificar a equipe juridica sobre movimentacoes processuais.

Regras de notificacao:

1. **URGENTE**: Notifique IMEDIATAMENTE o advogado responsavel.
   - Use a ferramenta 'notificar_responsavel' com canal 'email'.
   - A mensagem deve conter: numero do processo, movimentacao, data e acao recomendada.
   - Exemplo de acao: "Intimacao recebida - verificar prazo e providenciar resposta."

2. **INFORMATIVO**: Inclua no resumo diario.
   - Use 'notificar_responsavel' com canal 'email' agrupando todas as movimentacoes
     informativas em uma unica mensagem por responsavel.

3. **ROTINA**: NAO notifique. Apenas confirme que foram registradas.

Ao final, retorne um resumo das notificacoes enviadas:
- Quantas notificacoes urgentes foram enviadas
- Quantos responsaveis foram notificados
- Movimentacoes de rotina registradas sem notificacao
""",
    tools=[notificar_responsavel],
)

# --- Pipeline completo ---

root_agent = SequentialAgent(
    name="monitor_juridico",
    description=(
        "Pipeline completo de monitoramento processual: "
        "consulta tribunais, classifica movimentacoes e notifica a equipe."
    ),
    sub_agents=[monitor_agent, analista_agent, notificador_agent],
)
