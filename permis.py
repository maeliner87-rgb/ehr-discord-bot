import discord
from discord import app_commands
from datetime import datetime
from discord.ui import View, Button

def setup_permis(tree, client, conn, cursor):

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS permis (
        pseudo_roblox TEXT,
        nom TEXT,
        prenom TEXT,
        date_obtention TEXT,
        points INTEGER,
        dernier_gain TEXT,
        categorie TEXT,
        statut TEXT,
        salon_demande BIGINT,
        valide INTEGER DEFAULT 0,
        PRIMARY KEY (pseudo_roblox, categorie)
    )
    """)
    conn.commit()

    cursor.execute("""
    ALTER TABLE permis
    ADD COLUMN IF NOT EXISTS dernier_gain TEXT
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
            statut = "Refusé"
            raison = "Accident durant l'examen"

        elif feux_rouges >= 2:
            statut = "Refusé"
            raison = "Trop de feux rouges grillés"

        elif note >= 12:
            statut = "Permis obtenu"
            raison = None

        else:
            statut = "Refusé"
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
            SELECT statut
            FROM permis
            WHERE pseudo_roblox = %s
            AND categorie = %s
            """,
            (
                pseudo_roblox,
                categorie.value
            )
        )

        permis_existant = cursor.fetchone()

        if permis_existant:

            if permis_existant[0] == "Interdit de conduire":
                await interaction.response.send_message(
                    "❌ Ce joueur est interdit de conduire.",
                    ephemeral=True
                )
                return

            if permis_existant[0] != "Suspendu":
                await interaction.response.send_message(
                    f"Ce joueur possède déjà le permis {categorie.value}.",
                    ephemeral=True
                )
                return

            cursor.execute(
                """
                DELETE FROM permis
                WHERE pseudo_roblox = %s
                AND categorie = %s
                """,
                (
                    pseudo_roblox,
                    categorie.value
                )
            )

            conn.commit()

        embed = discord.Embed(
            title="Résultat de l'examen du permis",
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
                    dernier_gain,
                    categorie,
                    statut
                )
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT (pseudo_roblox, categorie)
                DO UPDATE SET
                    nom = EXCLUDED.nom,
                    prenom = EXCLUDED.prenom,
                    date_obtention = EXCLUDED.date_obtention,
                    points = EXCLUDED.points,
                    dernier_gain = EXCLUDED.dernier_gain,
                    categorie = EXCLUDED.categorie,
                    statut = EXCLUDED.statut
            """, (
                pseudo_roblox,
                nom,
                prenom,
                date_obtention,
                6,
                date_obtention,
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

        # SYSTEME DE RECUPERATION DES POINTS

        for ligne in resultats:

            points = ligne[3]

            cursor.execute(
                """
                SELECT dernier_gain
                FROM permis
                WHERE pseudo_roblox = %s
                AND categorie = %s
                """,
                (pseudo_roblox, ligne[4])
            )

            dernier_gain = cursor.fetchone()[0]

            if dernier_gain:

                derniere_date = datetime.strptime(
                    dernier_gain,
                    "%d/%m/%Y"
                )

                aujourd_hui = datetime.now()

                jours = (
                    aujourd_hui - derniere_date
                ).days

                points_a_gagner = jours // 7

                if points_a_gagner > 0:

                    nouveaux_points = min(
                        points + points_a_gagner,
                        12
                    )

                    cursor.execute(
                        """
                        UPDATE permis
                        SET points = %s,
                            dernier_gain = %s
                        WHERE pseudo_roblox = %s
                        AND categorie = %s
                        """,
                        (
                            nouveaux_points,
                            aujourd_hui.strftime("%d/%m/%Y"),
                            pseudo_roblox,
                            ligne[4]
                        )
                    )

        conn.commit()

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
                "Aucun permis trouvé pour ce joueur.",
                ephemeral=True
            )
            return

        nom = resultats[0][0]
        prenom = resultats[0][1]

        categories_text = ""

        for ligne in resultats:

            categorie = ligne[4]
            points = ligne[3]
            statut = ligne[5]

            if categorie == "Voiture":
                emoji = "🚗"

            elif categorie == "Moto":
                emoji = "🏍️"

            elif categorie == "Camion":
                emoji = "🚛"

            else:
                emoji = "📄"

            if statut == "Suspendu":

                categories_text += (
                    f"{emoji} {categorie} - 🔴 Suspendu\n"
                )

            elif statut == "Interdit de conduire":

                categories_text += (
                    f"{emoji} {categorie} - ⛔ Interdit de conduire\n"
                )

            else:

                categories_text += (
                    f"{emoji} {categorie} - {points}/12 points\n"
                )

        embed = discord.Embed(
            title="📄 Permis de conduire",
            color=0x3498db
        )

        embed.description = (
            f"**Pseudo Roblox :** {pseudo_roblox}\n\n"
            f"**Nom :** {nom}\n"
            f"**Prénom :** {prenom}\n\n"
            f"**Permis :**\n"
            f"{categories_text}"
        )

        await interaction.response.send_message(
            embed=embed
        )

    class PermisListeView(View):

        def __init__(self, donnees):
            super().__init__(timeout=300)

            self.donnees = donnees
            self.page = 0
            self.par_page = 5

        def creer_embed(self):

            debut = self.page * self.par_page
            fin = debut + self.par_page

            embed = discord.Embed(
                title="📋 Liste des permis",
                color=0x3498db
            )

            texte = ""

            for i, ligne in enumerate(
                self.donnees[debut:fin],
                start=debut + 1
            ):

                pseudo = ligne[0]
                nom = ligne[1]
                prenom = ligne[2]
                points = ligne[3]
                categories = ligne[4]

                texte += (
                    f"**{i}. {pseudo}**\n"
                    f"Nom : {nom}\n"
                    f"Prénom : {prenom}\n"
                    f"Permis : {categories}\n"
                    f"Points : {points}/12\n\n"
                )

            embed.description = texte

            total_pages = (
                len(self.donnees) - 1
            ) // self.par_page + 1

            embed.set_footer(
                text=f"Page {self.page + 1}/{total_pages}"
            )

            return embed

        @discord.ui.button(label="⬅️")
        async def precedent(
            self,
            interaction: discord.Interaction,
            button: Button
        ):

            if self.page > 0:
                self.page -= 1

            await interaction.response.edit_message(
                embed=self.creer_embed(),
                view=self
            )

        @discord.ui.button(label="➡️")
        async def suivant(
            self,
            interaction: discord.Interaction,
            button: Button
        ):

            total_pages = (
                len(self.donnees) - 1
            ) // self.par_page

            if self.page < total_pages:
                self.page += 1

            await interaction.response.edit_message(
                embed=self.creer_embed(),
                view=self
            )

    @tree.command(
        name="listepermis",
        description="Afficher tous les permis"
    )
    async def listepermis(
        interaction: discord.Interaction
    ):

        cursor.execute("""
            SELECT
                pseudo_roblox,
                nom,
                prenom,
                MAX(points),
                STRING_AGG(categorie, ', ')
            FROM permis
            GROUP BY
                pseudo_roblox,
                nom,
                prenom
            ORDER BY nom
        """)

        donnees = cursor.fetchall()

        if not donnees:
            await interaction.response.send_message(
                "Aucun permis enregistré."
            )
            return

        view = PermisListeView(donnees)

        await interaction.response.send_message(
            embed=view.creer_embed(),
            view=view
        )

    @tree.command(
        name="supprimerpermis",
        description="Supprimer un permis"
    )
    @app_commands.choices(
        categorie=[
            app_commands.Choice(
                name="Voiture",
                value="Voiture"
            ),
            app_commands.Choice(
                name="Camion",
                value="Camion"
            ),
            app_commands.Choice(
                name="Moto",
                value="Moto"
            )
        ]
    )
    async def supprimerpermis(
        interaction: discord.Interaction,
        pseudo_roblox: str,
        categorie: app_commands.Choice[str]
    ):

        cursor.execute(
            """
            DELETE FROM permis
            WHERE pseudo_roblox = %s
            AND categorie = %s
            """,
            (
                pseudo_roblox,
                categorie.value
            )
        )

        conn.commit()

        await interaction.response.send_message(
            f"✅ Le permis {categorie.value} de **{pseudo_roblox}** a été supprimé."
        )

    @tree.command(
        name="sanctionpermis",
        description="Sanctionner un permis"
    )
    @app_commands.choices(
        categorie=[
            app_commands.Choice(
                name="Voiture",
                value="Voiture"
            ),
            app_commands.Choice(
                name="Camion",
                value="Camion"
            ),
            app_commands.Choice(
                name="Moto",
                value="Moto"
            )
        ],
        sanction=[
            app_commands.Choice(
                name="Retrait de points",
                value="Retrait de points"
            ),
            app_commands.Choice(
                name="Suspension",
                value="Suspendu"
            ),
            app_commands.Choice(
                name="Interdiction de conduire",
                value="Interdit de conduire"
            )
        ]
    )
    async def sanctionpermis(
        interaction: discord.Interaction,
        pseudo_roblox: str,
        categorie: app_commands.Choice[str],
        sanction: app_commands.Choice[str],
        motif: str,
        points: int = 0
    ):

        cursor.execute(
            """
            SELECT points, statut
            FROM permis
            WHERE pseudo_roblox = %s
            AND categorie = %s
            """,
            (
                pseudo_roblox,
                categorie.value
            )
        )

        permis = cursor.fetchone()

        if not permis:
            await interaction.response.send_message(
                "Aucun permis trouvé.",
                ephemeral=True
            )
            return

        points_actuels = permis[0]

        if sanction.value == "Retrait de points":

            nouveaux_points = max(
                points_actuels - points,
                0
            )

            statut = (
                "Suspendu"
                if nouveaux_points == 0
                else "Valide"
            )

            cursor.execute(
                """
                UPDATE permis
                SET points = %s,
                    statut = %s
                WHERE pseudo_roblox = %s
                AND categorie = %s
                """,
                (
                    nouveaux_points,
                    statut,
                    pseudo_roblox,
                    categorie.value
                )
            )

            texte_sanction = (
                f"Retrait de {points} point(s)\n"
                f"Points restants : {nouveaux_points}/12"
            )

            if nouveaux_points == 0:
                texte_sanction += (
                    "\n⚠️ Le permis est désormais suspendu."
                )

        else:

            cursor.execute(
                """
                UPDATE permis
                SET statut = %s
                WHERE pseudo_roblox = %s
                AND categorie = %s
                """,
                (
                    sanction.value,
                    pseudo_roblox,
                    categorie.value
                )
            )

            texte_sanction = sanction.value

        conn.commit()

        salon = client.get_channel(
            1513017794214498414
        )

        if salon:

            embed = discord.Embed(
                title="🚔 Sanction de permis",
                color=0xe74c3c
            )

            embed.description = (
                f"**Pseudo Roblox :** {pseudo_roblox}\n"
                f"**Catégorie :** {categorie.value}\n\n"
                f"**Sanction :**\n"
                f"{texte_sanction}\n\n"
                f"**Motif :**\n"
                f"{motif}\n\n"
                f"**Agent :** {interaction.user.mention}"
            )

            await salon.send(
                embed=embed
            )

        await interaction.response.send_message(
            "✅ Sanction appliquée."
        )
