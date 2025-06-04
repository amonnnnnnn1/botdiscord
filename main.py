import discord
from discord import ui
from discord.ext import commands
import os
import math
from datetime import datetime, timezone
from aiohttp import web
import asyncio
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
LOG_CHANNEL_ID = int(os.getenv("LOG_CHANNEL_ID", "0"))
TICKET_CATEGORY_ID = int(os.getenv("TICKET_CATEGORY_ID", "0"))

# Роли, которые имеют доступ к конвертации для продавцов
ALLOWED_SELLER_ROLE_IDS = {
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

FORBIDDEN_ROLE_ID = 1347656051331174490  # Роль, которой запрещён доступ к кнопке для продавцов

PANEL_TEXT = (
    "**Курсы конвертации:**\n"
    "Меньше 1.999 ₽ - 2.000 $\n"
    "От 2.000 ₽ до 3.999 ₽ - 2.500 $\n"
    "От 4.000 ₽ до 5.999 ₽ - 3.000 $\n"
    "От 6.000 ₽ до 9.999 ₽ - 3.500 $\n"
    "От 10.000 ₽ и выше - 4.500 $\n\n"
    "Нажмите кнопку ниже, чтобы ввести сумму и конвертировать.\n\n"
    "> **ОФОРМЛЕНИЕ ЗАЯВКИ НА ПОКУПКУ ДОНАТА**\n"
    "> - Ваш ник:\n"
    "> - Интересующий донат:\n"
    "> - На каком сервере: (RPM WEST | RPM NORTH | BossHunt)\n"
    "> - Вид валюты для оплаты: (Валюта RPM WEST | Валюта RPM NORTH | Валюта BH)\n"
    "> - Пинг продавцов:\n\n"
    "```Подсказка по пингам:\n"
    "@Продавец | RPM WESNORT - продают донаты на всех серверах RPM и принимают все валюты серверов RPM.\n"
    "@Продавец | RPM WEST - продают донаты только на сервере RPM WEST и только за валюту сервера RPM WEST.\n"
    "@Продавец | RPM NORTH - продают донаты только на сервере RPM NORTH и только за валюту сервера RPM NORTH.\n"
    "@Продавец | BH - продают донаты только на сервере BossHunt и только за валюту сервера BossHunt.```"
)

OLD_PANEL_TEXT = (
    "**Курсы конвертации:**\n"
    "Меньше 1.999 ₽ - 2.000 $\n"
    "От 2.000 ₽ до 3.999 ₽ - 2.500 $\n"
    "От 4.000 ₽ до 5.999 ₽ - 3.000 $\n"
    "От 6.000 ₽ до 9.999 ₽ - 3.500 $\n"
    "От 10.000 ₽ и выше - 4.500 $\n\n"
    "Нажмите кнопку ниже, чтобы ввести сумму и конвертировать."
)

def round_to_tens(number: int) -> int:
    return number + (10 - number % 10) if number % 10 >= 5 else number - number % 10

def adjust_amount(amount: float) -> int:
    return round_to_tens(math.ceil(amount))

def get_rate(amount: int) -> int:
    if amount < 1999: return 2000
    if amount < 4000: return 2500
    if amount < 6000: return 3000
    if amount < 10000: return 3500
    return 4500

def format_with_dots(number) -> str:
    if isinstance(number, float) and number.is_integer():
        number = int(number)
    return f"{number:,}".replace(",", ".")

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
            total_commission = commission_1 + commission_5
            total = result + total_commission
            raw_clean = int(raw_amount) if raw_amount.is_integer() else raw_amount

            embed = discord.Embed(title="Итог конвертации:", color=0x2ecc71)
            embed.add_field(name="Сумма (₽)", value=f"{format_with_dots(raw_clean)}₽", inline=False)
            embed.add_field(name="Округлено (₽)", value=f"{format_with_dots(adjusted)}₽", inline=False)
            embed.add_field(name="Курс ($)", value=f"{format_with_dots(rate)}$", inline=False)
            embed.add_field(name="Результат ($ | ʊ)", value=f"{format_with_dots(result)}$", inline=False)
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
                log.add_field(name="Результат ($ | ʊ)", value=f"{format_with_dots(result)}$", inline=True)
                log.add_field(name="Комиссия 1% + 5% ($)", value=f"{format_with_dots(commission_1)}$ + {format_with_dots(commission_5)}$", inline=True)
                log.add_field(name="Итоговая сумма ($)", value=f"{format_with_dots(total)}$", inline=True)
                await log_channel.send(embed=log)

        except ValueError:
            await interaction.response.send_message("Ошибка: введите корректное число!", ephemeral=True)

class SellerConvertModal(ui.Modal, title="Конвертация для продавцов"):
    amount = ui.TextInput(label="Сумма (₽)", placeholder="Введите число")

    async def on_submit(self, interaction: discord.Interaction):
        try:
            # Проверка ролей
            member_roles = {role.id for role in interaction.user.roles}
            if FORBIDDEN_ROLE_ID in member_roles or len(member_roles) == 0 or not member_roles.intersection(ALLOWED_SELLER_ROLE_IDS):
                await interaction.response.send_message("❌ У вас нет доступа к этой конвертации.", ephemeral=True)
                return

            raw_amount = float(self.amount.value)
            adjusted = adjust_amount(raw_amount)
            rate = get_rate(adjusted)
            result = adjusted * rate
            commission_5a = int(result * 0.05)
            commission_5b = int(result * 0.05)
            total_commission = commission_5a + commission_5b
            raw_clean = int(raw_amount) if raw_amount.is_integer() else raw_amount

            embed = discord.Embed(title="Итог конвертации для продавцов:", color=0xe67e22)
            embed.add_field(name="Сумма (₽)", value=f"{format_with_dots(raw_clean)}₽", inline=False)
            embed.add_field(name="Округлено (₽)", value=f"{format_with_dots(adjusted)}₽", inline=False)
            embed.add_field(name="Курс ($)", value=f"{format_with_dots(rate)}$", inline=False)
            embed.add_field(name="Результат ($ | ʊ)", value=f"{format_with_dots(result)}$", inline=False)
            embed.add_field(name="**Итоговая комиссия (10%)**", value=f"**{format_with_dots(total_commission)}$**", inline=False)
            embed.add_field(name="\u200b", value="**Присылать комиссию на счёт -> 142153\nФотку отправленной комиссии отправьте в закрытый тикет**", inline=False)

            await interaction.response.send_message(embed=embed, ephemeral=True)

            log_channel = interaction.guild.get_channel(LOG_CHANNEL_ID)
            if log_channel:
                log = discord.Embed(title="Лог конвертации для продавцов:", color=0xe67e22, timestamp=datetime.now(timezone.utc))
                log.add_field(name="Пользователь", value=str(interaction.user), inline=False)
                log.add_field(name="Канал", value=interaction.channel.mention, inline=False)
                log.add_field(name="Сумма (₽)", value=f"{format_with_dots(raw_clean)}₽", inline=True)
                log.add_field(name="Округлено (₽)", value=f"{format_with_dots(adjusted)}₽", inline=True)
                log.add_field(name="Курс ($)", value=f"{format_with_dots(rate)}$", inline=True)
                log.add_field(name="Результат ($ | ʊ)", value=f"{format_with_dots(result)}$", inline=True)
                log.add_field(name="Итоговая комиссия (10%)", value=f"{format_with_dots(total_commission)}$", inline=True)
                await log_channel.send(embed=log)

        except ValueError:
            await interaction.response.send_message("Ошибка: введите корректное число!", ephemeral=True)

class PanelView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @ui.button(label="Конвертировать", style=discord.ButtonStyle.primary, custom_id="convert_button")
    async def convert_button(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.send_modal(ConvertModal())

    @ui.button(label="Конвертация для продавцов", style=discord.ButtonStyle.secondary, custom_id="seller_convert_button")
    async def seller_convert_button(self, interaction: discord.Interaction, button: ui.Button):
        member_roles = {role.id for role in interaction.user.roles}
        # Проверяем доступ
        if FORBIDDEN_ROLE_ID in member_roles or len(member_roles) == 0 or not member_roles.intersection(ALLOWED_SELLER_ROLE_IDS):
            await interaction.response.send_message("❌ У вас нет доступа к этой конвертации.", ephemeral=True)
            return
        await interaction.response.send_modal(SellerConvertModal())

    @ui.button(label="Дополнительно", style=discord.ButtonStyle.secondary, custom_id="additional_button")
    async def additional_button(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.send_message(PANEL_TEXT, ephemeral=True)

class OldPanelView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @ui.button(label="Конвертировать", style=discord.ButtonStyle.primary, custom_id="old_convert_button")
    async def old_convert_button(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.send_modal(ConvertModal())

    @ui.button(label="Дополнительно", style=discord.ButtonStyle.secondary, custom_id="old_additional_button")
    async def old_additional_button(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.send_message(OLD_PANEL_TEXT, ephemeral=True)

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Бот запущен как {bot.user}")

@bot.command()
async def panelz(ctx):
    """Отправляет обновленную панель с тремя кнопками и текстом"""
    await ctx.send(PANEL_TEXT, view=PanelView())

@bot.command()
async def panelzz(ctx):
    """Отправляет старую панель с двумя кнопками и старым текстом"""
    await ctx.send(OLD_PANEL_TEXT, view=OldPanelView())

bot.run(TOKEN)
