# activity_selector.py

import random
import asyncio
from datetime import datetime, timedelta

async def can_tweet(memory):
    async with memory.get_db_connection() as db:
        cursor = await db.execute('''
            SELECT timestamp FROM activity_logs 
            WHERE activity = 'post_tweet' 
            ORDER BY timestamp DESC LIMIT 1
        ''')
        last_tweet = await cursor.fetchone()
        
        if not last_tweet:
            return True
            
        last_tweet_time = datetime.fromisoformat(last_tweet[0])
        time_since_last_tweet = datetime.now() - last_tweet_time
        
        return time_since_last_tweet > timedelta(minutes=1)

async def select_activity(state, activity_functions, memory):
    activities = list(activity_functions.keys())
    probabilities = []
    
    # Remove post_tweet from options if on cooldown
    if 'post_tweet' in activities:
        can_tweet_now = await can_tweet(memory)
        if not can_tweet_now:
            activities.remove('post_tweet')
    
    # Adjust probabilities based on state
    if state.energy < 30 and 'nap' in activities:
        probabilities = [0.6 if a == 'nap' else 0.2 for a in activities]
    elif state.happiness < 40 and 'play' in activities:
        probabilities = [0.6 if a == 'play' else 0.2 for a in activities]
    else:
        # Give post_tweet a higher base probability (30% instead of 10%)
        probabilities = [0.3 if a == 'post_tweet' else 1 for a in activities]
        # Normalize probabilities
        total = sum(probabilities)
        probabilities = [p/total for p in probabilities]
    
    activity = random.choices(activities, probabilities)[0]
    return activity
