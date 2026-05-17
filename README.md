# Conferência Documento

Plataforma interna da Consiste Contabilidade para conferência operacional de minutas societárias brasileiras com apoio de IA.

## Instalação

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python run.py
```

Acesse `http://127.0.0.1:5060`.

## IA

No `.env`, use `AI_MODE=mock` para desenvolvimento local sem chave. Nesse modo, as regras fixas alimentam um retorno estruturado compatível com a camada de IA.

Para usar API:

```env
AI_MODE=api
OPENAI_API_KEY=sua-chave
OPENAI_MODEL=gpt-4.1-mini
DEFAULT_OPENAI_MODEL=gpt-4.1-mini
OPENAI_TIMEOUT=45
SAVE_AI_RAW=false
```

A chave fica somente no `.env`, que é ignorado pelo Git. Todas as chamadas passam por `app/ai/client.py`.

Teste a conectividade sem enviar documento real:

```powershell
python scripts/testar_ia.py
```

## Fluxo V1

1. Upload de PDF ou DOCX.
2. Extração de texto por página.
3. Classificação documental estimada.
4. Regras fixas iniciais.
5. Revisão por IA mock/API com JSON validado.
6. Consolidação dos apontamentos.
7. PDF grifado quando o original for PDF.
8. Relatório técnico em PDF.
9. DOCX/PDF corrigido para revisão.
10. DOCX/PDF final somente após confirmação humana.

## Catálogo de tipos documentais

A V5.0 adiciona o Catálogo Interno de Tipos Documentais para preparar a futura criação de minutas e atas do zero.

Na interface, o usuário vê dois caminhos simples:

- Conferir / corrigir minuta existente.
- Criar nova minuta ou ata.

O segundo caminho ainda é preparatório: permite escolher categoria e tipo documental, visualizar campos obrigatórios, documentos de apoio e pontos de atenção. Ele não gera minuta, não chama IA e não salva dados no banco nesta etapa.

Documentação completa:

```text
docs/DOCUMENT_TYPE_CATALOG.md
```

Decisão importante: para criação de minutas, dados sensíveis devem ser preenchidos manualmente. OCR pode ser apoio futuro, mas não será fonte automática definitiva para nomes, CPF, RG, CNH, endereços, valores ou qualificações.

## Geração inicial de Constituição LTDA

A V5.1 implementa o primeiro gerador real, limitado ao modelo `CONSTITUICAO_LTDA_PADRAO`.

Escopo permitido:

- sócios pessoas físicas;
- residentes no Brasil;
- capital em moeda corrente nacional;
- quotas simples;
- administrador sócio;
- administração isolada;
- integralização em moeda corrente nacional;
- sede única;
- sem cláusulas sensíveis automáticas.

Casos avançados são bloqueados antes da geração padrão, incluindo sócio pessoa jurídica, sócio estrangeiro, menor/incapaz, administrador não sócio, administração conjunta, capital em bens, filial na constituição e cláusulas sensíveis.

A saída é uma minuta para revisão humana em `storage/generated`, com DOCX, PDF e payload JSON local. Esses arquivos são ignorados pelo Git.

## Avaliação local da revisão

Na V2, documentos reais de teste ficam apenas localmente em:

```text
tests/documentos_referencia/entrada
```

Esses arquivos são ignorados pelo Git. Para avaliar a revisão em lote:

```powershell
python scripts/avaliar_revisao.py --mode mock
```

O script processa todos os PDFs da pasta `entrada` e gera:

- PDFs grifados e relatórios em `tests/documentos_referencia/saida`;
- JSONs de avaliação em `tests/documentos_referencia/relatorios_avaliacao`;
- totais por tipo, gravidade, origem e localização visual no PDF.

Use os JSONs para identificar excesso de falsos positivos, trechos não localizados e tipos de erro recorrentes.

Para comparar regras/mock com API:

```powershell
python scripts/avaliar_revisao.py --compare
```

Use `--compare` somente depois de configurar a chave, pois esse modo envia o texto extraído dos PDFs locais para a API.

## Base de Referência 01

A V2.5 adiciona uma base local maior para maturação da revisão:

```text
tests/documentos_referencia/base_01/entrada/<categoria>
```

Categorias disponíveis: `constituicao_ltda`, `alteracao_endereco`, `alteracao_socios`, `alteracao_capital`, `alteracao_objeto`, `consolidacao_contratual`, `ata_age`, `ata_ago`, `estatuto_social` e `documentos_bons`.

Comandos:

```powershell
python scripts/criar_manifesto_base.py --base base_01
python scripts/avaliar_revisao.py --base base_01 --mode mock
python scripts/avaliar_revisao.py --base base_01 --mode api
python scripts/avaliar_revisao.py --base base_01 --api-summary
```

A avaliação gera JSON com `risk_score` e `risk_level`, checklist humano por documento e resumo consolidado da base. Documentos reais, saídas, manifestos, JSONs e checklists preenchidos ficam ignorados pelo Git.

## Observação

O sistema não substitui advogado e não toma decisão jurídica definitiva. Ele é assistente operacional avançado para conferência, produção e padronização documental.
