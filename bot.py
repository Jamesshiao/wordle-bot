import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import string

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

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
    await ctx.send(f"對戰已建立！請 <@{player1}> 私訊我使用 `!setword` 設定答案單字。")

@bot.command()
async def setword(ctx, word: str):
    user_id = ctx.author.id
    for key in games:
        if user_id in key and games[key]["word"] is None:
            if len(word) != 5 or not word.isalpha():
                await ctx.send("請輸入5個英文字母的單字。")
                return
            games[key]["word"] = word.upper()
            await ctx.send("答案已設定成功。等待對方猜測吧！")
            return
    await ctx.send("目前沒有你需要設定單字的遊戲。")

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
            await ctx.send(f"{word} ➤ {fb}")

            # 更新字母狀態
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
            await ctx.send(f"鍵盤狀態：\n{keyboard_view}")

            if fb == "🟩🟩🟩🟩🟩":
                await ctx.send(f"🎉 猜中啦！共嘗試 {game['tries']} 次。遊戲結束！")
                del games[key]
            elif game["tries"] >= 6:
                await ctx.send(f"❌ 猜錯 6 次了，正確答案是 {game['word']}。")
                del games[key]
            return
    await ctx.send("目前沒有你可以猜的遊戲，或是單字還沒設定。")

@bot.event
async def on_ready():
    print(f"✅ Bot 已啟動：{bot.user}")

@bot.event
async def on_message(message):
    print(f"[DEBUG] 收到訊息：{message.content}，來自：{message.author}")
    await bot.process_commands(message)

bot.run(TOKEN)
