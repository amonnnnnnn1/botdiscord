import os
import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import Button, View
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
LOG_CHANNEL_ID = int(os.getenv("LOG_CHANNEL_ID", 0))

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.messages = True

bot = commands.Bot(command_prefix="!", intents=intents)

class ConvertButton(Button):
    def __init__(self):
        super().__init__(label="Конвертировать", style=discord.ButtonStyle.primary, custom_id="convert_button")

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(ConvertModal())

class SellerConvertButton(Button):
    def __init__(self):
        super().__init__(label="Конвертация для продавцов", style=discord.ButtonStyle.success, custom_id="seller_convert_button")

    async def callback(self, interaction: discord.Interaction):
        if any(role.id == 1347656051331174490 for role in interaction.user.roles) or not interaction.user.roles:
            await interaction.response.send_message("У вас нет доступа к этой кнопке.", ephemeral=True)
            return

        await interaction.response.send_modal(SellerConvertModal())

        # Отправка в лог-канал
        log_channel = bot.get_channel(LOG_CHANNEL_ID)
        if log_channel:
            await log_channel.send(f"Пользователь {interaction.user.mention} нажал кнопку **Конвертация для продавцов**.")

class ExtraButton(Button):
    def __init__(self):
        super().__init__(label="Дополнительно", style=discord.ButtonStyle.secondary, custom_id="extra_button")

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_message("Здесь может быть дополнительная информация.", ephemeral=True)

class ConvertModal(discord.ui.Modal, title="Введите сумму"):
    amount = discord.ui.TextInput(label="Сумма в ₽", style=discord.TextStyle.short, required=True)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            amount_rub = float(self.amount.value)
            result = round(amount_rub / 1000 * 1.05, 2)
            await interaction.response.send_message(f"💱 **Конвертация:** {amount_rub} ₽ → {result} $\n(Комиссия: 1% + 5%)", ephemeral=True)
        except ValueError:
            await interaction.response.send_message("❌ Введите корректную сумму.", ephemeral=True)

class SellerConvertModal(discord.ui.Modal, title="Введите сумму для продавцов"):
    amount = discord.ui.TextInput(label="Сумма в ₽", style=discord.TextStyle.short, required=True)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            amount_rub = float(self.amount.value)
            result = round(amount_rub / 1000 * 1.10, 2)
            await interaction.response.send_message(f"💰 **Конвертация для продавцов:** {amount_rub} ₽ → {result} $\n(Итоговая комиссия: 10%)", ephemeral=True)
        except ValueError:
            await interaction.response.send_message("❌ Введите корректную сумму.", ephemeral=True)

@bot.event
async def on_ready():
    print(f"Бот запущен как {bot.user}")

@bot.command()
async def panelz(ctx):
    view = View()
    view.add_item(ConvertButton())
    view.add_item(SellerConvertButton())
    view.add_item(ExtraButton())

    await ctx.send("Нажмите кнопку ниже, чтобы ввести сумму и конвертировать.", view=view)
    await ctx.message.delete()

@bot.command()
async def panelzz(ctx):
    view = View()
    view.add_item(ConvertButton())
    view.add_item(SellerConvertButton())
    view.add_item(ExtraButton())

    embed = discord.Embed(
        title="💸 Курсы конвертации",
        description=(
            "**Курсы конвертации:**\n"
            "Меньше 1.999 ₽ — 2.000 $\n"
            "От 2.000 ₽ до 3.999 ₽ — 2.500 $\n"
            "От 4.000 ₽ до 5.999 ₽ — 3.000 $\n"
            "От 6.000 ₽ до 9.999 ₽ — 3.500 $\n"
            "От 10.000 ₽ и выше — 4.500 $\n\n"
            "Нажмите кнопку ниже, чтобы ввести сумму и конвертировать."
        ),
        color=discord.Color.blue()
    )

    await ctx.send(embed=embed, view=view)
    await ctx.message.delete()

bot.run(TOKEN)
