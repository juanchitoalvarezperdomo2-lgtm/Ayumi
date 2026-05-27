import discord
from discord.ext import commands

intents = discord.Intents.all()
bot = commands.Bot(command_prefix=",", intents=intents, help_command=None)

# ================= CONFIG =================
VERIFIED_ROLE = "Verified"
MUTED_ROLE = "Muted"
TICKET_CATEGORY = "Tickets"
VERIFY_LOG_CHANNEL = "verification-logs"

STAFF_ROLES = ["Senior Moderator", "Developer", "Helper", "Moderator"]
HB_ALLOWED_ROLES = ["Developer", "."]

# ================= MEMORY =================
jail_backup = {}
warn_data = {}


# ================= CHECKS =================
def is_staff(member: discord.Member):
    return any(discord.utils.get(member.roles, name=r) for r in STAFF_ROLES)


def can_hb(member: discord.Member):
    return any(discord.utils.get(member.roles, name=r) for r in HB_ALLOWED_ROLES)


def is_verified(member: discord.Member):
    return discord.utils.get(member.roles, name=VERIFIED_ROLE) is not None


def no_perm_embed():
    return discord.Embed(
        title="⛔ ACCESS DENIED",
        description="You need permissions to use this command.",
        color=0xff0000
    )


# ================= SAY COMMAND (PRO) =================
@bot.command()
async def say(ctx, *, message=None):

    if message is None:
        return await ctx.send("Uso: ,say mensaje")

    try:
        await ctx.message.delete()
    except:
        pass

    embed = discord.Embed(
        title="📢 ANNOUNCEMENT",
        description=message,
        color=0x00ffcc
    )

    embed.set_author(
        name=f"Mensaje de {ctx.author.name}",
        icon_url=ctx.author.display_avatar.url
    )

    embed.set_footer(text="Sistema oficial del servidor")

    await ctx.send(embed=embed)


# ================= VERIFY =================
class VerifyModal(discord.ui.Modal):
    def __init__(self):
        super().__init__(title="📋 Verificación")

        self.edad = discord.ui.TextInput(label="Edad")
        self.roblox = discord.ui.TextInput(label="Roblox")
        self.stats = discord.ui.TextInput(label="Stats")
        self.discord_user = discord.ui.TextInput(label="Discord")
        self.como = discord.ui.TextInput(label="Cómo nos conociste")

        self.add_item(self.edad)
        self.add_item(self.roblox)
        self.add_item(self.stats)
        self.add_item(self.discord_user)
        self.add_item(self.como)

    async def on_submit(self, interaction: discord.Interaction):

        role = discord.utils.get(interaction.guild.roles, name=VERIFIED_ROLE)
        if role:
            await interaction.user.add_roles(role)

        log = discord.utils.get(interaction.guild.text_channels, name=VERIFY_LOG_CHANNEL)

        embed = discord.Embed(title="📥 Verificación", color=0x00ffcc)
        embed.add_field(name="Usuario", value=interaction.user.mention, inline=False)

        if log:
            await log.send(embed=embed)

        await interaction.response.send_message("✅ Verificado", ephemeral=True)


class VerifyView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="VERIFICAR", style=discord.ButtonStyle.success)
    async def verify(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(VerifyModal())


# ================= TICKETS =================
class TicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="RECLAMAR", style=discord.ButtonStyle.success)
    async def claim(self, interaction: discord.Interaction, button: discord.ui.Button):

        if not is_staff(interaction.user):
            return await interaction.response.send_message(embed=no_perm_embed(), ephemeral=True)

        await interaction.response.send_message(f"📌 Reclamado por {interaction.user.mention}")

    @discord.ui.button(label="CERRAR", style=discord.ButtonStyle.danger)
    async def close(self, interaction: discord.Interaction, button: discord.ui.Button):

        if not is_staff(interaction.user):
            return await interaction.response.send_message(embed=no_perm_embed(), ephemeral=True)

        await interaction.response.send_message("🔒 Cerrando ticket...")
        await interaction.channel.delete()


# ================= SETUP VERIFY =================
@bot.command()
async def setupverify(ctx):

    embed = discord.Embed(
        title="🔽 VERIFICACIÓN 🔽",
        description="Presiona el botón para verificarte",
        color=0x00ffcc
    )

    view = discord.ui.View()

    button = discord.ui.Button(label="VERIFICAR", style=discord.ButtonStyle.success)

    async def cb(i: discord.Interaction):
        await i.response.send_modal(VerifyModal())

    button.callback = cb
    view.add_item(button)

    await ctx.send(embed=embed, view=view)


# ================= SETUP TICKETS =================
@bot.command()
async def setup(ctx):

    embed = discord.Embed(
        title="🎫 SISTEMA DE REPORTES",
        description="Reporta jugadores sospechosos.\nCREA TU TICKET ABAJO 👇",
        color=0x00ffcc
    )

    view = discord.ui.View()

    button = discord.ui.Button(label="CREAR TICKET", style=discord.ButtonStyle.primary)

    async def create(i: discord.Interaction):

        category = discord.utils.get(i.guild.categories, name=TICKET_CATEGORY)

        overwrites = {
            i.guild.default_role: discord.PermissionOverwrite(view_channel=False),
            i.user: discord.PermissionOverwrite(view_channel=True, send_messages=True)
        }

        for r in STAFF_ROLES:
            role = discord.utils.get(i.guild.roles, name=r)
            if role:
                overwrites[role] = discord.PermissionOverwrite(view_channel=True)

        channel = await i.guild.create_text_channel(
            name=f"ticket-{i.user.name}",
            category=category,
            overwrites=overwrites
        )

        embed = discord.Embed(
            title="🎫 Ticket abierto",
            description="Nuestro staff te atenderá pronto.\n• Razón\n• Evidencia",
            color=0x00ffcc
        )

        await channel.send(content=i.user.mention, embed=embed, view=TicketView())

        await i.response.send_message(f"✅ Ticket creado: {channel.mention}", ephemeral=True)

    button.callback = create
    view.add_item(button)

    await ctx.send(embed=embed, view=view)


# ================= PURGE =================
@bot.command()
async def purge(ctx):

    if not is_staff(ctx.author):
        return await ctx.send(embed=no_perm_embed())

    ch = ctx.channel
    name = ch.name
    category = ch.category
    overwrites = ch.overwrites

    await ch.delete()

    new = await ctx.guild.create_text_channel(
        name=name,
        category=category,
        overwrites=overwrites
    )

    await new.send("FIRST")


# ================= HARD BAN =================
@bot.command(aliases=["hardban"])
async def hb(ctx, member: discord.Member = None, *, reason=None):

    if not can_hb(ctx.author):
        return await ctx.send(embed=no_perm_embed())

    if member is None:
        return await ctx.send("Uso: ,hb @user razón")

    await member.ban(reason=reason or "Sin razón")

    await ctx.message.add_reaction("✅")
    await ctx.message.add_reaction("👍")

    await ctx.send(f"🚫 HB: {member} | ID: {member.id}")


# ================= LOCK / UNLOCK =================
@bot.command()
async def lock(ctx):

    if not is_staff(ctx.author):
        return await ctx.send(embed=no_perm_embed())

    overwrite = ctx.channel.overwrites_for(ctx.guild.default_role)
    overwrite.send_messages = False

    await ctx.channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)

    await ctx.message.add_reaction("🔒")


@bot.command()
async def unlock(ctx):

    if not is_staff(ctx.author):
        return await ctx.send(embed=no_perm_embed())

    overwrite = ctx.channel.overwrites_for(ctx.guild.default_role)
    overwrite.send_messages = True

    await ctx.channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)

    await ctx.message.add_reaction("🔓")


# ================= MUTE =================
@bot.command()
async def mute(ctx, member: discord.Member):

    if not is_staff(ctx.author):
        return await ctx.send(embed=no_perm_embed())

    if is_verified(member):
        return await ctx.send("❌ No puedes mutear Verified")

    role = discord.utils.get(ctx.guild.roles, name=MUTED_ROLE)
    if role:
        await member.add_roles(role)

    await ctx.message.add_reaction("🔇")


@bot.command()
async def unmute(ctx, member: discord.Member):

    if not is_staff(ctx.author):
        return await ctx.send(embed=no_perm_embed())

    role = discord.utils.get(ctx.guild.roles, name=MUTED_ROLE)
    if role:
        await member.remove_roles(role)

    await ctx.message.add_reaction("🔊")


# ================= JAIL =================
@bot.command()
async def jail(ctx, member: discord.Member, *, reason=None):

    if not is_staff(ctx.author):
        return await ctx.send(embed=no_perm_embed())

    jail_role = discord.utils.get(ctx.guild.roles, name="jail")

    jail_backup[member.id] = [r for r in member.roles if r != ctx.guild.default_role]

    await member.edit(roles=[jail_role])

    await ctx.message.add_reaction("🔒")


@bot.command()
async def unjail(ctx, member: discord.Member):

    if not is_staff(ctx.author):
        return await ctx.send(embed=no_perm_embed())

    jail_role = discord.utils.get(ctx.guild.roles, name="jail")

    await member.remove_roles(jail_role)

    roles = jail_backup.get(member.id)
    if roles:
        await member.edit(roles=roles)
        jail_backup.pop(member.id)

    await ctx.message.add_reaction("🔓")


# ================= WARN SYSTEM =================
@bot.command()
async def warn(ctx, member: discord.Member, *, reason=None):

    if not is_staff(ctx.author):
        return await ctx.send(embed=no_perm_embed())

    warn_data.setdefault(member.id, []).append({
        "reason": reason or "Sin razón",
        "mod": ctx.author.name
    })

    embed = discord.Embed(title="⚠ USER WARNED", color=0xffa500)
    embed.add_field(name="User", value=member.mention)
    embed.add_field(name="Reason", value=reason)
    embed.add_field(name="Moderator", value=ctx.author.mention)

    await ctx.send(embed=embed)


@bot.command()
async def warns(ctx, member: discord.Member):

    data = warn_data.get(member.id, [])

    embed = discord.Embed(title="📋 WARNS", color=0xffcc00)

    if not data:
        embed.description = "No warns"
    else:
        text = "\n".join([f"{i+1}. {w['reason']} ({w['mod']})" for i, w in enumerate(data)])
        embed.description = text

    await ctx.send(embed=embed)


# ================= COMMANDS =================
@bot.command(name="commands")
async def commands_cmd(ctx):

    embed = discord.Embed(title="📜 COMMAND LIST", color=0x00ffcc)

    embed.add_field(name=",setupverify", value="Verify")
    embed.add_field(name=",setup", value="Tickets")
    embed.add_field(name=",purge", value="Reset channel")
    embed.add_field(name=",hb", value="Hardban")
    embed.add_field(name=",lock / ,unlock", value="Channel lock")
    embed.add_field(name=",mute / ,unmute", value="Mute")
    embed.add_field(name=",jail / ,unjail", value="Jail")
    embed.add_field(name=",warn / ,warns", value="Warn system")
    embed.add_field(name=",say", value="Bot speaks")

    await ctx.send(embed=embed)


# ================= RUN =================
bot.run("")
