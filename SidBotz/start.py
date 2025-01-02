
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
from config import AUTH_CHANNEL as channel_username, VERIFY_MODE, VERIFY_TUTORIAL, LOG_CHANNEL, GIVEAWAYCHNL, REFFERLOG
# Function to check if the user is a member of the channel
async def is_member(client, user_id, channel_username):
    try:
        member = await client.get_chat_member(channel_username, user_id)
        return member.status in [enums.ChatMemberStatus.MEMBER, enums.ChatMemberStatus.OWNER, enums.ChatMemberStatus.ADMINISTRATOR]
    except:
        return False

@Client.on_message(filters.command("start") & filters.incoming)
async def start(client, message):
    username = (await client.get_me()).username
    user_id = message.from_user.id
    first_name = message.from_user.first_name
    try:
        await client.send_message(LOG_CHANNEL, f"#StartCount\n{user_id}, {message.from_user.mention} Started Bot")
    except Exception as e:
        print(f"log send faild {e}")
    # Replace with your channel username

    # Check if the user is a member of the channel
    if not await is_member(client, user_id, channel_username):
        while True:
            # Prompt user to join the channel
            reply_markup = ReplyKeyboardMarkup(
                [[KeyboardButton("Joined ✅")]],
                resize_keyboard=True,
                one_time_keyboard=True
            )
            ask_message = await client.ask(
                chat_id=user_id,
                text=(
                    f"**🔔 You must join our channel to use this bot!**</b>\n\n"
                    f"👉 Click the button below to join:\n"
                    f"➡️ Join [@{channel_username}](https://t.me/{channel_username})\n\n"
                    f"Once you've joined, click 'Joined ✅'."
                ),
                reply_markup=reply_markup,
                parse_mode=enums.ParseMode.MARKDOWN
            )

            # Check if the user responded with "Joined ✅"
            if ask_message.text == "Joined ✅":
                if await is_member(client, user_id, channel_username):
                    await ask_message.reply(
                        "**✅ Thank you for joining! You can now use the bot.**\nNow /Start To Participate",
                        reply_markup=ReplyKeyboardRemove()
                    )
                    if not await db.is_user_exist(user_id):
                        await db.add_user(user_id, first_name)
                        try:
                            await client.send_message(LOG_CHANNEL, f"#NewUser\n{user_id}, {message.from_user.mention} Started Bot")
                        except:
                            print("ok")
                        if len(message.command) == 2:
                            referrer_id = message.command[1]
                            if referrer_id.isdigit() and referrer_id != str(user_id):
                                await db.add_referral(referrer_id, user_id)
                                try:
                                    await client.send_message(referrer_id, f"{message.from_user.mention} Started From Your Refferal Link\n\nYou Got 2 Points(points increase winning chance)")
                                    await client.send_message(REFFERLOG, f"Name:- {message.from_user.mention}\nId:- {message.from_user.id}\n\n #Id{referrer_id}Date{datetime.now().strftime('%d/%m/%Y')}")
                                    
                                except Exception as e:
                                    print(f"Failed To Send Message {e}")
                                    await client.send_message(REFFERLOG, f"Name:- {message.from_user.mention}\nId:- {message.from_user.id}\n\n #Id{referrer_id}Date{datetime.now().strftime('%d/%m/%Y')}")
                                    await client.send_message(referrer_id, f"{message.from_user.mention} Started From Your Refferal Link\n\nYou Got 2 Points(points increase winning chance)")
                                    

                                
                    break
                else:
                    await ask_message.reply(
                        "❌ You are not a member of the channel. Please join and try again."
                    )
            else:
                await ask_message.reply(
                    "❌ Invalid response. Please click 'Joined ✅' after joining the channel."
                )
        return

    try:
        hmm = await message.reply(
            "✨",
            reply_markup=ReplyKeyboardRemove()
            )
        await asyncio.sleep(1)
        await hmm.delete()
    except Exception as e:
        print(f"Okkk error {e}")

    # Check if user exists in the database
    
    if not await db.is_user_exist(user_id):
        await db.add_user(user_id, first_name)
        await client.send_message(LOG_CHANNEL, f"#NewUser\n{user_id}, {message.from_user.mention} Started Bot")

        # Referral logic if the user is new and a referral ID is provided
        if len(message.command) == 2:
            referrer_id = message.command[1]
            if referrer_id.isdigit() and referrer_id != str(user_id):
                # Add referral if valid referrer ID
                await db.add_referral(referrer_id, user_id)
                try:
                    await client.send_message(REFFERLOG, f"Name:- {message.from_user.mention}\nId:- {message.from_user.id}\n\n #Id{referrer_id}Date{datetime.now().strftime('%d/%m/%Y')}")
                    await client.send_message(referrer_id, f"{message.from_user.mention} Started From Your Refferal Link\n\nYou Got 2 Points(points increase winning chance)")
                except:
                    print("Failed To Send Message")

    # Token verification or referral logic
    if len(message.command) == 2:
        data = message.command[1]
        if data.split("-", 1)[0] == "verify":
            try:
                userid = data.split("-", 2)[1]
                token = data.split("-", 3)[2]
                if str(user_id) != str(userid):
                    return await message.reply_text(
                        text="<b>Invalid link or Expired link!</b>",
                        protect_content=True
                    )

                # Check token validity
                is_valid = await check_token(client, userid, token)
                if is_valid:
                    await message.reply_text(
                        text=(
                            f"<b>Hey {message.from_user.mention}, You are successfully verified!</b>\n"
                            f"Now you have access to participate ."
                        ),
                        protect_content=False
                    )
                    await verify_user(client, userid, token)
                else:
                    return await message.reply_text(
                        text="<b>Invalid link or Expired link!</b>",
                        protect_content=True
                    )
            except Exception as e:
                return await message.reply_text(
                    text="<b>Invalid link or an error occurred during verification!</b>",
                    protect_content=True
                )

    # Default buttons for `/start` command
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton('📢 Bot Updates', url='https://t.me/JeetoDaily')],
    #    [
       #     InlineKeyboardButton('🎁 Participate in Giveaway', callback_data='participate'),
       # ],
        [
            InlineKeyboardButton('👥 Referral Program', callback_data='referral')
        ]
    ])
    referrals = await db.get_referral_count(user_id)  # Assuming this function exists
    await message.reply_text(
        text=(
            f"👋 Hello {message.from_user.mention},\n\n"
            f"Welcome to our bot! 🎉\n\n"
            f"📌 Use the buttons below to participate in Refferal program\n\n"
            f"📊 **Your Stats:**\n"
            f"✅ Referrals: {referrals}\n\n"
            f"🚀 Invite your friends to participate in refferal giveaway of 25₹!\n#Jo Jyada Reffer Karega Wahi Jitega\n"
            f"<blockquote>We are adding Task Features by completing task you will earn more and daily</blockquote>"
        ),
        reply_markup=buttons
    )




@Client.on_callback_query(filters.regex("participate"))
async def participate_handler(client, callback_query):
    user_id = callback_query.from_user.id
    username = callback_query.from_user.mention

    try:
        # Check if participation is open
        participation = await db.is_participation()  # Assuming this function checks if participation is active
        if not participation:
            await callback_query.message.edit_text(
                "Participation is Closed.\nFor the result of the giveaway, join @LinkOfSexxyy"
            )
            return
    except Exception as e:
        await callback_query.message.edit_text(
            text="<b>Unable to verify participation status. Please try again later.</b>"
        )
        return

    # Check if the user is verified
    if not await check_verification(client, user_id) and VERIFY_MODE:
        try:
            verify_url = await get_token(client, user_id, f"https://telegram.me/{(await client.get_me()).username}?start=")
            btn = [
                [InlineKeyboardButton("Verify", url=verify_url)],
                [InlineKeyboardButton("How To Verify", url=VERIFY_TUTORIAL)]
            ]
            await callback_query.message.edit_text(
                text="<b>You are not verified!\nKindly verify to participate in the giveaway!</b>",
                reply_markup=InlineKeyboardMarkup(btn)
            )
        except Exception as e:
            await callback_query.message.edit_text(
                text="<b>An error occurred during verification. Please try again later.</b>"
            )
        return

    # Fetch giveaway amount and add participation
    try:
        giveaway_amount = await db.get_amount()  # Assuming this function retrieves the giveaway amount
        if await db.is_already_participated(user_id):  # Check if the user has already participated
            await callback_query.message.edit_text(
                text="<b>You have already participated in the giveaway!</b>"
            )
            return

        await db.add_participant(user_id)  # Add the user as a participant
        await callback_query.message.edit_text(
            text=f"<b>🎉 Congratulations {username}!\nYou have successfully participated in the giveaway of {giveaway_amount}₹\nFor WinnerList and All Participated User List Join Here\n[Join And Check](https://t.me/+dFa46D-m-lhhNGY1)!</b>"
        )
        await client.send_message(GIVEAWAYCHNL, f"{callback_query.from_user.first_name} Participated In Giveaway")
    except Exception as e:
        await callback_query.message.edit_text(
            text="<b>Something went wrong. Please try again later.</b>"
        )



@Client.on_callback_query(filters.regex("referral"))
async def referral_program_callback(client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    first_name = callback_query.from_user.first_name

    # Generate the referral link
    bot_username = (await client.get_me()).username
    referral_link = f"https://t.me/{bot_username}?start={user_id}"

    # Fetch user-specific referral stats
    referrals = await db.get_referral_count(user_id)  # Assuming this function exists
    earnings_range = "₹10 - ₹20"  # Adjust as needed

    # Referral message
    referral_message = (
        f"👥 **Referral Program**\n\n"
        f"Earn rewards for each successful referral! 🎉\n\n"
        f"🔗 **Your Referral Link:**\n"
        f"[{referral_link}]({referral_link})\n\n"
        f"📊 **Your Stats:**\n"
        f"✅ Referrals: {referrals}\n\n"
        f"🚀 Invite your friends to increase your winning chances!\n\n"
        f"⚠️ **Notice:**\n"
        f"Using fake accounts will lead to a permanent ban."
    )

    # Share button
    share_url = (
        f"https://t.me/share/url?url=%F0%9F%94%A5%20I%27m%20earning%20daily%20%E2%82%B910-%E2%82%B920%20"
        f"by%20completing%20tasks%20on%20this%20amazing%20bot%21%20%F0%9F%A4%91%20%20%0A%0A%F0%9F%92%B5%20"
        f"Earn%20extra%20rewards%20by%20inviting%20your%20friends%21%20Use%20my%20referral%20link%20to%20start%3A%20"
        f"%0A%0A%F0%9F%91%89%20{referral_link}%20%0A%0AStart%20your%20earnings%20today%21"
    )

    # Buttons
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 Share Referral", url=share_url)],
        [InlineKeyboardButton("🔙 Back to Home", callback_data="home")]
    ])

    # Send referral information
    await callback_query.message.edit_text(referral_message, reply_markup=buttons, disable_web_page_preview=True)
