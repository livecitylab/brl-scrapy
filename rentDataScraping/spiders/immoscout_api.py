# -*- coding: utf-8 -*-
import scrapy
import json
from datetime import datetime
# from scrapy.shell import inspect_response
from rentDataScraping.items import ImmoscoutItemAPI
from rentDataScraping.models import Session, Rental

date_time = datetime.now()
NOW = date_time.strftime("%y%m%d_%H%M")

class ImmoscoutApiSpider(scrapy.Spider):
    name = 'immoscout-api'
    allowed_domains = ['immobilienscout24.de']

    def get_scraped_ids(self):
        session = Session()
        ids = [r.offer_id for r in
               session.query(Rental.offer_id).filter_by(site="immoscout").order_by(Rental.offer_id)]
        # print(ids)
        session.close()
        print("-----")
        print("Got existing IDS in DB, to avoid scraping duplicates... [" + str(len(ids)) + "]")
        print("-----")
        return ids

    def start_requests(self):
        # First get an authorization token
        url = 'https://publicauth.immobilienscout24.de/oauth/token'
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        body = 'client_secret=1Wg0YZtnQQZCntxN&client_id=AndroidApp-QuickCheckKey&grant_type=client_credentials'
        yield scrapy.Request(url=url, body=body, headers=headers, method="POST", callback=self.parse_token,
                             meta={'proxy': None})

    def parse_token(self, response):
        json_response = json.loads(response.body)
        # Assemble headers
        token = json_response['access_token']
        headers = {
            'Authorization': 'Bearer ' + token
        }

        self.scraped_ids = self.get_scraped_ids()

        # Assemble URLs
        base_url = "https://api.mobile.immobilienscout24.de/search/map/v3?searchType=region&features=adKeysAndStringValues%2Cviareporting%2CvirtualTour&geocodes=1276003001&sorting=standard"
        num_pages = 1
        items_per_page = 300
        realestatetypes = ['apartmentrent', "houserent"]
        urls = []
        for realestatetype in realestatetypes:
            url = base_url + '&realestatetype=' + realestatetype
            for i in range(1, num_pages + 1):
                url = url + '&pagesize=' + str(items_per_page) + '&pagenumber=' + str(i)
                urls.append(url)

        # CRAWL
        for url in urls:
            yield scrapy.Request(url=url, headers=headers, callback=self.parse_offer_list)

    def parse_offer_list(self, response):
        # debug
        # inspect_response(response, self)
        json_response = json.loads(response.body)
        offer_ids = []
        for marker in json_response['markers']:
            offer_ids.extend([i['id'] for i in marker['objects']])
        print(offer_ids)
        urls = []
        for offer_id in offer_ids:
            if int(offer_id) in self.scraped_ids:
                print("Item ID " + str(offer_id) + " already scraped. SKIPPING.")
                continue
            urls.append("https://api.mobile.immobilienscout24.de/expose/" + offer_id + "?searchId=&nextgen=false")
        if len(urls) > 0:
            print("---")
            print("Found [" + str(len(urls)) + "] new rentals to scrape. STARTING")
            for url in urls:
                yield scrapy.Request(url=url, headers=response.request.headers, callback=self.parse_offer)
        else:
            print("---")
            print("No new rentals in this page to scrape.")
            return


    def convert_boolean_field(self, value):
        if value == 'y':
            return 1
        elif value == 'n':
            return 0
        else:
            return None

    def parse_offer(self, response):
        # debug: uncomment the following line to debug the response in the terminal, using Scrapy Shell
        # inspect_response(response, self)

        json_response = json.loads(response.body)
        # get main sections
        sections = json_response['sections']

        # initialize variables
        title = geo_latitude = geo_longitude = address = kaution = preis_qm_kalt = available_from_date = freetext_other = freetext_property_description = freetext_area_description = freetext_ausstattung = None

        # loop through all sections
        for section in sections:
            if section['type'] == 'TITLE':
                title = section['title']

            # LOCATION
            elif section['type'] == 'MAP':
                if 'location' in section:
                    geo_latitude = section['location'].get('lat', None)
                    geo_longitude = section['location'].get('lng', None)
                addressLine1 = section.get('addressLine1', None)
                addressLine2 = section.get('addressLine2', None)
                address = addressLine1 + ' ' + addressLine2
                if 'The full address is available from the agent.' in address:
                    address = address.replace('The full address is available from the agent.', '')

            # the sections below come in either German or English,
            # depending on the location of the proxy used in the request

            # some costs (more later)
            elif section['type'] == 'ATTRIBUTE_LIST':
                if any(item in section['title'] for item in ['Kosten', 'Costs']):
                    attrs = section['attributes']
                    for attr in attrs:
                        if any(item in attr['label'] for item in ['Kaution', 'Deposit']):
                            kaution = attr['text']
                        elif any(item in attr['label'] for item in ['Preis/m', 'Net Price/m']):
                            preis_qm_kalt =attr['text']

                # date
                elif any(item in section['title'] for item in ['Hauptkriterien', 'Main criteria']):
                    attrs = section['attributes']
                    for attr in attrs:
                        if any(item in attr['label'] for item in ['Bezugsfrei', 'Vacant']):
                            available_from_date = attr['text']
                            break

            # free text
            elif section['type'] == 'TEXT_AREA':
                if any(item in section['title'] for item in ['Objektbeschreibung', 'Property description']):
                    freetext_property_description = section['text']
                elif any(item in section['title'] for item in ['Ausstattung', 'Furnishing']):
                    freetext_ausstattung = section['text']
                elif any(item in section['title'] for item in ['Lage', 'Location']):
                    freetext_area_description = section['text']
                elif any(item in section['title'] for item in ['Sonstiges', 'Further notes']):
                    freetext_other = section['text']

        # this section contain lots of the wanted parameters in a more direct way
        parameters = json_response['adTargetingParameters']

        warmmiete = parameters.get('obj_totalRent')
        kaltmiete = parameters.get('obj_baseRent')
        nebenkosten = parameters.get('obj_serviceCharge')
        heizungskosten = parameters.get('obj_heatingCosts')
        area = parameters.get('obj_livingSpace')
        num_rooms = parameters.get('obj_noRooms')
        postcode = parameters.get('obj_zipCode')
        balcony = self.convert_boolean_field(parameters.get('obj_balcony'))
        energy_building_year = parameters.get('obj_yearConstructed')
        offer_id = parameters.get('obj_scoutId')
        kitchen_availability = self.convert_boolean_field(parameters.get('obj_hasKitchen'))
        cellar = self.convert_boolean_field(parameters.get('obj_cellar'))
        pets_allowed = self.convert_boolean_field(parameters.get('obj_petsAllowed'))
        energy_efficiency_class = parameters.get('obj_energyEfficiencyClass')
        elevator = self.convert_boolean_field(parameters.get('obj_lift'))
        energy_consumption = parameters.get('obj_thermalChar')
        floor_level = parameters.get('obj_floor')
        garden = self.convert_boolean_field(parameters.get('obj_garden'))
        handicap_accessible = self.convert_boolean_field(parameters.get('obj_barrierFree'))
        heating = parameters.get('obj_heatingType')
        property_type=parameters.get('obj_immotype')
        if property_type == 'haus_miete':
            property_type = 'Haus'
        elif property_type == 'wohnung_miete':
            property_type = 'Wohnung'

        # assemble the item and return it
        item = ImmoscoutItemAPI(
            site="immoscout",
            title=title,
            url=response.url,
            property_type=property_type,
            image=None,
            warmmiete=warmmiete,
            kaltmiete=kaltmiete,
            nebenkosten=nebenkosten,
            heizungskosten=heizungskosten,
            kaution=kaution,
            area=area,
            num_rooms=num_rooms,
            address=address,
            postcode=postcode,
            geo_latitude=geo_latitude,
            geo_longitude=geo_longitude,
            offer_id=offer_id,
            balcony=balcony,
            energy_building_year=energy_building_year,
            kitchen_availability=kitchen_availability,
            cellar=cellar,
            pets_allowed=pets_allowed,
            energy_efficiency_class=energy_efficiency_class,
            energy_consumption=energy_consumption,
            elevator=elevator,
            floor_level=floor_level,
            garden=garden,
            handicap_accessible=handicap_accessible,
            freetext_property_description=freetext_property_description,
            freetext_area_description=freetext_area_description,
            freetext_other=freetext_other,
            heating=heating,
            available_from_date=available_from_date,
            preis_qm_kalt=float(kaltmiete) / float(area)
        )
        yield item
