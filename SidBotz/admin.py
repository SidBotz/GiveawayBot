from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
import os
import logging
import random
import asyncio
from validators import domain
from SidBotz.dbusers import db
from pyrogram import Client, filters, enums
from pyrogram.errors import ChatAdminRequired, FloodWait
from pyrogram.types import *
from utils import verify_user, check_token, check_verification, get_token
from config import *
import re
import json
import base64
from urllib.parse import quote_plus
from pyrogram import enums
from pyrogram import Client, filters
from pyrogram.types import CallbackQuery

ADMIN_USER_ID = 6521935712  # Admin User ID

from pyrogram import Client, filters
import subprocess
import os
import sys

# Define the repository URL
REPO_URL = "https://github.com/SidBotz/GiveawayBot"

async def get_top_referrers_command(limit=10):
    top_referrers = await db.get_top_referrers(limit)
    if not top_referrers:
        return "No referrers found."
    
    result = "Top Referrers:\n"
    for idx, user in enumerate(top_referrers, 1):
        result += f"{idx}. ID: {user['id']}, Name: {user['name']}, Referrals: {user['referral_count']}\n"
    return result
    
@Client.on_message(filters.command("admin") & filters.user(ADMIN_USER_ID))
async def admin_commands(client, message):
    buttons = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("💰 Set Giveaway Amount", callback_data="set_amount")
        ],
        [
            InlineKeyboardButton("🚫 Clear All Participants", callback_data="clear_participants")
        ],
        [
            InlineKeyboardButton("✅ Enable Participation", callback_data="enable_participation")
        ],
        [
            InlineKeyboardButton("❌ Disable Participation", callback_data="disable_participation")
        ],
        [
            InlineKeyboardButton("🎉 Choose Giveaway Winner", callback_data="choose_winner")
        ],
        [
            InlineKeyboardButton("📊 View Stats", callback_data="view_stats"),
            InlineKeyboardButton("🔝 Ten refferar", callback_data="topten")
        ]
    ])
    await message.reply_text(
        text="Admin Panel: Choose an action below:",
        reply_markup=buttons
    )


# Pyrogram callback handler for showing top 10 referrers
@Client.on_callback_query(filters.user(ADMIN_USER_ID) & filters.regex("topten"))
async def top_ten_referrers_callback(client: Client, callback_query: CallbackQuery):
    try:
        # Get the top 10 referrers from the database
        top_referrers = await db.get_top_referrers(limit=10)

        # Prepare the response message
        if not top_referrers:
            response = "No referrers found."
        else:
            response = "**Top 10 Referrers:**\n"
            for idx, user in enumerate(top_referrers, 1):
                response += f"{idx}. **Name:** {user['name']}, **Referrals:** {user['referral_count']}\n"

        # Edit the message with the response
        await callback_query.message.edit_text(response)
    except Exception as e:
        await callback_query.message.edit_text(f"An error occurred: {str(e)}")

@Client.on_callback_query(filters.user(ADMIN_USER_ID) & filters.regex("set_amount"))
async def set_amount_callback(client, callback_query):
    # Ask admin for the giveaway amount
    ask_message = await client.ask(
        chat_id=callback_query.from_user.id,
        text="💸 Please enter the giveaway amount (e.g., 100, 500):",
        reply_markup=ReplyKeyboardRemove()
    )
    
    if ask_message.text.isdigit():
        amount = int(ask_message.text)
        await db.set_amount(amount)  # Save the amount in the database
        await ask_message.reply_text(f"🎉 Giveaway amount set to ₹{amount}!")
    else:
        await ask_message.reply_text("❌ Invalid amount. Please send a valid number.")


@Client.on_callback_query(filters.user(ADMIN_USER_ID) & filters.regex("clear_participants"))
async def clear_participants_callback(client, callback_query):
    # Clear all participants from the database
    await db.clear_participants()
    await callback_query.message.edit_text("✅ All participants have been cleared for the next giveaway!")


@Client.on_callback_query(filters.user(ADMIN_USER_ID) & filters.regex("enable_participation"))
async def enable_participation_callback(client, callback_query):
    # Enable participation for the giveaway
    await db.set_participation_status(True)
    await callback_query.message.edit_text("✅ Participation is now enabled for the giveaway!")


@Client.on_callback_query(filters.user(ADMIN_USER_ID) & filters.regex("disable_participation"))
async def disable_participation_callback(client, callback_query):
    # Disable participation for the giveaway
    await db.set_participation_status(False)
    await callback_query.message.edit_text("❌ Participation is now disabled for the giveaway!")


@Client.on_callback_query(filters.user(ADMIN_USER_ID) & filters.regex("choose_winner"))
async def choose_winner_callback(client, callback_query):
    # Choose a random winner using client.ask
    participants = await db.get_all_participants()
    if not participants:
        await callback_query.message.edit_text("❌ No participants found.")
        return

    participant_mentions = "\n".join(
        [f"{index + 1}. [{(await client.get_users(user_id)).first_name}](tg://user?id={user_id})" 
         for index, user_id in enumerate(participants)]
    )
    ask_message = await client.ask(
        chat_id=callback_query.from_user.id,
        text=f"🎉 Participants List:\n\n{participant_mentions}\n\n"
             "Select a participant by entering their number or type `random` for a random winner:",
        reply_markup=ReplyKeyboardRemove()
    )

    if ask_message.text.lower() == "random":
        winner_id = random.choice(participants)
    elif ask_message.text.isdigit() and 1 <= int(ask_message.text) <= len(participants):
        winner_id = participants[int(ask_message.text) - 1]
    else:
        await ask_message.reply_text("❌ Invalid input. Please try again.")
        return

    winner = await client.get_users(winner_id)
    await ask_message.reply_text(
        f"🎉 The winner is: [{winner.first_name}](tg://user?id={winner.id})",
        disable_web_page_preview=True
    )
    await db.remove_participant(winner_id)  # Ensure this user doesn't win again


@Client.on_callback_query(filters.user(ADMIN_USER_ID) & filters.regex("view_stats"))
async def view_stats_callback(client, callback_query):
    # View total number of users and participants in the giveaway
    total_users = await db.total_users_count()
    total_participants = await db.get_participant_count()
    is_participation_open = await db.is_participation()
    giveaway_amount = await db.get_amount()
    
    stats_message = (
        f"📊 **Bot Stats**:\n\n"
        f"👥 Total Users: {total_users}\n"
        f"👤 Total Participants: {total_participants}\n"
        f"🎉 Giveaway Amount: ₹{giveaway_amount}\n"
        f"✅ Participation Active: {'Yes' if is_participation_open else 'No'}"
    )
    await callback_query.message.edit_text(stats_message)

@Client.on_message(filters.command("update") & filters.user(ADMIN_USER_ID))
async def update_bot(client, message):
    try:
        await message.reply_text("🚀 Starting the update process...")

        # Check if the repository is already linked
        process = subprocess.Popen(
            ["git", "remote", "-v"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        stdout, stderr = process.communicate()

        if REPO_URL not in stdout:
            # Add the repository as the remote if not already linked
            await message.reply_text("🔗 Repository not linked. Adding remote...")
            add_remote_process = subprocess.Popen(
                ["git", "remote", "add", "origin", REPO_URL],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            add_stdout, add_stderr = add_remote_process.communicate()
            if add_remote_process.returncode != 0:
                await message.reply_text(f"❌ Failed to add remote!\n\nError:\n<code>{add_stderr}</code>", parse_mode="html")
                return

        # Pull the latest changes from the repository
        await message.reply_text("📥 Pulling latest updates from the repository...")
        pull_process = subprocess.Popen(
            ["git", "pull", "origin", "main"],  # Adjust branch name if not "main"
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        pull_stdout, pull_stderr = pull_process.communicate()

        if pull_process.returncode != 0:
            await message.reply_text(f"❌ Failed to update the bot!\n\nError:\n<code>{pull_stderr}</code>", parse_mode="html")
            return

        # Install updated dependencies (if any)
        await message.reply_text("📦 Installing updated dependencies (if any)...")
        install_process = subprocess.Popen(
            [sys.executable, "-m", "pip", "install", "-r", "req.txt"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        install_stdout, install_stderr = install_process.communicate()

        if install_process.returncode != 0:
            await message.reply_text(f"⚠️ Dependencies installation failed!\n\nError:\n<code>{install_stderr}</code>", parse_mode="html")
            return

        # Notify the admin that the update was successful
        await message.reply_text(f"✅ Bot updated successfully!\n\n<b>Git Output:</b>\n<code>{pull_stdout}</code>", parse_mode="html")

        # Restart the bot
        await message.reply_text("♻️ Restarting the bot...")
        os.execv(sys.executable, ['python'] + sys.argv)

    except Exception as e:
        await message.reply_text(f"❌ An error occurred during the update process!\n\nError:\n<code>{e}</code>", parse_mode="html")

