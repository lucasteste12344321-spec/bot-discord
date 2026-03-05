import discord
from discord.ext import commands
import sqlite3
import os

TOKEN = os.getenv("TOKEN")

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ==========================
# BANCO DE DADOS
# ==========================

conn = sqlite3.connect("torneio.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS torneio (
    id INTEGER PRIMARY KEY,
    ativo INTEGER
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS inscritos (
    user_id INTEGER PRIMARY KEY
)
""")

cursor.execute("INSERT OR IGNORE INTO torneio (id, ativo) VALUES (1, 0)")
conn.commit()

# ==========================
# FUNÇÕES AUXILIARES
# ==========================

def listar_inscritos():
    cursor.execute("SELECT user_id FROM inscritos")
    return [row[0] for row in cursor.fetchall()]

def gerar_embed_inscritos(bot):
    inscritos_ids = listar_inscritos()
    total = len(inscritos_ids)

    nomes = []
    for user_id in inscritos_ids[:25]:
        user = bot.get_user(user_id)
        nome = user.name if user else f"ID {user_id}"
        nomes.append(nome)

    lista = "\n".join(nomes) if nomes else "Nenhum ainda."

    embed = discord.Embed(
        title="🔥 TORNEIO",
        description=f"👥 **Participantes ({total}):**\n\n{lista}",
        color=0xed4245
    )

    embed.set_footer(text="Mostrando até 25 nomes")

    return embed

# ==========================
# VIEW PERSISTENTE
# ==========================

class EntrarTorneioView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Entrar no Torneio",
        style=discord.ButtonStyle.green,
        emoji="🔥",
        custom_id="botao_entrar_torneio"
    )
    async def entrar(self, interaction: discord.Interaction, button: discord.ui.Button):

        await interaction.response.defer(ephemeral=True)

        cursor.execute("SELECT ativo FROM torneio WHERE id = 1")
        ativo = cursor.fetchone()[0]

        if not ativo:
            return await interaction.followup.send(
                "❌ Não há torneio aberto.",
                ephemeral=True
            )

        cursor.execute("SELECT 1 FROM inscritos WHERE user_id = ?", (interaction.user.id,))
        if cursor.fetchone():
            return await interaction.followup.send(
                "⚠️ Você já está inscrito.",
                ephemeral=True
            )

        cursor.execute("INSERT INTO inscritos (user_id) VALUES (?)", (interaction.user.id,))
        conn.commit()

        await interaction.followup.send(
            "✅ Você entrou no torneio!",
            ephemeral=True
        )

        # Atualiza embed da mensagem original
        embed = gerar_embed_inscritos(interaction.client)
        await interaction.message.edit(embed=embed, view=self)

# ==========================
# EVENTO READY
# ==========================

@bot.event
async def on_ready():
    bot.add_view(EntrarTorneioView())
    print(f"✅ Bot online como {bot.user}")

# ==========================
# COMANDOS
# ==========================

@bot.command()
@commands.has_permissions(administrator=True)
async def abrirtorneio(ctx):

    cursor.execute("UPDATE torneio SET ativo = 1 WHERE id = 1")
    cursor.execute("DELETE FROM inscritos")
    conn.commit()

    embed = gerar_embed_inscritos(bot)
    await ctx.send(embed=embed, view=EntrarTorneioView())


@bot.command()
@commands.has_permissions(administrator=True)
async def fechartorneio(ctx):

    cursor.execute("UPDATE torneio SET ativo = 0 WHERE id = 1")
    conn.commit()

    inscritos_ids = listar_inscritos()
    total = len(inscritos_ids)

    nomes = []
    for user_id in inscritos_ids:
        user = bot.get_user(user_id)
        nome = user.name if user else f"ID {user_id}"
        nomes.append(nome)

    lista = "\n".join(nomes) if nomes else "Nenhum."

    embed = discord.Embed(
        title="🏁 TORNEIO FECHADO",
        description=f"👥 Total: {total}\n\n{lista}",
        color=0x5865f2
    )

    await ctx.send(embed=embed)


@bot.command()
async def inscritos(ctx):
    embed = gerar_embed_inscritos(bot)
    await ctx.send(embed=embed)

# ==========================
# START
# ==========================

if TOKEN is None:
    print("❌ TOKEN não encontrado. Configure na Railway.")
else:
    bot.run(TOKEN)
