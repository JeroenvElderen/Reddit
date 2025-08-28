import os 
import praw 

reddit_owner = praw.Reddit(
    client_id=os.getenv("OWNER_REDDIT_CLIENT_ID"),
    client_secret=os.getenv("OWNER_REDDIT_CLIENT_SECRET"),
    username=os.getenv("OWNER_REDDIT_USERNAME"),
    password=os.getenv("OWNER_REDDIT_PASSWORD"),
    user_agent=os.getenv("OWNER_REDDIT_USER_AGENT"),
)