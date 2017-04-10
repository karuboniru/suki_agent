#! /usr/bin/env python
# coding: utf-8
import os
from os.path import expanduser
import logging
import subprocess

try:
    import requests
except ImportError:
    raise ImportError, '`requests` lib is requied!'


username = os.environ.get('SUKI_USER')
password = os.environ.get('SUKI_PASSWORD')

FORMAT = '%(asctime)-15s - %(message)s'
logging.basicConfig(format=FORMAT, level=logging.DEBUG)

assert username and password, \
    'You must provide `SUKI_USER` and `SUKI_PASSWORD` environment variables!'


class SukiAgent(object):
    my_bangumi_api = 'https://suki.moe/api/home/my_bangumi'
    login_api = 'https://suki.moe/api/user/login'

    def __init__(self, username, password):
        self.logger = logging.getLogger(__name__)
        self.session = requests.Session()
        self.login(username, password)

    def login(self, username, password):
        self.session.post(
            self.login_api,
            json=dict(name=username, password=password))

    def download_episode(self, episode):
        episode_id = episode['id']
        api = self.episode_api(episode_id)
        rsp = self.session.get(api).json()
        videos = rsp.get('videos')
        if not videos:
            self.logger.warn(
                'Episode %(id)s has nothing to download.'.format(episode))
            return
        video = videos[0]
        self.logger.info('Start downloading %(bangumi)s'.format(episode))
        subprocess.Popen(['wget', '-P', expanduser('~/Downloads'), video])
        self.set_read(episode)

    def set_read(self, episode):
        episode_id = episode['id']
        bangumi_id = episode['bangumi_id']
        api = self.episode_history_api(episode_id)
        self.logger.info('Setting episode %(id)s as read.'.format(episode))
        self.session.post(
            api,
            json=dict(
                is_finished=True,
                bangumi_id=bangumi_id,
                last_watch_position=1450.048,
                percentage=1))

    def get_unwatched_episodes(self, anime_id):
        api = self.bangumi_api(anime_id)
        rsp = self.session.get(api)
        episodes = rsp.json()['data']['episodes']
        unwatched_episodes = filter(
            lambda x: (x.get('watch_progress') or {}).get('watch_status') != 2,
            episodes)
        self.logger.info('Get unwatched episodes: %s' % unwatched_episodes)
        return unwatched_episodes

    def notify(self, anime):
        args = ['/usr/local/bin/terminal-notifier',
                '-message', 'New anime from suki.moe',
                '-open', 'https://suki.moe',
                '-subtitle', 'New update!',
                '-title', anime['name_cn'],
                '-actions', 'Download,Dismiss,Set read']
        output = subprocess.check_output(args)
        anime_id = anime['id']
        unwatched_episodes = self.get_unwatched_episodes(anime_id)

        if output == 'Download':
            self.logger.info('Downloading %(name)s...'.format(anime))
            map(self.download_episode, unwatched_episodes)
        elif output == 'Dismiss':
            self.logger.info('Dismissed %(name)s...'.format(anime))
        else:
            self.logger.info('Setting %(name)s as read.'.format(anime))
            map(self.set_read, unwatched_episodes)

    def check_and_notify(self):
        self.logger.info('Starting now......')
        animes = self.session.get(self.my_bangumi_api).json()
        for anime in animes['data']:
            if anime.get('unwatched_count'):
                self.notify(anime)
        self.logger.info('Finished successfully!')

    def episode_api(self, episode_id):
        return 'https://suki.moe/api/home/episode/%s' % episode_id

    def episode_history_api(self, episode_id):
        return 'https://suki.moe/api/watch/history/%s' % episode_id

    def bangumi_api(self, anime_id):
        return 'https://suki.moe/api/home/bangumi/%s' % anime_id


SukiAgent(username, password).check_and_notify()
