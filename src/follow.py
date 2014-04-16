# -*- coding: utf-8 -*-
'''
フォローのリクエストをハンドルする
Created on 2014/04/09

@author: kumagai
'''

import webapp2
import logging
from google.appengine.api.labs import taskqueue
from bot import TwitterBot

class RefollowHandler(webapp2.RequestHandler):
    '''
    リフォローリクエストをハンドするためのクラス。
    ronにより定期的に行われるリクエストをハンドルしている
    '''
    
    def get(self):
        logging.info('start refollow ...')
        
        bot = TwitterBot()
        not_follow_users = bot.get_not_follow_users()
        
        if not not_follow_users:
            self.response.headers['Content-Type'] = 'text/plain'
            self.response.write('follow all users\n')
            return
            
        for i, not_follow_id in enumerate(not_follow_users):
            if i >= TwitterBot.NUM_OF_FOLLOW:
                break
            
            taskqueue.add(queue_name='follow', 
                          url='/follow', 
                          params={'task': 'refollow', 'id':not_follow_id})
 
class UnfollowHandler(webapp2.RequestHandler):
    '''
    フォロー解除リクエストをハンドするためのクラス。
    ronにより定期的に行われるリクエストをハンドルしている
    '''
    
    def get(self):
        logging.info('start unfollow ...')
        
        bot = TwitterBot()
        not_firend_users = bot.get_not_friend_users()
        
        if not not_firend_users:
            self.response.headers['Content-Type'] = 'text/plain'
            self.response.write('Not the user who is only follow\n')
            return
        
        for i, not_friend_id in enumerate(not_firend_users):
            if i >= TwitterBot.NUM_OF_FOLLOW:
                break
           
            taskqueue.add(queue_name='follow', 
                          url='/follow', 
                          params={'task': 'unfollow', 'id': not_friend_id})
            
class FollowTaskHandler(webapp2.RequestHandler):
    '''
    フォローのリクエストをハンドルするクラス。
    タスクキューがpostリクエストを送るのでこのクラスでハンドルして処理している
    '''
    
    def post(self):
        bot = TwitterBot()
        user_id = self.request.get('id')
        logging.info('user id: ' + str(user_id))
        if self.request.get('task') == 'refollow':
            bot.refollow(user_id)
        else:
            bot.unfollow(user_id)
        
logging.getLogger().setLevel(logging.DEBUG)
app = webapp2.WSGIApplication(
                              [('/refollow', RefollowHandler),
                               ('/unfollow', UnfollowHandler),
                               ('/follow', FollowTaskHandler)], debug=True)
