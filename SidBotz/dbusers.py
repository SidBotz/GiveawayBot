import motor.motor_asyncio
from config import DB_NAME, DB_URI
import random

DATABASE_NAME = DB_NAME
DATABASE_URI = DB_URI

class Database:
    
    def __init__(self, uri, database_name):
        self._client = motor.motor_asyncio.AsyncIOMotorClient(uri)
        self.db = self._client[database_name]
        self.users_col = self.db.users
        self.participation_col = self.db.participation
        self.settings_col = self.db.settings  # For storing giveaway settings, including amount, status, etc.

    def new_user(self, id, name):
        return dict(
            id=id,
            name=name,
            referrals=[],
            ban_status=dict(
                is_banned=False,
                ban_reason="",
            ),
        )

    async def add_user(self, id, name):
        user = self.new_user(id, name)
        await self.users_col.insert_one(user)

    async def is_user_exist(self, id):
        user = await self.users_col.find_one({'id': int(id)})
        return bool(user)

    async def add_referral(self, referrer_id, referred_id):
        # Adds referred user to the referrer’s referral list
        await self.users_col.update_one(
            {'id': int(referrer_id)},
            {'$push': {'referrals': referred_id}}
        )

    async def get_referral_count(self, user_id):
        # Returns the number of successful referrals
        user = await self.users_col.find_one({'id': int(user_id)})
        if user and 'referrals' in user:
            return len(user['referrals'])
        return 0

    async def total_users_count(self):
        count = await self.users_col.count_documents({})
        return count

    async def get_all_users(self):
        return self.users_col.find({})

    async def delete_user(self, user_id):
        await self.users_col.delete_many({'id': int(user_id)})

    async def is_participation(self):
        # Check if participation is active
        settings = await self.settings_col.find_one({'type': 'giveaway'})
        return settings and settings.get('participation_active', False)

    async def set_participation_status(self, status: bool):
        # Enable or disable participation
        await self.settings_col.update_one(
            {'type': 'giveaway'},
            {'$set': {'participation_active': status}},
            upsert=True
        )

    async def add_participant(self, user_id):
        # Add user to the list of participants
        await self.participation_col.update_one(
            {'type': 'giveaway'},
            {'$addToSet': {'participants': user_id}},
            upsert=True
        )

    async def is_already_participated(self, user_id):
        # Check if the user has already participated
        giveaway = await self.participation_col.find_one({'type': 'giveaway'})
        return giveaway and user_id in giveaway.get('participants', [])

    async def get_amount(self):
        # Fetch the giveaway amount
        settings = await self.settings_col.find_one({'type': 'giveaway'})
        return settings.get('amount', 0) if settings else 0

    async def set_amount(self, amount):
        # Set the giveaway amount
        await self.settings_col.update_one(
            {'type': 'giveaway'},
            {'$set': {'amount': amount}},
            upsert=True
        )

    async def clear_participants(self):
        # Clears all participants for a new giveaway
        await self.participation_col.update_one(
            {'type': 'giveaway'},
            {'$set': {'participants': []}},
            upsert=True
        )

    async def get_all_participants(self):
        """
        Retrieve all participant user IDs for the giveaway.
        Returns:
            list: A list of user IDs of participants.
        """
        data = await self.participation_col.find_one({'type': 'giveaway'})
        return data.get('participants', []) if data else []

    async def get_participant_count(self):
        """
        Get the total number of participants in the giveaway.
        Returns:
            int: Number of participants.
        """
        data = await self.participation_col.find_one({'type': 'giveaway'})
        return len(data.get('participants', [])) if data else 0
    
    async def choose_winner(self):
        # Chooses a random winner from participants
        giveaway = await self.participation_col.find_one({'type': 'giveaway'})
        if giveaway and giveaway.get('participants'):
            participants = giveaway['participants']
            winner_id = random.choice(participants)
            
            # Ensure a winner has not won twice
            winner = await self.users_col.find_one({'id': winner_id})
            if winner and 'won_giveaways' in winner and len(winner['won_giveaways']) > 0:
                # Check if the winner has already won before and select another winner
                return await self.choose_winner()

            # Mark this user as a winner (add to won_giveaways list)
            await self.users_col.update_one(
                {'id': winner_id},
                {'$push': {'won_giveaways': 'giveaway_id'}}  # Replace 'giveaway_id' with the actual giveaway ID or name
            )
            return winner_id
        return None


# Initialize the Database instance
db = Database(DATABASE_URI, DATABASE_NAME)
