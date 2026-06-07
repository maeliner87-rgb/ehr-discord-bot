import discord
from discord import app_commands
import sqlite3
import os
import aiohttp
from discord.ui import View, Button

intents = discord.Intents.default()

client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

import os

if os.path.exists("identites.db"):
    os.remove("identites.db")
    
# Base de données
conn = sqlite3.connect("identites.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS identites (
    pseudo_discord TEXT PRIMARY KEY,
    nom TEXT,
    prenom TEXT,
    naissance TEXT,
    ville_naissance TEXT,
    age TEXT,
    sexe TEXT,
    nationalite TEXT,
    pseudo_roblox TEXT,
    valide INTEGER DEFAULT 0
)
""")
conn.commit()


async def verifier_pseudo_roblox(pseudo):
    url = "https://users.roblox.com/v1/usernames/users"

    async with aiohttp.ClientSession() as session:
        async with session.post(
            url,
            json={
                "usernames": [pseudo],
                "excludeBannedUsers": False
            }
        ) as response:

            print("STATUS =", response.status)

            if response.status != 200:
                return None

            data = await response.json()

            print("ROBLOX DATA =", data)

            if not data["data"]:
                return None

            return data["data"][0]


@client.event
async def on_ready():
    await tree.sync()
    print(f"✅ Connecté en tant que {client.user}")


@tree.command(
    name="créeid",
    description="Créer une carte d'identité"
)
async def creeridentite(
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

    user_data = await verifier_pseudo_roblox(pseudo_roblox)

    if user_data is None:
        await interaction.response.send_message(
            "❌ Ce pseudo Roblox n'existe pas.",
            ephemeral=True
        )
        return

    cursor.execute("""
INSERT OR REPLACE INTO identites
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
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

    salon = client.get_channel(1513017794214498414)

    embed_validation = discord.Embed(
        title="📋 Nouvelle demande de carte d'identité",
        color=0xf1c40f
    )

    embed_validation.description = (
        f"**Pseudo Roblox**\n"
        f"{pseudo_roblox}\n\n"

        f"**Nom :** {nom}\u00A0\u00A0\u00A0\u00A0\u00A0\u00A0\u00A0\u00A0\u00A0\u00A0\u00A0\u00A0\u00A0\u00A0\u00A0\u00A0\u00A0\u00A0**Prénom :** {prenom}\n\n"

        f"**Date de naissance :** {naissance}\n"
        f"**Ville de naissance :** {ville_naissance}\n\n"

        f"**Âge :** {age}\u00A0\u00A0\u00A0\u00A0\u00A0\u00A0\u00A0\u00A0\u00A0\u00A0\u00A0\u00A0\u00A0\u00A0\u00A0\u00A0\u00A0\u00A0\u00A0\u00A0**Sexe :** {sexe}\n\n"

        f"**Nationalité :** {nationalite}"
    )

    embed_validation.set_footer(
        text="Emergency Hamburg RP"
    )

    await salon.send(embed=embed_validation)

    await interaction.response.send_message(
        "✅ Votre demande de carte d'identité a été envoyée pour validation.",
        ephemeral=True
    )


@tree.command(
    name="id",
    description="Rechercher une carte d'identité"
)
async def identite(
    interaction: discord.Interaction,
    pseudo_roblox: str
):

    cursor.execute(
        "SELECT * FROM identites WHERE pseudo_roblox = ?",
        (pseudo_roblox,)
    )


    data = cursor.fetchone()

    if data and data[9] == 0:
        await interaction.response.send_message(
            "⏳ Cette carte d'identité est en attente de validation."
        )
        return

    user_data = await verifier_pseudo_roblox(pseudo_roblox)

    if user_data is None:
        await interaction.response.send_message(
            "❌ Impossible de récupérer les informations Roblox."
        )
        return

    roblox_id = user_data["id"]

    avatar_url = (
        f"https://www.roblox.com/headshot-thumbnail/image"
        f"?userId={roblox_id}&width=420&height=420&format=png"
    )

    profil_url = f"https://www.roblox.com/users/{roblox_id}/profile"

    if not data:
        await interaction.response.send_message(
            "❌ Aucune carte d'identité trouvée."
        )
        return

    embed = discord.Embed(
        title="Carte d'identité",
        color=0x2b2d31
    )
    embed.description = (
    f"**Pseudo Roblox**\n"
    f"{data[8]}\n\n"

    f"**Nom :** {data[1]}\u00A0\u00A0\u00A0\u00A0\u00A0\u00A0\u00A0\u00A0\u00A0\u00A0\u00A0\u00A0\u00A0\u00A0\u00A0\u00A0\u00A0\u00A0**Prénom :** {data[2]}\n\n"

    f"**Date de naissance :** {data[3]}\n"
    f"**Ville de naissance :** {data[4]}\n\n"

    f"**Âge :** {data[5]}\u00A0\u00A0\u00A0\u00A0\u00A0\u00A0\u00A0\u00A0\u00A0\u00A0\u00A0\u00A0\u00A0\u00A0\u00A0\u00A0\u00A0\u00A0\u00A0\u00A0**Sexe :** {data[6]}\n\n"

    f"**Nationalité :** {data[7]}"
)

    embed.set_thumbnail(url=avatar_url)

    embed.set_footer(
        text="Emergency Hamburg RP"
    )

    view = View()

    view.add_item(
        Button(
            label="Profil Roblox",
            url=profil_url
        )
    )

    await interaction.response.send_message(
        embed=embed,
        view=view
    )


TOKEN = os.getenv("TOKEN")

client.run(TOKEN)
