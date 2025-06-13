import discord
from discord.ext import commands
from discord import app_commands
import os
from dotenv import load_dotenv
import string

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree 

games = {}

# Wordle feedback
def feedback(guess, answer):
    result = []
    answer_chars = list(answer)
    for i in range(len(guess)):
        if guess[i] == answer[i]:
            result.append("\U0001f7e9")  # → ⬛
            answer_chars[i] = None
        else:
            result.append(None)
    for i in range(len(guess)):
        if result[i] is None:
            if guess[i] in answer_chars:
                result[i] = "\U0001f7e8"
                answer_chars[answer_chars.index(guess[i])] = None
            else:
                result[i] = "\u2b1b"
    return "".join(result)

# 鍵盤樣式顯示
def render_keyboard(correct, present, wrong):
    def style(ch):
        if ch in correct:
            return f"\U0001f7e9{ch}"
        elif ch in present:
            return f"\U0001f7e8{ch}"
        elif ch in wrong:
            return f"\u2b1b{ch}"
        else:
            return f" {ch}"

    row1 = "QWERTYUIOP"
    row2 = "ASDFGHJKL"
    row3 = "ZXCVBNM"

    line1 = " ".join([style(c) for c in row1])
    line2 = " ".join([style(c) for c in row2])
    line3 = " ".join([style(c) for c in row3])

    return f"```{line1}\n{line2}\n{line3}```"

# /setword 指令
@tree.command(name="setword", description="設定 Wordle 答案（只有自己看得到）")
@app_commands.describe(word="請輸入 5 個英文字母單字")
async def setword(interaction: discord.Interaction, word: str):
    user_id = interaction.user.id
    word = word.upper()

    for key, game in games.items():
        if user_id in key:
            if game["word"] is not None:
                await interaction.response.send_message("\u26a0\ufe0f 該對戰已經設定過答案了。", ephemeral=True)
                return

            if len(word) != 5 or not word.isalpha():
                await interaction.response.send_message("\u274c 請輸入 5 個英文字母的單字。", ephemeral=True)
                return

            game["word"] = word
            await interaction.response.send_message(f"\u2705 答案已設定成功：{word}", ephemeral=True)
            return

    await interaction.response.send_message("\u274c 找不到你可以設定答案的對戰。", ephemeral=True)

# /resetgame 指令
@tree.command(name="resetgame", description="重置你參與的 Wordle 對戰")
async def resetgame(interaction: discord.Interaction):
    user_id = interaction.user.id
    print(f"[DEBUG] {user_id} 嘗試執行 /resetgame，現有 games.keys(): {list(games.keys())}")
    for key in list(games.keys()):
        if user_id in key:
            del games[key]
            await interaction.response.send_message("🔄 對戰已重置成功。", ephemeral=True)
            return
    await interaction.response.send_message("❌ 沒有找到你參與的對戰。", ephemeral=True)

# !startgame 指令
@bot.command()
async def startgame(ctx, opponent: discord.Member):
    player1 = ctx.author.id
    player2 = opponent.id
    key = tuple(sorted((player1, player2)))
    if key in games:
        await ctx.send("這場對戰已經開始了。")
        return
    games[key] = {
        "word": None,
        "guesser": player2,
        "tries": 0,
        "correct": set(),
        "present": set(),
        "wrong": set()
    }
    await ctx.send(f"對戰已建立！請 <@{player1}> 使用 `/setword` 指令設定答案單字。")

# !guess 指令
@bot.command()
async def guess(ctx, word: str):
    user_id = ctx.author.id
    for key, game in games.items():
        if user_id == game["guesser"] and game["word"]:
            if len(word) != 5 or not word.isalpha():
                await ctx.send("請輸入5個英文字母的單字。")
                return
            word = word.upper()
            game["tries"] += 1
            fb = feedback(word, game["word"])
            await ctx.send(f"{word} \u2794 {fb}")

            for i in range(len(word)):
                ch = word[i]
                if fb[i] == "\U0001f7e9":
                    game["correct"].add(ch)
                elif fb[i] == "\U0001f7e8":
                    if ch not in game["correct"]:
                        game["present"].add(ch)
                elif fb[i] == "\u2b1b":
                    if ch not in game["correct"] and ch not in game["present"]:
                        game["wrong"].add(ch)

            keyboard_view = render_keyboard(game["correct"], game["present"], game["wrong"])
            await ctx.send(f"鍵盤狀態：\n{keyboard_view}")

            if fb == "\U0001f7e9\U0001f7e9\U0001f7e9\U0001f7e9\U0001f7e9":
                await ctx.send(f"\U0001f389 猜中啦！共嘗試 {game['tries']} 次。遊戲結束！")
                del games[key]
            elif game["tries"] >= 6:
                await ctx.send(f"\u274c 猜錯 6 次了，正確答案是 {game['word']}。")
                del games[key]
            return
    await ctx.send("目前沒有你可以猜的遊戲，或是單字還沒設定。")

@bot.event
async def on_ready():
    print(f"\u2705 Bot \u5df2\u4e0a\u7dda：{bot.user}")
    await tree.sync()
    print("\u2705 Slash \u6307\u4ee4\u5df2\u540c\u6b65\u5b8c\u6210")

@bot.event
async def on_message(message):
    await bot.process_commands(message)

bot.run(TOKEN)
