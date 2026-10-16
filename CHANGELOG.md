# Histórico do formato e da base

Formato baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/).
O **formato de contribuição** tem versão própria (`versao_formato`); a **base
compilada** é publicada com etiquetas `vAAAA.MM.N`.

## [Não lançado]
### Adicionado
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
