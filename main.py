import discord
from discord import ui
from discord.ext import commands
import os
import math
from datetime import datetime, timezone
from aiohttp import web
import asyncio

TOKEN = os.getenv("TOKEN")
LOG_CHANNEL_ID = int(os.getenv("LOG_CHANNEL_ID", "0"))
TICKET_CATEGORY_ID = int(os.getenv("TICKET_CATEGORY_ID", "0"))  # ID категории с тикетами

# --- Текст панели ---
PANEL_TEXT = (
    "**Курсы конвертации:**\n"
    "Меньше 1.999 ₽ — 2.000 $\n"
    "От 2.000 ₽ до 3.999 ₽ — 2.500 $\n"
    "От 4.000 ₽ до 5.999 ₽ — 3.000 $\n"
    "От 6.000 ₽ до 9.999 ₽ — 3.500 $\n"
    "От 10.000 ₽ и выше — 4.500 $\n\n"
    "Нажмите кнопку ниже, чтобы ввести сумму и конвертировать."
)

# --- Функции конвертации и форматирования ---

def round_to_tens(number: int) -> int:
    remainder = number % 10
    if remainder == 0:
        return number
    if remainder >= 5:
        return number + (10 - remainder)
    else:
        return number - remainder

def adjust_amount(amount: float) -> int:
    amount_int = math.ceil(amount)
    return round_to_tens(amount_int)

def get_rate(amount: int) -> int:
    if amount < 1999:
        return 2000
    elif amount < 4000:
        return 2500
    elif amount < 6000:
        return 3000
    elif amount < 10000:
        return 3500
    else:
        return 4500

def format_with_dots(number) -> str:
    if isinstance(number, float) and number.is_integer():
        number = int(number)
    return f"{number:,}".replace(",", ".")

# --- Модал конвертации ---

class ConvertModal(ui.Modal, title="Конвертация"):
    amount = ui.TextInput(label="Сумма (₽)", placeholder="Введите число")

    async def on_submit(self, interaction: discord.Interaction):
        try:
            raw_amount = float(self.amount.value)
            adjusted_amount = adjust_amount(raw_amount)
            rate = get_rate(adjusted_amount)
            result = adjusted_amount * rate
            commission = int(result * 0.01)
            total = result + commission

            raw_amount_clean = int(raw_amount) if raw_amount.is_integer() else raw_amount

            embed_user = discord.Embed(title="Итог конвертации:", color=0x2ecc71)
            embed_user.add_field(name="Сумма (₽)", value=f"{format_with_dots(raw_amount_clean)}₽", inline=False)
            embed_user.add_field(name="Округлено (₽)", value=f"{format_with_dots(adjusted_amount)}₽", inline=False)
            embed_user.add_field(name="Курс ($)", value=f"{format_with_dots(rate)}$", inline=False)
            embed_user.add_field(name="Результат ($ | ʊ)", value=f"{format_with_dots(result)}$", inline=False)
            embed_user.add_field(name="Комиссия 1% ($)", value=f"{format_with_dots(commission)}$", inline=False)
            embed_user.add_field(name="**Итоговая сумма ($)**", value=f"**{format_with_dots(total)}$**", inline=False)
            await interaction.response.send_message(embed=embed_user, ephemeral=True)

            log_channel = interaction.guild.get_channel(LOG_CHANNEL_ID)
            if log_channel:
                embed_log = discord.Embed(title="Лог конвертации:", color=0x3498db)
                timestamp = datetime.now(tz=timezone.utc)
                embed_log.add_field(name="Пользователь", value=str(interaction.user), inline=False)
                embed_log.timestamp = timestamp
                embed_log.add_field(name="Канал", value=interaction.channel.mention, inline=False)
                embed_log.add_field(name="Сумма (₽)", value=f"{format_with_dots(raw_amount_clean)}₽", inline=True)
                embed_log.add_field(name="Округлено (₽)", value=f"{format_with_dots(adjusted_amount)}₽", inline=True)
                embed_log.add_field(name="Курс ($)", value=f"{format_with_dots(rate)}$", inline=True)
                embed_log.add_field(name="Результат ($ | ʊ)", value=f"{format_with_dots(result)}$", inline=True)
                embed_log.add_field(name="Комиссия 1% ($)", value=f"{format_with_dots(commission)}$", inline=True)
                embed_log.add_field(name="Итоговая сумма ($)", value=f"{format_with_dots(total)}$", inline=True)
                await log_channel.send(embed=embed_log)

        except ValueError:
            await interaction.response.send_message("Ошибка: введите корректное число!", ephemeral=True)

# --- Кнопка и вью ---

class ConvertButton(ui.Button):
    def __init__(self):
        super().__init__(label="Конвертировать", style=discord.ButtonStyle.primary, custom_id="convert_btn")

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(ConvertModal())

class AdditionalButton(ui.Button):
    def __init__(self):
        super().__init__(label="Дополнительно", style=discord.ButtonStyle.secondary, custom_id="additional_btn")

    async def callback(self, interaction: discord.Interaction):
        additional_text = (
            "```"
            "Другое :\n\n"
            "Приоритетная очередь в тикете -> 300.000$ (Меньше 1.500 рублей), 700.000$ (Больше 1.500 рублей)\n"
            "Разбан в дискорде «ТП» -> 500.000$\n"
            "Снятие чс-доната и т.д. -> 400.000$\n"
            "Разбан в дискорде RPM -> цену узнавать у justlead"
            "```"
        )
        await interaction.response.send_message(additional_text, ephemeral=True)

class RatesView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(ConvertButton())
        self.add_item(AdditionalButton())

# --- Discord Bot Setup ---

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.command(name="panelz")
@commands.has_permissions(administrator=True)
async def panelz(ctx):
    await ctx.send(PANEL_TEXT, view=RatesView())
    await ctx.message.delete()

@bot.event
async def on_ready():
    bot.add_view(RatesView())
    print(f"Бот {bot.user} запущен и готов к работе!")

@bot.event
async def on_guild_channel_create(channel):
    if (
        isinstance(channel, discord.TextChannel)
        and channel.category_id == TICKET_CATEGORY_ID
    ):
        await asyncio.sleep(1)  # Ждём, чтобы TicketTool успел отправить своё сообщение
        try:
            await channel.send(PANEL_TEXT, view=RatesView())
        except Exception as e:
            print(f"Ошибка при отправке панели в канал {channel.name}: {e}")

# --- Webserver для Replit ---

async def handle(request):
    return web.Response(text="Бот работает!")

async def run_webserver():
    app = web.Application()
    app.add_routes([web.get('/', handle)])
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 8081))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    print(f"Веб-сервер запущен на порту {port}")

# --- Основная точка входа ---

async def main():
    await run_webserver()
    await bot.start(TOKEN)

if __name__ == "__main__":
    asyncio.run(main())
