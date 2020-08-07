# -*- coding: utf-8 -*-
import scrapy
import json
import re
from datetime import datetime
from scrapy.shell import inspect_response
from rentDataScraping.items import WgGesuchtItemAPI
from rentDataScraping.models import Session, Rental

date_time = datetime.now()
NOW = date_time.strftime("%y%m%d_%H%M")

headers = {
    "X-Client-Id": "wg_mobile_app",
    "X-Requested-With": "com.wggesucht.android"
}


class WgGesuchtApiSpider(scrapy.Spider):
    '''Spider to crawl the private API endpoint, instead of the live website'''
    name = 'wg-gesucht-api'
    allowed_domains = ['wg-gesucht.de']

    def get_scraped_ids(self):
        session = Session()
        ids = [r.offer_id for r in session.query(Rental.offer_id).filter_by(site="wg-gesucht").order_by(Rental.offer_id)]
        # print(ids)
        session.close()
        print("Got existing IDS in DB, to avoid scraping duplicates... [" + str(len(ids))+"]")
        return ids



    def start_requests(self):
        NUM_PAGES_TO_CRAWL = 2
        RESULTS_PER_PAGE = "100"

        self.scraped_ids = self.get_scraped_ids()

        # Assemble URLs
        base_url = 'https://www.wg-gesucht.de/api/asset/offers/?ad_type=0&bal=&city_id=8&dFr=&dFrDe=&dTo=&dToDe=&exContAds=&exc=&ff=&fur=&gar=&han=&img=1&img_only=1&kit=&noDeact=1&ot=&pet=&rMax=&radAdd=&radDis=&radLat=&radLng=&rmMax=&rmMin=&sMin=&sin=&sort_column=&sort_order=&wgAge=&wgArt=&wgFla=&wgMnF=&wgMxT=&wgSea=&wgSmo='
        categories = ["1", "2", "3"]  # 0=WG-Zimmer, 1=1-Zimmer Wohnung, 2=Wohnung, 3=Haus
        rent_type = "2"  # 2=unbefristes, 1=befristet
        urls = []
        for category in categories:
            for i in range(1, NUM_PAGES_TO_CRAWL + 1):
                urls.append(
                    base_url + "&category=" + category + "&rent_type=" + rent_type + "&limit=" + RESULTS_PER_PAGE + "&page=" + str(
                        i))

        for url in urls:
            yield scrapy.Request(url=url, headers=headers, callback=self.parse)

    def parse(self, response):
        json_response = json.loads(response.body)
        offers = json_response['_embedded']["offers"]
        # existing_ids = self.get_scraped_ids()
        # print(existing_ids)
        urls = []
        for offer in offers:
            # try to skip offers that are tausch/swap
            if self.is_swap(title=offer['offer_title']): continue
            # see if offer_id has already been scraped
            offer_id = int(offer['offer_id'])
            if offer_id in self.scraped_ids:
                print("Item ID " + str(offer_id) + " already scraped. SKIPPING.")
                continue
            #finally if all the checks pass, add the URL to be scraped in the next step
            urls.append("https://www.wg-gesucht.de/api/public/offers/" + str(offer_id))

        # if the loop above generated any URLs, scrape them
        if len(urls) > 0:
            print("---")
            print("Found ["+ str(len(urls)) + "] new rentals to scrape. STARTING")
            for url in urls:
                yield scrapy.Request(url=url, headers=headers, callback=self.parse_offer)
        else:
            print("---")
            print("No new rentals in this page to scrape.")
            return

    def parse_offer(self, response):
        json_response = json.loads(response.body)
        # debug (uncomment next line to debug)
        # inspect_response(response, self)

        # define property type
        property_types = [None, 'Wohnung', 'Wohnung', 'Haus']
        property_type = property_types[int(json_response['category'])]

        # fix kitchen availability
        # 0 = no info > None
        # 1 = Eigene Küche > 1
        # 2 = Kochnische > 1
        # 3 = Küchenmitbenutzung > 1
        # 4 = Nicht vorhanden > 0
        kitchen_values = [None, 1, 1, 1, 0]
        kitchen_availability = kitchen_values[int(json_response["kitchen_availability"])]

        # fix handicap_accessible
        # 0 = no info > None
        # 1 = Barrierefrei or EG > 1
        # 2 = No > 0
        handicap_values = [None, 1, 0]
        handicap_accessible = handicap_values[int(json_response["handicap_accessible"])]

        # fix heating
        # 0 = no info > None
        # 1 = Zentralheizung
        # 2 = Gasheizung
        # 3 = Ofenheizung
        # 4 = Fernwärme
        heating_values = [None, 'central_heating', 'gas_heating', 'self_contained_central_heating', 'district_heating']
        heating = heating_values[int(json_response["heating"])]

        item = WgGesuchtItemAPI(
            site="wg-gesucht",
            title=json_response['offer_title'],
            url=response.url,
            property_type=property_type,
            warmmiete=json_response['total_costs'],
            kaltmiete=json_response['rent_costs'],
            nebenkosten=json_response['utility_costs'],
            heizungskosten=None,
            kaution=json_response['bond_costs'],
            area=json_response['property_size'],
            num_rooms=json_response['number_of_rooms'],
            pets_allowed=None,
            address=json_response['street'],
            postcode=json_response['postcode'],
            geo_latitude=json_response['geo_latitude'],
            geo_longitude=json_response['geo_longitude'],
            preis_qm_kalt=float(json_response['rent_costs']) / float(json_response['property_size']),
            offer_id=json_response['offer_id'],
            available_from_date=json_response["available_from_date"],
            freetext_property_description=json_response["freetext_property_description"],
            freetext_area_description=json_response["freetext_area_description"],
            freetext_other=json_response["freetext_other"],
            floor_level=json_response["floor_level"],
            kitchen_availability=kitchen_availability,
            balcony=json_response["balcony"],
            garden=json_response["garden"],
            cellar=json_response["cellar"],
            heating=heating,
            elevator=json_response["elevator"],
            energy_building_year=json_response["energy_building_year"],
            energy_efficiency_class=json_response["energy_efficiency_class"],
            energy_consumption=json_response["energy_consumption"],
            handicap_accessible=handicap_accessible,
        )
        yield item

    def is_swap(self, title):
        return re.search('tausch', title, re.IGNORECASE) or re.search('swap', title, re.IGNORECASE)
