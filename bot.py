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
    "Mahoraga",
    "Perfection",
    "Blood Manipulator",
    "Switcher",
    "Defense Attorney",
    "Cursed Partners",
    "Puppet Master",
    "Head of the Hei",
    "Salaryman",
    "Lucky Coward"
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
    ativo INTEGER DEFAULT 0
)
""")

cursor.execute("INSERT OR IGNORE INTO torneio (rowid, ativo) VALUES (1, 0)")
conn.commit()

inscritos = []

# ================= FUNÇÕES =================

def is_admin(user_id):
    if user_id == OWNER_ID:
        return True
    cursor.execute("SELECT * FROM admins WHERE user_id = ?", (user_id,))
    return cursor.fetchone() is not None

def registrar_usuario(user_id):
    cursor.execute("INSERT OR IGNORE INTO jogadores (user_id) VALUES (?)", (user_id,))
    conn.commit()

# ================= AJUDA =================

@bot.command()
async def ajuda(ctx):
    embed = discord.Embed(title="📖 Comandos do Bot", color=0x00ff00)

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
        value="!abrirtorneio\n!entrar\n!fechartorneio\n!sortear",
        inline=False
    )

    embed.add_field(
        name="🔐 Staff",
        value="!addadmin @usuario\n!removeadmin @usuario\n!addvitoria @usuario\n!setnivel @usuario número",
        inline=False
    )

    await ctx.send(embed=embed)

# ================= PERSONAGENS =================

@bot.command()
async def personagens(ctx):
    lista = "\n".join(PERSONAGENS)
    embed = discord.Embed(title="🎭 Personagens Disponíveis", description=lista, color=0x00ff00)
    await ctx.send(embed=embed)

@bot.command()
async def setpersonagem(ctx, *, nome):
    nome_formatado = nome.lower()
    personagem_encontrado = None

    for p in PERSONAGENS:
        if nome_formatado == p.lower():
            personagem_encontrado = p
            break

    if not personagem_encontrado:
        lista = "\n".join(PERSONAGENS)
        return await ctx.send(f"❌ Personagem inválido.\n\nOpções disponíveis:\n{lista}")

    registrar_usuario(ctx.author.id)
    cursor.execute(
        "UPDATE jogadores SET personagem = ? WHERE user_id = ?",
        (personagem_encontrado, ctx.author.id)
    )
    conn.commit()

    await ctx.send(f"✅ Personagem definido como **{personagem_encontrado}**.")

# ================= PERFIL =================

@bot.command()
async def perfil(ctx, membro: discord.Member = None):
    membro = membro or ctx.author
    registrar_usuario(membro.id)

    cursor.execute("SELECT * FROM jogadores WHERE user_id = ?", (membro.id,))
    dados = cursor.fetchone()

    embed = discord.Embed(title=f"Perfil de {membro.name}", color=0x00ff00)
    embed.add_field(name="Personagem", value=dados[1], inline=False)
    embed.add_field(name="Estilo", value=dados[2], inline=False)
    embed.add_field(name="Vitórias", value=dados[3], inline=False)
    embed.add_field(name="Nível", value=dados[4], inline=False)

    await ctx.send(embed=embed)

@bot.command()
async def setestilo(ctx, *, estilo):
    registrar_usuario(ctx.author.id)
    cursor.execute("UPDATE jogadores SET estilo = ? WHERE user_id = ?", (estilo, ctx.author.id))
    conn.commit()
    await ctx.send("✅ Estilo atualizado.")

# ================= RANKING =================

@bot.command()
async def ranking(ctx):
    cursor.execute("SELECT user_id, vitorias FROM jogadores ORDER BY vitorias DESC LIMIT 10")
    ranking = cursor.fetchall()

    texto = ""
    for i, (user_id, vitorias) in enumerate(ranking, 1):
        user = await bot.fetch_user(user_id)
        texto += f"{i}. {user.name} - {vitorias} vitórias\n"

    await ctx.send(f"🏆 Ranking:\n\n{texto}")

# ================= STAFF =================

@bot.command()
async def addadmin(ctx, membro: discord.Member):
    if not is_admin(ctx.author.id):
        return await ctx.send("Sem permissão.")

    cursor.execute("INSERT OR IGNORE INTO admins (user_id) VALUES (?)", (membro.id,))
    conn.commit()
    await ctx.send("✅ Admin adicionado.")

@bot.command()
async def removeadmin(ctx, membro: discord.Member):
    if not is_admin(ctx.author.id):
        return await ctx.send("Sem permissão.")

    cursor.execute("DELETE FROM admins WHERE user_id = ?", (membro.id,))
    conn.commit()
    await ctx.send("✅ Admin removido.")

@bot.command()
async def addvitoria(ctx, membro: discord.Member):
    if not is_admin(ctx.author.id):
        return await ctx.send("Sem permissão.")

    registrar_usuario(membro.id)
    cursor.execute("UPDATE jogadores SET vitorias = vitorias + 1 WHERE user_id = ?", (membro.id,))
    conn.commit()
    await ctx.send("🏆 Vitória adicionada.")

@bot.command()
async def setnivel(ctx, membro: discord.Member, nivel: int):
    if not is_admin(ctx.author.id):
        return await ctx.send("Sem permissão.")

    registrar_usuario(membro.id)
    cursor.execute("UPDATE jogadores SET nivel = ? WHERE user_id = ?", (nivel, membro.id))
    conn.commit()
    await ctx.send("⭐ Nível atualizado.")

# ================= TORNEIO =================

@bot.command()
async def abrirtorneio(ctx):
    if not is_admin(ctx.author.id):
        return await ctx.send("Sem permissão.")

    global inscritos
    inscritos = []
    cursor.execute("UPDATE torneio SET ativo = 1 WHERE rowid = 1")
    conn.commit()
    await ctx.send("🔥 Torneio aberto! Use !entrar")

@bot.command()
async def fechartorneio(ctx):
    if not is_admin(ctx.author.id):
        return await ctx.send("Sem permissão.")

    cursor.execute("UPDATE torneio SET ativo = 0 WHERE rowid = 1")
    conn.commit()
    await ctx.send("❌ Inscrições encerradas.")

@bot.command()
async def entrar(ctx):
    cursor.execute("SELECT ativo FROM torneio WHERE rowid = 1")
    ativo = cursor.fetchone()[0]

    if not ativo:
        return await ctx.send("Nenhum torneio aberto.")

    if ctx.author.id in inscritos:
        return await ctx.send("Você já está inscrito.")

    inscritos.append(ctx.author.id)
    await ctx.send("✅ Inscrição confirmada!")

@bot.command()
async def sortear(ctx):
    if not is_admin(ctx.author.id):
        return await ctx.send("Sem permissão.")

    if len(inscritos) < 2:
        return await ctx.send("Participantes insuficientes.")

    random.shuffle(inscritos)

    confrontos = ""
    for i in range(0, len(inscritos), 2):
        if i + 1 < len(inscritos):
            p1 = await bot.fetch_user(inscritos[i])
            p2 = await bot.fetch_user(inscritos[i+1])
            confrontos += f"{p1.name} vs {p2.name}\n"
        else:
            p1 = await bot.fetch_user(inscritos[i])
            confrontos += f"{p1.name} avança automaticamente\n"

    await ctx.send(f"🔥 Confrontos:\n\n{confrontos}")

# ================= START =================

@bot.event
async def on_ready():
    print(f"Bot online como {bot.user}")

bot.run(TOKEN)
