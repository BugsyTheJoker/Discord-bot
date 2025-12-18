from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict

import discord
from discord import app_commands
from dotenv import load_dotenv

# ---------- Paths / config ----------
BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / ".env"
RESPONSES_PATH = BASE_DIR / "responses.json"

# Tving .env fra samme mappe som bot.py
load_dotenv(ENV_PATH)

TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID", "0"))

if not TOKEN:
    raise RuntimeError(
        "DISCORD_TOKEN mangler.\n"
        "Tjek at .env ligger i samme mappe som bot.py og indeholder:\n"
        "DISCORD_TOKEN=din_token_her\n"
        "Uden citationstegn og uden mellemrum omkring '='."
    )

# ---------- Defaults ----------
DEFAULT_RESPONSES: Dict[str, str] = {
    "lockpicks": (
        "Jeg kan ikke hjælpe med instruktioner til at fremstille lockpicks eller materialelister til det.\n"
        "Hvis du interesserer dig for lockpicking som hobby, så hold det lovligt: brug kun træningsudstyr, "
        "og øv kun på egne låse eller låse du har udtrykkelig tilladelse til."
    )
}

# ---------- Discord klient ----------
intents = discord.Intents.default()


class MyClient(discord.Client):
    def __init__(self) -> None:
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)
        self.responses: Dict[str, str] = {}

    def load_responses(self) -> None:
        """Load (or create) responses.json."""
        if not RESPONSES_PATH.exists():
            RESPONSES_PATH.write_text(
                json.dumps(DEFAULT_RESPONSES, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

        try:
            data = json.loads(RESPONSES_PATH.read_text(encoding="utf-8"))
            if not isinstance(data, dict):
                raise ValueError("responses.json skal være et JSON-objekt (dictionary).")
            # behold kun string værdier
            cleaned: Dict[str, str] = {}
            for k, v in data.items():
                if isinstance(k, str) and isinstance(v, str):
                    cleaned[k] = v
            if not cleaned:
                cleaned = DEFAULT_RESPONSES.copy()
            self.responses = cleaned
        except Exception:
            # fallback til standart hvis der er fejl
            self.responses = DEFAULT_RESPONSES.copy()

    def save_responses(self) -> None:
        RESPONSES_PATH.write_text(
            json.dumps(self.responses, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    async def setup_hook(self) -> None:
        # Indlæs svar ved opstart
        self.load_responses()

        # Synkroniser kommandoer til guild hvis GUILD_ID er sat, ellers globalt
        if GUILD_ID:
            guild = discord.Object(id=GUILD_ID)
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)
        else:
            await self.tree.sync()


client = MyClient()


# ---------- Hjælpere ----------
def is_admin(interaction: discord.Interaction) -> bool:
    """True if the user has Administrator permission in the guild."""
    if not interaction.guild or not isinstance(interaction.user, discord.Member):
        return False
    return interaction.user.guild_permissions.administrator


# ---------- Kommando ----------
@client.tree.command(
        name="lockpicks",
        description="Vis opskrift for Lockpicks"
)
async def lockpicks(interaction: discord.Interaction) -> None:
    msg = client.responses.get("lockpicks", "Ingen tekst sat for 'lockpicks' endnu.")
    await interaction.response.send_message(msg, ephemeral=True)


@client.tree.command(
        name="9mm",
        description="Vis opskrift for 9mm"
)
async def _9mm(interaction: discord.Interaction) -> None:
    msg = client.responses.get("9mm", "Ingen tekst sat for '9mm' endnu.")
    await interaction.response.send_message(msg, ephemeral=True)

@client.tree.command(
        name="vaskemaskine",
        description="Vis opskrift for Vaskemaskine"
)
async def vaskemaskine(interaction: discord.Interaction) -> None:
    msg = client.responses.get("vaskemaskine", "Ingen tekst sat for 'vaskemaskine' endnu.")
    await interaction.response.send_message(msg, ephemeral=True)

@client.tree.command(
        name="blæser",
        description="Vis opskrift for Blæser"
)
async def blæser(interaction: discord.Interaction) -> None:
    msg = client.responses.get("blæser", "Ingen tekst sat for 'blæser' endnu.")
    await interaction.response.send_message(msg, ephemeral=True)

@client.tree.command(
        name="vasketøjskurv",
        description="Vis opskrift for Vasketøjskurv"
)
async def vasketøjskurv(interaction: discord.Interaction) -> None:
    msg = client.responses.get("vasketøjskurv", "Ingen tekst sat for 'vasketøjskurv' endnu.")
    await interaction.response.send_message(msg, ephemeral=True)


@client.tree.command(
    name="crafting",
    description="Vis primære crafting lokation"
)
async def crafting(interaction: discord.Interaction) -> None:
    image_path = BASE_DIR / "parkeringcrafting.png"

    embed = discord.Embed(
        title="Primære crafting lokation",
        description="Her er vores primære lokation for crafting.",
    )

    if image_path.exists():
        file = discord.File(str(image_path), filename="parkeringcrafting.png")
        embed.set_image(url="attachment://parkeringcrafting.png")
        await interaction.response.send_message(
            embed=embed,
            file=file,
            ephemeral=True   # 👈 DETTE er forskellen
        )
    else:
        await interaction.response.send_message(
            "Her er lokation for primær crafting\n\n(Billedet mangler: parkeringcrafting.png)",
            ephemeral=True
        )
    

@client.tree.command(name="showtext", description="Vis teksten for en nøgle (fx lockpicks)")
@app_commands.describe(key="Nøglen i responses.json, fx lockpicks")
async def showtext(interaction: discord.Interaction, key: str) -> None:
    msg = client.responses.get(key)
    if msg is None:
        await interaction.response.send_message(f"Ukendt nøgle: `{key}`", ephemeral=True)
        return
    await interaction.response.send_message(f"**{key}:**\n{msg}", ephemeral=True)


@client.tree.command(name="settext", description="(Admin) Sæt/ændr tekst for en nøgle i responses.json")
@app_commands.describe(
    key="Nøglen der skal oprettes/ændres (fx lockpicks)",
    text="Teksten der skal gemmes"
)
async def settext(interaction: discord.Interaction, key: str, text: str) -> None:
    if not is_admin(interaction):
        await interaction.response.send_message("Kun admins kan bruge denne kommando.", ephemeral=True)
        return

    key = key.strip()
    if not key:
        await interaction.response.send_message("Key må ikke være tom.", ephemeral=True)
        return

    # Gem og skriv fil
    client.responses[key] = text
    client.save_responses()

    await interaction.response.send_message(
        f"Gemte tekst for `{key}` (responses.json opdateret).",
        ephemeral=True,
    )


@client.tree.command(name="reload", description="(Admin) Genindlæs responses.json uden at genstarte botten")
async def reload_cmd(interaction: discord.Interaction) -> None:
    if not is_admin(interaction):
        await interaction.response.send_message("Kun admins kan bruge denne kommando.", ephemeral=True)
        return

    client.load_responses()
    await interaction.response.send_message("Genindlæste responses.json ✅", ephemeral=True)


@client.tree.command(name="ping", description="Tjek at botten kører")
async def ping(interaction: discord.Interaction) -> None:
    await interaction.response.send_message("Pong ✅", ephemeral=True)


# ---------- Kør bot ----------
client.run(TOKEN)
