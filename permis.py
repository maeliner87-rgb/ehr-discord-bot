import discord
from discord import app_commands
from discord.ui import View, Button
from datetime import datetime

def setup_permis(tree, client, conn, cursor):

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

            embed.title = "✅ Permis accepté"
            embed.color = 0x2ecc71

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

            embed.title = "❌ Permis refusé"
            embed.color = 0xe74c3c

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
        poteaux: int,
        trottoirs: int,
        feux_rouges: int,
        priorites: int,
        accidents: int
    ):

        date_obtention = datetime.now().strftime("%d/%m/%Y")

        note = 20

        note -= poteaux * 2
        note -= trottoirs * 2
        note -= priorites * 3
        note -= feux_rouges * 5

        if note < 0:
            note = 0

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

        if accidents >= 1:
            statut = "❌ Refusé"
            raison = "Accident durant l'examen"

        elif feux_rouges >= 2:
            statut = "❌ Refusé"
            raison = "Trop de feux rouges grillés"

        elif note >= 12:
            statut = "✅ Permis obtenu"
            raison = None

        else:
            statut = "❌ Refusé"
            raison = "Note insuffisante"

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
            color=0x2ecc71 if "obtenu" in statut else 0xe74c3c
        )

        embed.description = (
            f"**Pseudo Roblox**\n{pseudo_roblox}\n\n"
            f"**Nom :** {nom}\n"
            f"**Prénom :** {prenom}\n\n"
            f"**Date :** {date_obtention}\n"
            f"**Catégorie :** Voiture\n\n"
            f"**Note :** {note}/20\n"
            f"**Statut :** {statut}\n\n"
            f"**Fautes constatées :**\n"
            f"{motifs_text}"
        )

        if raison:
            embed.add_field(
                name="Motif du refus",
                value=raison,
                inline=False
            )

        await interaction.response.send_message(
            embed=embed
        )
