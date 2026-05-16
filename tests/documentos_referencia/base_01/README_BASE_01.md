# Base de Referência 01

Base local para maturação operacional da revisão de minutas societárias.

Coloque documentos reais apenas nas subpastas de `entrada/`, conforme o tipo do ato:

- `constituicao_ltda`
- `alteracao_endereco`
- `alteracao_socios`
- `alteracao_capital`
- `alteracao_objeto`
- `consolidacao_contratual`
- `ata_age`
- `ata_ago`
- `estatuto_social`
- `documentos_bons`

Os documentos reais, saídas, relatórios de avaliação e checklists preenchidos são ignorados pelo Git.

Comandos principais:

```powershell
python scripts/criar_manifesto_base.py --base base_01
python scripts/avaliar_revisao.py --base base_01 --mode mock
python scripts/avaliar_revisao.py --base base_01 --mode api
python scripts/avaliar_revisao.py --base base_01 --api-summary
```

A pasta `documentos_bons` serve para medir falso positivo em documentos aparentemente corretos.
