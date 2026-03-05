import discord
from discord.ext import commands
import sqlite3
import random
import os

TOKEN = os.getenv("TOKEN")
OWNER_ID = 1224163183426670722

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
CREATE TABLE IF NOT EXISTS jogadores(
user_id INTEGER PRIMARY KEY,
personagem TEXT DEFAULT 'Não definido',
estilo TEXT DEFAULT 'Não definido',
vitorias INTEGER DEFAULT 0,
nivel INTEGER DEFAULT 0
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS admins(
user_id INTEGER PRIMARY KEY
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS inscritos(
user_id INTEGER PRIMARY KEY
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS torneio(
id INTEGER PRIMARY KEY CHECK (id = 1),
ativo INTEGER DEFAULT 0
)
""")

cursor.execute("INSERT OR IGNORE INTO torneio (id,ativo) VALUES (1,0)")
conn.commit()

# ================= FUNÇÕES =================

def registrar_usuario(user_id):
    cursor.execute(
        "INSERT OR IGNORE INTO jogadores(user_id) VALUES(?)",
        (user_id,)
    )
    conn.commit()

def is_admin(user_id):

    if user_id == OWNER_ID:
        return True

    cursor.execute(
        "SELECT 1 FROM admins WHERE user_id=?",
        (user_id,)
    )

    return cursor.fetchone() is not None

# ================= BOTÃO TORNEIO =================

class TorneioView(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Entrar no Torneio",
        style=discord.ButtonStyle.success,
        emoji="🔥",
        custom_id="entrar_torneio"
    )

    async def entrar(self, interaction: discord.Interaction, button: discord.ui.Button):

        cursor.execute("SELECT ativo FROM torneio WHERE id=1")
        ativo = cursor.fetchone()[0]

        if not ativo:
            return await interaction.response.send_message(
                "Torneio fechado.",
                ephemeral=True
            )

        cursor.execute(
            "SELECT 1 FROM inscritos WHERE user_id=?",
            (interaction.user.id,)
        )

        if cursor.fetchone():
            return await interaction.response.send_message(
                "Você já entrou.",
                ephemeral=True
            )

        cursor.execute(
            "INSERT INTO inscritos VALUES(?)",
            (interaction.user.id,)
        )

        conn.commit()

        await interaction.response.send_message(
            "Inscrição confirmada 🔥",
            ephemeral=True
        )

# ================= PERFIL =================

@bot.command()
async def perfil(ctx, membro: discord.Member = None):

    membro = membro or ctx.author
    registrar_usuario(membro.id)

    cursor.execute(
        "SELECT * FROM jogadores WHERE user_id=?",
        (membro.id,)
    )

    dados = cursor.fetchone()

    embed = discord.Embed(
        title=f"Perfil de {membro.name}",
        color=0x00ff00
    )

    embed.add_field(name="Personagem", value=dados[1])
    embed.add_field(name="Estilo", value=dados[2])
    embed.add_field(name="Vitórias", value=dados[3])
    embed.add_field(name="Nível", value=dados[4])

    await ctx.send(embed=embed)

# ================= PERSONAGENS =================

@bot.command()
async def personagens(ctx):

    embed = discord.Embed(
        title="Personagens",
        description="\n".join(PERSONAGENS)
    )

    await ctx.send(embed=embed)

@bot.command()
async def setpersonagem(ctx, *, nome):

    personagem = next(
        (p for p in PERSONAGENS if p.lower() == nome.lower()),
        None
    )

    if not personagem:
        return await ctx.send("Personagem inválido.")

    registrar_usuario(ctx.author.id)

    cursor.execute(
        "UPDATE jogadores SET personagem=? WHERE user_id=?",
        (personagem, ctx.author.id)
    )

    conn.commit()

    await ctx.send(f"Personagem definido: {personagem}")

# ================= ESTILO =================

@bot.command()
async def setestilo(ctx, *, estilo):

    registrar_usuario(ctx.author.id)

    cursor.execute(
        "UPDATE jogadores SET estilo=? WHERE user_id=?",
        (estilo, ctx.author.id)
    )

    conn.commit()

    await ctx.send("Estilo atualizado.")

# ================= RANKING =================

@bot.command()
async def ranking(ctx):

    cursor.execute(
        "SELECT user_id,vitorias FROM jogadores ORDER BY vitorias DESC LIMIT 10"
    )

    ranking = cursor.fetchall()

    texto = ""

    for i,(user_id,vitorias) in enumerate(ranking,1):

        user = await bot.fetch_user(user_id)

        texto += f"{i}. {user.name} — {vitorias} vitórias\n"

    await ctx.send(f"🏆 Ranking\n\n{texto}")

# ================= ADMIN =================

@bot.command()
async def addadmin(ctx, membro: discord.Member):

    if not is_admin(ctx.author.id):
        return

    cursor.execute(
        "INSERT OR IGNORE INTO admins VALUES(?)",
        (membro.id,)
    )

    conn.commit()

    await ctx.send("Admin adicionado.")

@bot.command()
async def addvitoria(ctx, membro: discord.Member):

    if not is_admin(ctx.author.id):
        return

    registrar_usuario(membro.id)

    cursor.execute(
        "UPDATE jogadores SET vitorias=vitorias+1 WHERE user_id=?",
        (membro.id,)
    )

    conn.commit()

    await ctx.send("Vitória adicionada.")

@bot.command()
async def setnivel(ctx, membro: discord.Member, nivel: int):

    if not is_admin(ctx.author.id):
        return

    registrar_usuario(membro.id)

    cursor.execute(
        "UPDATE jogadores SET nivel=? WHERE user_id=?",
        (nivel, membro.id)
    )

    conn.commit()

    await ctx.send("Nível atualizado.")

# ================= TORNEIO =================

@bot.command()
async def abrirtorneio(ctx):

    if not is_admin(ctx.author.id):
        return

    cursor.execute("UPDATE torneio SET ativo=1 WHERE id=1")
    cursor.execute("DELETE FROM inscritos")

    conn.commit()

    embed = discord.Embed(
        title="🔥 TORNEIO ABERTO",
        description="Clique para participar"
    )

    await ctx.send(embed=embed, view=TorneioView())

@bot.command()
async def fechartorneio(ctx):

    if not is_admin(ctx.author.id):
        return

    cursor.execute("UPDATE torneio SET ativo=0 WHERE id=1")

    conn.commit()

    await ctx.send("Torneio fechado.")

@bot.command()
async def inscritos(ctx):

    cursor.execute("SELECT user_id FROM inscritos")

    lista = cursor.fetchall()

    if not lista:
        return await ctx.send("Nenhum inscrito.")

    nomes = []

    for user_id, in lista:

        user = await bot.fetch_user(user_id)

        nomes.append(user.name)

    texto = "\n".join(nomes)

    await ctx.send(
        f"Participantes ({len(nomes)}):\n\n{texto}"
    )

@bot.command()
async def sortear(ctx):

    if not is_admin(ctx.author.id):
        return

    cursor.execute("SELECT user_id FROM inscritos")

    inscritos = [x[0] for x in cursor.fetchall()]

    if len(inscritos) < 2:
        return await ctx.send("Poucos jogadores.")

    random.shuffle(inscritos)

    texto = ""

    for i in range(0, len(inscritos), 2):

        if i+1 < len(inscritos):

            p1 = await bot.fetch_user(inscritos[i])
            p2 = await bot.fetch_user(inscritos[i+1])

            texto += f"{p1.name} vs {p2.name}\n"

        else:

            p1 = await bot.fetch_user(inscritos[i])

            texto += f"{p1.name} avança automaticamente\n"

    await ctx.send(f"🔥 Confrontos\n\n{texto}")

# ================= UTIL =================

@bot.command()
async def ping(ctx):
    await ctx.send(f"Pong {round(bot.latency*1000)}ms")

@bot.command()
async def ajuda(ctx):

    embed = discord.Embed(title="Comandos")

    embed.add_field(
        name="Perfil",
        value="!perfil !setpersonagem !setestilo !personagens"
    )

    embed.add_field(
        name="Ranking",
        value="!ranking"
    )

    embed.add_field(
        name="Torneio",
        value="!abrirtorneio !fechartorneio !inscritos !sortear"
    )

    embed.add_field(
        name="Admin",
        value="!addadmin !addvitoria !setnivel"
    )

    await ctx.send(embed=embed)

# ================= READY =================

@bot.event
async def on_ready():

    bot.add_view(TorneioView())

    print(f"Bot online como {bot.user}")

bot.run(TOKEN)
