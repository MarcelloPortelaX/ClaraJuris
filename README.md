# ClaraJuris Dashboard

Dashboard em Python/Dash para estudos do **5º módulo de Direito da UFLA**, calibrado com as disciplinas informadas por Marcello e redesenhado com uma interface rosa, responsiva e alternável entre tema claro e escuro.

## Disciplinas calibradas

- **GDI117 — Direito Civil IV** — foco operacional: contratos.
- **GDI126 — Direito do Trabalho I** — fundamentos, princípios, relação de emprego e contrato individual.
- **GDI157 — Ética Profissional** — ética jurídica, Estatuto da Advocacia, Código de Ética da OAB e profissões jurídicas.
- **GDI176 — Direito Penal IV** — crimes contra dignidade sexual, incolumidade pública e demais blocos finais da Parte Especial.
- **GDI263 — Direito Processual Civil II** — procedimento comum, tutela, prova, decisão, coisa julgada e execução inicial.

## O que a versão atual entrega

- Interface mais limpa e intuitiva, com sidebar compacta, cards responsivos e textos mais neutros.
- Botão **Tema escuro / Tema claro** na sidebar, alternando imediatamente a paleta, os gráficos Plotly, tabelas e controles.
- Correções de overflow em cards, tabelas, títulos longos e botões da biblioteca.
- Base `data/temas_concursos.csv` expandida para **60 temas**, com **12 temas por matéria**, calibrados por incidência, dificuldade, OAB e concursos públicos.
- Base `data/livros_direito.csv` com **50 livros reais**, sendo **10 por matéria**.
- Cards da biblioteca com botão **Ver na Amazon**.
- Links de busca direcionada na Amazon Brasil por título + autor, reduzindo quebra por mudança de edição, estoque ou URL.
- Gráficos de concurso X:
  - qual matéria cai mais em concurso X;
  - top temas por concurso X;
  - mapa de calor matéria × concurso.
- Anotações persistentes em SQLite local.
- Aba **Personalizar** para adicionar temas próprios pelo próprio dashboard, sem abrir CSV. Os temas personalizados entram nos gráficos, rankings e tabelas.

## Como rodar

```bash
python -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
python app.py
```

Abra: `http://127.0.0.1:8050`

## Dados editáveis

- `data/disciplinas_5_periodo.csv`
- `data/temas_concursos.csv`
- `data/livros_direito.csv`

Os pesos são heurísticos iniciais. Para virar estatística rígida, o próximo passo é alimentar uma base com editais/provas reais por banca e ano.

Temas adicionados pela aba **Personalizar** ficam salvos no banco local `data/anotacoes.db`, na tabela `temas_personalizados`.
