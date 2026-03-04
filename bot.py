import discord
from discord.ext import commands
import sqlite3
import random
import os

# ================= CONFIG =================

OWNER_ID = 1224163183426670722
TOKEN = os.getenv("TOKEN")

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ================= PERSONAGENS =================

PERSONAGENS = [
    "Honored One",
    "Vessel",
    "Restless Gambler",
    "Ten Shadows",
    "Perfection",
    "Blood Manipulator",
    "Switcher",
    "Defense Attorney",
    "Cursed Partners",
    "Puppet Master",
    "Head of the Hei",
    "Salaryman",
    "Lucky Coward",
    "Locust Guy",
    "Star Rage",
    "Aspiring Mangaká"
]

# ================= BANCO =================

conn = sqlite3.connect("torneio.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS jogadores (
    user_id INTEGER PRIMARY KEY,
    personagem TEXT DEFAULT "Não definido",
    estilo TEXT DEFAULT "Não definido",
    vitorias INTEGER DEFAULT 0,
    nivel INTEGER DEFAULT 0
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS admins (
    user_id INTEGER PRIMARY KEY
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS torneio (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    ativo INTEGER DEFAULT 0
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS inscritos (
    user_id INTEGER PRIMARY KEY
)
""")

cursor.execute("INSERT OR IGNORE INTO torneio (id, ativo) VALUES (1, 0)")
conn.commit()

# ================= FUNÇÕES =================

def is_admin(user_id):
    if user_id == OWNER_ID:
        return True
    cursor.execute("SELECT 1 FROM admins WHERE user_id = ?", (user_id,))
    return cursor.fetchone() is not None

def registrar_usuario(user_id):
    cursor.execute("INSERT OR IGNORE INTO jogadores (user_id) VALUES (?)", (user_id,))
    conn.commit()

def contar_inscritos():
    cursor.execute("SELECT COUNT(*) FROM inscritos")
    return cursor.fetchone()[0]

# ================= BOTÃO =================

class EntrarTorneioView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Entrar no Torneio", style=discord.ButtonStyle.green, emoji="🔥")
    async def entrar(self, interaction: discord.Interaction, button: discord.ui.Button):

        cursor.execute("SELECT ativo FROM torneio WHERE id = 1")
        ativo = cursor.fetchone()[0]

        if not ativo:
            return await interaction.response.send_message(
                "❌ Não há torneio aberto.",
                ephemeral=True
            )

        cursor.execute("SELECT 1 FROM inscritos WHERE user_id = ?", (interaction.user.id,))
        if cursor.fetchone():
            return await interaction.response.send_message(
                "⚠️ Você já está inscrito.",
                ephemeral=True
            )

        cursor.execute("INSERT INTO inscritos (user_id) VALUES (?)", (interaction.user.id,))
        conn.commit()

        total = contar_inscritos()

        embed = discord.Embed(
            title="🔥 TORNEIO ABERTO!",
            description=(
                "Clique no botão abaixo para participar.\n\n"
                f"👥 **Participantes atuais:** {total}"
            ),
            color=0xed4245
        )

        embed.set_footer(text="Prove que você é o mais forte.")

        await interaction.response.edit_message(embed=embed, view=self)

        await interaction.followup.send(
            "✅ Você entrou no torneio!",
            ephemeral=True
        )

# ================= AJUDA =================

@bot.command()
async def ajuda(ctx):
    embed = discord.Embed(title="📖 Comandos do Bot", color=0x2b2d31)

    embed.add_field(
        name="👤 Perfil",
        value="!perfil\n!setpersonagem Nome\n!setestilo Texto\n!personagens",
        inline=False
    )

    embed.add_field(
        name="🏆 Ranking",
        value="!ranking",
        inline=False
    )

    embed.add_field(
        name="🎮 Torneio",
        value="!abrirtorneio\n!fechartorneio\n!sortear",
        inline=False
    )

    embed.add_field(
        name="🔐 Staff",
        value="!addadmin @usuario\n!removeadmin @usuario\n!addvitoria @usuario\n!setnivel @usuario número",
        inline=False
    )

    await ctx.send(embed=embed)

# ================= TORNEIO =================

@bot.command()
async def abrirtorneio(ctx):
    if not is_admin(ctx.author.id):
        return await ctx.send("Sem permissão.")

    cursor.execute("UPDATE torneio SET ativo = 1 WHERE id = 1")
    cursor.execute("DELETE FROM inscritos")
    conn.commit()

    total = contar_inscritos()

    embed = discord.Embed(
        title="🔥 TORNEIO ABERTO!",
        description=(
            "Clique no botão abaixo para participar.\n\n"
            f"👥 **Participantes atuais:** {total}"
        ),
        color=0xed4245
    )

    embed.set_footer(text="As inscrições serão fechadas pelo administrador.")

    view = EntrarTorneioView()
    await ctx.send(embed=embed, view=view)

@bot.command()
async def fechartorneio(ctx):
    if not is_admin(ctx.author.id):
        return await ctx.send("Sem permissão.")

    cursor.execute("UPDATE torneio SET ativo = 0 WHERE id = 1")
    conn.commit()
    await ctx.send("❌ Inscrições encerradas.")

@bot.command()
async def sortear(ctx):
    if not is_admin(ctx.author.id):
        return await ctx.send("Sem permissão.")

    cursor.execute("SELECT user_id FROM inscritos")
    inscritos = [row[0] for row in cursor.fetchall()]

    if len(inscritos) < 2:
        return await ctx.send("Participantes insuficientes.")

    random.shuffle(inscritos)

    confrontos = ""
    for i in range(0, len(inscritos), 2):
        if i + 1 < len(inscritos):
            p1 = await bot.fetch_user(inscritos[i])
            p2 = await bot.fetch_user(inscritos[i+1])
            confrontos += f"⚔️ {p1.name} vs {p2.name}\n"
        else:
            p1 = await bot.fetch_user(inscritos[i])
            confrontos += f"👑 {p1.name} avança automaticamente\n"

    embed = discord.Embed(
        title="🔥 Confrontos do Torneio",
        description=confrontos,
        color=0xed4245
    )

    await ctx.send(embed=embed)

# ================= START =================

@bot.event
async def on_ready():
    bot.add_view(EntrarTorneioView())  # importante pra Railway
    print(f"Bot online como {bot.user}")

bot.run(TOKEN)
