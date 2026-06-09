import discord
from discord import app_commands
from discord.ui import View, Button
import psycopg2
import os

intents = discord.Intents.default()

client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

conn = psycopg2.connect(os.getenv("DATABASE_URL"))
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS permis (
    pseudo_roblox TEXT PRIMARY KEY,
    nom TEXT,
    prenom TEXT,
    date_obtention TEXT,
    points INTEGER,
    categorie TEXT,
    statut TEXT,
    salon_demande BIGINT,
    valide INTEGER DEFAULT 0
)
""")
conn.commit()
class ValidationPermisView(View):
    def __init__(self, pseudo_roblox):
        super().__init__(timeout=None)
        self.pseudo_roblox = pseudo_roblox

        accepter = Button(
            label="✅ Accepter",
            style=discord.ButtonStyle.green
        )

        refuser = Button(
            label="❌ Refuser",
            style=discord.ButtonStyle.red
        )

        accepter.callback = self.accepter
        refuser.callback = self.refuser

        self.add_item(accepter)
        self.add_item(refuser)

    async def accepter(self, interaction: discord.Interaction):

        cursor.execute(
            "UPDATE permis SET valide = 1 WHERE pseudo_roblox = %s",
            (self.pseudo_roblox,)
        )

        conn.commit()

        embed = interaction.message.embeds[0]

        embed.color = 0x2ecc71
        embed.title = "Permis accepté"

        await interaction.response.edit_message(
            embed=embed,
            view=None
        )

    async def refuser(self, interaction: discord.Interaction):

        cursor.execute(
            "DELETE FROM permis WHERE pseudo_roblox = %s",
            (self.pseudo_roblox,)
        )

        conn.commit()

        embed = interaction.message.embeds[0]

        embed.color = 0xe74c3c
        embed.title = "Permis refusé"

        await interaction.response.edit_message(
            embed=embed,
            view=None
        )
        
@tree.command(
    name="examenpermis",
    description="Créer une demande de permis"
)
async def demandepermis(
    interaction: discord.Interaction,
    pseudo_roblox: str,
    date_obtention: str,
    poteaux: int,
    trottoirs: int,
    feux_rouges: int,
    priorites: int,
    accidents: int
):

    points = (
        12
        - poteaux
        - (trottoirs * 2)
        - (feux_rouges * 3)
        - (priorites * 2)
        - (accidents * 4)
    )

    if points < 0:
        points = 0

    statut = "Valide" if points >= 8 else "Refusé"

    motifs = []

    if poteaux > 0:
        motifs.append(f"• {poteaux} poteau(x) touché(s)")

    if trottoirs > 0:
        motifs.append(f"• {trottoirs} trottoir(s) monté(s)")

    if feux_rouges > 0:
        motifs.append(f"• {feux_rouges} feu(x) rouge(s) grillé(s)")

    if priorites > 0:
        motifs.append(f"• {priorites} priorité(s) non respectée(s)")

    if accidents > 0:
        motifs.append(f"• {accidents} accident(s)")

    motifs_text = "\n".join(motifs)

    if not motifs_text:
        motifs_text = "Aucune faute"

    cursor.execute(
        "SELECT nom, prenom FROM identites WHERE pseudo_roblox = %s",
        (pseudo_roblox,)
    )

    identite = cursor.fetchone()

    if not identite:
        await interaction.response.send_message(
            "Aucune carte d'identité trouvée pour ce joueur.",
            ephemeral=True
        )
        return

    nom = identite[0]
    prenom = identite[1]

    embed = discord.Embed(
        title="📋 Résultat de l'examen du permis",
        color=0x2ecc71 if statut == "Valide" else 0xe74c3c
    )

    embed.description = (
        f"**Pseudo Roblox**\n{pseudo_roblox}\n\n"

        f"**Nom :** {nom}\n"
        f"**Prénom :** {prenom}\n\n"

        f"**Date d'obtention :** {date_obtention}\n"
        f"**Catégorie :** Voiture\n\n"

        f"**Points :** {points}/12\n"
        f"**Statut :** {statut}\n\n"

        f"**Fautes constatées :**\n"
        f"{motifs_text}"
    )

    cursor.execute("""
        INSERT INTO permis (
            pseudo_roblox,
            nom,
            prenom,
            date_obtention,
            points,
            categorie,
            statut,
            salon_demande,
            valide
        )
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
        ON CONFLICT (pseudo_roblox)
        DO UPDATE SET
            nom = EXCLUDED.nom,
            prenom = EXCLUDED.prenom,
            date_obtention = EXCLUDED.date_obtention,
            points = EXCLUDED.points,
            categorie = EXCLUDED.categorie,
            statut = EXCLUDED.statut,
            salon_demande = EXCLUDED.salon_demande,
            valide = 0
    """, (
        pseudo_roblox,
        nom,
        prenom,
        date_obtention,
        points,
        "Voiture",
        statut,
        interaction.channel.id,
        0
    ))

    conn.commit()

    salon = client.get_channel(1513043166566285312)

    if salon:
        await salon.send(
            embed=embed,
            view=ValidationPermisView(pseudo_roblox)
        )

    await interaction.response.send_message(
        "Le résultat de l'examen a été envoyé pour validation.",
        ephemeral=True
    )
@client.event
async def on_ready():
    await tree.sync()
    print(f"✅ Connecté en tant que {client.user}")

TOKEN = os.getenv("TOKEN")

client.run(TOKEN)
