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
- Anotações persistentes em banco de dados: usa `DATABASE_URL` em produção para PostgreSQL/Supabase/Neon e faz fallback para SQLite local.
- Aba **Personalizar** para adicionar temas próprios pelo próprio dashboard, sem abrir CSV. Os temas personalizados entram nos gráficos, rankings e tabelas e também persistem no banco configurado.
- Correção dos gráficos de concursos: os gráficos de “Top temas” agora ficam em painel largo, com legenda fora da área das barras e rótulos longos abreviados visualmente, mantendo o texto completo no hover.

## Deploy com banco persistente

No Render, configure:

```text
Build Command: pip install -r requirements.txt
Start Command: gunicorn app:server
```

Em **Environment Variables**, adicione:

```text
DATABASE_URL = postgresql://usuario:senha@host:5432/postgres?sslmode=require
```

Se a senha tiver `#`, use `%23` na URL. Exemplo: `Mochila23##` vira `Mochila23%23%23`.

Com `DATABASE_URL`, anotações e temas personalizados ficam no PostgreSQL externo. Sem `DATABASE_URL`, o app usa `data/anotacoes.db` localmente.

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

Temas adicionados pela aba **Personalizar** ficam salvos no banco configurado. Em produção, use `DATABASE_URL` para PostgreSQL/Supabase/Neon; localmente, o fallback é `data/anotacoes.db`.
