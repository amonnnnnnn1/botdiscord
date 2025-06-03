import discord
from discord import ui
from discord.ext import commands
import os
import math
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

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

# Твои исходные тексты для панелей (без изменений)
PANELZ_TEXT = (
    "**Курсы конвертации:**\n"
    "Меньше 1.999 ₽ - 2.000 $\n"
    "От 2.000 ₽ до 3.999 ₽ - 2.500 $\n"
    "От 4.000 ₽ до 5.999 ₽ - 3.000 $\n"
    "От 6.000 ₽ до 9.999 ₽ - 3.500 $\n"
    "От 10.000 ₽ и выше - 4.500 $\n\n"
    "Нажмите кнопку ниже, чтобы ввести сумму и конвертировать."
)

PANELZZ_TEXT = (
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

def round_to_tens(number: int) -> int:
    return number + (10 - number % 10) if number % 10 >= 5 else number - number % 10

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
            total_sum = result + total_commission
            raw_clean = int(raw_amount) if raw_amount.is_integer() else raw_amount

            embed = discord.Embed(title="Итог конвертации:", color=0x2ecc71)
            embed.add_field(name="Сумма (₽)", value=f"{format_with_dots(raw_clean)}₽", inline=False)
            embed.add_field(name="Округлено (₽)", value=f"{format_with_dots(adjusted)}₽", inline=False)
            embed.add_field(name="Курс ($)", value=f"{format_with_dots(rate)}$", inline=False)
            embed.add_field(name="Результат ($)", value=f"{format_with_dots(result)}$", inline=False)
            embed.add_field(name="Комиссия 1% + 5% ($)", value=f"{format_with_dots(commission_1)}$ + {format_with_dots(commission_5)}$", inline=False)
            embed.add_field(name="**Итоговая сумма ($)**", value=f"**{format_with_dots(total_sum)}$**", inline=False)

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
                log.add_field(name="Итоговая сумма ($)", value=f"{format_with_dots(total_sum)}$", inline=True)
                await log_channel.send(embed=log)

        except ValueError:
            await interaction.response.send_message("Ошибка: введите корректное число!", ephemeral=True)

class SellerConvertModal(ui.Modal, title="Конвертация для продавцов"):
    amount = ui.TextInput(label="Сумма (₽)", placeholder="Введите число")

    async def on_submit(self, interaction: discord.Interaction):
        try:
            raw_amount = float(self.amount.value)
            adjusted = adjust_amount(raw_amount)
            rate = get_rate(adjusted)
            result = adjusted * rate
            commission_5 = int(result * 0.05)
            commission_10 = commission_5 * 2  # 5% + 5% = 10%
            raw_clean = int(raw_amount) if raw_amount.is_integer() else raw_amount

            embed = discord.Embed(title="Итог конвертации (для продавцов):", color=0xe67e22)
            embed.add_field(name="Сумма (₽)", value=f"{format_with_dots(raw_clean)}₽", inline=False)
            embed.add_field(name="Округлено (₽)", value=f"{format_with_dots(adjusted)}₽", inline=False)
            embed.add_field(name="Курс ($)", value=f"{format_with_dots(rate)}$", inline=False)
            embed.add_field(name="Результат ($)", value=f"{format_with_dots(result)}$", inline=False)
            embed.add_field(name="Итоговая комиссия (10%) ($)", value=f"{format_with_dots(commission_10)}$", inline=False)
            embed.add_field(name="**Присылать комиссию на счёт -> 142153**", value="**Фотку отправленной комиссии отправьте в закрытый тикет**", inline=False)

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
                log.add_field(name="Итоговая комиссия (10%) ($)", value=f"{format_with_dots(commission_10)}$", inline=True)
                await log_channel.send(embed=log)

        except ValueError:
            await interaction.response.send_message("Ошибка: введите корректное число!", ephemeral=True)

class ConvertView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)

        # Порядок кнопок: Конвертировать, Конвертация для продавцов, Дополнительно
        self.add_item(ConvertButton())
        self.add_item(SellerConvertButton())
        self.add_item(MoreButton())

class ConvertButton(ui.Button):
    def __init__(self):
        super().__init__(label="Конвертировать", style=discord.ButtonStyle.green)

    async def callback(self, interaction: discord.Interaction):
        modal = ConvertModal()
        await interaction.response.send_modal(modal)

class SellerConvertButton(ui.Button):
    def __init__(self):
        # Цвет такой же, как у кнопки "Дополнительно"
        super().__init__(label="Конвертация для продавцов", style=discord.ButtonStyle.secondary)

    async def callback(self, interaction: discord.Interaction):
        user_roles = {role.id for role in interaction.user.roles}
        # Проверяем разрешённые роли
        if not user_roles.intersection(SELLER_ROLE_IDS):
            await interaction.response.send_message("У вас нет доступа к этой конвертации.", ephemeral=True)
            return
        modal = SellerConvertModal()
        await interaction.response.send_modal(modal)

class MoreButton(ui.Button):
    def __init__(self):
        super().__init__(label="Дополнительно", style=discord.ButtonStyle.secondary)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_message("Дополнительные функции скоро!", ephemeral=True)

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Бот {bot.user} готов к работе!")

@bot.command(name="panelz")
async def panelz(ctx):
    embed = discord.Embed(title="Панель конвертации", description=PANELZ_TEXT, color=0x3498db)
    await ctx.send(embed=embed, view=ConvertView())

@bot.command(name="panelzz")
async def panelzz(ctx):
    embed = discord.Embed(title="Панель конвертации (расширенная)", description=PANELZZ_TEXT, color=0x3498db)
    await ctx.send(embed=embed, view=ConvertView())

bot.run(TOKEN)
