# Quality Baseline

Este arquivo orienta a calibração dos documentos de referência da V2.1. Ele não deve reproduzir documentos completos nem dados sensíveis além dos trechos mínimos necessários para testar a revisão.

## GOGA

- Razão social esperada: `GOGA EMPREENDIMENTOS E PARTICIPAÇÕES LTDA`.
- Detectar erros de gênero na qualificação masculina quando aparecem `portadora`, `inscrita` e `domiciliada`.
- Detectar `DA INICIO`/`DO INICIO`, vírgulas indevidas em cláusulas de administração e redações frágeis recorrentes.
- Tratar `pesa a cláusula restritiva` como cláusula sensível a conferir, não como simples ortografia.
- Tratar `foro da sede` como dado/redação a conferir, sugerindo validação da comarca.

## LUFISA

- Razão social esperada: `LUFISA EMPREENDIMENTOS E PARTICIPAÇÕES LTDA`.
- Regras equivalentes aos contratos LTDA de constituição, com atenção a qualificação, administração, exercício social, distribuição de lucros e fechamento.
- Não marcar título principal em caixa alta como erro de formatação.

## QUOREN

- Razão social esperada: `QUOREN EMPREENDIMENTOS E PARTICIPAÇÕES LTDA`.
- Detectar erros de gênero quando cláusulas se referem a sócia administradora em contexto incompatível.
- Detectar redações sensíveis de quotas/restrições e pontos de conferência sem transformar tudo em erro definitivo.

## JBX

- Razão social esperada: `JBX CONSTRUÇÃO E EMPREENDIMENTOS COMERCIAIS S/A.`.
- O documento AGE/estatuto não deve retornar zero apontamentos.
- Detectar `Saida`, `livra e espontânea vontade`, `Cargo de Diretor e Acionista a Sr.ª`, `Ao Diretor Presidente compete os poderes`, `cláusula adjudicia e a extra`, `contas-corrente`, repetição de `ordenar títulos de créditos para protesto` e `é consolidado o estatuto social anexo a presente ata`.
- Em alteração de endereço, não marcar como erro a coexistência de endereço anterior e novo quando isso for esperado pelo ato.
## Base de Referência 01

A Base 01 amplia a maturação para documentos reais variados. Ela deve ser usada para medir:

- falsos positivos em `documentos_bons`;
- falsos negativos apontados por checklist humano;
- tipos de erro recorrentes;
- trechos não localizados no PDF;
- comportamento por categoria documental;
- distribuição de risco operacional.

Os relatórios locais da Base 01 ficam em `tests/documentos_referencia/base_01/relatorios_avaliacao` e são ignorados pelo Git.
