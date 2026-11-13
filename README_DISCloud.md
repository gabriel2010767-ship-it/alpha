# Rei Dado — Discloud

## Pacote
Este projeto foi preparado para iniciar pela Discloud usando `discloud.config`.

## Antes de enviar
1. Baixe o ZIP do repositório pela opção **Code → Download ZIP** no GitHub.
2. Extraia o ZIP no computador.
3. Renomeie `.env.example` para `.env`.
4. Abra o `.env` e preencha `DISCORD_TOKEN` com o token privado do bot.
5. Mantenha os IDs dos dois servidores:
   - `GUILD_ID=1536903015678873710`
   - `GUILD_IDS=1558617789231661096`
6. Compacte novamente os arquivos do projeto, deixando `discloud.config`, `main.py`, `requirements.txt`, `config.py`, `database.py` e a pasta `cogs` diretamente na raiz do ZIP.
7. Envie o ZIP na Discloud.

## Importante
- Nunca compartilhe o arquivo `.env` nem publique o token do bot.
- O módulo de apostas e os módulos de jogos que continham apostas foram retirados. Os sistemas de economia, comunidade, tickets, moderação, cargos e TikTok permanecem.
- O banco SQLite é criado automaticamente em `data/alpha.db`. Confira as regras de armazenamento da sua hospedagem para garantir persistência.
- Se os comandos não aparecerem imediatamente, aguarde a sincronização e confira os logs.
