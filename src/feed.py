# -*- coding: utf-8 -*-
'''
feedparserを利用してGoogleアラートのRSSフィードをパースする
Created on 2014/04/08

@author: kumagai
'''
import feedparser, re
import logging
from urlparse import urlparse, parse_qs
from google.appengine.ext import ndb

class FeedFetcher(object):
    '''
    GoogleアラートのRSSフィードをパースするためのクラス
    '''
    
    _NEWS_FEED = 'YOUR_RSS_FEED_URL'
    _ACTOR_NEWS_FEED = 'YOUR_RSS_FEED_URL'
    
    def __init__(self):
        self._keywords = []
    
    def fetch_new_entries(self):
        '''
        RSSフィードから新しいエントリを取得する。
        定期的にこの処理が呼ばれるため、DataStoreを利用して重複の確認をしているため、
        新しいエントリーがない場合は空のリストが返る
        @return: RSSフィードから取得したエントリリスト
        '''
        
        new_entries = []
        for feed_url in (self._NEWS_FEED, self._ACTOR_NEWS_FEED):
            data = feedparser.parse(feed_url);
            if not data:
                continue
             
            # アラートのキーワードをハッシュタグにしているので、フィードのキーワードを抽出しておく
            self._keywords = self.__parse_keyword(data.feed.title)
            # 新しいエントリのみ取得する
            entries = self.__ignore_exists_entry(data.entries)
            if entries:
                new_entries.extend(entries)
        else:
            return new_entries
    
    def __parse_keyword(self, feed_title):
        '''
        フィードのタイトルからGoogleアラートで設定しているキーワードを抽出する
        @param feed_title: RSSフィードタイトル
        @return: キーワードリスト
        '''
        
        # タイトルは [Google アラート - キーワード1 OR ...] となっているため、
        # 定形文字を除いてキーワードのみ文字列を分割する形で取り出している
        s = feed_title.index('-') + 2
        return feed_title[s:].split(u' OR ')
    
    def __ignore_exists_entry(self, entries):
        '''
        フィード内のエントリで重複しているものを無視する
        @param entries:フィード内のエントリリスト
        @return: 新しいエントリリスト 
        '''
        
        return [self.__make_new_entry(entry) for entry in entries if not self.__exists_entry(entry.title)]
    
    def __exists_entry(self, raw_title):
        '''
        既に使用しているエントリーかどうか確認する
        @param raw_title: エントリーのタイトル
        @return: Trueの場合使用済み、Falseの場合新エントリ
        '''
        
        # エントリータイトルにキーワードが含まれている場合<b>タグが付いているが不要なので削除
        # 重複確認はエントリーのタイトルが重複していないかで判断している
        title = re.sub(r'<\/?b>', '', raw_title)
        entry = EntryModel.query(EntryModel.title == title).get()
        return True if entry else False
    
    def __make_new_entry(self, entry):
        '''
        新しいエントリーオブジェクトを作成する
        @param entry: パースしたRSSフィードのエントリー
        @return: 新しいエントリーオブジェクト
        '''
        
        new_entry = Entry(title = re.sub(r'<\/?b>', '', entry.title),
                            shorten_url = self.__make_shorten_url(entry.link),
                            hash_tag = self.__make_hash_tag(entry.title, entry.summary))
        # 重複確認のため、DataStoreに保存しておく
        self.__put_datastore(new_entry.title)
        
        return new_entry
    
    def __make_hash_tag(self, title, summary):
        '''
        ハッシュタグを作成する。
        アラートのキーワードはエントリー内のタイトルとサマリー内に含まれている。
        2つの情報から含まれているキーワードを抽出してハッシュタグにしている
        @param title: エントリーのタイトル
        @param summary: エントリーのサマリー
        @return: ハッシュタグ文字列（複数有り）
        '''
        
        matched = re.findall(r'<b>(.+?)</b>', title + summary)
        if not matched:
            return ''
        
        # 抽出したキーワードとマッチしているか確認する
        # 「...」のように不要な単語がキーワード化されている場合があった
        tags = [u'#' + m for m in set(matched) if  m in self._keywords];
        # 現在は最大3タグ内までにしておく
        return u' '.join(tags[:3])
    
    def __make_shorten_url(self, url):
        '''
        フィードのリンク情報からつぶやき用のURLを作成する
        @param url: フィードのリンクURL
        @return: 呟き用のURL
        '''
        
        # linkはgoogle.com/url?q=リンク の形式になっているので
        # URLクエリを解析してリンクURLを抽出している
        query_dict = parse_qs(urlparse(url).query)
        return query_dict['q'][0]

    def __put_datastore(self, title):
        '''
        DataStore へエントリーのタイトルを登録する
        @param title: エントリーのタイトル
        '''
        
        model = EntryModel()
        model.title = title
        model.put()
        logging.info('put datastore:' + model.title)
       
class Entry(object):
    '''
    解析したエントリー情報を格納するためのクラス
    '''
    
    def __init__(self, title, shorten_url, hash_tag=''):
        self._title = title
        self._shorten_url = shorten_url
        self._hash_tag = hash_tag
        
    def make_tweets(self):
        '''
        呟き内容を作成する
        @return: 呟き内容
        '''
        
        return u"%s %s %s" % (self._title, self._shorten_url, self._hash_tag)
        
    @property
    def title(self):
        return self._title 
    
    @title.setter
    def title(self, title): 
        self._title = title
        
    @property
    def shorten_url(self):
        return self._shorten_url
    
    @shorten_url.setter
    def shorten_url(self, shorten_url):
        self._shorten_url = shorten_url
        
    @property
    def hash_tag(self):
        return self._hash_tag
    
    @hash_tag.setter
    def hash_tag(self, hash_tag):
        self._hash_tag = hash_tag
        
class EntryModel(ndb.Model):
    '''
    フィードエントリのタイトルを保存するためのDataStoreオブジェクト
    '''
    
    title = ndb.StringProperty()
    