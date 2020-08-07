# -*- coding: utf-8 -*-
import scrapy
import re
import pathlib
from datetime import datetime
# from scrapy.shell import inspect_response
from rentDataScraping.items import WgGesuchtItem

date_time = datetime.now()
NOW = date_time.strftime("%y%m%d_%H%M")
NUM_PAGES_TO_CRAWL = 10

class WgGesuchtSpider(scrapy.Spider):
    name = 'wg-gesucht'
    allowed_domains = ['wg-gesucht.de']

    custom_settings = {
        'FEEDS': {
            pathlib.Path('./data/wg-gesucht/'+NOW+'_items.json'): {
                'format': 'json',
                'encoding': 'utf8',
                'store_empty': False,
                'indent': 4,
            },
            pathlib.Path('./data/wg-gesucht/'+NOW+'_items.csv'): {
                'format': 'csv',
            },
        }
    }

    urls = []
    for i in range(NUM_PAGES_TO_CRAWL):
        urls.append( 'https://www.wg-gesucht.de/wohnungen-in-Berlin.8.2.1.' + str(i) + '.html')
    start_urls = urls

    def parse(self, response):
        #debug
        # inspect_response(response, self)

        offers = response.css('div.offer_list_item')
        links = offers.xpath('//h3/a/@href').getall()
        for url in links:
            if not url.startswith("http"):
                yield response.follow(url=url, callback=self.parse_offer)



    def parse_offer(self, response):
        # parsing each rental offer entry

        head = response.xpath('/html/head')
        title = head.xpath(
            './meta[@property="og:title"]/@content').get()
        image = head.xpath(
            './meta[@property="og:image"]/@content').get()
        url = head.xpath(
            './meta[@property="og:url"]/@content').get()

        key_facts = response.css(
            'h2.headline-key-facts::text').getall()
        area = float(re.findall(r'\d+', key_facts[0])[0])
        warmmiete = float(re.findall(r'\d+', key_facts[1])[0])
        num_rooms = float(re.findall(r'\d+', key_facts[2])[0])

        # cost breakdown table
        costs = {
            'miete': None,
            'kaution': None,
            'ablösevereinbarung': None,
            'sonstige kosten': None,
            'nebenkosten': None
        }
        costs_div = response.xpath('//h3[contains(text(), "Kosten")]/..')
        costs_rows = costs_div.xpath('./table/tr')
        # offer['costs'] = dict()
        for row in costs_rows:
            # TODO: keys are in German, do we want to translate to English?
            key = row.xpath('./td[1]/text()').get().strip().replace(':', '')
            if len(key) > 0:
                value = row.xpath('./td[2]/b/text()').get()
                if value != 'n.a.':
                    value = float(re.findall(
                        r'\d+', value)[0])
                costs[key.lower()] = value

        # address
        address_div = response.xpath('//h3[contains(text(), "Adresse")]/..')
        address_parts_dirty = address_div.xpath('./a/text()').getall()
        address_parts = [i.strip()
                         for i in address_parts_dirty if len(i.strip()) > 0]
        for i in range(len(address_parts)):
            address_parts[i] = address_parts[i].strip()
        address = ', '.join(address_parts)

        # availability
        availability_div = response.xpath(
            '//h3[contains(text(), "Verfügbarkeit")]/..')
        availability_parts_dirty = availability_div.xpath(
            './p//text()').getall()
        availability = [i.strip() for i in availability_parts_dirty if len(i.strip()) > 0]
        from_date = availability[1]
        to_date = ''
        # check if there is a "frei bis" date
        if len(availability) == 4:
            to_date = availability[3]

        # time the offer has been online
        # can be either "X Stunden" or a date
        # TODO: always get a date and time (calculate when it is "X Stunden")
        online_since = response.xpath(
            '//b[contains(text(), "Online")]/text()').get().strip().replace('Online: ', '')

        # List of facts about the offer ("Altbau", "3. OG", "mobliert", "Eigene Kuche", etc)
        # TODO: figure out all the possibilities and put them into their own columns, with a True or False value
        facts_div = response.xpath(
            '//h3[contains(text(), "Angaben zum Objekt")]/..')
        facts_dirty = facts_div.css('div.row ::text').getall()

        facts = [i.strip()
              for i in facts_dirty if (len(i.strip()) > 0) and not 'Ab dem 1. Mai' in i]

        # free text description of the ads
        # there are 3 types of blocks, each with an id of freitext_X
        # freitext_0 = "Wohnung"
        # freitext_1 = "Lage"
        # freitext_2 = ? , not existing
        # freitext_3 = "Sonstiges"
        freitext = {
            'wohnung': '',
            'lage': '',
            'sonstiges': ''
        }
        description_divs = response.xpath(
            '//div[contains(@id, "freitext")]')
        keys = ["Wohnung", "Lage", "X", "Sonstiges"]  # TODO: figure out if X is something
        for div in description_divs:
            text_list = div.xpath('./p[1]//text()').getall()
            if len(text_list) > 0:
                # get the title based on the last number of the div id ("freitext_01", for ex)
                div_id = div.xpath('./@id').get()
                key = keys[int(div_id[-1])]
                freitext[key.lower()] = ' '.join(text_list).strip()

        # generate item
        # which will be collected and later written to the csv file
        item = WgGesuchtItem(
            title=title,
            url = url,
            image = image,
            warmmiete=warmmiete,
            address= address,
            kaltmiete=costs['miete'],
            nebenkosten = costs['nebenkosten'],
            kaution = costs['kaution'],
            area = area,
            num_rooms = num_rooms,
            facts = facts,
            # below is specific to wg-gesucht
            sonstige_kosten=costs['sonstige kosten'],
            abloesevereinbarung = costs['ablösevereinbarung'],
            from_date = from_date,
            to_date = to_date,
            online_since = online_since,
            text_wohnung = freitext['wohnung'],
            text_lage = freitext['lage'],
            text_sonstiges = freitext['sonstiges']
        )
        yield item
