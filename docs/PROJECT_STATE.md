# Conferência Documento - Estado Atual do Projeto

Atualizado em: 2026-05-17

## Objetivo do Sistema

O Conferência Documento é uma plataforma interna da Consiste Contabilidade para o setor LEGAL/SOCIETÁRIO.

O objetivo é revisar, grifar, explicar, corrigir e finalizar minutas societárias brasileiras com apoio de API de inteligência artificial, mantendo revisão humana obrigatória antes de qualquer documento final para protocolo.

O sistema é uma ferramenta operacional avançada de conferência documental. Ele não substitui advogado, não toma decisão jurídica definitiva e não deve alterar dados sensíveis sem confirmação humana.

## Stack

- Python 3.12+
- Flask
- SQLite
- PyMuPDF
- python-docx
- reportlab
- python-dotenv
- OpenAI API ou camada compatível
- HTML/CSS simples
- pytest

## Arquitetura

Estrutura principal:

- `app/routes/`: rotas Flask de dashboard, upload, revisão, geração e exportação.
- `app/services/`: serviços de domínio e orquestração.
- `app/ai/`: cliente de IA, prompts, JSON guard e schemas.
- `app/repositories/`: acesso ao SQLite.
- `app/database/`: conexão e schema do banco.
- `app/templates/`: interface HTML.
- `app/static/`: CSS/JS.
- `scripts/`: avaliação operacional, manifesto e teste de IA.
- `tests/`: testes automatizados e estrutura das bases de referência.
- `docs/`: documentação técnica.

Arquivos centrais:

- `app/services/review_orchestrator_service.py`: coordena o fluxo de revisão.
- `app/services/rule_review_service.py`: regras fixas de apoio.
- `app/services/ai_review_service.py`: prepara contexto e chama IA revisora.
- `app/ai/client.py`: ponto único de chamada à API.
- `app/ai/json_guard.py`: extrai, valida e normaliza JSON da IA.
- `app/services/issue_merge_service.py`: consolida RULE/AI/BOTH.
- `app/services/pdf_locator_service.py`: localiza trechos no PDF.
- `app/services/pdf_annotation_service.py`: gera PDF grifado.
- `app/services/report_pdf_service.py`: gera relatório técnico.
- `app/services/corrected_document_service.py`: gera documento corrigido para revisão.
- `app/services/final_document_service.py`: gera documento final para protocolo.
- `app/services/docx_output_service.py`: formata DOCX/PDF corrigido e final.
- `app/document_types/catalog.py`: catálogo interno de tipos documentais para criação futura.
- `app/services/ltda_generation_service.py`: gera minuta padrão de constituição de LTDA.
- `app/services/ltda_generation_validation_service.py`: valida formulário estruturado de constituição de LTDA.
- `app/services/advanced_case_detector_service.py`: bloqueia casos avançados no modelo padrão.
- `app/generation/generation_payload_builder.py`: monta payload estruturado para geração.
- `scripts/avaliar_revisao.py`: avaliação operacional mock/api/compare/summary.
- `scripts/criar_manifesto_base.py`: manifesto local de base de referência.

## Versões Concluídas

### V1

Base funcional Flask:

- upload de PDF/DOCX;
- extração de texto;
- regras fixas iniciais;
- camada IA mock/api;
- banco SQLite;
- PDF grifado;
- relatório;
- base de DOCX/PDF corrigido e final.

### V2

Avaliação operacional:

- estrutura `tests/documentos_referencia/`;
- script `scripts/avaliar_revisao.py`;
- métricas por documento;
- comparação mock/api.

### V2.1

Calibração inicial com documentos reais:

- melhor extração de empresa;
- regras de qualificação de sócios;
- regras para AGE/estatuto;
- relatórios com acentuação correta;
- melhoria de códigos no PDF.

### V2.2

Preparação para API real:

- `scripts/testar_ia.py`;
- modo compare mock/api;
- fallback seguro;
- exibição de origem RULE/AI/BOTH;
- documentação de uso da API.

### V2.3

Correção de falsos positivos da IA:

- contexto de administrador/administradora;
- bloqueio de sugestão absurda para termos jurídicos;
- preservação de expressões como `peita ou suborno`;
- deduplicação de substrings;
- testes de proteção.

### V2.4

Consolidação da revisão API:

- localização PDF aprimorada;
- estratégia de localização;
- repetição de ocorrência em páginas diferentes;
- resumo API;
- prompt mais forte para AGE/estatuto;
- classificação melhor de itens sensíveis.

### V2.5

Base de Referência 01:

- estrutura `tests/documentos_referencia/base_01/`;
- categorias documentais;
- manifesto local;
- checklist humano;
- risk_score/risk_level;
- resumo consolidado;
- proteção LGPD para documentos reais.

### V3

Visual profissional de PDF grifado e relatório:

- capa/resumo executivo;
- cores por gravidade;
- sumário de apontamentos;
- blocos detalhados;
- layout profissional;
- nomes de arquivos profissionais;
- interface de download melhorada.

### V4

Documento corrigido e final:

- distinção entre corrigido para revisão e final para protocolo;
- prompts de geração corrigida/final reforçados;
- auditoria de correções;
- confirmação humana obrigatória;
- proteção contra aplicação automática de itens sensíveis;
- DOCX/PDF corrigido e final.

### V4.1

Acabamento visual de DOCX/PDF:

- margens profissionais;
- Times New Roman;
- títulos e razão social centralizados;
- cláusulas/artigos em negrito;
- parágrafos justificados;
- assinaturas mais organizadas;
- proteção reforçada também na etapa final;
- validação com documento de referência em `AI_MODE=api`;
- testes automatizados ampliados.

### V5.0

Catálogo interno de tipos documentais e preparação da experiência de criação:

- pacote `app/document_types/`;
- catálogo de LTDA, S/A, Empresário Individual / SLU e documentos acessórios;
- funções públicas de consulta, busca, agrupamento e menu de criação;
- dashboard com dois caminhos simples;
- tela de criação por categoria amigável;
- tela de detalhe do tipo documental;
- formulário visual preparatório;
- documentação em `docs/DOCUMENT_TYPE_CATALOG.md`;
- sem geração real de minuta;
- sem chamada de IA;
- sem persistência de formulário no banco.

### V5.1

Primeiro gerador real de minuta:

- implementação de `CONSTITUICAO_LTDA_PADRAO`;
- formulário guiado para constituição padrão de LTDA;
- payload estruturado em `app/generation/`;
- validação de campos obrigatórios, capital, quotas, percentuais e administrador;
- detector de caso avançado para impedir uso indevido do modelo padrão;
- prompt `generate_constituicao_ltda.md`;
- serviço `LtdaGenerationService`;
- geração mock de minuta para desenvolvimento local;
- geração de DOCX/PDF para revisão em `storage/generated`;
- gravação local do payload de geração;
- tela de resultado com aviso de revisão humana;
- bloqueio de geração padrão para casos avançados;
- sem dependência de OCR como fonte primária.

Último commit publicado da V4.1:

```text
83fd629 V4.1-polish-final-document-layout
```

## Comandos Principais

Instalação:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Execução local:

```bash
python run.py
```

Acesso:

```text
http://127.0.0.1:5060
```

Testes:

```bash
python -m pytest -q
python -m compileall app scripts tests
```

## Decisão V5 Sobre OCR

Para criação de minutas do zero, dados sensíveis não devem depender de OCR.

Documentos de identidade, contratos antigos e comprovantes podem estar em imagem, baixa resolução ou com texto ruim. OCR pode errar nomes, CPF, RG, CNH, endereços, valores e outros dados críticos.

Portanto:

- campos obrigatórios devem ser preenchidos manualmente;
- OCR pode ser apoio futuro;
- OCR nunca será fonte automática definitiva;
- IA não deve inventar dados ausentes;
- a geração real de minuta deve partir de dados estruturados e confirmados pelo usuário.

## Próximo Passo Recomendado - V5.2

Evoluir a geração iniciada na V5.1 sem ampliar tipos documentais antes de estabilizar `CONSTITUICAO_LTDA_PADRAO`.

Escopo recomendado:

1. Revisar automaticamente a minuta gerada usando o motor de revisão existente.
2. Integrar a minuta gerada ao fluxo de PDF grifado e relatório técnico.
3. Permitir confirmação humana dos dados antes de chamar IA.
4. Evoluir o formulário para múltiplos sócios dinâmicos no frontend.
5. Criar histórico/persistência própria de gerações, se necessário.
6. Preparar fluxo final para protocolo a partir da minuta gerada e revisada.

Teste de conectividade IA:

```bash
python scripts/testar_ia.py
```

Avaliação padrão:

```bash
python scripts/avaliar_revisao.py --mode mock
python scripts/avaliar_revisao.py --mode api
python scripts/avaliar_revisao.py --compare
python scripts/avaliar_revisao.py --api-summary
```

Base de Referência 01:

```bash
python scripts/criar_manifesto_base.py --base base_01
python scripts/avaliar_revisao.py --base base_01 --mode mock
python scripts/avaliar_revisao.py --base base_01 --mode api
python scripts/avaliar_revisao.py --base base_01 --compare
python scripts/avaliar_revisao.py --base base_01 --api-summary
```

## Configuração da API

Configurar localmente no `.env`:

```env
AI_MODE=api
OPENAI_API_KEY=<chave-local>
OPENAI_MODEL=gpt-4.1-mini
DEFAULT_OPENAI_MODEL=gpt-4.1-mini
OPENAI_TIMEOUT=120
SAVE_AI_RAW=false
```

Nunca colocar chave no código, no Git, em documentação pública ou em mensagens de chat.

## Fluxo de Revisão

Fluxo principal em `ReviewOrchestratorService`:

1. Carrega documento.
2. Extrai texto por página.
3. Classifica tipo documental e empresa.
4. Roda regras fixas.
5. Chama IA revisora se `AI_MODE=api`.
6. Usa mock/fallback quando aplicável.
7. Consolida apontamentos em `IssueMergeService`.
8. Localiza trechos com `PdfLocatorService`.
9. Salva sessão e issues no banco.
10. Gera PDF grifado.
11. Gera relatório técnico.
12. Disponibiliza arquivos para download.
13. Permite gerar documento corrigido.
14. Permite gerar final somente após confirmação humana.

## Fluxo da API

Toda chamada passa por `app/ai/client.py`.

Modos:

- `AI_MODE=mock`: não chama API, usa regras/mock.
- `AI_MODE=api`: chama OpenAI API com chave do `.env`.

O client:

- usa `OPENAI_API_KEY`;
- usa `OPENAI_MODEL` ou `DEFAULT_OPENAI_MODEL`;
- exige resposta JSON;
- usa `json_guard`;
- trata timeout, autenticação, modelo inválido, JSON inválido e resposta vazia;
- não loga texto completo sensível;
- salva raw apenas se `SAVE_AI_RAW=true` e ambiente local.

## Fluxo do PDF Grifado

1. Issues consolidadas recebem `original_text`.
2. `PdfLocatorService` tenta localizar por estratégia:
   - exata;
   - normalizada;
   - substring;
   - expressão-chave.
3. Cada issue recebe `located_in_pdf` e `location_strategy`.
4. `PdfAnnotationService` abre o PDF com PyMuPDF.
5. Aplica highlight discreto.
6. Insere código próximo ao trecho ou em margem.
7. Anexa relatório visual ao PDF.
8. Gera arquivo em `storage/annotated`.

Se o trecho não for localizado, ele continua no relatório.

## Fluxo do Corrigido e Final

### Corrigido Para Revisão

Serviço: `CorrectedDocumentService`.

Características:

- usa texto original e apontamentos;
- em API, usa prompt `generate_corrected_document.md`;
- em mock, aplica substituições simples apenas quando seguras;
- não aplica automaticamente itens protegidos;
- gera DOCX/PDF em `storage/corrected`;
- gera JSON de auditoria de correções;
- status: `CORRIGIDO_PARA_REVISAO`.

### Final Para Protocolo

Serviço: `FinalDocumentService`.

Características:

- exige documento corrigido;
- exige confirmação humana;
- usa prompt `generate_final_document.md`;
- remove observações internas;
- protege trechos sensíveis também na etapa final;
- gera DOCX/PDF em `storage/final`;
- status: `FINAL_PARA_PROTOCOLO`;
- não deve conter grifos, comentários, alertas internos, relatório ou menção à IA.

## Base de Referência 01

Estrutura:

```text
tests/documentos_referencia/base_01/
├── entrada/
│   ├── constituicao_ltda/
│   ├── alteracao_endereco/
│   ├── alteracao_socios/
│   ├── alteracao_capital/
│   ├── alteracao_objeto/
│   ├── consolidacao_contratual/
│   ├── ata_age/
│   ├── ata_ago/
│   ├── estatuto_social/
│   └── documentos_bons/
├── saida/
├── relatorios_avaliacao/
├── checklist_humano/
└── README_BASE_01.md
```

Uso:

- colocar documentos reais localmente em `entrada/<categoria>`;
- gerar manifesto;
- rodar mock;
- rodar API em lotes pequenos;
- gerar resumo;
- preencher checklist humano.

Documentos reais, saídas, JSONs e checklists preenchidos não devem subir ao Git.

## Proteções LGPD

O `.gitignore` deve impedir versionamento de:

- `.env`;
- bancos SQLite;
- PDFs/DOCX reais;
- uploads;
- PDFs grifados;
- relatórios;
- documentos corrigidos/finais;
- respostas raw da IA;
- arquivos temporários;
- JSONs de avaliação;
- checklists preenchidos.

Podem subir:

- código;
- testes;
- prompts;
- docs;
- templates;
- CSS/JS;
- `.gitkeep`;
- modelos vazios de checklist.

## Regras Que Não Podem Ser Quebradas

1. Nunca subir documentos reais ao GitHub.
2. Nunca versionar `.env` ou API key.
3. Nunca aplicar automaticamente:
   - `DADO_A_CONFERIR`;
   - gravidade `CONFERIR`;
   - `CLAUSULA_JURIDICA_SENSIVEL`.
4. Não alterar CPF, RG, CNH, CNPJ, NIRE, endereço, datas, valores, nomes ou OAB sem confirmação.
5. Não permitir que a IA altere termos sensíveis no documento final sem aprovação.
6. Documento final não pode conter:
   - grifos;
   - comentários;
   - alertas internos;
   - relatório;
   - menção à IA;
   - OpenAI;
   - ChatGPT.
7. Versão final só pode ser gerada após confirmação humana.
8. Regras fixas são reforço; a API é o cérebro da revisão.
9. Evitar falso positivo.
10. Priorizar apontamentos úteis e revisão profissional, não quantidade.

## Como Refatorar Com Novos Documentos

Procedimento recomendado para uma nova base com aproximadamente 50 documentos:

1. Criar nova base, por exemplo `tests/documentos_referencia/base_02/`.
2. Repetir categorias da Base 01 e adicionar `outros`, se necessário.
3. Atualizar `.gitignore` antes de inserir documentos.
4. Colocar PDFs/DOCX reais apenas localmente.
5. Gerar manifesto local.
6. Rodar `--mode mock`.
7. Rodar `--mode api` em lotes pequenos por categoria.
8. Gerar resumo consolidado.
9. Preencher checklist humano.
10. Classificar problemas:
    - falso positivo;
    - falso negativo;
    - erro não localizado;
    - duplicidade;
    - prompt insuficiente;
    - regra fixa inadequada;
    - falha de localização PDF;
    - falha de corrigido/final.
11. Implementar melhorias pequenas e testáveis.
12. Rodar testes e reavaliar.
13. Só commitar código/docs/testes, nunca documentos ou outputs.

## Riscos Conhecidos

- Documentos digitalizados sem OCR ainda podem falhar na extração/localização.
- PDFs com quebras de linha ou layout tabular podem gerar trechos difíceis de localizar.
- A IA pode variar resposta entre rodadas.
- A IA pode tentar aplicar alteração sensível se o prompt não for obedecido; por isso há proteção pós-IA.
- Documentos bons podem revelar excesso de falso positivo.
- Muitas regras fixas podem aumentar ruído se não forem calibradas por contexto.
- Documento final depende de confirmação humana, mas a responsabilidade de revisão final continua operacional/jurídica humana.
- Conversão PDF via reportlab é uma geração própria a partir do texto, não uma conversão fiel de DOCX para PDF.

## Próximos Passos Recomendados - Base de Referência 02

Objetivo sugerido para maturação contínua: usar a Base de Referência 02 e refatoração incremental orientada por evidência.

Tarefas recomendadas:

1. Criar `base_02` para aproximadamente 50 documentos reais.
2. Atualizar `.gitignore` para cobrir a nova base.
3. Criar manifesto local da `base_02`.
4. Rodar mock em todos os documentos.
5. Rodar API em lotes pequenos.
6. Gerar resumo consolidado.
7. Preencher checklist humano por amostra.
8. Mapear falsos positivos/falsos negativos.
9. Melhorar prompt apenas onde houver evidência.
10. Melhorar regras fixas apenas onde forem precisas.
11. Melhorar localização PDF para casos reais não localizados.
12. Melhorar documento corrigido/final apenas se a auditoria apontar falhas reais.
13. Criar testes para cada bug encontrado.
14. Validar novamente por lote.
15. Commitar somente código, docs, prompts e testes.

Antes de iniciar V5, rodar:

```bash
git status
python -m pytest -q
python -m compileall app scripts tests
```
