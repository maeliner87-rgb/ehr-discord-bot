import discord
from discord import app_commands
import psycopg2
import os
import aiohttp
from discord.ui import View, Button
from datetime import datetime

intents = discord.Intents.default()

client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)
    
# Base de données
conn = psycopg2.connect(os.getenv("DATABASE_URL"))
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS identites (
    pseudo_discord TEXT,
    nom TEXT,
    prenom TEXT,
    naissance TEXT,
    ville_naissance TEXT,
    age TEXT,
    sexe TEXT,
    nationalite TEXT,
    pseudo_roblox TEXT PRIMARY KEY,
    salon_demande BIGINT,
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

class ValidationView(View):
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
            "UPDATE identites SET valide = 1 WHERE pseudo_roblox = %s",
            (self.pseudo_roblox,)
        )
        conn.commit()

        heure = datetime.now().strftime("%d/%m/%Y à %H:%M:%S")

        embed = interaction.message.embeds[0]

        embed.color = 0x2ecc71
        embed.title = "Carte d'identité acceptée"

        embed.add_field(
            name=" ",
            value=(
                "\n"
                f"**Acceptée par :** {interaction.user.mention}\n"
                f"**Date :** {heure}"
            ),
            inline=False
        )
        
        cursor.execute(
            "SELECT salon_demande FROM identites WHERE pseudo_roblox = %s",
            (self.pseudo_roblox,)
        )

        result = cursor.fetchone()

        if result:
            salon = client.get_channel(result[0])

            if salon:
                await salon.send(
                    f"La carte d'identité de **{self.pseudo_roblox}** a été acceptée."
                )

        await interaction.response.edit_message(
            embed=embed,
            view=None
        )

    async def refuser(self, interaction: discord.Interaction):
        cursor.execute(
            "SELECT salon_demande FROM identites WHERE pseudo_roblox = %s",
            (self.pseudo_roblox,)
        )

        result = cursor.fetchone()

        heure = datetime.now().strftime("%d/%m/%Y à %H:%M:%S")

        embed = interaction.message.embeds[0]

        embed.color = 0xe74c3c
        embed.title = "Carte d'identité refusée"

        embed.add_field(
            name=" ",
            value=(
                "\n"
                f"**Refusée par :** {interaction.user.mention}\n"
                f"**Date :** {heure}"
            ),
            inline=False
        )


        if result:
            salon = client.get_channel(result[0])

            if salon:
                await salon.send(
                    f"La carte d'identité de **{self.pseudo_roblox}** a été refusée."
                )

        cursor.execute(
            "DELETE FROM identites WHERE pseudo_roblox = %s",
            (self.pseudo_roblox,)
        )
        conn.commit()

        await interaction.response.edit_message(
            embed=embed,
            view=None
        )
class ListeIDView(View):
    def __init__(self, cartes):
        super().__init__(timeout=None)

        self.cartes = cartes
        self.page = 0
        self.par_page = 10

    def creer_embed(self):

        debut = self.page * self.par_page
        fin = debut + self.par_page

        cartes_page = self.cartes[debut:fin]

        embed = discord.Embed(
            title=f"📋 Liste des cartes d'identité ({self.page + 1}/{(len(self.cartes)-1)//self.par_page + 1})",
            color=0x3498db
        )

        description = ""

        for data in cartes_page:
            description += (
                f"• **{data[8]}** — {data[2]} {data[1]}\n"
            )

        embed.description = description

        return embed

    @discord.ui.button(label="⬅️", style=discord.ButtonStyle.grey)
    async def precedent(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        if self.page > 0:
            self.page -= 1

        await interaction.response.edit_message(
            embed=self.creer_embed(),
            view=self
        )

    @discord.ui.button(label="➡️", style=discord.ButtonStyle.grey)
    async def suivant(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        max_page = (len(self.cartes)-1)//self.par_page

        if self.page < max_page:
            self.page += 1

        await interaction.response.edit_message(
            embed=self.creer_embed(),
            view=self
        )        
@client.event
async def on_ready():

    await tree.sync()

    cursor.execute("SELECT COUNT(*) FROM identites")
    print("NB CARTES =", cursor.fetchone()[0])

    print(f"✅ Connecté en tant que {client.user}")


@tree.command(
    name="demandeid",
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

    salon_demande = interaction.channel.id

    user_data = await verifier_pseudo_roblox(pseudo_roblox)

    if user_data is None:
        await interaction.response.send_message(
            "❌ Ce pseudo Roblox n'existe pas.",
            ephemeral=True
        )
        return

    cursor.execute("""
    INSERT INTO identites (
        pseudo_discord,
        nom,
        prenom,
        naissance,
        ville_naissance,
        age,
        sexe,
        nationalite,
        pseudo_roblox,
        salon_demande,
        valide
    )
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    ON CONFLICT (pseudo_roblox)
    DO UPDATE SET
        pseudo_discord = EXCLUDED.pseudo_discord,
        nom = EXCLUDED.nom,
        prenom = EXCLUDED.prenom,
        naissance = EXCLUDED.naissance,
        ville_naissance = EXCLUDED.ville_naissance,
        age = EXCLUDED.age,
        sexe = EXCLUDED.sexe,
        nationalite = EXCLUDED.nationalite,
        salon_demande = EXCLUDED.salon_demande,
        valide = 0
    """, (
        str(interaction.user),
        nom,
        prenom,
        naissance,
        ville_naissance,
        age,
        sexe,
        nationalite,
        pseudo_roblox,
        salon_demande,
        0
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

    await salon.send(
        embed=embed_validation,
        view=ValidationView(pseudo_roblox)
    )

    await interaction.response.send_message(
        "Votre demande de carte d'identité a été envoyée pour validation.",
        ephemeral=True
    )


@tree.command(
    name="listeid",
    description="Afficher toutes les cartes d'identité"
)
async def listeid(interaction: discord.Interaction):

    cursor.execute(
        "SELECT * FROM identites WHERE valide = 1"
    )

    cartes = cursor.fetchall()

    if not cartes:
        await interaction.response.send_message(
            "Aucune carte d'identité trouvée."
        )
        return

    view = ListeIDView(cartes)

    await interaction.response.send_message(
        embed=view.creer_embed(),
        view=view
    )
@tree.command(
    name="supprimerid",
    description="Supprimer une carte d'identité"
)
async def supprimerid(
    interaction: discord.Interaction,
    pseudo_roblox: str
):

    cursor.execute(
        "SELECT * FROM identites WHERE pseudo_roblox = %s",
        (pseudo_roblox,)
    )

    data = cursor.fetchone()

    if not data:
        await interaction.response.send_message(
            "❌ Aucune carte d'identité trouvée.",
            ephemeral=True
        )
        return

    cursor.execute(
        "DELETE FROM identites WHERE pseudo_roblox = %s",
        (pseudo_roblox,)
    )
    conn.commit()

    await interaction.response.send_message(
        f"✅ La carte d'identité de **{pseudo_roblox}** a été supprimée.",
        ephemeral=True
    )

@tree.command(
    name="modifierid",
    description="Modifier une carte d'identité"
)
async def modifierid(
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

    cursor.execute(
        "SELECT * FROM identites WHERE pseudo_roblox = %s",
        (pseudo_roblox,)
    )

    if not cursor.fetchone():
        await interaction.response.send_message(
            "❌ Aucune carte d'identité trouvée.",
            ephemeral=True
        )
        return

    cursor.execute("""
        UPDATE identites
        SET
            nom = %s,
            prenom = %s,
            naissance = %s,
            ville_naissance = %s,
            age = %s,
            sexe = %s,
            nationalite = %s
        WHERE pseudo_roblox = %s
    """, (
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
        f"✅ La carte d'identité de **{pseudo_roblox}** a été modifiée.",
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
        "SELECT * FROM identites WHERE pseudo_roblox = %s",
        (pseudo_roblox,)
    )


    data = cursor.fetchone()

    if data and data[10] == 0:
        await interaction.response.send_message(
            "Cette carte d'identité est en attente de validation."
        )
        return

    user_data = await verifier_pseudo_roblox(pseudo_roblox)

    if user_data is None:
        await interaction.response.send_message(
            "Impossible de récupérer les informations Roblox."
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
            "Aucune carte d'identité trouvée."
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
