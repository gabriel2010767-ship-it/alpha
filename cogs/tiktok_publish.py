import asyncio
import json
import logging
from pathlib import Path

import discord
import yt_dlp
from discord import app_commands
from discord.ext import commands, tasks

log = logging.getLogger("Rei Dado.TikTok")

TIKTOK_PROFILE = "https://www.tiktok.com/@gulosinhosgameplays"
ANNOUNCEMENT_CHANNEL_ID = 1570288138465583164
PING_ROLE_NAME = "Ping Canal"
STATE_FILE = Path(__file__).resolve().parent.parent / "tiktok_last_video.json"


def _extract_latest_video_sync() -> dict | None:
    """Obtém os metadados do primeiro vídeo listado no perfil público."""
    options = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "extract_flat": "in_playlist",
        "playlistend": 1,
        "ignoreerrors": True,
    }
    with yt_dlp.YoutubeDL(options) as ydl:
        info = ydl.extract_info(TIKTOK_PROFILE, download=False)

    if not info:
        return None

    entries = info.get("entries")
    video = next((item for item in entries or [] if item), None) if entries is not None else info
    if not video:
        return None

    video_id = str(video.get("id") or "").strip()
    if not video_id:
        return None

    url = video.get("webpage_url") or video.get("original_url")
    if not url or not str(url).startswith("http"):
        url = f"https://www.tiktok.com/@gulosinhosgameplays/video/{video_id}"

    return {
        "id": video_id,
        "url": str(url),
        "title": str(video.get("title") or "Novo vídeo no TikTok")[:250],
    }


async def fetch_latest_video() -> dict | None:
    return await asyncio.to_thread(_extract_latest_video_sync)


def read_last_video_id() -> str | None:
    try:
        data = json.loads(STATE_FILE.read_text(encoding="utf-8"))
        value = data.get("last_video_id")
        return str(value) if value else None
    except FileNotFoundError:
        return None
    except (OSError, json.JSONDecodeError, AttributeError, TypeError):
        log.exception("Não foi possível ler o arquivo de estado do TikTok.")
        return None


def save_last_video_id(video_id: str) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    temporary = STATE_FILE.with_suffix(".tmp")
    temporary.write_text(
        json.dumps({"last_video_id": video_id}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    temporary.replace(STATE_FILE)


class TikTokPublish(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def cog_load(self):
        self.watch_new_videos.start()

    async def cog_unload(self):
        self.watch_new_videos.cancel()

    async def get_announcement_channel(self):
        channel = self.bot.get_channel(ANNOUNCEMENT_CHANNEL_ID)
        if channel is None:
            try:
                channel = await self.bot.fetch_channel(ANNOUNCEMENT_CHANNEL_ID)
            except discord.HTTPException:
                log.exception("Não foi possível acessar o canal de anúncios.")
                return None

        if not isinstance(channel, (discord.TextChannel, discord.Thread)):
            log.error("O canal configurado para anúncios não é um canal de texto.")
            return None
        return channel

    @app_commands.command(
        name="publicar_video",
        description="Testa a publicação do vídeo mais recente do TikTok, sem marcar ninguém.",
    )
    @app_commands.default_permissions(manage_guild=True)
    async def publicar_video(self, interaction: discord.Interaction):
        # Diagnóstico: mede o atraso entre a criação da interação e o callback.
        interaction_delay = (discord.utils.utcnow() - interaction.created_at).total_seconds()
        log.info(
            "Comando /publicar_video recebido | interaction_id=%s | atraso=%.3fs | bot_latency=%.3fs | response_done=%s",
            interaction.id,
            interaction_delay,
            self.bot.latency if self.bot.latency is not None else -1,
            interaction.response.is_done(),
        )

        # Outra instância do bot pode já ter reconhecido esta interação.
        if interaction.response.is_done():
            log.warning("Interação /publicar_video já reconhecida antes do callback; execução ignorada.")
            return

        try:
            await interaction.response.defer(ephemeral=True, thinking=True)
        except discord.HTTPException as error:
            if getattr(error, "code", None) in (40060, 10062):
                log.warning(
                    "Interação /publicar_video já reconhecida ou expirada (código %s). "
                    "Verifique se existe outra instância do bot usando o mesmo token.",
                    error.code,
                )
                return
            raise

        try:
            video = await fetch_latest_video()
        except Exception:
            log.exception("Falha ao consultar o perfil do TikTok no comando manual.")
            await interaction.followup.send(
                "❌ Não consegui consultar o TikTok agora. Confira os logs do bot e tente novamente mais tarde.",
                ephemeral=True,
            )
            return

        if not video:
            await interaction.followup.send(
                "⚠️ Não encontrei vídeos públicos nesse perfil.",
                ephemeral=True,
            )
            return

        channel = await self.get_announcement_channel()
        if channel is None:
            await interaction.followup.send(
                "❌ Não consegui acessar o canal configurado para os anúncios.",
                ephemeral=True,
            )
            return

        try:
            await channel.send(
                f"🎬 **Novo vídeo de @gulosinhosgameplays!**\n"
                f"**{video['title']}**\n{video['url']}",
                allowed_mentions=discord.AllowedMentions.none(),
            )
        except discord.HTTPException:
            log.exception("Falha ao publicar o vídeo pelo comando manual.")
            await interaction.followup.send(
                "❌ O Discord não aceitou a publicação. Confira as permissões do bot no canal.",
                ephemeral=True,
            )
            return

        await interaction.followup.send(
            f"✅ Vídeo publicado em {channel.mention}, sem marcar ninguém.",
            ephemeral=True,
        )

    @tasks.loop(minutes=5)
    async def watch_new_videos(self):
        try:
            video = await fetch_latest_video()
            if not video:
                log.warning("O monitor do TikTok não encontrou um vídeo nesta verificação.")
                return

            last_video_id = read_last_video_id()

            # Na primeira execução, registra o vídeo atual como referência.
            # Assim, o bot não anuncia um vídeo antigo ao iniciar.
            if last_video_id is None:
                save_last_video_id(video["id"])
                log.info("Vídeo inicial do TikTok registrado como referência: %s", video["id"])
                return

            if video["id"] == last_video_id:
                return

            channel = await self.get_announcement_channel()
            if channel is None:
                return

            # Proteção adicional contra repetição após reinício ou perda do arquivo.
            try:
                async for message in channel.history(limit=100):
                    if video["id"] in message.content or video["url"] in message.content:
                        save_last_video_id(video["id"])
                        log.info("Vídeo %s já estava no histórico do canal; anúncio duplicado evitado.", video["id"])
                        return
            except discord.HTTPException:
                log.exception("Não foi possível verificar o histórico do canal antes do anúncio.")
                return

            guild = channel.guild
            role = discord.utils.get(guild.roles, name=PING_ROLE_NAME) if guild else None
            if role is None:
                log.error("Cargo '%s' não encontrado no servidor; anúncio automático não enviado.", PING_ROLE_NAME)
                return

            await channel.send(
                f"{role.mention}\n"
                f"🎬 **Novo vídeo de @gulosinhosgameplays!**\n"
                f"**{video['title']}**\n{video['url']}",
                allowed_mentions=discord.AllowedMentions(
                    roles=[role],
                    users=False,
                    everyone=False,
                ),
            )
            save_last_video_id(video["id"])
            log.info("Novo vídeo %s anunciado automaticamente com o cargo %s.", video["id"], role.name)

        except Exception:
            log.exception("Erro durante a verificação automática do TikTok.")

    @watch_new_videos.before_loop
    async def before_watch_new_videos(self):
        await self.bot.wait_until_ready()


async def setup(bot: commands.Bot):
    await bot.add_cog(TikTokPublish(bot))
