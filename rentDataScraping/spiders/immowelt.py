# -*- coding: utf-8 -*-
import scrapy
import pathlib
import time
from datetime import datetime
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.wait import WebDriverWait
from rentDataScraping.items import ImmoweltItem

date_time = datetime.now()
NOW = date_time.strftime("%y%m%d_%H%M")
NUM_PAGES_TO_CRAWL = 10

class ImmoweltSpider(scrapy.Spider):
    def __init__(self,*args, **kwargs):
        super().__init__(*args,**kwargs)
        self.driver = webdriver.Chrome(ChromeDriverManager().install())

    custom_settings = {
        'FEEDS': {
            pathlib.Path('./data/immowelt/' + NOW + '_items.json'): {
                'format': 'json',
                'encoding': 'utf8',
                'store_empty': False,
                'indent': 4,
            },
            pathlib.Path('./data/immowelt/' + NOW + '_items.csv'): {
                'format': 'csv',
            },
        },

    }

    name = 'immowelt'
    allowed_domains = ['immowelt.de']
    start_urls = ['http://immowelt.de/']

    @staticmethod
    def get_selenium_response(driver, url, num_ids):
        '''Because Immowelt uses lazy-loading as you scroll to show all offers,
        this method first scrolls to the bottom of the page, then waits 5 seconds and checks if all offer ids are loaded,
        before passing the response back to scrapy'''
        driver.get(url)

        try:
            def scroll_down(driver):
                """A method for scrolling the page."""
                # Get scroll height.
                last_height = driver.execute_script("return document.body.scrollHeight")
                while True:
                    # Scroll down to the bottom.
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    # Wait to load the page.
                    time.sleep(2)
                    # Calculate new scroll height and compare with last scroll height.
                    new_height = driver.execute_script("return document.body.scrollHeight")
                    if new_height == last_height:
                        break
                    last_height = new_height

            def find(driver):
                '''Check if all offers are loaded'''
                iw_items = driver.find_elements_by_class_name('listitem_wrap')
                if len(iw_items) == num_ids:
                    return iw_items
                else:
                    return False

            # first, scroll down
            scroll_down(driver)
            # then wait 5 seconds and check for the offers
            element = WebDriverWait(driver, 5).until(find)
            # if all ok, return response
            return driver.page_source.encode('utf-8')

        except:
            driver.quit()

    urls = []
    for i in range(NUM_PAGES_TO_CRAWL):
        urls.append('https://www.immowelt.de/liste/berlin/wohnungen/mieten?sort=createdate%20desc&cp=' + str(i + 1))
    start_urls = urls

    def parse(self, response):
        # in the Immowelt page there is a hidden input field with the values of all ids to be displayed in the page
        # we use these values to determine how many offers should be displayed on the page, after all lazy-loading is done.
        estateIds = response.xpath('//input[@id="estateIds"]/@value').get().split(',')
        num_estateIds = len(estateIds)
        # then we load the page with selenium
        first_response = response
        response = scrapy.Selector(
            text=self.get_selenium_response(self.driver, response.url, num_estateIds))

        # get all offer divs
        offer_divs = response.css('div.listitem_wrap')
        for offer_div in offer_divs:
            estateId = offer_div.xpath('./@data-estateid').get()
            url = offer_div.css('div.listitem > a::attr(href)').get()
            yield first_response.follow(url=url, callback=self.parse_offer, meta={'estateId': estateId})

    def parse_offer(self, response):
        # parsing each entry

        # get main data from the html's head
        head = response.xpath('/html/head')
        title = head.xpath(
            './meta[@property="og:title"]/@content').get()
        image = head.xpath(
            './meta[@property="og:image"]/@content').get()
        url = response.url
        # summary = head.xpath(
        #     './meta[@name="description"]/@content').get()

        quickfacts = response.css('div.quickfacts')
        summary = quickfacts.css('h1::text').get()
        address = quickfacts.xpath('./div[@class="location"]/span[1]/text()').get()
        facts = quickfacts.css('div.merkmale::text').get()

        hardfacts = response.css('div.hardfacts')
        warmmiete = hardfacts.xpath('./div[1]/strong/text()').get().split(' ')[0].replace('.','')
        area = hardfacts.xpath('./div[2]/text()').get().split(' ')[0].strip()
        num_rooms = hardfacts.xpath('./div[3]/text()').get().strip()

        # PREISE UND KOSTEN
        preise_container = response.xpath('//h2[contains(text(), "Preise")]/..')
        kaltmiete = nebenkosten = heizkosten = kaution = None
        ## KALTMIETE
        container = preise_container.xpath('.//strong[contains(text(), "Kaltmiete")]/../..')
        if len(container) > 0:
            kaltmiete = container.css('div.datacontent > strong::text').get().split(' ')[0].strip()

        ## NEBENKOSTEN
        container = preise_container.xpath('.//div[contains(text(), "Nebenkosten")]/../..')
        if len(container) > 0:
            nebenkosten = container.css('div.datacontent::text').get().split(' ')[0].strip()

        ## HEIZKOSTEN
        container = preise_container.xpath('.//div[contains(text(), "Heizkosten")]/../..')
        if len(container) > 0:
            heizkosten = container.css('div.datacontent::text').get()

        ## WARMMIETE
        container = preise_container.xpath('.//div[contains(text(), "Warmmiete")]/../..')
        if len(container) > 0:
            warmmiete = container.css('div.datacontent::text').get()

        ## KAUTION
        container = response.xpath('//div[contains(text(), "Kaution")]/..')
        if len(container) > 0:
            kaution = container.css('div.section_content > p::text').get().strip().split(' ')[0]

        # Get the parent div of the div whose content is 'Immobilie' to get the online ID
        immobilie_container = response.xpath('//h2[contains(text(), "Immobilie")]/../..')
        online_id = immobilie_container.css('div.section_content > p::text').get().strip().replace('Online-ID: ', '')

        # Get the parent div of the div whose content is 'Die Wohnung' to get details
        # TODO: Needs some text recognition to get main facts?
        # whg_container = response.xpath('//div[contains(text(), "Die Wohnung")]/..')
        # offer['type'] = whg_container.xpath('./div[2]/p/text()').get().strip()
        # offer['floor'] = whg_container.xpath('./div[2]/p/span/text()').get().strip()
        # offer['availability'] = whg_container.xpath('./div[2]/p/strong/text()').get().strip()
        # TODO: get more details from UL > LIs?

        # Get the parent div of the div whose content is 'Wohnalage' to get details
        whg_container = response.xpath('//div[contains(text(), "Wohnanlage")]/..')
        building_year = whg_container.xpath('./div[2]/p/text()').get().strip()
        # TODO: get more details from UL > LIs?

        # Get the parent div of the div whose content is 'Objektbeschreibung' to get details
        container = response.xpath('//div[contains(text(), "Objektbeschreibung")]/..')
        text_content = container.xpath('./div[2]/p//text()').getall()
        text_description = '\n'.join([i.strip() for i in text_content if len(i.strip()) > 0])

        # Get the parent div of the div whose content is 'Ausstattung' to get details
        container = response.xpath('//div[contains(text(), "Ausstattung")]/..')
        text_content = container.xpath('./div[2]/p//text()').getall()
        text_ausstattung = '\n'.join([i.strip() for i in text_content if len(i.strip()) > 0])

        # Get the parent div of the div whose content is 'Sonstiges' to get details
        text_sonstiges = None
        container = response.xpath('//div[contains(text(), "Sonstiges")]/..')
        if len(container) > 0:
            text_content = container.xpath('./div[2]/p//text()').getall()
            text_sonstiges = '\n'.join([i.strip() for i in text_content if len(i.strip()) > 0])

        # Get the parent div of the div whose content is 'KFZ Stellplatz' to get details
        container = response.xpath('//div[contains(text(), "KFZ Stellplatz")]/..')
        text_content = container.xpath('./div[2]/p//text()').getall()
        parking = '\n'.join([i.strip() for i in text_content if len(i.strip()) > 0])

        # Get the parent div of the div whose content is 'Stichworte' to get details
        container = response.xpath('//div[contains(text(), "Stichworte")]/..')
        text_content = container.xpath('./div[2]/p//text()').getall()
        keywords = '\n'.join([i.strip() for i in text_content if len(i.strip()) > 0])

        # Get the parent div of the div whose content is 'Lagebeschreibung' to get details
        container = response.xpath('//div[contains(text(), "Lagebeschreibung")]/..')
        text_content = container.xpath('./div[2]/p//text()').getall()
        text_lage = '\n'.join([i.strip() for i in text_content if len(i.strip()) > 0])

        item = ImmoweltItem(
            title=title,
            url=url,
            image=image,
            warmmiete=warmmiete,
            address=address,
            kaltmiete=kaltmiete,
            nebenkosten=nebenkosten,
            kaution=kaution,
            area=area,
            num_rooms=num_rooms,
            facts=facts,
            # below is specific to immoscout
            heizkosten=heizkosten,
            keywords=keywords,
            parking=parking,
            text_summary=summary,
            text_description=text_description,
            text_ausstattung=text_ausstattung,
            text_lage=text_lage,
            text_sonstiges=text_sonstiges,
            building_year = building_year,
            online_id=online_id
        )
        yield item