import discord
from discord.ext import commands
from discord import ui
import os

TOKEN = os.getenv("DISCORD_TOKEN")

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

FORBIDDEN_ROLE_ID = 1347656051331174490

LOG_CHANNEL_ID = 123456789012345678  # Твой ID лог-канала

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)


def format_money(amount):
    return f"{amount:,.0f}$".replace(",", ".")


class ConvertModal(ui.Modal, title="Конвертация"):

    amount = ui.TextInput(label="Введите сумму (₽)", placeholder="Например: 200000")

    async def on_submit(self, interaction: discord.Interaction):
        try:
            amount = float(self.amount.value.replace(",", "."))
        except:
            await interaction.response.send_message("Введите корректное число!", ephemeral=True)
            return

        commission_1 = amount * 0.01
        commission_5 = amount * 0.05
        total = amount + commission_1 + commission_5

        text = (
            "**Комиссия 1% + 5% ($):**\n"
            f"{format_money(commission_1)} + {format_money(commission_5)}\n\n"
            f"**Итоговая сумма:** {format_money(total)}"
        )

        await interaction.response.send_message(text, ephemeral=True)


class SellerConvertModal(ui.Modal, title="Конвертация для продавцов"):

    amount = ui.TextInput(label="Введите сумму (₽)", placeholder="Например: 200000")

    async def on_submit(self, interaction: discord.Interaction):
        try:
            amount = float(self.amount.value.replace(",", "."))
        except:
            await interaction.response.send_message("Введите корректное число!", ephemeral=True)
            return

        commission_10 = amount * 0.10

        text = (
            f"**Итоговая комиссия (10%):** {format_money(commission_10)}\n\n"
            f"**Присылать комиссию на счёт -> 142153**\n"
            f"**Фотку отправленной комиссии отправьте в закрытый тикет**"
        )

        await interaction.response.send_message(text, ephemeral=True)

        log_channel = bot.get_channel(LOG_CHANNEL_ID)
        if log_channel:
            await log_channel.send(
                f"Пользователь {interaction.user} выполнил конвертацию для продавцов.\n"
                f"Сумма: {format_money(amount)} ₽\n"
                f"Комиссия (10%): {format_money(commission_10)}"
            )


class ConvertButton(ui.Button):
    def __init__(self):
        super().__init__(label="Конвертировать", style=discord.ButtonStyle.green)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(ConvertModal())


class SellerConvertButton(ui.Button):
    def __init__(self):
        super().__init__(label="Конвертация для продавцов", style=discord.ButtonStyle.grey)

    async def callback(self, interaction: discord.Interaction):
        user_roles = {role.id for role in interaction.user.roles}

        # Проверка доступа
        has_allowed_role = len(user_roles.intersection(ALLOWED_SELLER_ROLE_IDS)) > 0
        if not has_allowed_role or FORBIDDEN_ROLE_ID in user_roles or len(interaction.user.roles) == 1:
            await interaction.response.send_message("У вас нет доступа к этой кнопке.", ephemeral=True)
            return

        await interaction.response.send_modal(SellerConvertModal())


class MoreButton(ui.Button):
    def __init__(self):
        super().__init__(label="Дополнительно", style=discord.ButtonStyle.grey)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_message("Дополнительно пока нет.", ephemeral=True)


class PanelView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        # Порядок кнопок: Конвертировать, Конвертация для продавцов, Дополнительно
        self.add_item(ConvertButton())
        self.add_item(SellerConvertButton())
        self.add_item(MoreButton())


@bot.command()
async def panelz(ctx):
    # Панель без строки Комиссия: 1% + 5%
    await ctx.send(
        "**Панель конвертации:**",
        view=PanelView()
    )


@bot.command()
async def panelzz(ctx):
    # Аналогично panelz, чтобы работала команда
    await ctx.send(
        "**Панель конвертации расширенная:**",
        view=PanelView()
    )


@bot.event
async def on_ready():
    print(f"Бот {bot.user} запущен!")


bot.run(TOKEN)
