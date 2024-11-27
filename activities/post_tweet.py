import asyncio
import json
import random
from datetime import datetime, timedelta

TWEET_COOLDOWN_MINUTES = 1  # Only tweet every 1 minute

async def can_tweet(memory):
    async with memory.get_db_connection() as db:
        # Check last tweet time
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
        
        return time_since_last_tweet > timedelta(minutes=TWEET_COOLDOWN_MINUTES)

async def get_recent_activities(memory, limit=5):
    async with memory.get_db_connection() as db:
        cursor = await db.execute('''
            SELECT activity, state_changes
            FROM activity_logs
            WHERE activity != 'post_tweet'
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (limit,))
        activities = await cursor.fetchall()
        return [(act, json.loads(changes) if changes else {}) for act, changes in activities]

async def generate_tweet_content(recent_activities, state):
    # List of tweet templates
    templates = [
        "Just finished {activity}! My {stat} is now {value}. {mood}",
        "Another day in the life! {activity} got my {stat} to {value}. {mood}",
        "Guess what? {activity} was fun! Now my {stat} is {value}. {mood}",
        "Living my best virtual life! {activity} brought my {stat} to {value}. {mood}"
    ]
    
    # Get the most recent activity and its effects
    if not recent_activities:
        return "Just hanging out and being my virtual self! 🐾"
        
    activity, changes = recent_activities[0]
    
    # Clean up activity name
    activity_name = activity.replace('_', ' ').title()
    
    # Get a significant stat change if any
    stat_change = None
    if changes:
        stat_change = max(changes.items(), key=lambda x: abs(x[1]))
    
    # Generate mood based on current state
    moods = []
    if state.energy > 80:
        moods.append("Feeling energetic! ⚡")
    elif state.energy < 30:
        moods.append("Getting a bit tired... 😴")
    if state.happiness > 80:
        moods.append("Life is good! 🌟")
    elif state.happiness < 30:
        moods.append("Could use some cheering up 🥺")
    
    mood = random.choice(moods) if moods else "🐾"
    
    # Fill template
    template = random.choice(templates)
    tweet = template.format(
        activity=activity_name,
        stat=stat_change[0] if stat_change else "mood",
        value=stat_change[1] if stat_change else "great",
        mood=mood
    )
    
    return tweet

async def run(state, memory):
    # Check if enough time has passed since last tweet
    if not await can_tweet(memory):
        print("Too soon to tweet again!")
        return
    
    # Get recent activities
    recent_activities = await get_recent_activities(memory)
    
    # Generate tweet content
    tweet_content = await generate_tweet_content(recent_activities, state)
    
    print(f"Generated tweet: {tweet_content}")
    
    # Here you would integrate with Twitter API to actually post the tweet
    # For now, we'll just simulate it
    print("Tweet posted successfully!")
    
    # Update state
    state.energy -= 5  # Tweeting takes a little energy
    state.happiness += 10  # But it makes Pippin happy to share! 