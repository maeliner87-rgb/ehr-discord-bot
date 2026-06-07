import discord
from discord import app_commands
import sqlite3
import os

intents = discord.Intents.default()

client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

# Base de données
conn = sqlite3.connect("identites.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS identites (
    pseudo TEXT PRIMARY KEY,
    nom TEXT,
    prenom TEXT,
    naissance TEXT,
    ville_naissance TEXT,
    age TEXT,
    sexe TEXT,
    nationalite TEXT,
    pseudo_roblox TEXT
)
""")
conn.commit()


@client.event
async def on_ready():
    await tree.sync()
    print(f"Connecté en tant que {client.user}")


@tree.command(
    name="createid",
    description="Créer ou modifier une carte d'identité"
)
async def createid(
    interaction: discord.Interaction,
    pseudo_roblox: str,
    nom: str,
    prenom: str,
    naissance: str,
    ville_naissance: str,
    age: str,
    sexe: str,
    nationalite: str
):

    cursor.execute("""
    INSERT OR REPLACE INTO identites
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        str(interaction.user),
        nom,
        prenom,
        naissance,
        ville_naissance,
        age,
        sexe,
        nationalite,
        pseudo_roblox
    ))

    conn.commit()

    await interaction.response.send_message(
        "✅ Carte d'identité enregistrée avec succès.",
        ephemeral=True
    )


@tree.command(
    name="id",
    description="Rechercher une carte d'identité"
)
async def rechercher(
    interaction: discord.Interaction,
    pseudo_roblox: str
):

    cursor.execute(
        "SELECT * FROM identites WHERE pseudo_roblox = ?",
        (pseudo_roblox,)
    )

    data = cursor.fetchone()

    if not data:
        await interaction.response.send_message(
            "❌ Aucune carte trouvée pour ce pseudo Roblox."
        )
        return

    embed = discord.Embed(
        title="🪪 CARTE D'IDENTITÉ",
        color=0x2b2d31
    )

    embed.add_field(
        name="Pseudo Roblox",
        value=data[8],
        inline=False
    )

    embed.add_field(
        name="Nom",
        value=data[1],
        inline=True
    )

    embed.add_field(
        name="Prénom",
        value=data[2],
        inline=True
    )

    embed.add_field(
        name="Date de naissance",
        value=data[3],
        inline=False
    )

    embed.add_field(
        name="Ville de naissance",
        value=data[4],
        inline=False
    )

    embed.add_field(
        name="Âge",
        value=data[5],
        inline=True
    )

    embed.add_field(
        name="Sexe",
        value=data[6],
        inline=True
    )

    embed.add_field(
        name="Nationalité",
        value=data[7],
        inline=False
    )

    await interaction.response.send_message(embed=embed)


TOKEN = os.getenv("TOKEN")
client.run(TOKEN)
