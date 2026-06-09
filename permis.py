import discord
from discord import app_commands
from discord.ui import View, Button


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
        date_obtention: str,
        poteaux: int,
        trottoirs: int,
        feux_rouges: int,
        priorites: int,
        accidents: int
    ):

        await interaction.response.send_message(
            "🚧 Commande permis détectée.",
            ephemeral=True
        )
