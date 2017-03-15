#! /usr/bin/env python
# coding: utf-8
import os
from os.path import expanduser
import subprocess
import requests

username = os.environ.get('SUKI_USER')
password = os.environ.get('SUKI_PASSWORD')

assert username and password, \
    'You must provide `SUKI_USER` and `SUKI_PASSWORD` environment variables!'

session = requests.Session()
session.post('https://suki.moe/api/user/login',
             json=dict(name=username, password=password))
animes = session.get('https://suki.moe/api/home/my_bangumi').json()


def download_episode(episode):
    episode_id = episode['id']
    bangumi_id = episode['bangumi_id']
    api = 'https://suki.moe/api/home/episode/%s' % episode_id
    rsp = session.get(api).json()
    video = rsp['videos'][0]
    subprocess.Popen(['wget', '-P', expanduser('~/Downloads'), video])

    history_api = 'https://suki.moe/api/watch/history/%s' % episode_id
    session.post(history_api,
                 json=dict(
                     is_finished=True,
                     bangumi_id=bangumi_id,
                     last_watch_position=1450.048,
                     percentage=1))


def download(anime_id):
    api = 'https://suki.moe/api/home/bangumi/%s' % anime_id
    rsp = session.get(api)
    episodes = rsp.json()['data']['episodes']
    unwatched_episodes = filter(
        lambda x: x['watch_progress']['watch_status'] != 2, episodes)
    map(download_episode, unwatched_episodes)


def notify(anime):
    args = ['terminal-notifier', '-message', 'New anime from suki.moe',
            '-open', 'https://suki.moe',
            '-subtitle', 'New update!',
            '-title', anime['name_cn'],
            '-actions', 'Download,Dismiss,Set read']

    output = subprocess.check_output(args)
    anime_id = anime['id']
    if output == 'Download':
        download(anime_id)
    elif output == 'Dismiss':
        print 'dismissed...'
    else:
        print 'Have read.'

for anime in animes['data']:
    if anime.get('unwatched_count'):
        notify(anime)

