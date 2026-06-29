# Pack de correções — gráficos e persistência

## 1. Gráfico de “Top temas”

Correções aplicadas:

- o gráfico de top temas por concurso agora fica em painel largo;
- a legenda foi movida para fora da área das barras;
- rótulos longos são encurtados visualmente, mantendo o tema completo no hover;
- a altura do gráfico foi aumentada para evitar barras comprimidas;
- o eixo Y perdeu o título redundante para liberar espaço.

Arquivos alterados:

- `app.py`
- `assets/style.css`

## 2. Persistência real em banco externo

O app agora usa SQLAlchemy com esta regra:

- se existir `DATABASE_URL`, usa PostgreSQL externo, como Supabase ou Neon;
- se não existir `DATABASE_URL`, usa SQLite local em `data/anotacoes.db`.

Dados salvos no banco:

- anotações;
- temas personalizados adicionados pela usuária.

Esses dados são recarregados em:

- cards;
- tabelas;
- métricas;
- gráficos;
- rankings por concurso.

## 3. Render

No Render, configurar:

```text
Build Command: pip install -r requirements.txt
Start Command: gunicorn app:server
```

Environment Variable:

```text
DATABASE_URL = postgresql://usuario:senha_codificada@host:5432/postgres?sslmode=require
```

Se a senha tiver `#`, use `%23`.

Exemplo:

```text
Mochila23## -> Mochila23%23%23
```


## Ajuste adicional — textos e persistência visível

- Removido o texto `Temas adicionados por ela`; a interface agora mostra `Temas personalizados`.
- Removidas mensagens visíveis que davam a entender que tudo ficava apenas em `data/anotacoes.db`.
- A interface principal agora usa texto genérico: anotações e temas ficam salvos no banco de dados do app.
- A explicação técnica sobre PostgreSQL/SQLite ficou restrita à aba Dados.
- Adicionados tratamentos de erro nos salvamentos de anotações e temas; se a conexão com o banco externo falhar, a mensagem aparece na própria interface.
- Mantida a regra: com `DATABASE_URL` configurado no Render, tudo que for criado pela interface persiste no PostgreSQL externo; sem `DATABASE_URL`, o app usa fallback local.
