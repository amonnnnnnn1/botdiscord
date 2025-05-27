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
TICKET_CATEGORY_ID = int(os.getenv("TICKET_CATEGORY_ID", "0"))

PANEL_TEXT = (
    "**Курсы конвертации:**\n"
    "Меньше 1.999 ₽ — 2.000 $\n"
    "От 2.000 ₽ до 3.999 ₽ — 2.500 $\n"
    "От 4.000 ₽ до 5.999 ₽ — 3.000 $\n"
    "От 6.000 ₽ до 9.999 ₽ — 3.500 $\n"
    "От 10.000 ₽ и выше — 4.500 $\\n\n"
    "Нажмите кнопку ниже, чтобы ввести сумму и конвертировать."
)

def round_to_tens(n: int) -> int:
    rem = n % 10
    return n if rem == 0 else (n + 10 - rem if rem >= 5 else n - rem)

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

def format_with_dots(num) -> str:
    # Поддержка int и float, убирает .0 для целых
    if isinstance(num, float) and num.is_integer():
        num = int(num)
    return f"{num:,}".replace(",", ".")

class ConvertModal(ui.Modal, title="Конвертация"):
    amount = ui.TextInput(label="Сумма (₽)", placeholder="Введите число")

    async def on_submit(self, interaction: discord.Interaction):
        try:
            raw = float(self.amount.value)
            adj = adjust_amount(raw)
            rate = get_rate(adj)
            result = adj * rate
            commission = int(result * 0.01)
            total = result + commission

            raw_display = int(raw) if raw.is_integer() else raw

            embed = discord.Embed(title="Итог конвертации:", color=0x2ecc71)
            embed.add_field(name="Сумма (₽)", value=f"{format_with_dots(raw_display)}₽", inline=False)
            embed.add_field(name="Округлено (₽)", value=f"{format_with_dots(adj)}₽", inline=False)
            embed.add_field(name="Курс ($)", value=f"{format_with_dots(rate)}$", inline=False)
            embed.add_field(name="Результат ($)", value=f"{format_with_dots(result)}$", inline=False)
            embed.add_field(name="Комиссия 1% ($)", value=f"{format_with_dots(commission)}$", inline=False)
            embed.add_field(name="Итог ($)", value=f"**{format_with_dots(total)}$**", inline=False)

            await interaction.response.send_message(embed=embed, ephemeral=True)

            log_channel = interaction.guild.get_channel(LOG_CHANNEL_ID)
            if log_channel:
                log_embed = discord.Embed(title="Лог конвертации", color=0x3498db, timestamp=datetime.now(tz=timezone.utc))
                log_embed.add_field(name="Пользователь", value=str(interaction.user), inline=False)
                log_embed.add_field(name="Канал", value=interaction.channel.mention, inline=False)
                log_embed.add_field(name="Сумма (₽)", value=f"{format_with_dots(raw_display)}₽", inline=True)
                log_embed.add_field(name="Округлено (₽)", value=f"{format_with_dots(adj)}₽", inline=True)
                log_embed.add_field(name="Курс ($)", value=f"{format_with_dots(rate)}$", inline=True)
                log_embed.add_field(name="Результат ($)", value=f"{format_with_dots(result)}$", inline=True)
                log_embed.add_field(name="Комиссия 1% ($)", value=f"{format_with_dots(commission)}$", inline=True)
                log_embed.add_field(name="Итог ($)", value=f"{format_with_dots(total)}$", inline=True)
                await log_channel.send(embed=log_embed)

        except ValueError:
            await interaction.response.send_message("Ошибка: введите корректное число!", ephemeral=True)

class ConvertButton(ui.Button):
    def __init__(self):
        super().__init__(label="Конвертировать", style=discord.ButtonStyle.primary, custom_id="convert_btn")

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(ConvertModal())

class AdditionalButton(ui.Button):
    def __init__(self):
        super().__init__(label="Дополнительно", style=discord.ButtonStyle.secondary, custom_id="additional_btn")

    async def callback(self, interaction: discord.Interaction):
        additional = (
            "```"
            "Другое :\n\n"
            "Приоритетная очередь в тикете -> 300.000$ (Меньше 1.500 рублей), 700.000$ (Больше 1.500 рублей)\n"
            "Разбан в дискорде «ТП» -> 500.000$\n"
            "Снятие чс-доната и т.д. -> 400.000$\n"
            "Разбан в дискорде RPM -> цену узнавать у justlead"
            "```"
        )
        await interaction.response.send_message(additional, ephemeral=True)

class RatesView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(ConvertButton())
        self.add_item(AdditionalButton())

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
    print(f"Бот {bot.user} запущен!")

@bot.event
async def on_guild_channel_create(channel):
    if isinstance(channel, discord.TextChannel) and channel.category_id == TICKET_CATEGORY_ID:
        await asyncio.sleep(1)
        try:
            await channel.send(PANEL_TEXT, view=RatesView())
        except Exception as e:
            print(f"Ошибка отправки панели в {channel.name}: {e}")

async def handle(request):
    return web.Response(text="Бот работает!")

async def run_webserver():
    app = web.Application()
    app.router.add_route('*', '/', handle)  # Принимаем все HTTP методы
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 8000))
    print(f"Запуск веб-сервера на порту {port}")
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()

async def main():
    await asyncio.gather(run_webserver(), bot.start(TOKEN))

if __name__ == "__main__":
    asyncio.run(main())
