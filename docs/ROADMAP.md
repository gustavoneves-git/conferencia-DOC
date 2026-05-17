# Roadmap

- OCR para PDFs digitalizados.
- Tela de aceite/rejeição por apontamento.
- Geração completa do Modo B.
- Modelos documentais por tipo de ato.
- Comparação entre minuta original e corrigida.
- Autenticação interna e perfis.
- Auditoria detalhada de ações humanas.
- Exportação com padrões visuais da Consiste.

## V2

- Avaliação operacional local com PDFs reais ignorados pelo Git.
- Prompt mais rigoroso e contextual para revisão de minutas existentes.
- JSON guard mais tolerante a respostas imperfeitas da IA.
- Consolidação de apontamentos por similaridade.
- Localização visual melhorada no PDF.
- Relatórios mais profissionais.
- DOCX corrigido com formatação mais adequada para revisão.

## V2.5

- Base de Referência 01 organizada por categoria documental.
- Manifesto local de documentos reais sem envio ao Git.
- Avaliação por base com `--base base_01`.
- Resumo consolidado com origem, gravidade, tipo, localização e recorrência.
- Checklist humano por documento para medir falso positivo/falso negativo.
- Classificação de risco operacional por documento.

## TODO OCR

Preparar futura etapa de OCR para PDFs escaneados ou com texto ruim. A V2 apenas documenta essa necessidade; não implementa OCR.

## TODO V3.1

- Gerar relatório PDF consolidado da Base de Referência a partir do `--api-summary`.

## V5.0

- Catálogo interno de tipos documentais.
- Tela simples com dois caminhos: revisar minuta existente ou criar nova minuta/ata.
- Seleção de categoria amigável e tipo documental.
- Tela de detalhes do tipo com finalidade, campos, documentos de apoio e pontos de atenção.
- Formulário preparatório visual, sem geração real.
- Documentação do princípio de preenchimento manual de dados sensíveis.

## Decisão OCR Para Criação

Para criação de minutas do zero, OCR não será fonte primária de dados sensíveis.

Dados como nomes, CPF, RG, CNH, endereços, datas, valores, razão social e OAB devem ser preenchidos ou confirmados manualmente. OCR pode ser apoio futuro, mas nunca fonte automática definitiva.

## V5.1

- Iniciar geração real pelo tipo `CONSTITUICAO_LTDA_PADRAO`.
- Criar schema estruturado de entrada.
- Validar campos obrigatórios.
- Detectar caso avançado e bloquear geração padrão.
- Gerar minuta preliminar com IA ou mock.
- Entregar DOCX/PDF para revisão humana.
- Salvar payload local em `storage/generated`.

## TODO V5.2

- Rodar revisão automática sobre a minuta gerada.
- Integrar minuta gerada ao fluxo completo de revisão/correção/final.
- Permitir revisão humana dos dados antes da chamada de IA.
- Evoluir formulário para múltiplos sócios dinâmicos.
