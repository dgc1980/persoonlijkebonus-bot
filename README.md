docker-compose.yml


```
version: '2.0'
services:
  persoonlijkebonus-bot:
    image: dgc1980/persoonlijkebonus-bot
    environment:
      REDDIT_USER: YOUR_REDDIT_BOT_USERNAME
      REDDIT_PASS: YOUR_REDDIT_BOT_PASS
      # get your Client_ID and Secret from https://www.reddit.com/prefs/apps
      REDDIT_CID: YOURCLIENTID
      REDDIT_SECRET: YOURSECRET
      # you can monitor multiple subreddits using subreddit1+subreddit2+subreddit3
      REDDIT_SUBREDDIT: SubReddit

      DB_FILE: database.db
    volumes:
      - ./data:/data
    restart: always

```


