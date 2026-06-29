# Prompt para evoluir o ClaraJuris Dashboard no Codex

Você está trabalhando no ClaraJuris Dashboard, um app Python/Dash inspirado na arquitetura do Demeter Dashboard, mas com identidade própria para estudos jurídicos.

## Regras fundamentais

1. Não trocar Dash por Streamlit ou outro framework sem autorização explícita.
2. Manter a identidade visual rosa, responsiva e alternável entre tema claro e escuro em `assets/style.css`. O botão `theme-toggle`, o `dcc.Store(id="theme-store")` e a classe `app-shell theme-light/theme-dark` não devem ser removidos.
3. Preservar as abas: Resumo, Matérias, Concursos, Biblioteca, Anotações, Plano, Personalizar e Dados.
4. Preservar o SQLite em `data/anotacoes.db`, incluindo anotações e temas personalizados.
5. Manter textos visíveis neutros, elegantes e úteis. Evitar sarcasmo dentro da interface.
6. Não remover os gráficos de concurso X:
   - qual matéria cai mais em concurso X;
   - top temas por concurso X;
   - mapa de calor matéria × concurso.
7. Preservar a base calibrada para o 5º módulo informado:
   - GDI117 — Direito Civil IV;
   - GDI126 — Direito do Trabalho I;
   - GDI157 — Ética Profissional;
   - GDI176 — Direito Penal IV;
   - GDI263 — Direito Processual Civil II.
8. Preservar a biblioteca com 10 livros por matéria e os links `url_amazon`.
9. Preservar a base de 60 temas, com 12 temas por matéria.
10. Preservar a aba Personalizar e a tabela SQLite `temas_personalizados`, porque ela permite que a usuária complete o painel sem editar CSV.
11. Se adicionar livros, manter colunas compatíveis em `data/livros_direito.csv`.
12. Se mudar pesos de concurso, documentar no README.
13. Evitar grades fixas que possam quebrar em telas menores. Preferir `auto-fit`, `minmax` e textos com `overflow-wrap`/clamp.
14. Ao criar novos gráficos Plotly, receber o parâmetro `theme` e passar por `base_fig(..., theme)`, para o tema escuro atualizar imediatamente junto com a interface.

## Próximos upgrades bons

- Adicionar status por tema: não iniciado, estudando, revisado, dominado.
- Salvar progresso em SQLite.
- Permitir marcar livro como “quero ler”, “lendo”, “lido”.
- Exportar plano de estudos em PDF.
- Adicionar importação de provas/editais para calibrar estatística real por banca.
