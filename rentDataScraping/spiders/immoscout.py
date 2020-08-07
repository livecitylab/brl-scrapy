# -*- coding: utf-8 -*-
import scrapy
import pathlib
from datetime import datetime
# from locale import atof, setlocale, LC_NUMERIC
from rentDataScraping.items import ImmoscoutItem

date_time = datetime.now()
NOW = date_time.strftime("%y%m%d_%H%M")
NUM_PAGES_TO_CRAWL = 10

class ImmoscoutSpider(scrapy.Spider):
    name = 'immoscout'
    allowed_domains = ['immobilienscout24.de']

    custom_settings = {
        'FEEDS': {
            pathlib.Path('./data/immoscout/' + NOW + '_items.json'): {
                'format': 'json',
                'encoding': 'utf8',
                'store_empty': False,
                'indent': 4,
            },
            pathlib.Path('./data/immoscout/' + NOW + '_items.csv'): {
                'format': 'csv',
            },
        },

    }

    urls = []
    for i in range(NUM_PAGES_TO_CRAWL):
        urls.append('https://www.immobilienscout24.de/Suche/de/berlin/berlin/wohnung-mieten?pagenumber=' + str(i+1))
    start_urls = urls

    def parse(self, response):
        offers = response.css('ul#resultListItems > li')
        for offer in offers:
            url = offer.xpath('.//a[1]/@href').get()
            if url:
                yield response.follow(url=url, callback=self.parse_offer)

    def parse_offer(self, response):
        offer = dict()

        # get main data from the html's head
        head = response.xpath('/html/head')
        title = head.css('title::text').get()
        image = head.xpath(
            './meta[@property="og:image"]/@content').get()
        url = response.url
        description = head.xpath(
            './meta[@name="description"]/@content').get()

        # ADDRESS
        address_block = response.xpath('//div[@class="address-block"]')[0]
        address = address_block.xpath('.//text()').getall()
        address = '\n'.join([i.strip() for i in address if len(i.strip()) > 0])

        num_rooms = response.css('div.is24qa-zi::text').get().strip()
        area = response.css('div.is24qa-flaeche::text').get().strip().split(' ')[0]

        # MERKMALE
        facts = response.css('div.criteriagroup.boolean-listing > span.palm-hide::text').getall()

        # COSTS
        costs = {
            'kaltmiete': None,
            'nebenkosten': None,
            'gesamtmiete': None,
            'kaution': None,
            'area': None,
            'num_rooms': None,
            'heizkosten': None,
            'miete garage/stellplatz': None
        }
        details = response.css('dl.grid')
        for detail in details:
            key = detail.xpath('./dt/text()').get().strip()
            value = detail.xpath('./dd//text()').getall()
            value = [i.strip() for i in value if len(i.strip()) > 0]

            # basic cleanup of values from DOM
            # TODO: need to better clean up values and convert them to numeric
            if key == 'Kaltmiete':
                value = [i for i in value if 'Mit lokalem' not in i] # usual value ['1.940,30 €', 'Mit lokalem Mietspiegel vergleichen']
                value = value[0]
            elif key == 'Nebenkosten' or key=='Heizkosten':
                value = [i for i in value if i != '+'] # usual value ['+', '125 €']
                value = value[0]
            elif 'Kaution' in key: # Kaution o. Genossenschafts­anteile
                key = 'kaution'
                value = [i for i in value if 'Kaution' not in i] # usual value  ['9341.20', 'Kaution später zahlen']
                value = value[0]
            elif 'Miete für Garage/Stellplatz' in key: # Miete für Garage/Stellplatz
                key = 'miete garage/stellplatz'
            elif key == "Wohnfläche ca.":
                key = 'area'
            elif key == "Zimmer":
                key = 'num_rooms'

            if (len(value) == 1):
                value = value[0]
            costs[key.lower()] = value


        # LONG TEXT

        object_description = response.css('pre.is24qa-objektbeschreibung::text').get()
        ausstattung = response.css('pre.is24qa-ausstattung::text').get()
        lage = response.css('pre.is24qa-lage::text').get()
        sonstiges = response.css('pre.is24qa-sonstiges::text').get()

        item = ImmoscoutItem(
            title=title,
            url=url,
            image=image,
            warmmiete=costs['gesamtmiete'],
            address=address,
            kaltmiete=costs['kaltmiete'],
            nebenkosten=costs['nebenkosten'],
            kaution=costs['kaution'],
            area=area,
            num_rooms=num_rooms,
            facts=facts,
            # below is specific to immoscout
            heizkosten=costs['heizkosten'],
            miete_garage_stellplatz=costs['miete garage/stellplatz'],
            text_summary=description,
            text_description = object_description,
            text_ausstattung= ausstattung,
            text_lage = lage,
            text_sonstiges = sonstiges,
        )
        yield item
