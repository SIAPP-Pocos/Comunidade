# Como contribuir com dados

## Pelo SIAPP (recomendado)

1. Trabalhe no SIAPP: corrija o OCR e transcreva dados na aba **2. Documentos**; compartilhe avaliações de
   formação na aba **3. Perfis** (Compartilhar na biblioteca).
2. Na aba **Comunidade** › Contribuir, clique em **Enviar para a comunidade** (SIAPP 1.4 ou mais novo). Na primeira
   vez, entre com a sua conta do GitHub (gratuita) pelo código que o SIAPP mostra. Confirme o que vai e pronto: um
   robô deste repositório confere o pacote e abre o pull request no seu nome; em **Seus envios** você acompanha.

### Pelo site do GitHub (SIAPP mais antigo, ou se preferir)

1. Na aba **Comunidade** › Contribuir, clique em **Exportar pacote**. O SIAPP grava um arquivo `.json` com o seu
   trabalho (não com os documentos do REATE) e **Abrir a pasta** mostra onde ele ficou.
2. Mande o arquivo para cá pelo site do GitHub (precisa de uma conta, gratuita):
   1. Abra <https://github.com/SIAPP-Pocos/Comunidade/tree/main/contribuicoes>.
   2. **Add file › Upload files** e arraste o `.json`.
   3. Em "Propose changes", escreva uma linha sobre o que vai no pacote e clique em **Propose changes** e depois em
      **Create pull request**. O GitHub faz a cópia do repositório na sua conta sozinho.
   4. A validação roda em minutos (o resultado aparece no pull request). Depois da revisão e do aceite, a base nova
      sai sozinha e o SIAPP de todo mundo avisa.

   Sem conta no GitHub, mande o arquivo para um mantenedor, que faz o envio com o seu nome no pacote.

O que **não** vem para cá: os arquivos do REATE (PDF, DLIS, LAS…). Eles já são públicos na ANP; o pacote leva só a
referência (SHA-256 e caminho no REATE), a página e a caixa de onde cada dado saiu.

### Como o envio pelo SIAPP chega aqui

O SIAPP abre uma issue com um resumo e a marca `<!-- siapp-pacote id=… partes=n sha256=… -->`, e põe o pacote
(JSON compactado com gzip, em base64) em comentários `<!-- siapp-parte i/n -->`. O workflow **receber pacote**
(`ferramentas/receber_pacote.py`) junta as partes (só as do autor da issue), confere o SHA-256, valida e abre o pull
request no nome de quem enviou; se não serve, comenta o motivo e fecha a issue. Nada do que vem na issue é executado.
O aplicativo do GitHub "SIAPP Comunidade" só tem permissão de abrir issues e ler pull requests, e só neste repositório.

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
Assim que o pull request é aceito, o GitHub publica sozinho uma versão nova da base, e o
SIAPP de quem usa avisa que há novidade.

Ao participar, você concorda com o [Código de conduta](CODE_OF_CONDUCT.md).
