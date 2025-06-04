import os
from dotenv import load_dotenv
load_dotenv()

import discord
from discord import ui
from discord.ext import commands
from datetime import datetime, timezone
import math

TOKEN = os.getenv("DISCORD_TOKEN")
LOG_CHANNEL_ID = int(os.getenv("LOG_CHANNEL_ID", "0"))

SELLER_ROLE_IDS = {
    1378693028415541363,
    1378774315683545180,
    1060540032944971936,
    1240036406366306314,
    1078988379171065856,
    1378693416585658478,
    1070069188581937202,
    1347660316263321713,
    1306688727179067523,
    1377349570006224996,
    1303338660183146496,
}

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

def format_with_dots(number) -> str:
    if isinstance(number, float) and number.is_integer():
        number = int(number)
    return f"{number:,}".replace(",", ".")

def round_to_tens(number: int) -> int:
    if number % 10 >= 5:
        return number + (10 - number % 10)
    else:
        return number - number % 10

def adjust_amount(amount: float) -> int:
    return round_to_tens(math.ceil(amount))

def get_rate(amount: int) -> int:
    if amount < 1999:
        return 2000
    if amount < 4000:
        return 2500
    if amount < 6000:
        return 3000
    if amount < 10000:
        return 3500
    return 4500

class ConvertModal(ui.Modal, title="Конвертация"):
    amount = ui.TextInput(label="Сумма (₽)", placeholder="Введите число")

    async def on_submit(self, interaction: discord.Interaction):
        try:
            raw_amount = float(self.amount.value)
            adjusted = adjust_amount(raw_amount)
            rate = get_rate(adjusted)
            result = adjusted * rate
            commission_1 = int(result * 0.01)
            commission_5 = int(result * 0.05)
            total = result + commission_1 + commission_5
            raw_clean = int(raw_amount) if raw_amount.is_integer() else raw_amount

            embed = discord.Embed(title="Итог конвертации:", color=0x2ecc71)
            embed.add_field(name="Сумма (₽)", value=f"{format_with_dots(raw_clean)}₽", inline=False)
            embed.add_field(name="Округлено (₽)", value=f"{format_with_dots(adjusted)}₽", inline=False)
            embed.add_field(name="Курс ($)", value=f"{format_with_dots(rate)}$", inline=False)
            embed.add_field(name="Результат ($)", value=f"{format_with_dots(result)}$", inline=False)
            embed.add_field(name="Комиссия 1% + 5% ($)", value=f"{format_with_dots(commission_1)}$ + {format_with_dots(commission_5)}$", inline=False)
            embed.add_field(name="**Итоговая сумма ($)**", value=f"**{format_with_dots(total)}$**", inline=False)

            await interaction.response.send_message(embed=embed, ephemeral=True)

            log_channel = interaction.guild.get_channel(LOG_CHANNEL_ID)
            if log_channel:
                log = discord.Embed(title="Лог конвертации:", color=0x3498db, timestamp=datetime.now(timezone.utc))
                log.add_field(name="Пользователь", value=str(interaction.user), inline=False)
                log.add_field(name="Канал", value=interaction.channel.mention, inline=False)
                log.add_field(name="Сумма (₽)", value=f"{format_with_dots(raw_clean)}₽", inline=True)
                log.add_field(name="Округлено (₽)", value=f"{format_with_dots(adjusted)}₽", inline=True)
                log.add_field(name="Курс ($)", value=f"{format_with_dots(rate)}$", inline=True)
                log.add_field(name="Результат ($)", value=f"{format_with_dots(result)}$", inline=True)
                log.add_field(name="Комиссия 1% + 5% ($)", value=f"{format_with_dots(commission_1)}$ + {format_with_dots(commission_5)}$", inline=True)
                log.add_field(name="Итоговая сумма ($)", value=f"{format_with_dots(total)}$", inline=True)
                await log_channel.send(embed=log)
        except ValueError:
            await interaction.response.send_message("Ошибка: введите корректное число!", ephemeral=True)

class SellerConvertModal(ui.Modal, title="Конвертация для продавцов"):
    amount = ui.TextInput(label="Сумма (₽)", placeholder="Введите число")

    async def on_submit(self, interaction: discord.Interaction):
        member = interaction.user
        if not any(role.id in SELLER_ROLE_IDS for role in member.roles):
            await interaction.response.send_message("❌ У вас нет доступа к этой конвертации.", ephemeral=True)
            return

        try:
            raw_amount = float(self.amount.value)
            adjusted = adjust_amount(raw_amount)
            rate = get_rate(adjusted)
            result = adjusted * rate
            commission_10 = int(result * 0.10)  # 10%
            raw_clean = int(raw_amount) if raw_amount.is_integer() else raw_amount

            embed = discord.Embed(title="Итог конвертации для продавцов:", color=0xe67e22)
            embed.add_field(name="Сумма (₽)", value=f"{format_with_dots(raw_clean)}₽", inline=False)
            embed.add_field(name="Округлено (₽)", value=f"{format_with_dots(adjusted)}₽", inline=False)
            embed.add_field(name="Курс ($)", value=f"{format_with_dots(rate)}$", inline=False)
            embed.add_field(name="Результат ($)", value=f"{format_with_dots(result)}$", inline=False)
            embed.add_field(name="Итоговая комиссия (10%)", value=f"{format_with_dots(commission_10)}$", inline=False)

            await interaction.response.send_message(embed=embed, ephemeral=True)

            log_channel = interaction.guild.get_channel(LOG_CHANNEL_ID)
            if log_channel:
                log = discord.Embed(title="Лог конвертации для продавцов:", color=0xe67e22, timestamp=datetime.now(timezone.utc))
                log.add_field(name="Пользователь", value=str(interaction.user), inline=False)
                log.add_field(name="Канал", value=interaction.channel.mention, inline=False)
                log.add_field(name="Сумма (₽)", value=f"{format_with_dots(raw_clean)}₽", inline=True)
                log.add_field(name="Округлено (₽)", value=f"{format_with_dots(adjusted)}₽", inline=True)
                log.add_field(name="Курс ($)", value=f"{format_with_dots(rate)}$", inline=True)
                log.add_field(name="Результат ($)", value=f"{format_with_dots(result)}$", inline=True)
                log.add_field(name="Итоговая комиссия (10%)", value=f"{format_with_dots(commission_10)}$", inline=True)
                await log_channel.send(embed=log)
        except ValueError:
            await interaction.response.send_message("Ошибка: введите корректное число!", ephemeral=True)

class ConvertButton(ui.Button):
    def __init__(self):
        super().__init__(label="Конвертировать", style=discord.ButtonStyle.primary, custom_id="convert_btn")

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(ConvertModal())

class SellerConvertButton(ui.Button):
    def __init__(self):
        # стиль такой же как у Дополнительно - secondary (серый)
        super().__init__(label="Конвертация для продавцов", style=discord.ButtonStyle.secondary, custom_id="seller_convert_btn")

    async def callback(self, interaction: discord.Interaction):
        member = interaction.user
        if not any(role.id in SELLER_ROLE_IDS for role in member.roles):
            await interaction.response.send_message("❌ У вас нет доступа к этой конвертации.", ephemeral=True)
            return
        await interaction.response.send_modal(SellerConvertModal())

class AdditionalButton(ui.Button):
    def __init__(self):
        super().__init__(label="Дополнительно", style=discord.ButtonStyle.secondary, custom_id="additional_btn")

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            "```Другое:\n\n"
            "Приоритетная очередь в тикете -> 300.000$ (< 1.500₽), 700.000$ (> 1.500₽)\n"
            "Разбан в дискорде «ТП» -> 500.000$\n"
            "Снятие чс-доната и т.д. -> 400.000$\n"
            "Разбан в дискорде RPM -> цену узнавать у justlead```",
            ephemeral=True
        )

class RatesView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        # Порядок кнопок: Конвертировать, Конвертация для продавцов, Дополнительно
        self.add_item(ConvertButton())
        self.add_item(SellerConvertButton())
        self.add_item(AdditionalButton())

@bot.command(name="panelz")
@commands.has_permissions(administrator=True)
async def panelz(ctx):
    # Удаляем команду пользователя сразу после вызова
    await ctx.message.delete()

    panel_text = (
        "**Курсы конвертации:**\n"
        "Меньше 1.999 ₽ — 2.000 $\n"
        "От 2.000 ₽ до 3.999 ₽ — 2.500 $\n"
        "От 4.000 ₽ до 5.999 ₽ — 3.000 $\n"
        "От 6.000 ₽ до 9.999 ₽ — 3.500 $\n"
        "От 10.000 ₽ и выше — 4.500 $\n\n"
        "Нажмите кнопку ниже, чтобы ввести сумму и конвертировать.\n\n"
        "> **ОФОРМЛЕНИЕ ЗАЯВКИ НА ПОКУПКУ ДОНАТА**\n"
        "> - Ваш ник:\n"
        "> - Интересующий донат:\n"
        "> - На каком сервере: (RPM WEST | RPM NORTH | BossHunt)\n"
        "> - Вид валюты для оплаты: (Валюта RPM WEST | Валюта RPM NORTH | Валюта BH)\n"
        "> - Пинг продавцов:\n"
    )
    await ctx.send(panel_text, view=RatesView())

@bot.command(name="panelzz")
@commands.has_permissions(administrator=True)
async def panelzz(ctx):
    # Удаляем команду пользователя сразу после вызова
    await ctx.message.delete()

    panel_text = (
        "**Курсы конвертации:**\n"
        "Меньше 1.999 ₽ — 2.000 $\n"
        "От 2.000 ₽ до 3.999 ₽ — 2.500 $\n"
        "От 4.000 ₽ до 5.999 ₽ — 3.000 $\n"
        "От 6.000 ₽ до 9.999 ₽ — 3.500 $\n"
        "От 10.000 ₽ и выше — 4.500 $\n\n"
        "Нажмите кнопку ниже, чтобы ввести сумму и конвертировать."
    )
    await ctx.send(panel_text, view=RatesView())

bot.run(TOKEN)
