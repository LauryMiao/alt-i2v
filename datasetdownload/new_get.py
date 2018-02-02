import bs4
import sys
import os.path
import argparse
import datetime
import pickle
import signal
import http.cookiejar
import re
import json
import random
from multiprocessing import Pool  
from multiprocessing import Process, Queue
import multiprocessing as mp
from concurrent import futures
import time
from threading import Thread as Th
import glob
import requests
from fake_useragent import UserAgent
from multiprocessing import Pool


def html_fetcher(url, phost):
  html = None
  ua = UserAgent()
  for ret in range(10) :
    TIME_OUT = 10.
    try:
      response = requests.get(url, headers = {'User-Agent':str(ua.random)})
      if response.status_code == 200: 
        html = response.text
        break
    except Exception as e:
      print( e )
      continue
  if html == None:
    return (None, None, None)
  soup = bs4.BeautifulSoup(html, "html.parser")
  return (html, soup)

def exit_gracefully(signum, frame):
  signal.signal(signal.SIGINT, original_sigint)
  try:
    if input("\nReally quit? (y/n)> ").lower().startswith('y'): sys.exit(1)
  except KeyboardInterrupt:
    print("Ok ok, quitting")
    sys.exit(1)
  signal.signal(signal.SIGINT, exit_gracefully)

def analyzing(inputs):
  url, index, phost = inputs
  url = bytes(url, 'utf-8')
  html, soup = html_fetcher(url, phost)
  if soup is None:
    print('except miss')
    return None
  img = soup.find('img', {'id':'image'} )
  if img is None:
    return None
  img_url = 'https:{}'.format(img.get('src'))
  save_name = re.sub(r'\?.*$', '', img_url)
  data_tags = img.get('alt')
  data_tags = bytes(data_tags, 'utf-8')
  ua = UserAgent()
  for trial in range(15):

    try:
      response = requests.get(img_url, headers = {'User-Agent':str(ua.random)})
      if response.status_code == 200:     
        with open('imgs/{name}.jpg'.format(name=save_name.split('/')[-1] ),'wb') as f:
            f.write(response.content)
        with open('imgs/{name}.txt'.format(name=save_name.split('/')[-1] ),'wb') as f:
            f.write(data_tags)
        with open('imgs/{name}.url'.format(name=save_name.split('/')[-1] ),'wb') as f:
            f.write(url)
        print('complete storing image of {url}'.format(url=img_url) )
        break
    except Exception as e:
      print( phost )
      print('========', e ,'========')
      time.sleep(1.)
      continue


if __name__ == '__main__':
  original_sigint = signal.getsignal(signal.SIGINT)
  signal.signal(signal.SIGINT, exit_gracefully)
  parser = argparse.ArgumentParser(description='Process Safebooru image tag scraper.')
  parser.add_argument('--mode', help='you can specify mode...')
  parser.add_argument('--proxy', help='you can specify mode...')
  args_obj = vars(parser.parse_args())
  mode = (lambda x:x if x else 'undefined')( args_obj.get('mode') )
  proxy = (lambda x:x if x else 'undefined')( args_obj.get('proxy') )
  phosts = ['http://{proxy}:{proxy}awr003@{phost}:8086'.format(proxy=proxy, phost=phost.strip()) for phost in open('proxys.txt')] 
  if mode == 'scrape':
    finished = set(name.split('/')[-1] for name in glob.glob('./finished/*'))
    samples  = filter( lambda x: str(x) not in finished, range(1, 2653427))
    urls = [ ('http://safebooru.org/index.php?page=post&s=view&id={i}'.format(i=i), i, random.choice(phosts)) for i in samples]
    random.shuffle(urls)
   
    #[ analyzing(url) for url in urls ] 
    # 元々は768で並列処理
    with futures.ProcessPoolExecutor(max_workers=100) as executor:
      executor.map( analyzing, urls )
