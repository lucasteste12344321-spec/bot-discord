import discord
from discord.ext import commands
from discord import ui
import sqlite3
import random

TOKEN = "MTQ3ODA2Nzc1NDYyMjc3OTU1NQ.Gaz8FO.9YR1n0POznEini3_LHBjfcvPZkH_dihsLmHdlM"

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

conn = sqlite3.connect("torneio.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS torneio (
    id INTEGER PRIMARY KEY,
    ativo INTEGER,
    data TEXT,
    premiacao TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS participantes (
    user_id INTEGER
)
""")

conn.commit()

class ViewTorneio(ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @ui.button(
        label="Entrar no Torneio",
        style=discord.ButtonStyle.green,
        emoji="⚔️",
        custom_id="btn_entrar_torneio"
    )
    async def entrar(self, interaction: discord.Interaction, button: ui.Button):

        cursor.execute("SELECT ativo FROM torneio WHERE id = 1")
        resultado = cursor.fetchone()

        if not resultado or resultado[0] == 0:
            return await interaction.response.send_message(
                "❌ Não há torneio aberto!",
                ephemeral=True
            )

        cursor.execute("SELECT user_id FROM participantes WHERE user_id = ?", (interaction.user.id,))
        if cursor.fetchone():
            return await interaction.response.send_message(
                "Você já está no torneio!",
                ephemeral=True
            )

        cursor.execute("INSERT INTO participantes (user_id) VALUES (?)", (interaction.user.id,))
        conn.commit()

        await interaction.response.send_message(
            "✅ Você entrou no torneio!",
            ephemeral=True
        )

@bot.event
async def on_ready():
    bot.add_view(ViewTorneio())
    print("Bot online como", bot.user)

@bot.command()
@commands.has_permissions(administrator=True)
async def abrir_torneio(ctx, data: str, premiacao: str):

    cursor.execute("SELECT ativo FROM torneio WHERE id = 1")
    resultado = cursor.fetchone()

    if resultado and resultado[0] == 1:
        embed = discord.Embed(
            title="⚠️ Torneio já em andamento!",
            description="Já existe um torneio ativo no momento.",
            color=discord.Color.red()
        )
        return await ctx.send(embed=embed)

    cursor.execute("DELETE FROM torneio")
    cursor.execute("DELETE FROM participantes")

    cursor.execute(
        "INSERT INTO torneio (id, ativo, data, premiacao) VALUES (1, 1, ?, ?)",
        (data, premiacao)
    )

    conn.commit()

    embed = discord.Embed(
        title="🏆 TORNEIO OFICIAL ABERTO!",
        description=f"📅 Data: {data}\n🏆 Premiação: {premiacao}\n\nClique no botão para participar!",
        color=discord.Color.green()
    )

    await ctx.send("@everyone O torneio começou!", embed=embed, view=ViewTorneio())

@bot.command()
@commands.has_permissions(administrator=True)
async def fechar_torneio(ctx):

    cursor.execute("UPDATE torneio SET ativo = 0 WHERE id = 1")
    conn.commit()

    await ctx.send("🔒 Inscrições encerradas.")

@bot.command()
@commands.has_permissions(administrator=True)
async def anunciar(ctx):

    cursor.execute("SELECT data, premiacao FROM torneio WHERE id = 1 AND ativo = 1")
    resultado = cursor.fetchone()

    if not resultado:
        return await ctx.send("Não há torneio ativo.")

    data, premiacao = resultado

    embed = discord.Embed(
        title="📢 TORNEIO OFICIAL",
        description=(
            f"📅 Data: {data}\n"
            f"🏆 Premiação: {premiacao}\n\n"
            "📜 REGRAS:\n"
            "1. Melhor de 3.\n"
            "2. Proibido spam.\n"
            "3. Respeito obrigatório.\n"
            "4. Decisão da staff é final."
        ),
        color=discord.Color.blurple()
    )

    await ctx.send(embed=embed)

@bot.command()
@commands.has_permissions(administrator=True)
async def sortear(ctx):

    cursor.execute("SELECT user_id FROM participantes")
    jogadores = cursor.fetchall()

    if len(jogadores) < 2:
        return await ctx.send("Precisa de pelo menos 2 participantes.")

    ids = [j[0] for j in jogadores]
    random.shuffle(ids)

    confrontos = []

    while len(ids) >= 2:
        p1 = ctx.guild.get_member(ids.pop())
        p2 = ctx.guild.get_member(ids.pop())

        if p1 and p2:
            confrontos.append(f"{p1.mention} vs {p2.mention}")

    if ids:
        restante = ctx.guild.get_member(ids.pop())
        if restante:
            confrontos.append(f"{restante.mention} avançou por WO!")

    await ctx.send("🎲 **Confrontos:**\n" + "\n".join(confrontos))

bot.run(TOKEN)