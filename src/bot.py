# -*- coding: utf-8 -*-
'''
Twitter-Python を使用しTwitter APIを叩く
Created on 2014/04/08

@author: kumagai
'''

import logging
from requests import ConnectionError
import twitter
from twitter import TwitterError

class TwitterBot(object):
    '''
    Twitterへの呟き、ユーザのリフォローとフォロー解除を行うためのクラス
    '''
    
    _CONSUMER_KEY = 'YOUR_CONSUMER_KEY'
    _CONSUMER_SECRET = 'YOUR_CONSUMER_SECRET'
    _ACCESS_TOKEN = 'YOUR_ACCESS_TOKEN'
    _ACCESS_TOKEN_SECRET = 'YOUR_ACCESS_TOKEN_SECRET'
    
    NUM_OF_FOLLOW = 20

    def __init__(self):
        try:
            self._api = twitter.Api(consumer_key=self._CONSUMER_KEY,
                                    consumer_secret=self._CONSUMER_SECRET,
                                    access_token_key=self._ACCESS_TOKEN,
                                    access_token_secret=self._ACCESS_TOKEN_SECRET,
                                    cache=None)
            self._id = self._api.VerifyCredentials().GetId()
        except ConnectionError, e:
            logging.exception(e)
        
    def tweet(self, message):
        '''
        Twitterへ対象の内容を呟く
        @param message: ツイート内容 
        '''
        
        if message:
            try:
                status = self._api.PostUpdate(message)
                logging.info('tweet with %s, id: %d' % (message, status.GetId()))
            except TwitterError, e:
                logging.exception(e)
                logging.debug('error tweet with ' + message)
            except ConnectionError, e:
                logging.exception(e)
                
    def get_not_follow_users(self):
        '''
        未フォローユーザのIDリストを取得する
        @return:  未フォローユーザのIDリスト
        '''
        
        return set(self._api.GetFollowerIDs(self._id)) - set(self._api.GetFriendIDs(self._id))
    
    def get_not_friend_users(self):
        '''
        フォローのみのユーザIDリストを取得する
        @return: フォローのみのユーザIDリスト
        '''
        
        return set(self._api.GetFriendIDs(self._id)) - set(self._api.GetFollowerIDs(self._id))
        
    def refollow(self, not_follow_id):
        '''
        対象のユーザをフォローする
        @param not_follow_id: フォローするユーザのID
        '''
        
        try:
            followed = self._api.CreateFriendship(not_follow_id)
            logging.info('followd user %s, id: %s' % (followed.GetName(), followed.GetId()))
        except TwitterError, e:
            logging.exception(e)
        except ConnectionError, e:
            logging.exception(e)
            
    def unfollow(self, only_follow_id):
        '''
        対象のユーザのフォローを解除する
        @param  only_follow_id: 対象のユーザID
        '''
        
        try:
            unfollowed = self._api.DestroyFriendship(only_follow_id)
            logging.info('unfollowd user %s, id: %s' % (unfollowed.GetName(), unfollowed.GetId()))
        except TwitterError, e:
            logging.exception(e)
        except ConnectionError, e:
            logging.exception(e)
