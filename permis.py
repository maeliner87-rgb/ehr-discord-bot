import discord
from discord import app_commands
from discord.ui import View, Button
import psycopg2
import os

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
