import os
import json
import pandas as pd

import re

# Mail Modules
import smtplib
import mimetypes
from email.message import EmailMessage

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Date Time Modules
import datetime
from dateutil.relativedelta import relativedelta


YOUTUBE_TRENDING_URL = 'https://www.youtube.com/feed/trending'

def get_driver():
  chrome_options = Options()
  chrome_options.add_argument('--no-sandbox')
  chrome_options.add_argument('--headless')
  chrome_options.add_argument('--disable-dev-shm-usage') 
  driver = webdriver.Chrome(options=chrome_options)
  return driver

def get_videos(driver):
  VIDEO_DIV_TAG = 'ytd-video-renderer'
  driver.get(YOUTUBE_TRENDING_URL)
  #videos = driver.find_elements(By.TAG_NAME, VIDEO_DIV_TAG)
  videos = []
  try:
    WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located((By.TAG_NAME, VIDEO_DIV_TAG)))
    
    videos = driver.find_elements(By.TAG_NAME,VIDEO_DIV_TAG)
  except Exception:
    driver.quit()
  return videos
  

def parse_video(video):
  title_tag = video.find_element(By.ID, 'video-title')
  title = title_tag.text
  url = title_tag.get_attribute('href')
  
  thumbnail_tag = video.find_element(By.TAG_NAME, 'img')
  thumbnail_url = thumbnail_tag.get_attribute('src')

  channel_div = video.find_element(By.CLASS_NAME, 'ytd-channel-name')
  channel_name = channel_div.text
  
  description = video.find_element(By.ID, 'description-text').text  

  views = "" 
  upload_time = "" 
  all_spans = video.find_elements(By.ID, "metadata-line")
  
  for i in all_spans:
    spans = (i.text).split("\n")
    views, upload_time = spans

  views = int (view_convert(views))
  upload_time = get_past_date(upload_time)

  return {
    'title': title,
    'url': url,
    'thumbnail_url': thumbnail_url,
    'channel': channel_name,
    'description': description,
    'views' : views,
    'upload_time': upload_time
  }

def send_email(body):
  try :
    message = EmailMessage()
    sender = "nikhil.kumar@iic.ac.in"
    recipient = "nikhil.kumar@iic.ac.in"
    password = os.environ['GMAIL_PASSWORD']

    message['From'] = sender
    message['To'] = recipient
    message['Subject'] = 'Scrap Top Trending YouTube Videos'
    
    message.set_content(body)
    mime_type, _ = mimetypes.guess_type('trending.csv')
    mime_type, mime_subtype = mime_type.split('/')

    with open('trending.csv', 'rb') as file:
      message.add_attachment(file.read(),
      maintype=mime_type,
      subtype=mime_subtype,
      filename='trending.csv')
  
    mail_server = smtplib.SMTP_SSL('smtp.gmail.com')
    mail_server.login(sender, password)
    mail_server.send_message(message)
    mail_server.quit()

  except:
    print('Something went wrong...')


def view_convert(str):
    res = re.findall(r'([-+]?\d*\.?\d+|\d+)(\w+?)', str.split()[0])
    num = float(res[0][0])
    val = res[0][1]
    mul = 0
    if val == "M":
        mul = num * 1000000
    elif val == "B":
        mul = num * 1000000000
    elif val == "K":
        mul = num * 1000
    else:
        mul = num * 1
    return mul



def get_past_date(str_days_ago):
    TODAY = datetime.date.today()
    splitted = str_days_ago.split()
    if len(splitted) == 1 and splitted[0].lower() == 'today':
        return str(TODAY.isoformat())
    elif len(splitted) == 1 and splitted[0].lower() == 'yesterday':
        date = TODAY - relativedelta(days=1)
        return str(date.isoformat())
    elif splitted[1].lower() in ['hour', 'hours', 'hr', 'hrs', 'h']:
        date = datetime.datetime.now() - relativedelta(hours=int(splitted[0]))
        return str(date.date().isoformat())
    elif splitted[1].lower() in ['day', 'days', 'd']:
        date = TODAY - relativedelta(days=int(splitted[0]))
        return str(date.isoformat())
    elif splitted[1].lower() in ['wk', 'wks', 'week', 'weeks', 'w']:
        date = TODAY - relativedelta(weeks=int(splitted[0]))
        return str(date.isoformat())
    elif splitted[1].lower() in ['mon', 'mons', 'month', 'months', 'm']:
        date = TODAY - relativedelta(months=int(splitted[0]))
        return str(date.isoformat())
    elif splitted[1].lower() in ['yrs', 'yr', 'years', 'year', 'y']:
        date = TODAY - relativedelta(years=int(splitted[0]))
        return str(date.isoformat())
    else:
        return "Wrong Argument format"    


if __name__ == "__main__":
  print('Creating driver')
  driver = get_driver()

  print('Fetching trending videos')
  videos = get_videos(driver)
  if not videos:
    print ("No videos ")
  
  print(f'Found {len(videos)} videos')

  print('Parsing top videos')
  videos_data = [parse_video(video) for video in videos[:10]]
  
  print('Save the data to a CSV')
  videos_df = pd.DataFrame([parse_video(video) for video in videos])
  #print(videos_df)
  videos_df.to_csv('trending.csv', index=None)

  print("Send the results over email")
  body = json.dumps(videos_data, indent=2)
  send_email(body)

  print('Finished.')