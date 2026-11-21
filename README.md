# SIAPP — Dados comunitários do acervo REATE

[![validar](https://github.com/SIAPP-Pocos/Comunidade/actions/workflows/validar.yml/badge.svg)](https://github.com/SIAPP-Pocos/Comunidade/actions/workflows/validar.yml)
[![licença: CC BY 4.0](https://img.shields.io/badge/licen%C3%A7a-CC%20BY%204.0-lightgrey)](LICENSE)

Base aberta e revisada de **correções e dados tratados** do acervo público de poços
da ANP (portal [REATE](https://reate.cprm.gov.br/anp/TERRESTRE), ANP/CPRM),
produzida com a ferramenta [SIAPP](https://github.com/SIAPP-Pocos/SIAPP).

Quem usa o SIAPP baixa esta base e recebe os documentos **já tratados**: palavras
lidas errado pelo OCR corrigidas, vocabulário técnico e **dados transcritos e
conferidos por pessoas** (topos de formação, revestimentos, testes de formação,
intervalos-alvo…), cada um com a página e o trecho do documento de onde saiu, e
**interpretações de perfil** (avaliações de formação com os parâmetros de quem fez).

> **Estado:** formato de contribuição **v3** (SIAPP 0.35 ou mais novo; a v1 e a v2
> continuam aceitas). Pode mudar até a primeira versão estável da base.

## O que tem aqui

```
contribuicoes/      um arquivo JSON por pacote de contribuição (fonte da verdade)
esquema/            formato oficial das contribuições (JSON Schema, v1, v2 e v3)
vocabulario/        dicionário de domínio da comunidade
ferramentas/
  validar.py        confere cada contribuição (roda automaticamente em todo pull request)
  compilar.py       junta tudo numa base única (SQLite + JSON)
tests/dados/        pacotes exportados de verdade pelo SIAPP: o contrato entre os repositórios
```

## O que vai num pacote

| Parte | O que é | Exemplo |
|---|---|---|
| `vocabulario.correcoes` | forma lida pelo OCR → forma escrita no papel | `BARIGIRAS` → `BARREIRAS` |
| `vocabulario.palavras` | termos técnicos que viram atalho de busca | `Açu` |
| `vocabulario.manter_original` | palavras que a correção automática não deve mexer | `AMOSTRAS` |
| `fatos` | dado transcrito, com poço, tipo, profundidade e **fonte** (SHA-256 e caminho do documento no REATE, página e caixa na imagem) | teste de formação 590,0–610,5 m, pág. 28 |
| `apelidos` | outras grafias do nome de um poço | `7GMR0013RN` → `7-GMR-13-RN` |
| `interpretacoes` (v3) | avaliação de formação: poço, arquivo de perfil (SHA-256), curvas, métodos (Vsh, φ, Sw), parâmetros e o resumo de cada intervalo — **sem as curvas calculadas**; quem tem o mesmo arquivo refaz o cálculo | Açu 1005–1035 m, Archie com Rw 0,05: net pay 10 m |

## Como os dados entram

1. Quem usa o SIAPP corrige o texto dos documentos e **exporta uma contribuição**.
2. A contribuição chega aqui por *pull request* (ou é enviada a um mantenedor).
3. O GitHub **valida automaticamente**: formato, campos obrigatórios, ausência de
   correção de números, e **conflitos** com correções de outros autores.
4. Um mantenedor **revisa** e aceita.
5. **Logo depois de cada aceite**, o GitHub compila tudo e publica uma versão nova da base em
   **Releases** (etiqueta `vAAAA.MM.N`, ex.: `v2026.11.0`) — é o que o SIAPP baixa. Junto vai
   `resumo.json`, um arquivo pequeno com o que tem na base, para o SIAPP saber se vale baixar.

`contribuicoes/exemplo.json` mostra o formato e não entra na base.

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
