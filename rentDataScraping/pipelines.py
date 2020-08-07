# -*- coding: utf-8 -*-
# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html

import pandas as pd
import pgeocode
from datetime import datetime
from rentDataScraping.models import Session, Rental
from dotenv import load_dotenv
load_dotenv()

nomi = pgeocode.Nominatim('de')

class RentdatascrapingPipeline:
    def process_item(self, item, spider):
        return item


class pandasExportExcelPipeline:
    def open_spider(self, spider):
        self.offer_list = []

    def close_spider(self, spider):
        df = pd.DataFrame(self.offer_list)
        date_time = datetime.now()
        now = date_time.strftime("%y%m%d_%H%M")
        df.to_excel('data/' + spider.name + '/' + now + '_items.xlsx')

    def process_item(self, item, spider):
        self.offer_list.append(item)
        return item

class pgPipeline(object):
    def open_spider(self, spider):
        self.session = Session()

    def close_spider(self, spider):
        self.session.close()

    def process_item(self, item, spider):
        # convert offer_id to int
        item['offer_id'] = int(item['offer_id'])

        # if postcode is wrong, do not add
        item['postcode'] = self.change_none_to_zero(self.convert_to_int(item['postcode']))
        if item['postcode'] is None or item['postcode'] < 10000: return

        # convert coordinates to floats
        item['geo_latitude'] = self.convert_to_float(item['geo_latitude'])
        item['geo_longitude'] = self.convert_to_float(item['geo_longitude'])

        if item['geo_latitude'] is None or item['geo_longitude'] is None:
            pcode = nomi.query_postal_code(item['postcode'])
            item['geo_latitude'] = pcode['latitude']
            item['geo_longitude'] = pcode['longitude']

        # convert costs to floats
        item['warmmiete'] = self.convert_to_float(item['warmmiete'])
        item['kaltmiete'] = self.convert_to_float(item['kaltmiete'])
        item['nebenkosten'] = self.convert_to_float(item['nebenkosten'])
        item['heizungskosten'] = self.convert_to_float(item['heizungskosten'])
        item['preis_qm_kalt'] = self.convert_to_float(item['preis_qm_kalt'])

        item['area'] = self.convert_to_float(item['area'])
        item['num_rooms'] = self.convert_to_float(item['num_rooms'])
        if item['num_rooms'] == 0 or item['num_rooms'] is None:
            item['num_rooms'] = 1

        # convert values to ints
        item['kitchen_availability'] = self.change_none_to_zero(self.convert_to_int(item['kitchen_availability']))
        item['handicap_accessible'] = self.change_none_to_zero(self.convert_to_int(item['handicap_accessible']))
        item['balcony'] = self.change_none_to_zero(self.convert_to_int(item['balcony']))
        item['energy_building_year'] = self.change_none_to_zero(self.convert_to_int(item['energy_building_year']))
        item['cellar'] = self.change_none_to_zero(self.convert_to_int(item['cellar']))
        item['pets_allowed'] = self.change_none_to_zero(self.convert_to_int(item['pets_allowed']))
        item['garden'] = self.change_none_to_zero(self.convert_to_int(item['garden']))
        item['elevator'] = self.change_none_to_zero(self.convert_to_int(item['elevator']))

        item['floor_level'] = self.convert_to_int(item['floor_level'])

        rental = Rental(**item)
        self.session.add(rental)
        self.session.commit()
        return item

    def change_none_to_zero(self, value):
        if value is None:
            return 0
        return value

    def convert_to_int(self, value):
        try:
           return int(value)
        except (ValueError, TypeError):
            return None
    
    def convert_to_float(self, value):
        try:
            return float(value)
        except (ValueError, TypeError):
            return None