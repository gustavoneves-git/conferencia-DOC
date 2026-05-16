# Base de Referência 01

A Base de Referência 01 é uma área local para testar a revisão com documentos societários reais variados, sem enviar documentos sensíveis ao GitHub.

## Estrutura

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
└── checklist_humano/
```

Use `documentos_bons` para documentos aparentemente corretos. Eles ajudam a medir falso positivo.

## Comandos

Gerar manifesto local:

```powershell
python scripts/criar_manifesto_base.py --base base_01
```

Rodar em mock:

```powershell
python scripts/avaliar_revisao.py --base base_01 --mode mock
```

Rodar em API, apenas quando autorizado:

```powershell
python scripts/avaliar_revisao.py --base base_01 --mode api
```

Gerar resumo consolidado:

```powershell
python scripts/avaliar_revisao.py --base base_01 --api-summary
```

## Checklist Humano

O modelo fica em:

```text
tests/documentos_referencia/base_01/checklist_humano/MODELO_CHECKLIST_REVISAO.csv
```

Após cada avaliação, o sistema gera `checklist_<id_documento>.csv` com os apontamentos para revisão humana. Marque cada item como `ACEITO`, `FALSO_POSITIVO`, `FALSO_NEGATIVO`, `MELHORIA_DE_ESTILO`, `DADO_A_CONFERIR`, `ERRO_GRAVE`, `IGNORAR`, `REGRA_PRECISA_MELHORAR`, `IA_PRECISA_MELHORAR` ou `LOCALIZACAO_INCORRETA`.

## Risco Operacional

Cada JSON de avaliação inclui `risk_score` e `risk_level`.

Esse risco é apenas operacional, para priorizar a revisão. Não é parecer jurídico e não substitui validação humana.

## Segurança

Documentos reais, relatórios, JSONs locais, manifesto e checklists preenchidos são ignorados pelo Git. Não coloque documentos reais fora das pastas protegidas.
