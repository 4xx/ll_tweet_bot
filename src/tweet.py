# -*- coding: utf-8 -*-
'''
Twitterへ呟くためのリクエストをハンドルする
Created on 2014/04/08

@author: kumagai
'''

import webapp2
import logging
from google.appengine.api.labs import taskqueue
from feed import FeedFetcher
from bot import TwitterBot

class MainHandler(webapp2.RequestHandler):
    '''
    ニュースを呟くためのリクエストをハンドルするためのクラス。
    cronにより定期的に行われるリクエストをハンドルしている
    '''
    
    def get(self):
        logging.info('start tweets ...')
        fetcher = FeedFetcher()
        entries = fetcher.fetch_new_entries()
        if not entries:
            self.response.headers['Content-Type'] = 'text/plain'
            self.response.write('no rss feed\n')
        else:
            for entry in entries:
                taskqueue.add(queue_name='tweet', url='/tweet', params={'message': entry.make_tweets()})
                
class FollowmeHandler(webapp2.RequestHandler):
    '''
    フォロミーを呟くためのリクエストをハンドルするためのクラス。
    cronにより定期的に行われるリクエストをハンドルしている
    '''
    
    _MESSAGE = u'ラブライブのニュースを呟いてます。よろしければフォローお願いします。 #ラブライブ'
    
    def get(self):
        logging.info('start follow me ...')
        taskqueue.add(queue_name='tweet', url='/tweet', params={'message': self._MESSAGE})

class TweetHandler(webapp2.RequestHandler):
    '''
    Twitterへ呟くためのリクエストをハンドルするクラス。
    タスクキューがpostリクエストを送るのでこのクラスでハンドルして呟いている
    '''
    
    def post(self):
        msg = self.request.get('message')
        bot = TwitterBot()
        bot.tweet(msg)
        
logging.getLogger().setLevel(logging.DEBUG)
app = webapp2.WSGIApplication(
                              [('/', MainHandler), 
                               ('/tweet', TweetHandler),
                               ('/followme', FollowmeHandler)], debug=True)