import discord
from discord import app_commands
from datetime import datetime

def setup_permis(tree, client, conn, cursor):

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS permis (
        pseudo_roblox TEXT,
        nom TEXT,
        prenom TEXT,
        date_obtention TEXT,
        points INTEGER,
        categorie TEXT,
        statut TEXT,
        salon_demande BIGINT,
        valide INTEGER DEFAULT 0,
        PRIMARY KEY (pseudo_roblox, categorie)
    )
    """)
    conn.commit()

    print("✅ TABLE PERMIS CRÉÉE")

    @tree.command(
        name="examenpermis",
        description="Créer une demande de permis"
    )
    @app_commands.choices(
        categorie=[
            app_commands.Choice(name="Voiture", value="Voiture"),
            app_commands.Choice(name="Camion", value="Camion"),
            app_commands.Choice(name="Moto", value="Moto")
        ]
    )
    async def demandepermis(
        interaction: discord.Interaction,
        pseudo_roblox: str,
        categorie: app_commands.Choice[str],
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

        cursor.execute(
            """
            SELECT 1
            FROM permis
            WHERE pseudo_roblox = %s
            AND categorie = %s
            """,
            (pseudo_roblox, categorie.value)
        )

        permis_existant = cursor.fetchone()

        if permis_existant:
            await interaction.response.send_message(
                f"❌ Ce joueur possède déjà le permis {categorie.value}.",
                ephemeral=True
            )
            return

        embed = discord.Embed(
            title="📋 Résultat de l'examen du permis",
            color=0x2ecc71 if "obtenu" in statut else 0xe74c3c
        )

        embed.description = (
            f"**Pseudo Roblox**\n{pseudo_roblox}\n\n"
            f"**Nom :** {nom}\n"
            f"**Prénom :** {prenom}\n\n"
            f"**Date :** {date_obtention}\n"
            f"**Catégorie :** {categorie.value}\n\n"
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

        if "obtenu" in statut:

            cursor.execute("""
                INSERT INTO permis (
                    pseudo_roblox,
                    nom,
                    prenom,
                    date_obtention,
                    points,
                    categorie,
                    statut
                )
                VALUES (%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT (pseudo_roblox, categorie)
                DO UPDATE SET
                    nom = EXCLUDED.nom,
                    prenom = EXCLUDED.prenom,
                    date_obtention = EXCLUDED.date_obtention,
                    points = EXCLUDED.points,
                    categorie = EXCLUDED.categorie,
                    statut = EXCLUDED.statut
            """, (
                pseudo_roblox,
                nom,
                prenom,
                date_obtention,
                6,
                categorie.value,
                "Valide"
            ))

            conn.commit()

        await interaction.response.send_message(
            embed=embed
        )

    @tree.command(
        name="permis",
        description="Consulter un permis"
    )
    async def permis(
        interaction: discord.Interaction,
        pseudo_roblox: str
    ):

        cursor.execute(
            """
            SELECT
                nom,
                prenom,
                date_obtention,
                points,
                categorie,
                statut
            FROM permis
            WHERE pseudo_roblox = %s
            """,
            (pseudo_roblox,)
        )

        resultats = cursor.fetchall()

        if not resultats:
            await interaction.response.send_message(
                "❌ Aucun permis trouvé pour ce joueur.",
                ephemeral=True
            )
            return

        nom = resultats[0][0]
        prenom = resultats[0][1]
        points = resultats[0][3]
        statut = resultats[0][5]

        categories_text = ""

        for ligne in resultats:

            categorie = ligne[4]
            date = ligne[2]

            emoji = "📄"

            if categorie == "Voiture":
                emoji = "🚗"

            elif categorie == "Moto":
                emoji = "🏍️"

            elif categorie == "Camion":
                emoji = "🚛"

        categories_text += (
            f"{emoji} {categorie} - {date}\n"
        )

        embed = discord.Embed(
            title="📄 Permis de conduire",
            color=0x3498db
        )

        embed.description = (
            f"**Pseudo Roblox :** {pseudo_roblox}\n\n"
            f"**Nom :** {nom}\n"
            f"**Prénom :** {prenom}\n\n"
            f"**Permis obtenus :**\n"
            f"{categories_text}\n"
            f"**Points :** {points}/12\n"
            f"**Statut :** {statut}"
        )

        await interaction.response.send_message(
            embed=embed
        )
