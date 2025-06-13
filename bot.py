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

def feedback(guess, answer):
    result = []
    answer_chars = list(answer)
    for i in range(len(guess)):
        if guess[i] == answer[i]:
            result.append("🟩")
            answer_chars[i] = None
        else:
            result.append(None)
    for i in range(len(guess)):
        if result[i] is None:
            if guess[i] in answer_chars:
                result[i] = "🟨"
                answer_chars[answer_chars.index(guess[i])] = None
            else:
                result[i] = "⬛"
    return "".join(result)

def render_keyboard(correct, present, wrong):
    def style(ch):
        if ch in correct:
            return f"🟩{ch}"
        elif ch in present:
            return f"🟨{ch}"
        elif ch in wrong:
            return f"⬛{ch}"
        else:
            return f" {ch}"

    row1 = "QWERTYUIOP"
    row2 = "ASDFGHJKL"
    row3 = "ZXCVBNM"

    line1 = " ".join([style(c) for c in row1])
    line2 = " ".join([style(c) for c in row2])
    line3 = " ".join([style(c) for c in row3])

    return f"```{line1}\n{line2}\n{line3}```"

@tree.command(name="startgame", description="與指定對象開始 Wordle 對戰")
@app_commands.describe(opponent="對手（會猜的人）")
async def startgame(interaction: discord.Interaction, opponent: discord.Member):
    player1 = interaction.user.id
    player2 = opponent.id
    key = tuple(sorted((player1, player2)))
    if key in games:
        await interaction.response.send_message("⚠️ 這場對戰已經開始了。", ephemeral=True)
        return
    games[key] = {
        "word": None,
        "guesser": player2,
        "tries": 0,
        "correct": set(),
        "present": set(),
        "wrong": set()
    }
    await interaction.response.send_message(f"🕹️ 對戰已建立！請 <@{player1}> 使用 `/setword` 指令設定答案單字（僅自己可見）")

@tree.command(name="setword", description="設定 Wordle 答案（只有自己看得到）")
@app_commands.describe(word="請輸入 5 個英文字母單字")
async def setword(interaction: discord.Interaction, word: str):
    user_id = interaction.user.id
    word = word.upper()

    for key, game in games.items():
        if user_id in key:
            if game["word"] is not None:
                await interaction.response.send_message("⚠️ 該對戰已經設定過答案了。", ephemeral=True)
                return

            if len(word) != 5 or not word.isalpha():
                await interaction.response.send_message("❌ 請輸入 5 個英文字母的單字。", ephemeral=True)
                return

            game["word"] = word
            await interaction.response.send_message(f"✅ 答案已設定成功：{word}", ephemeral=True)
            guesser_id = game["guesser"]
            channel = interaction.channel
            await channel.send(f"📢 對戰開始！<@{guesser_id}> 可以開始猜題！")
            return

    await interaction.response.send_message("❌ 找不到你可以設定答案的對戰。", ephemeral=True)

@tree.command(name="guess", description="猜一個單字")
@app_commands.describe(word="你要猜的 5 字母單字")
async def guess(interaction: discord.Interaction, word: str):
    user_id = interaction.user.id
    for key, game in games.items():
        if user_id == game["guesser"] and game["word"]:
            if len(word) != 5 or not word.isalpha():
                await interaction.response.send_message("請輸入5個英文字母的單字。")
                return
            word = word.upper()
            game["tries"] += 1
            fb = feedback(word, game["word"])

            for i in range(len(word)):
                ch = word[i]
                if fb[i] == "🟩":
                    game["correct"].add(ch)
                elif fb[i] == "🟨":
                    if ch not in game["correct"]:
                        game["present"].add(ch)
                elif fb[i] == "⬛":
                    if ch not in game["correct"] and ch not in game["present"]:
                        game["wrong"].add(ch)

            keyboard_view = render_keyboard(game["correct"], game["present"], game["wrong"])

            await interaction.response.send_message(f"{word} ({game['tries']}/6) \u279e {fb}\n鍵盤狀態：\n{keyboard_view}")

            if fb == "🟩🟩🟩🟩🟩":
                await interaction.channel.send(f"🎉 猜中啦！共嘗試 {game['tries']} 次。遊戲結束！")
                del games[key]
            elif game["tries"] >= 6:
                await interaction.channel.send(f"❌ 猜錯 6 次了，正確答案是 {game['word']}。")
                del games[key]
            return
    await interaction.response.send_message("目前沒有你可以猜的遊戲，或是單字還沒設定。")

@tree.command(name="resetgame", description="重置你參與的 Wordle 對戰")
async def resetgame(interaction: discord.Interaction):
    user_id = interaction.user.id
    for key in list(games.keys()):
        if user_id in key:
            del games[key]
            await interaction.response.send_message("🔄 對戰已重置成功。", ephemeral=True)
            return
    await interaction.response.send_message("❌ 沒有找到你參與的對戰。", ephemeral=True)

@bot.event
async def on_ready():
    print(f"✅ Bot 已上線：{bot.user}")
    try:
        synced = await tree.sync()
        print(f"✅ 成功同步 {len(synced)} 個 slash 指令")
    except Exception as e:
        print(f"❌ 指令同步失敗：{e}")

bot.run(TOKEN)
