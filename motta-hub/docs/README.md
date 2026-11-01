# Documentação do projeto Motta-hub

Este diretório explica o aplicativo. O acervo apresentado na tela **Documentações** tem fonte, cópia servida e índice gerado separados.

## Atalhos

- [Índice da biblioteca](INDICE-BIBLIOTECA.md): navegação por área e lista dos documentos Markdown.
- [Solicitações de colunas e central de notificações](FLUXO-SOLICITACOES-COLUNAS.md): regras do fluxo implementado.
- [Tracking](banco/tracking/README.md): localização dos materiais de tracking.

## Organização

- `documentation-source/`: fonte editável do acervo, organizada por assunto.
- `documentation-files/`: cópia dos arquivos servidos pelo hub, gerada da fonte.
- `documentations.json`: índice pesquisável servido pela API, gerado pelo importador.
- `docs/`: documentação técnica do aplicativo Motta-hub.

Depois de editar `documentation-source/`, execute `python import_documentations.py` na raiz do projeto. O importador analisa os arquivos e possíveis credenciais, e atualiza `documentation-files/` e `documentations.json`. Ele para quando encontra sinais de segredo; use placeholders nos exemplos.

A pasta original `Área de Trabalho/motta-hub/documentação` foi preservada.
