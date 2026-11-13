import random
import discord
from discord import app_commands
from discord.ext import commands


class JogosGratis(commands.Cog):
    """Jogos simples e gratuitos, sem apostas ou movimentação de moedas."""

    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="jogos", description="Mostra os jogos gratuitos do Rei Dado")
    async def jogos(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            "**🎮 Jogos gratuitos do Rei Dado**\n"
            "🪙 `/moeda` — cara ou coroa\n"
            "🎲 `/dado` — lança um dado\n"
            "✊ `/ppt` — pedra, papel ou tesoura\n\n"
            "Todos são apenas para diversão: não usam moedas e não têm apostas.",
            ephemeral=True,
        )

    @app_commands.command(name="moeda", description="Jogue cara ou coroa, sem apostas")
    async def moeda(self, interaction: discord.Interaction):
        resultado = random.choice(["Cara", "Coroa"])
        await interaction.response.send_message(f"🪙 A moeda caiu em **{resultado}**!")

    @app_commands.command(name="dado", description="Lance um dado de seis lados")
    async def dado(self, interaction: discord.Interaction):
        resultado = random.randint(1, 6)
        await interaction.response.send_message(f"🎲 Você tirou **{resultado}**!")

    @app_commands.command(name="ppt", description="Jogue pedra, papel ou tesoura")
    @app_commands.describe(escolha="Escolha sua jogada")
    @app_commands.choices(escolha=[
        app_commands.Choice(name="Pedra", value="pedra"),
        app_commands.Choice(name="Papel", value="papel"),
        app_commands.Choice(name="Tesoura", value="tesoura"),
    ])
    async def ppt(self, interaction: discord.Interaction, escolha: app_commands.Choice[str]):
        opcoes = ["pedra", "papel", "tesoura"]
        bot_escolha = random.choice(opcoes)
        nomes = {"pedra": "🪨 Pedra", "papel": "📄 Papel", "tesoura": "✂️ Tesoura"}
        if escolha.value == bot_escolha:
            resultado = "Empate!"
        elif (escolha.value, bot_escolha) in {
            ("pedra", "tesoura"), ("papel", "pedra"), ("tesoura", "papel")
        }:
            resultado = "Você venceu esta rodada!"
        else:
            resultado = "O Rei Dado venceu esta rodada!"
        await interaction.response.send_message(
            f"**Sua escolha:** {nomes[escolha.value]}\n"
            f"**Rei Dado:** {nomes[bot_escolha]}\n\n"
            f"🏁 **{resultado}**"
        )


async def setup(bot):
    await bot.add_cog(JogosGratis(bot))
