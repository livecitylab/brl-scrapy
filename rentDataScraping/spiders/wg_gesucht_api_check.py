# -*- coding: utf-8 -*-
import scrapy
import os
import json
import pathlib
import psycopg2 as pg
import urllib.parse as urlparse
from datetime import datetime
from rentDataScraping.items import WgGesuchtItemCheck

date_time = datetime.now()
NOW = date_time.strftime("%y%m%d_%H%M")

headers = {
    "X-Client-Id": "wg_mobile_app",
    "X-Requested-With": "com.wggesucht.android"
}


class WgGesuchtApiCheckSpider(scrapy.Spider):
    '''Spider created to update database fields with missing values,
    or to explore the current data to answer questions about it'''
    name = 'wg-gesucht-api-check'
    allowed_domains = ['wg-gesucht.de']

    custom_settings = {
        # 'FEEDS': {
        #     pathlib.Path('./data/wg-gesucht-api-check/' + NOW + '_items.json'): {
        #         'format': 'json',
        #         'encoding': 'utf8',
        #         'store_empty': False,
        #         'indent': 4,
        #     },
        # },
        'ITEM_PIPELINES': {
            'rentDataScraping.pipelines.pgPipeline': None
        }
    }

    def get_scraped_ids(self, query):
        '''Use this function to select the desired IDs from the DB
        you can change it as you use it'''
        url = urlparse.urlparse(os.environ['DATABASE_URL'])
        dbname = url.path[1:]
        user = url.username
        password = url.password
        host = url.hostname
        port = url.port
        self.connection = pg.connect(host=host, user=user, password=password, database=dbname,
                                     port=port, sslmode='require')
        self.cur = self.connection.cursor()
        self.cur.execute(query)
        id_tuples = self.cur.fetchall()
        self.cur.close()
        self.connection.close()
        return [i[0] for i in id_tuples]

    def start_requests(self):
        self.scraped_ids = self.get_scraped_ids(
            "SELECT offer_id FROM rental WHERE site='wg-gesucht' AND heating = '4' ORDER BY offer_id ASC")
        urls = []
        for offer_id in self.scraped_ids:
            urls.append("https://www.wg-gesucht.de/" + str(offer_id) + ".html")
        # print('urls to scrape:')
        # print(urls)
        if len(urls) > 0:
            for url in urls:
                yield scrapy.Request(url=url, headers=headers, callback=self.parse_offer)
        else:
            yield None

    def parse_offer(self, response):
        # parsing each rental offer entry
        # List of facts about the offer ("Altbau", "3. OG", "mobliert", "Eigene Kuche", etc)
        # TODO: figure out all the possibilities and put them into their own columns, with a True or False value
        facts_div = response.xpath(
            '//h3[contains(text(), "Angaben zum Objekt")]/..')
        facts_dirty = facts_div.css('div.row ::text').getall()

        facts = [i.strip()
                 for i in facts_dirty if (len(i.strip()) > 0) and not 'Ab dem 1. Mai' in i]

        item = WgGesuchtItemCheck(
            check="heating = 4",
            facts=facts
        )
        yield item
