import os

# Bot token @Botfather
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8193933377:AAFwZLRHsmFYnJgVnkkDgpwnFejlWHI0oto")

# Your API ID from my.telegram.org
API_ID = int(os.environ.get("API_ID", "5461760"))

# Your API Hash from my.telegram.org
API_HASH = os.environ.get("API_HASH", "396b10bcf5e1ed5fcc71f1603800b7cf")

# Your Owner / Admin Id For Broadcast 
ADMINS = int(os.environ.get("ADMINS", "6521935712"))

# Your Mongodb Database Url
DB_URI = os.environ.get("DB_URI", "mongodb+srv://SidBotz:2tDv408IfljeIb8h@cluster0.69ij8.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
DB_NAME = os.environ.get("DB_NAME", "GiveawayBot")

SHORTLINK_URL = "shortner.in"
SHORTLINK_API = "ddf18f32fa21d9cd97ba02fb30ad3aa109b91bc6"
AUTH_CHANNEL = "JeetoDaily"


VERIFY_MODE = "False"
VERIFY_TUTORIAL = "https://t.me/DailyGiveawayBotxhub/15"

LOG_CHANNEL = "-1002440575475"
REFFERLOG = "-1002440575475"
GIVEAWAYCHNL = "-1002489640426"
# If You Want Error Message In Your Personal Message Then Turn It True Else If You Don't Want Then Flase
ERROR_MESSAGE = bool(os.environ.get('ERROR_MESSAGE', True))

REFERRAL_CHANNELS = ["JeetoDaily"]
RefferalAmount = os.environ.get("RefferalAmount", "Upto 5 ₹")

# Configuration for tasks (update as per your bot setup)
TASKS = [
    {"name": "", "link": "", "api": ""},
    {"name": "", "link": "", "api": ""},
    {"name": "", "link": "", "api": ""},
    {"name": "", "link": "", "api": ""},
    {"name": "", "link": "", "api": ""},
    {"name": "", "link": "", "api": ""},
]



