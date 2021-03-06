import sqlite3

import time
import praw
import prawcore
import requests

import logging
import re
import os
import datetime

import schedule
import dateparser

os.environ['TZ'] = 'UTC'


reddit_cid = os.environ['REDDIT_CID']
reddit_secret = os.environ['REDDIT_SECRET']

reddit_user = os.environ['REDDIT_USER']
reddit_pass = os.environ['REDDIT_PASS']

reddit_subreddit = os.environ['REDDIT_SUBREDDIT']


DB_FILE = os.environ['DB_FILE']

web_useragent = 'python:persoonlijkebonus (by dgc1980)'


reddit = praw.Reddit(client_id=reddit_cid,
                     client_secret=reddit_secret,
                     password=reddit_pass,
                     user_agent=web_useragent,
                     username=reddit_user)
subreddit = reddit.subreddit(reddit_subreddit)



apppath='/data/'
#apppath='./'


con = sqlite3.connect(apppath+DB_FILE)
cursorObj = con.cursor()
cursorObj.execute("CREATE TABLE IF NOT EXISTS schedules(id integer PRIMARY KEY, postid text, schedtime integer)")
cursorObj.execute("CREATE TABLE IF NOT EXISTS weeklyposts(id integer PRIMARY KEY, username text, postcount integer, currentweek integer)")
con.commit()

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                    datefmt='%m-%d %H:%M',
                    filename=apppath+'affiliatebot.log',
                    filemode='a')



console = logging.StreamHandler()
console.setLevel(logging.INFO)
formatter = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
console.setFormatter(formatter)
logging.getLogger('').addHandler(console)
os.environ['TZ'] = 'UTC'


def download(url, file_name):
    with open(file_name, "wb") as file:
        response = requests.get(url)
        file.write(response.content)



f = open(apppath+"submissionids.txt","a+")
f.close()

def submissionID(postid):
    f = open(apppath+"submissionids.txt","a+")
    f.write(postid + "\n")
    f.close()


def check_post(post):
   if post.created < int(time.time()) - (86400*4):
       return
   if post.title[0:1].lower() == "[" or post.title[0:1].lower() == "[" or 1 == 1:
       if post.id in open(apppath+'submissionids.txt').read():
           return
       donotprocess=False
       for top_level_comment in post.comments:
           try:
               if top_level_comment.author and top_level_comment.author.name == reddit_user:
                   submissionID(post.id)
                   break
           except AttributeError:
               pass
       else:
           if not donotprocess:

### Weekly Post Limit
               if 1 > 0:
                  #wikistring = reddit.subreddit('machinatestsub').wiki['bonusbot-goodusers'].content_md
                  wikistring = reddit.subreddit('persoonlijkebonus').wiki['bonusbot-goodusers'].content_md
                  goodsubmittors = wikistring.split("\n")

                  goodsubmittor = 0
                  submittorname = post.author.name
                  for submittor in goodsubmittors:
                      if submittor.lower() == submittorname.lower():
                          goodsubmittor = 1

                  if goodsubmittor == 0:
                      curcount = 0
                      currentweek = time.strftime('%Y%W')
                      con = sqlite3.connect(apppath+DB_FILE, timeout=20)
                      cursorObj = con.cursor()
                      cursorObj.execute('SELECT * FROM weeklyposts WHERE username = "'+submittorname+'" AND currentweek = '+currentweek)
                      rows = cursorObj.fetchall()
                      if len(rows) == 0:
                        cursorObj.execute('INSERT INTO weeklyposts(username, postcount, currentweek) VALUES("'+submittorname+'",1,'+currentweek+')')
                        con.commit()
                      else:
                        curcount = rows[0][2]
                      if int(curcount) > 1:
                          weekly=True
                          logging.info(submittorname+' is over their weekly post limit')
                          post.mod.remove()
                          comment = post.reply("Beste profiteur, zo te zien post je deze week voor de tweede keer! In verband met misbruik moet deze post handmatig worden goedgekeurd. Dit gebeurt meestal dezelfde dag nog. Excuses voor het ongemak!")
                          comment.mod.distinguish(sticky=True)
                          comment.report("filtered submission due to weekly limit")
                      else:
                          curcount=curcount+1
                          cursorObj.execute("UPDATE weeklyposts SET postcount = " + str(curcount) + ' WHERE id = ' + str(rows[0][0]))
                          con.commit()
                      con.close()
###

               tm = dateparser.parse( "monday 3am GMT", settings={'PREFER_DATES_FROM': 'future', 'TIMEZONE': 'UTC', 'TO_TIMEZONE': 'UTC'} )
               tm2 = time.mktime( tm.timetuple() )

               con = sqlite3.connect(apppath+DB_FILE, timeout=20)
               cursorObj = con.cursor()
               cursorObj.execute('INSERT into schedules(postid, schedtime) values(?,?)',(post.id,tm2) )
               con.commit()
               con.close()

               submissionID(post.id)
               return


def run_schedule():
  tm = str(int(time.time()))
  con = sqlite3.connect(apppath+DB_FILE)
  cursorObj = con.cursor()
  cursorObj.execute('SELECT * FROM schedules WHERE schedtime <= ' + tm + ' ORDER BY schedtime DESC LIMIT 0,8;')
  rows = cursorObj.fetchall()
  if len(rows) > 0:
    for row in rows:
      submission = reddit.submission(row[1])
      cat = "None"
      try:
        cat = submission.removed_by_category
      except:
        cat = "None"
      try:
        poster = submission.author
      except:
        poster = "None"

      if cat != "None" and poster != "None":
        logging.info("running schedule on https://reddit.com/" + row[1])

        old_flair = ""
        try:
            old_flair = submission.link_flair_text.lower()
        except:
            pass

        if old_flair == "":
            return
        if old_flair == "Mededeling" or old_flair == "Vraag":
          return

        expiremode=0
        new_flair = ""
        if "VANAF MAANDAG / KOOPZEGELS UIT" in old_flair.upper():
          new_flair = "KORTING LOOPT / KOOPZEGELS UIT"
          flair_template = "9cce08ea-3080-11ea-bfee-0e3b5579f8e9"
        if "VANAF MAANDAG / KOOPZEGELS AAN" in old_flair.upper():
          new_flair = "KORTING LOOPT / KOOPZEGELS AAN"
          flair_template = "9003ce54-d261-11eb-b693-0e8f051ebff1"

        if "KORTING LOOPT / KOOPZEGELS UIT" in old_flair.upper():
          new_flair = "VERLOPEN"
          flair_template = "90cf8a28-3080-11ea-bdb1-0e7131329107"
          expiremode=1
        if "KORTING LOOPT / KOOPZEGELS AAN" in old_flair.upper():
          new_flair = "VERLOPEN"
          flair_template = "90cf8a28-3080-11ea-bdb1-0e7131329107"
          expiremode=1

        if old_flair != "" and new_flair != "":
            logging.info("Changing flair for https://redd.it/" + submission.id)
            submission.mod.flair(    flair_template_id=flair_template  , text=new_flair    )

      cursorObj.execute('DELETE FROM schedules WHERE postid = "'+ row[1]+'"')
      if expiremode == 0:
               tm = dateparser.parse( "sunday 23:59 GMT", settings={'PREFER_DATES_FROM': 'future', 'TIMEZONE': 'UTC', 'TO_TIMEZONE': 'UTC'} )
               tm2 = time.mktime( tm.timetuple() )
               cursorObj.execute('INSERT into schedules(postid, schedtime) values(?,?)',( row[1] ,tm2) )

      con.commit()

  con.close();



run_schedule()
schedule.every(1).minutes.do(run_schedule)
logging.info("bot initialized...." )
while True:
  schedule.run_pending()
  try:
    for post in subreddit.stream.submissions(pause_after=-1):
        if post is None:
            break
        if post.id in open(apppath+'submissionids.txt').read():
          continue
        check_post(post)
  except (prawcore.exceptions.RequestException, prawcore.exceptions.ResponseException):
    logging.info("Error connecting to reddit servers. Retrying in 30 seconds...")
    time.sleep(30)
  except (praw.exceptions.RedditAPIException):
    logging.info("API error. Retrying in 60 seconds...")
    time.sleep(60)
#  except:
#    logging.info("Error connecting to reddit servers. Retrying in 30 seconds...")
#    time.sleep(30)


