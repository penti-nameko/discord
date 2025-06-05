import discord
from discord.ext import commands
import asyncio
import signal
import os
import random
from discord import app_commands
import json
from datetime import datetime
from typing import Optional
from typing import Literal
from typing import Optional

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.messages = True

bot = commands.Bot(command_prefix="!", intents=intents)

# --- 汎用メッセージ/ファイル送信関数 ---
async def send_content(channel: discord.abc.Messageable, message: str = None, file_paths: list[str] = None):
    files = []
    if file_paths:
        for path in file_paths:
            if os.path.isfile(path):
                with open(path, "rb") as f:
                   files.append(discord.File(f, filename=os.path.basename(path)))
            else:
                print("[WARNING] ファイルが見つかりません: {path}")
    if not message and not files:
        await channel.send("⚠️ メッセージもファイルも指定されていません。")
    else:
        await channel.send(content=message or None, files=files if files else None)

# --- 起動時ログ（"ログ"チャンネルを検索） ---

@bot.event
async def on_ready():
    class BotInfo:
        def __init__(self, user, guilds):
            self.user = user
            self.guild_count = len(guilds)

        def summary(self):
            return f"✅ {self.user} - Connected to {self.guild_count} servers."

    info = BotInfo(bot.user, bot.guilds)
    print(info.summary())
    # 各サーバーごとに"ログ"チャンネルを探してメッセージ送信
@bot.event
async def on_ready():
    print("[INFO] Bot Online: {bot.user}")
    # スラッシュコマンドを毎回同期
    try:
        synced = await bot.tree.sync()
        print("✅ スラッシュコマンド同期完了: {len(synced)} 件")
    except Exception as e:
        print("❌ スラッシュコマンド同期失敗: {e}")
    # 各サーバーにログメッセージ送信
    for guild in bot.guilds:
        log_channel = discord.utils.find(
            lambda c: c.name == "ログ" and c.permissions_for(guild.me).send_messages,
            guild.text_channels
        )
        if log_channel:
            try:
                await send_content(log_channel, message="おはよ...ムニャ")
                await send_content(log_channel, message="🔁 スラッシュコマンド {len(synced)} 件を同期しました")
                print("✅ 起動ログ送信: {guild.name} → #{log_channel.name}")
            except Exception as e:
                print("❌ 起動ログ送信失敗: {guild.name}: {e}")
        else:
            print("⚠️ ログチャンネルが見つからない: {guild.name}")
# --- 終了時ログ（"ログ"チャンネルを検索） ---
def shutdown_handler():
    loop = asyncio.get_event_loop()
    async def shutdown():
        await bot.wait_until_ready()
        for guild in bot.guilds:
            log_channel = discord.utils.find(
                lambda c: c.name == "ログ" and c.permissions_for(guild.me).send_messages,
                guild.text_channels
            )
            if log_channel:
                try:
                    await send_content(log_channel, message="うう.....フィグロスしてたのに...")
                    print("✅ 終了ログ送信: {guild.name} → #{log_channel.name}")
                except Exception as e:
                    print("❌ 終了ログ送信失敗: {guild.name}: {e}")
            else:
                print("⚠️ ログチャンネルが見つからない: {guild.name}")
        await bot.close()
    loop.create_task(shutdown())
def setup_signal_handlers():
    for sig in (signal.SIGINT, signal.SIGTERM):
        signal.signal(sig, lambda s, f: shutdown_handler())
setup_signal_handlers()
SCHEDULE_FILE = "schedules.json"
def load_schedules():
    if os.path.exists(SCHEDULE_FILE):
        with open(SCHEDULE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}
def save_schedules(data):
    with open(SCHEDULE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
# --- /schedule_add ---
@bot.tree.command(name="schedule_add", description="予定を追加します（形式: YYYY-MM-DD HH:MM）")
@app_commands.describe(time="日時（例: 2025-05-24 19:00）", title="予定のタイトル")
async def schedule_add(interaction: discord.Interaction, time: str, title: str):
    try:
        dt = datetime.strptime(time, "%Y-%m-%d %H:%M")
    except ValueError:
        await interaction.response.send_message("⛔️ 日付形式が正しくありません。例: 2025-05-24 19:00", ephemeral=True)
        return
    data = load_schedules()
    user_id = str(interaction.user.id)
    data.setdefault(user_id, []).append({"time": dt.strftime("%Y-%m-%d %H:%M"), "title": title})
    save_schedules(data)
    await interaction.response.send_message("📅 予定を追加しました: {time} - {title}")
# --- /schedule_list ---
@bot.tree.command(name="schedule_list", description="あなたの予定一覧を表示します")
async def schedule_list(interaction: discord.Interaction):
    data = load_schedules()
    user_id = str(interaction.user.id)
    if user_id not in data or not data[user_id]:
        await interaction.response.send_message("📭 予定はありません。", ephemeral=True)
        return
    msg = "🗓 あなたの予定一覧：\n"
    for i, item in enumerate(data[user_id], start=1):
        msg += "{i}. {item['time']} - {item['title']}\n"
    await interaction.response.send_message(msg)
# --- /schedule_remove ---
@bot.tree.command(name="schedule_remove", description="予定を削除します（番号で指定）")
@app_commands.describe(index="予定番号（/schedule_list で確認）")
async def schedule_remove(interaction: discord.Interaction, index: int):
    data = load_schedules()
    user_id = str(interaction.user.id)
    if user_id not in data or index < 1 or index > len(data[user_id]):
        await interaction.response.send_message("❌ 無効な番号です。", ephemeral=True)
        return
    removed = data[user_id].pop(index - 1)
    save_schedules(data)
    await interaction.response.send_message("🗑 削除しました: {removed['time']} - {removed['title']}")
# --- /roll コマンド ---
@bot.tree.command(name="roll", description="ダイスを振ります")
@app_commands.describe(sides="ダイスの面数（例：6, 20, 100）")
async def roll(interaction: discord.Interaction, sides: int = 6):
    if sides <= 1:
        await interaction.response.send_message("⚠️ 面数は2以上にしてください。", ephemeral=True)
        return
    result = random.randint(1, sides)
    await interaction.response.send_message("1d{sides} → **{result}**!")
# --- コマンド：メッセージだけ送信 ---
@bot.command()
async def msg(ctx, *, text):
    await send_content(ctx.channel, message=text)
# --- コマンド：ファイルだけ送信 ---
@bot.command()
async def file(ctx, *, filename):
    await send_content(ctx.channel, file_paths=[filename])
# --- コマンド：メッセージ + ファイル送信 ---
@bot.command()
async def send(ctx, filename, *, message=None):
    await send_content(ctx.channel, message=message, file_paths=[filename])
#おみくじ
@bot.tree.command(name="fortune", description="今日の運勢を占います")
async def fortune(interaction: discord.Interaction):
    fortunes = ["大吉 🎉", "中吉 😊", "小吉 🙂", "末吉 🤔", "凶 😟", "大凶 😱"]
    result = random.choice(fortunes)
    await interaction.response.send_message("🎴 今日の運勢：{result}")
#ツッコミ
@bot.tree.command(name="tukkomi", description="つっこみます")
@app_commands.describe(target="誰に何をつっこむか")
async def tukkomi(interaction: discord.Interaction, target: str):
    await interaction.response.send_message("何言ってるの、{target}")
# --- /help_me コマンド定義 ---
@bot.tree.command(name="help_me", description="えーりんを呼ぶコマンド")
@app_commands.describe(who="誰を呼びたい？（例: e-rin）")
async def help_me(interaction: discord.Interaction, who: str):
    await interaction.response.send_message("{who}ーーーっ！！", ephemeral=False)
#タイマー
@bot.tree.command(name="timer", description="タイマーをセットします（例：3分30秒）")
@app_commands.describe(minutes="分（省略可）", seconds="秒（省略可）")
async def timer(interaction: discord.Interaction, minutes: int = 0, seconds: int = 0):
    total_seconds = minutes * 60 + seconds
    if total_seconds <= 0:
        await interaction.response.send_message("⏰ 有効な時間を指定してください。", ephemeral=True)
        return
    await interaction.response.send_message("⏳ タイマーを開始しました：{minutes}分 {seconds}秒")
    await asyncio.sleep(total_seconds)
    try:
        await interaction.followup.send("✅ {interaction.user.mention} タイマーが終了しました！")
    except Exception as e:
        print("❌ タイマー通知送信失敗: {e}")
#ping
@bot.tree.command(name="ping", description="Botの応答速度を表示します")
async def ping(interaction: discord.Interaction):
    latency_ms = round(bot.latency * 1000)
    await interaction.response.send_message("🏓Pong! レイテンシ: {latency_ms}ms")
# --- /kick コマンド ---
@bot.tree.command(name="kick", description="ユーザーをサーバーからキックします")
@app_commands.describe(member="キックしたいメンバー", reason="理由（任意）")
async def kick(interaction: discord.Interaction, member: discord.Member, reason: str = "なし"):
    if not interaction.user.guild_permissions.kick_members:
        await interaction.response.send_message("❌ キック権限がありません。", ephemeral=True)
        return
    try:
        await member.kick(reason=reason)
        await interaction.response.send_message("👢 {member} をキックしました。理由: {reason}")
    except Exception as e:
        await interaction.response.send_message("❌ キックに失敗しました: {e}", ephemeral=True)
# --- /ban コマンド ---
@bot.tree.command(name="ban", description="ユーザーをBANします")
@app_commands.describe(member="BANしたいメンバー", reason="理由（任意）")
async def ban(interaction: discord.Interaction, member: discord.Member, reason: str = "なし"):
    if not interaction.user.guild_permissions.ban_members:
        await interaction.response.send_message("❌ BAN権限がありません。", ephemeral=True)
        return
    try:
        await member.ban(reason=reason)
        await interaction.response.send_message("🔨 {member} をBANしました。理由: {reason}")
    except Exception as e:
        await interaction.response.send_message("❌ BANに失敗しました: {e}", ephemeral=True)
# --- /unban コマンド ---
@bot.tree.command(name="unban", description="BANされたユーザーを解除します")
@app_commands.describe(user_id="BAN解除したいユーザーのID")
async def unban(interaction: discord.Interaction, user_id: str):
    if not interaction.user.guild_permissions.ban_members:
        await interaction.response.send_message("❌ BAN解除権限がありません。", ephemeral=True)
        return
    try:
        user = await bot.fetch_user(int(user_id))
        await interaction.guild.unban(user)
        await interaction.response.send_message("✅ BAN解除しました: {user}")
    except Exception as e:
        await interaction.response.send_message("❌ BAN解除に失敗しました: {e}", ephemeral=True)
#ルーレット選出
@bot.tree.command(name="roulette", description="様々な条件でランダムに1人を選びます")
@app_commands.describe(
    mode="選択モード: vc = VC内 / all = 全メンバー / role = ロール指定 / text = テキストチャンネル参加者",
    role="ロールから選ぶ場合に指定",
    channel="テキストチャンネルを指定する場合に指定"
)
async def roulette(
    interaction: discord.Interaction,
    mode: Literal["vc", "all", "role", "text"],
    role: Optional[discord.Role] = None,
    channel: Optional[discord.TextChannel] = None
):
    guild = interaction.guild
    if mode == "vc":
        voice_state = interaction.user.voice
        if not voice_state or not voice_state.channel:
            await interaction.response.send_message("❌ あなたはボイスチャンネルにいません。", ephemeral=True)
            return
        members = voice_state.channel.members
    elif mode == "all":
        members = [m for m in guild.members if not m.bot]
    elif mode == "role":
        if not role:
            await interaction.response.send_message("❌ ロールが指定されていません。", ephemeral=True)
            return
        members = [m for m in role.members if not m.bot]
    elif mode == "text":
        if not channel:
            await interaction.response.send_message("❌ テキストチャンネルが指定されていません。", ephemeral=True)
            return
        history = [msg async for msg in channel.history(limit=1000)]
        members = list({msg.author for msg in history if not msg.author.bot})
    else:
        await interaction.response.send_message("❌ 不明なモードです。", ephemeral=True)
        return
    if not members:
        await interaction.response.send_message("❌ 対象のメンバーがいません。", ephemeral=True)
        return
    chosen = random.choice(members)
    await interaction.response.send_message("🎯 選ばれたのは… {chosen.mention} さんでした！")
# 例: 質問チャンネルの名前
QUESTION_CHANNEL_NAME = "質問"
# 担当者のDiscordユーザーID（右クリック「IDをコピー」で取得）
QUESTION_HANDLER_ID = 123456789012345678  # ← 実際のIDに置き換えてください
@bot.event
async def on_message(message):
    # ボット自身のメッセージは無視
    if message.author.bot:
        return
    # 質問チャンネルか確認
    if message.channel.name == QUESTION_CHANNEL_NAME:
        handler = await bot.fetch_user(QUESTION_HANDLER_ID)
        if handler:
            try:
                embed = discord.Embed(
                    title="📩 新しい質問が届きました",
                    description=message.content,
                    color=discord.Color.blue()
                )
                embed.set_author(name="{message.author}（{message.author.id}）")
                embed.set_footer(text="サーバー: {message.guild.name} / チャンネル: #{message.channel.name}")
                await handler.send(embed=embed)
                print("✅ 質問をDMに転送: {message.author} → {handler}")
            except Exception as e:
                print("❌ DM送信失敗: {e}")
    # 他のコマンドにも影響させないため、on_messageの最後にこれを書く
    await bot.process_commands(message)
@bot.event
async def on_app_command_completion(interaction: discord.Interaction, command: discord.app_commands.Command):
    user = interaction.user
    guild_name = interaction.guild.name if interaction.guild else "DM"
    channel_name = interaction.channel.name if isinstance(interaction.channel, discord.TextChannel) else "DM"
    print("📘 コマンド実行: /{command.name}")
    print("  ┣ ユーザー: {user}（ID: {user.id}）")
    print("  ┣ サーバー: {guild_name}")
    print("  ┗ チャンネル: {channel_name}")
# --- Bot起動（トークンを入力してください） ---
if __name__ == "__main__":
    token = os.getenv("DISCORD_BOT_TOKEN")
    if not token:
        raise RuntimeError("DISCORD_BOT_TOKEN 環境変数が設定されていません。")
    
# --- Flaskによるヘルスチェック用HTTPサーバー ---
from flask import Flask
import threading

app = Flask(__name__)

@app.route("/")
def index():
    return "Bot is alive!", 200

def run_flask():
    port = int(os.environ.get("PORT", 8000))  # Koyeb用ポート
    app.run(host="0.0.0.0", port=port)

threading.Thread(target=run_flask, daemon=True).start()

bot.run(DISCORD_BOT_TOKEN)