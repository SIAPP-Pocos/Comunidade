# Histórico do formato e da base

Formato baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/).
O **formato de contribuição** tem versão própria (`versao_formato`); a **base
compilada** é publicada com etiquetas `vAAAA.MM.N`.

## [Não lançado]
### Adicionado
- **Receber pacote enviado pelo SIAPP (1.4)**: workflow `receber pacote` e `ferramentas/receber_pacote.py`. O
  SIAPP manda o pacote como issue (cabeçalho e partes em comentários); o robô junta, confere o SHA-256, valida e
  abre o pull request no nome de quem enviou, ou comenta o motivo e fecha a issue.
- **Publicação automática:** logo depois de cada aceite que mexa em `contribuicoes/` ou
  `vocabulario/`, o GitHub valida, compila e publica a base como versão nova (`vAAAA.MM.N`,
  numerada por `ferramentas/proxima_versao.py`), com notas do que entrou desde a anterior
  (`ferramentas/notas.py`). "Run workflow" publica na hora. Sem contribuição aceita, nada sai.
- `resumo.json` junto da base: contagens e a lista de pacotes, com autor e poços de cada um,
  para o SIAPP saber o que mudou sem baixar a base inteira.
### Mudado
- O repositório passou a se chamar **Comunidade** (antes `SIAPP-dados`); endereços do README,
  da citação e dos esquemas atualizados.
- `contribuicoes/exemplo.json` não entra mais na base publicada: só mostra o formato.
- Interpretações (v3) aceitam os parâmetros da referência do GR do SIAPP 0.36 (`gr_referencia`,
  `gr_estatistica`, `gr_ref_topo`, `gr_ref_base`).
- Formato de contribuição **v3** (SIAPP 0.35): `interpretacoes` — interpretações de perfil
  da biblioteca do SIAPP (avaliação de formação com arquivo, curvas, métodos, parâmetros e
  resumo por intervalo, sem curvas calculadas) — e o tipo de fato `trecho` (citação de texto
  livre, até 4000 caracteres), que o SIAPP 0.31 já exportava. A v1 e a v2 continuam aceitas.
- Validador: interpretação com intervalo de base acima do topo é recusada; a mesma
  interpretação enviada por autores diferentes é conflito.
- Base compilada: tabela `interpretacoes` (o item do pacote em JSON, com autor e pacote de
  origem). O SIAPP 0.35+ aplica; versões anteriores ignoram a tabela (`versao_formato_base` segue 1).
- Pacote v3 exportado pelo SIAPP 0.35 (perfil sintético) como teste de contrato.
- Tipo de fato `propriedade_fluido` (grau API do óleo, densidade relativa do gás, RGO…),
  aceito no formato v2 — usado pelo SIAPP 0.29 na viabilidade de injeção.
- Formato de contribuição **v2**: dados transcritos (`fatos`) com fonte — SHA-256 e
  caminho do documento no REATE, página e caixa na imagem — e `apelidos` de poço.
  A v1 continua aceita.
- Validador: fato com base acima do topo é recusado; o mesmo fato enviado por autores
  diferentes é conflito; reenvio pelo mesmo autor é atualização.
- Base compilada no formato que o SIAPP 0.7+ aplica (`meta`, `contribuicoes`, `vocab`,
  `fatos`, `apelidos`), com a versão da etiqueta.
- Pacote exportado de verdade pelo SIAPP 0.10 como teste de contrato entre os repositórios.
- Formato de contribuição v1 (rascunho): vocabulário, correções, exceções e
  referência a textos de documentos por hash SHA-256.
- Validador com detecção de conflito entre autores; compilador SQLite + JSON.
- Publicação automática da base em Releases ao criar etiqueta.
- Modelos de issue e pull request, CODEOWNERS, Dependabot e código de conduta.
