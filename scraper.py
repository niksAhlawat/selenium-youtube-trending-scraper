import os
import json
import pandas as pd

# Mail Modules
import smtplib
import mimetypes
from email.message import EmailMessage

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


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

  views = "" #all_spans[0].text
  upload_time = "" #all_spans[1].text
  all_spans = video.find_elements(By.ID, "metadata-line")
  for span in all_spans:
    print (span.text)
    views, upload_time = all_spans
  

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
    sender = "temp.developmentmail@gmail.com"
    recipient = "temp.developmentmail@gmail.com"
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
  #videos_df = pd.DataFrame(videos_data)
  #print(videos_df)
  #videos_df.to_csv('trending.csv', index=None)

  print("Send the results over email")
  body = json.dumps(videos_data, indent=2)
  send_email(body)

  print('Finished.')