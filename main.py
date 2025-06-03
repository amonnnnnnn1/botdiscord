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
BLOCKED_ROLE_ID = 1347656051331174490

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
            commission1 = int(result * 0.01)
            commission5 = int(result * 0.05)
            total = result + commission1 + commission5
            raw_clean = int(raw_amount) if raw_amount.is_integer() else raw_amount

            embed = discord.Embed(title="Итог конвертации:", color=0x2ecc71)
            embed.add_field(name="Сумма (₽)", value=f"{format_with_dots(raw_clean)}₽", inline=False)
            embed.add_field(name="Округлено (₽)", value=f"{format_with_dots(adjusted)}₽", inline=False)
            embed.add_field(name="Курс ($)", value=f"{format_with_dots(rate)}$", inline=False)
            embed.add_field(name="Результат ($ | ʊ)", value=f"{format_with_dots(result)}$", inline=False)
            embed.add_field(name="Комиссия 1% + 5% ($)", value=f"{format_with_dots(commission1)}$ + {format_with_dots(commission5)}$", inline=False)
            embed.add_field(name="**Итоговая сумма ($)**", value=f"**{format_with_dots(total)}$**", inline=False)
            await interaction.response.send_message(embed=embed, ephemeral=True)

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
            commission_total = int(result * 0.10)
            raw_clean = int(raw_amount) if raw_amount.is_integer() else raw_amount

            embed = discord.Embed(title="Конвертация для продавцов", color=0x95a5a6)
            embed.add_field(name="Сумма (₽)", value=f"{format_with_dots(raw_clean)}₽", inline=False)
            embed.add_field(name="Округлено (₽)", value=f"{format_with_dots(adjusted)}₽", inline=False)
            embed.add_field(name="Курс ($)", value=f"{format_with_dots(rate)}$", inline=False)
            embed.add_field(name="Результат ($ | ʊ)", value=f"{format_with_dots(result)}$", inline=False)
            embed.add_field(name="**Итоговая комиссия (10%)**", value=f"**{format_with_dots(commission_total)}$**", inline=False)
            embed.add_field(
                name="⠀",
                value="**Присылать комиссию на счёт -> 142153**\nФотку отправленной комиссии отправьте в закрытый тикет",
                inline=False
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

        except ValueError:
            await interaction.response.send_message("Ошибка: введите корректное число!", ephemeral=True)

class ConvertButton(ui.Button):
    def __init__(self):
        super().__init__(label="Конвертировать", style=discord.ButtonStyle.primary, custom_id="convert_btn")

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(ConvertModal())

class SellerConvertButton(ui.Button):
    def __init__(self):
        super().__init__(label="Конвертация для продавцов", style=discord.ButtonStyle.secondary, custom_id="seller_convert_btn")

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.get_role(BLOCKED_ROLE_ID) or interaction.user.guild_permissions.administrator is False:
            await interaction.response.send_message("У вас нет доступа к этой кнопке.", ephemeral=True)
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
        self.add_item(ConvertButton())
        self.add_item(SellerConvertButton())
        self.add_item(AdditionalButton())

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.command(name="panelz")
@commands.has_permissions(administrator=True)
async def panelz(ctx):
    view = RatesView()
    await ctx.send(PANEL_TEXT, view=view)
    await ctx.message.delete()

@bot.command(name="panelzz")
@commands.has_permissions(administrator=True)
async def panelzz(ctx):
    view = RatesView()
    await ctx.send(OLD_PANEL_TEXT, view=view)
    await ctx.message.delete()

@bot.event
async def on_ready():
    bot.add_view(RatesView())
    print(f"✅ Бот {bot.user} запущен и готов к работе!")

@bot.event
async def on_guild_channel_create(channel):
    if isinstance(channel, discord.TextChannel) and channel.category_id == TICKET_CATEGORY_ID:
        await asyncio.sleep(1)
        try:
            async for msg in channel.history(limit=5):
                if msg.author == bot.user and msg.content.startswith("**Курсы конвертации:**"):
                    return
            view = RatesView()
            await channel.send(PANEL_TEXT, view=view)
        except Exception as e:
            print(f"Ошибка при отправке панели: {e}")

async def handle(request):
    return web.Response(text="Бот работает!")

async def run_webserver():
    app = web.Application()
    app.add_routes([web.get('/', handle)])
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 10000))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    print(f"🌐 Веб-сервер слушает на порту {port}")

async def main():
    await run_webserver()
    print("🚀 Запускаю Discord-бота...")
    await bot.start(TOKEN)

if __name__ == "__main__":
    asyncio.run(main())
