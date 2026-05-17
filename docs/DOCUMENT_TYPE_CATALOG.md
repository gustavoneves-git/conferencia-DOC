# Catálogo Interno de Tipos Documentais

## Objetivo

A V5.0 introduz o Catálogo Interno de Tipos Documentais do Conferência Documento.

O catálogo prepara o futuro fluxo de criação de minutas e atas do zero, mas ainda não gera documentos, não chama IA e não salva formulários no banco.

O objetivo é manter a experiência simples para o usuário:

1. Conferir / corrigir minuta existente.
2. Criar nova minuta ou ata.

A complexidade de tipos, campos obrigatórios, documentos de apoio, riscos e validações fica organizada internamente.

## Onde Fica

```text
app/document_types/
├── __init__.py
├── catalog.py
├── schemas.py
├── ltda.py
├── sa.py
├── empresario_individual.py
├── accessory.py
└── README.md
```

## Estrutura de Cada Tipo

Cada tipo documental possui:

- `code`
- `label`
- `user_label`
- `group`
- `user_group`
- `description`
- `purpose`
- `required_fields`
- `optional_fields`
- `supporting_documents`
- `output_documents`
- `validation_rules`
- `risk_points`
- `implemented`
- `generation_ready`
- `review_ready`
- `notes`

## Tipos Mapeados na V5.0

LTDA:

- `CONSTITUICAO_LTDA`
- `ALTERACAO_ENDERECO_LTDA`
- `ALTERACAO_OBJETO_LTDA`
- `ALTERACAO_CAPITAL_LTDA`
- `ALTERACAO_SOCIOS_LTDA`
- `ALTERACAO_ADMINISTRACAO_LTDA`
- `ALTERACAO_NOME_EMPRESARIAL_LTDA`
- `CONSOLIDACAO_CONTRATO_SOCIAL_LTDA`
- `DISTRATO_SOCIAL_LTDA`
- `TRANSFORMACAO_TIPO_JURIDICO`

S/A:

- `ATA_AGE`
- `ATA_AGO`
- `ATA_AGOE`
- `ESTATUTO_SOCIAL`
- `ESTATUTO_SOCIAL_CONSOLIDADO`
- `ALTERACAO_ENDERECO_SA`
- `ALTERACAO_DIRETORIA_SA`
- `ALTERACAO_ESTATUTO_SA`
- `AUMENTO_CAPITAL_SA`
- `REDUCAO_CAPITAL_SA`
- `TRANSFERENCIA_ACOES`
- `ELEICAO_DIRETORIA`
- `RENUNCIA_DIRETORIA`

Empresário Individual / SLU:

- `CONSTITUICAO_EMPRESARIO_INDIVIDUAL`
- `ALTERACAO_EMPRESARIO_INDIVIDUAL`
- `EXTINCAO_EMPRESARIO_INDIVIDUAL`
- `CONSTITUICAO_SLU`
- `ALTERACAO_SLU`
- `EXTINCAO_SLU`

Acessórios:

- `DECLARACAO_DESIMPEDIMENTO`
- `DECLARACAO_ENQUADRAMENTO_ME_EPP`
- `REENQUADRAMENTO_ME_EPP`
- `DESENQUADRAMENTO_ME_EPP`
- `PROCURACAO`
- `TERMO_DE_POSSE`
- `CARTA_RENUNCIA`
- `RECIBO_TRANSFERENCIA_QUOTAS`
- `LISTA_PRESENCA`
- `BOLETIM_SUBSCRICAO`

## Funções Públicas

Disponíveis em `app/document_types/catalog.py`:

- `get_all_document_types()`
- `get_document_type(code)`
- `get_document_types_by_group(group)`
- `get_document_types_by_user_group(user_group)`
- `get_generation_ready_types()`
- `get_review_ready_types()`
- `search_document_types(query)`
- `get_user_groups()`
- `get_types_for_creation_menu()`

Essas funções não dependem de banco de dados.

## Interface da V5.0

A tela de criação mostra grupos amigáveis, como:

- Contrato Social / LTDA
- Alteração Contratual
- Ata / Assembleia
- Estatuto Social
- Empresário Individual / SLU
- Documento acessório

Ao selecionar um tipo, o usuário vê:

- nome amigável;
- descrição;
- finalidade;
- campos obrigatórios;
- campos opcionais;
- documentos de apoio;
- pontos de atenção;
- status de geração;
- formulário visual preparatório.

Nenhuma minuta é gerada nesta versão.

## Decisão Sobre OCR e Dados Sensíveis

Para criação de minutas do zero, dados sensíveis não devem depender de OCR.

Motivos:

- documentos de identidade podem estar pixelizados;
- comprovantes podem ter baixa qualidade;
- OCR pode errar nomes, CPF, RG, CNH, endereços e números;
- a IA não deve inventar dados ausentes;
- a responsabilidade operacional exige confirmação humana.

Decisão:

- dados essenciais devem ser preenchidos manualmente;
- OCR poderá ser apoio futuro;
- OCR nunca será fonte automática definitiva para dados sensíveis;
- campos obrigatórios devem ser preenchidos pelo usuário;
- a IA só poderá gerar minuta a partir de dados estruturados e confirmados.

## Próxima Etapa Recomendada

V5.1 deve começar pelo tipo:

```text
CONSTITUICAO_LTDA
```

Escopo sugerido:

1. Criar schema estruturado de entrada.
2. Validar campos obrigatórios.
3. Montar prompt de geração específico.
4. Gerar minuta preliminar.
5. Rodar a própria revisão do sistema sobre a minuta gerada.
6. Produzir DOCX/PDF para revisão humana.

