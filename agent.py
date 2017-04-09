#! /usr/bin/env python
# coding: utf-8
import os
from os.path import expanduser
import logging
import subprocess

import requests


username = os.environ.get('SUKI_USER')
password = os.environ.get('SUKI_PASSWORD')

FORMAT = '%(asctime)-15s - %(message)s'
logging.basicConfig(format=FORMAT, level=logging.DEBUG)
logger = logging.getLogger(__name__)


logger.info('Starting now......')

assert username and password, \
    'You must provide `SUKI_USER` and `SUKI_PASSWORD` environment variables!'

session = requests.Session()
session.post('https://suki.moe/api/user/login',
             json=dict(name=username, password=password))
animes = session.get('https://suki.moe/api/home/my_bangumi').json()


def download_episode(episode):
    episode_id = episode['id']
    api = 'https://suki.moe/api/home/episode/%s' % episode_id
    rsp = session.get(api).json()
    videos = rsp.get('videos')
    if not videos:
        logger.warn('Episode %(id)s has nothing to download.'.format(episode))
        return
    video = videos[0]
    logger.info('Start downloading %(bangumi)s'.format(episode))
    subprocess.Popen(['wget', '-P', expanduser('~/Downloads'), video])
    logger.info('Setting episode %(id)s as read.'.format(episode))
    set_read(episode)


def get_unwatched_episodes(anime_id):
    api = 'https://suki.moe/api/home/bangumi/%s' % anime_id
    rsp = session.get(api)
    episodes = rsp.json()['data']['episodes']
    unwatched_episodes = filter(
        lambda x: (x.get('watch_progress') or {}).get('watch_status') != 2,
        episodes)
    logger.info('Unwatched episodes: %s' % str(unwatched_episodes))
    return unwatched_episodes


def set_read(episode):
    episode_id = episode['id']
    bangumi_id = episode['bangumi_id']
    api = 'https://suki.moe/api/watch/history/%s' % episode_id
    logger.info('Setting episode %(id)s as read.'.format(episode))
    session.post(api,
                 json=dict(
                     is_finished=True,
                     bangumi_id=bangumi_id,
                     last_watch_position=1450.048,
                     percentage=1))


def notify(anime):
    args = ['/usr/local/bin/terminal-notifier',
            '-message', 'New anime from suki.moe',
            '-open', 'https://suki.moe',
            '-subtitle', 'New update!',
            '-title', anime['name_cn'],
            '-actions', 'Download,Dismiss,Set read']

    output = subprocess.check_output(args)
    anime_id = anime['id']
    unwatched_episodes = get_unwatched_episodes(anime_id)

    if output == 'Download':
        logger.info('Downloading %(name)s...'.format(anime))
        map(download_episode, unwatched_episodes)
    elif output == 'Dismiss':
        logger.info('Dismissed %(name)s...'.format(anime))
    else:
        logger.info('Setting %(name)s as read.'.format(anime))
        map(set_read, unwatched_episodes)


for anime in animes['data']:
    if anime.get('unwatched_count'):
        notify(anime)


logger.info('Finished successfully!')
