from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove

ADMIN_USER_ID = 6521935712  # Admin User ID

@Client.on_message(filters.command("admin") & filters.user(ADMIN_USER_ID))
async def admin_commands(client, message):
    buttons = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("💰 Set Giveaway Amount", callback_data="set_amount"),
            InlineKeyboardButton("🚫 Clear All Participants", callback_data="clear_participants")
        ],
        [
            InlineKeyboardButton("✅ Enable Participation", callback_data="enable_participation"),
            InlineKeyboardButton("❌ Disable Participation", callback_data="disable_participation")
        ],
        [
            InlineKeyboardButton("🎉 Choose Giveaway Winner", callback_data="choose_winner"),
            InlineKeyboardButton("📊 View Stats", callback_data="view_stats")
        ]
    ])
    await message.reply_text(
        text="Admin Panel: Choose an action below:",
        reply_markup=buttons
    )


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
