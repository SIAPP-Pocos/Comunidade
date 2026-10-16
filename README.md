# SIAPP — Dados comunitários do acervo REATE

[![validar](https://github.com/SIAPP-Pocos/SIAPP-dados/actions/workflows/validar.yml/badge.svg)](https://github.com/SIAPP-Pocos/SIAPP-dados/actions/workflows/validar.yml)
[![licença: CC BY 4.0](https://img.shields.io/badge/licen%C3%A7a-CC%20BY%204.0-lightgrey)](LICENSE)

Base aberta e revisada de **correções e dados tratados** do acervo público de poços
da ANP (portal [REATE](https://reate.cprm.gov.br/anp/TERRESTRE), ANP/CPRM),
produzida com a ferramenta [SIAPP](https://github.com/SIAPP-Pocos/siapp).

Quem usa o SIAPP baixa esta base e recebe os documentos **já tratados**: palavras
lidas errado pelo OCR corrigidas, vocabulário técnico, e (em breve) textos extraídos
e transcrições conferidas por pessoas.

> **Estado:** formato de contribuição **v1, em rascunho**. Pode mudar até a primeira
> versão estável da base.

## O que tem aqui

```
contribuicoes/      um arquivo JSON por pacote de contribuição (fonte da verdade)
esquema/            formato oficial das contribuições (JSON Schema)
vocabulario/        dicionário de domínio da comunidade
ferramentas/
  validar.py        confere cada contribuição (roda automaticamente em todo pull request)
  compilar.py       junta tudo numa base única (SQLite + JSON)
```

## Como os dados entram

1. Quem usa o SIAPP corrige o texto dos documentos e **exporta uma contribuição**.
2. A contribuição chega aqui por *pull request* (ou é enviada a um mantenedor).
3. O GitHub **valida automaticamente**: formato, campos obrigatórios, ausência de
   correção de números, e **conflitos** com correções de outros autores.
4. Um mantenedor **revisa** e aceita.
5. A cada versão (etiqueta `vAAAA.MM.N`), a base consolidada é publicada em
   **Releases** — é o que o SIAPP baixa.

## Princípios

- **Nenhum arquivo original do REATE fica aqui.** Documentos são identificados pelo
  caminho no portal e pelo hash SHA-256 do conteúdo; quem precisa do original baixa do REATE.
- **Toda contribuição tem autor e data**, e a autoria segue até a base compilada.
- **Nada entra sem revisão.** Conflitos entre autores são resolvidos por pessoas.
- **Números não são corrigidos por regra global.** Corrigir "87"→"83" trocaria valores
  certos em outras páginas; números corrigidos virão das transcrições conferidas, página a página.

## Licença e citação

Os dados deste repositório estão sob **Creative Commons Atribuição 4.0 (CC-BY 4.0)** —
uso livre, inclusive comercial, **com citação**. Ver [`LICENSE`](LICENSE) e
[`CITATION.cff`](CITATION.cff). Ao contribuir, você licencia sua contribuição nos mesmos termos.

O acervo original pertence à ANP e é disponibilizado publicamente pelo REATE; esta
base contém apenas referências, correções e dados derivados.
