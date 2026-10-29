# Como contribuir com dados

## Pelo SIAPP (recomendado)

1. Processe e corrija documentos na aba **Documentos** do SIAPP.
2. Use **Exportar contribuição** — o SIAPP gera o arquivo no formato deste repositório.
3. Envie o arquivo para `contribuicoes/` por *pull request*, ou mande para um mantenedor.

## Regras de um bom pacote

- Nome do arquivo: `AAAA-MM-DD_sobrenome_assunto.json` (ex.: `2026-10-15_nobre_gmr13.json`).
- Corrija **a forma lida pelo OCR** (`de`) para a **forma escrita no documento** (`para`),
  mesmo que o documento tenha erro de digitação original — o objetivo é fidelidade ao papel.
- Não corrija números isolados (o validador recusa). Números entram como **fatos**,
  transcritos página a página e conferidos na imagem.
- Todo fato precisa da fonte: o SIAPP grava o documento (SHA-256 e caminho no REATE),
  a página e a caixa desenhada sobre a imagem.
- Interpretação de perfil (v3) vai com o arquivo (SHA-256), as curvas, os métodos e todos os
  parâmetros — o revisor confere que o resumo é coerente e, se quiser, refaz no SIAPP.
- Em caso de **conflito** com outra contribuição, o validador mostra os dois autores:
  confira a imagem da página e combine na revisão do pull request.

## Antes de enviar

```bash
pip install "jsonschema[format]"
python ferramentas/validar.py
```

## Revisão

Todo pull request precisa da aprovação de um mantenedor (`CODEOWNERS`). Na revisão,
o mantenedor confere uma amostra das correções e **todos os fatos novos** contra a
imagem da página no REATE (documento, página e caixa estão no próprio pacote).

Ao participar, você concorda com o [Código de conduta](CODE_OF_CONDUCT.md).
