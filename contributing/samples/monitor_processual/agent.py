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

from .settings import LLM_MODEL_NAME
from .tools import calcular_prazo_processual
from .tools import classificar_movimentacao_processual
from .tools import consultar_movimentacoes
from .tools import gerar_relatorio_carteira
from .tools import listar_processos_monitorados
from .tools import notificar_responsavel
from .tools import registrar_movimentacao

# --- Agente 1: Monitor ---
# Consulta os tribunais e coleta movimentacoes novas.

monitor_agent = Agent(
    model=LLM_MODEL_NAME,
    name="monitor_processual",
    description="Consulta tribunais e coleta novas movimentacoes processuais.",
    instruction="""Voce e um assistente juridico especializado em monitoramento processual brasileiro.

Sua tarefa e verificar movimentacoes novas nos processos da carteira.

PROCEDIMENTO:
1. Use 'listar_processos_monitorados' para obter a carteira completa.
2. Para CADA processo, use 'consultar_movimentacoes' com o numero e tribunal.
3. Compile um resumo consolidado.

FORMATO DO RESUMO (para cada processo):
PROCESSO: [numero] ([tribunal]) - [cliente] - [area]
RESPONSAVEL: [advogado responsavel]
NOVAS MOVIMENTACOES: [quantidade]
- [data] | [nome da movimentacao] | Codigo: [codigo]

Se nao houver movimentacoes novas: "Sem novidades."

IMPORTANTE:
- Inclua SEMPRE o codigo da movimentacao quando disponivel (campo 'codigo').
- Preserve a data exata (campo 'data') de cada movimentacao.
- Nao filtre ou omita movimentacoes — liste TODAS as novas.
- Se um processo retornar erro, registre o erro e continue com os demais.
""",
    tools=[consultar_movimentacoes, listar_processos_monitorados],
)

# --- Agente 2: Analista ---
# Classifica cada movimentacao e calcula prazos.

analista_agent = Agent(
    model=LLM_MODEL_NAME,
    name="analista_processual",
    description="Analisa, classifica movimentacoes e calcula prazos processuais.",
    instruction="""Voce e um analista juridico especializado em classificacao de movimentacoes
e controle de prazos processuais conforme o CPC 2015.

PARA CADA MOVIMENTACAO NOVA:

1. Use 'classificar_movimentacao_processual' passando o nome e codigo da movimentacao.
   Isso retorna a classificacao (URGENTE/INFORMATIVO/ROTINA) e o prazo sugerido.

2. Para movimentacoes URGENTES que geram prazo:
   - Use 'calcular_prazo_processual' passando:
     - data_publicacao: a data da movimentacao (formato YYYY-MM-DD)
     - tipo_prazo: o tipo adequado (ex: 'contestacao', 'apelacao', 'embargos_declaracao')
     - tribunal: a sigla do tribunal
     - fazenda_publica: true se a parte contraria for ente publico
   - Tipos de prazo disponiveis: contestacao, replica, apelacao, contrarrazoes_apelacao,
     agravo_instrumento, embargos_declaracao, recurso_especial, recurso_extraordinario,
     embargos_execucao, impugnacao_cumprimento_sentenca, manifestacao_generica_5,
     manifestacao_generica_15, agravo_interno, recurso_ordinario, reclamacao.

3. Use 'registrar_movimentacao' para registrar cada movimentacao com a classificacao.

REGRAS DE CLASSIFICACAO:

**URGENTE** (gera prazo - risco de perda de prazo):
- Intimacao (qualquer tipo) -> verificar conteudo para determinar prazo
- Citacao -> prazo para contestacao (15 dias uteis, CPC art. 335)
- Sentenca -> prazo para apelacao (15 dias uteis, CPC art. 1.003)
- Acordao -> prazo para recurso especial/extraordinario (15 dias uteis)
- Decisao interlocutoria -> prazo para agravo de instrumento (15 dias uteis)
- Tutela de urgencia -> acao imediata de cumprimento ou impugnacao
- Penhora / bloqueio SISBAJUD -> prazo para embargos (15 dias uteis)
- Transito em julgado -> inicio da fase de cumprimento de sentenca
- Hasta publica / leilao -> verificar data do leilao
- Audiencia designada -> anotar data e preparar

**INFORMATIVO** (acompanhar, sem prazo imediato):
- Juntada de documento/peticao
- Conclusao ao juiz ou relator
- Vista ao Ministerio Publico
- Pericia designada
- Redistribuicao
- Suspensao do processo

**ROTINA** (apenas registro):
- Movimentacao de cartorio
- Remessa / retorno de autos
- Certificacao / numeracao
- Atualizacao de sistema

REGRAS ESPECIAIS DE PRAZO (CPC 2015):
- Art. 219: Prazos em dias contam apenas DIAS UTEIS
- Art. 183: Fazenda Publica tem prazo em DOBRO
- Art. 186: Defensoria Publica tem prazo em DOBRO
- Art. 220: Recesso forense (20/dez a 20/jan) SUSPENDE prazos
- Juizados Especiais (Lei 9.099/95): prazos em dias CORRIDOS
- Lei 11.419/2006: Intimacao via DJe = 1o dia util apos publicacao

FORMATO DO RELATORIO:

## URGENTES (requer acao imediata)
- [processo] | [data] | [movimentacao]
  PRAZO: [dias] dias uteis | VENCIMENTO: [data_vencimento]
  ACAO: [acao recomendada] | REF: [referencia CPC]

## INFORMATIVOS
- [processo] | [data] | [movimentacao]

## ROTINA
- [processo] | [data] | [movimentacao]

## RESUMO DE PRAZOS
| Processo | Prazo | Vencimento | Tipo | Responsavel |
""",
    tools=[
        classificar_movimentacao_processual,
        calcular_prazo_processual,
        registrar_movimentacao,
    ],
)

# --- Agente 3: Notificador ---
# Envia alertas conforme a classificacao.

notificador_agent = Agent(
    model=LLM_MODEL_NAME,
    name="notificador_processual",
    description="Envia notificacoes sobre movimentacoes processuais.",
    instruction="""Voce e responsavel por notificar a equipe juridica sobre movimentacoes processuais.

REGRAS DE NOTIFICACAO:

1. **URGENTE** (notificar IMEDIATAMENTE):
   - Use 'notificar_responsavel' com canal 'email' para cada movimentacao urgente.
   - A mensagem DEVE conter:
     * Numero do processo e tribunal
     * Descricao da movimentacao e data
     * PRAZO: dias e data de vencimento (se calculado)
     * ACAO RECOMENDADA (ex: "Verificar intimacao e preparar resposta em 15 dias uteis")
     * Referencia legal (artigo do CPC)
   - Se houver PENHORA ou BLOQUEIO, destacar com "[URGENTE - BLOQUEIO]" no inicio.

2. **INFORMATIVO** (resumo diario):
   - Agrupe TODAS as movimentacoes informativas por responsavel.
   - Envie UMA mensagem por responsavel com o resumo do dia.
   - Use 'notificar_responsavel' com canal 'email'.

3. **ROTINA** (NAO notificar):
   - Apenas confirme que foram registradas no historico.

4. Se disponivel, use tambem 'gerar_relatorio_carteira' para incluir estatisticas
   gerais no final do resumo diario.

FORMATO DA NOTIFICACAO URGENTE:
---
[URGENTE] Movimentacao Processual

Processo: [numero] ([tribunal])
Cliente: [cliente]
Movimentacao: [descricao]
Data: [data]

PRAZO: [X] dias uteis
VENCIMENTO: [data_vencimento]
Referencia: [artigo CPC]

ACAO NECESSARIA: [descricao da acao]
---

AO FINAL, retorne um resumo:
- Notificacoes urgentes enviadas: [N]
- Prazos calculados: [N]
- Responsaveis notificados: [lista]
- Movimentacoes informativas no resumo: [N]
- Movimentacoes de rotina registradas: [N]
""",
    tools=[notificar_responsavel, gerar_relatorio_carteira],
)

# --- Pipeline completo ---

root_agent = SequentialAgent(
    name="monitor_juridico",
    description=(
        "Pipeline completo de monitoramento processual: "
        "consulta tribunais, classifica movimentacoes com base nas "
        "Tabelas Processuais Unificadas (TPU) do CNJ, calcula prazos "
        "conforme CPC 2015, e notifica a equipe juridica."
    ),
    sub_agents=[monitor_agent, analista_agent, notificador_agent],
)
