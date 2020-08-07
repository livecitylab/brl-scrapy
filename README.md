# Data Scraping for berlinrents.live

This repository contains a [Scrapy](https://scrapy.org/) project with spiders to crawl commercial rental websites and extract data about rental offers.

Current spiders include:
- [WG-Gesucht](https://wg-gesucht.de)
- [Immowelt](https://immowelt.de)
- [Immobilienscout24](https://immobilienscout24.de)

## How does it work?

Each spider is specific to its website. It loads the given URLs and then parse the DOM, finding the desired pieces of information in it and storing it in a CSV file. Each run of the spiders will generate a timestamped CSV file in the `/data` folder.

The spiders have built-in "politeness" using the [AutoThrottle Extension](The spiders have built-in "politeness" using the [AutoThrottle Extension](). It works by rate-limiting access to their target website to avoid being detected by anti-scraping methods. Therefore, some crawl processes might take a longer time.
). It works by rate-limiting access to their target website to avoid being detected by anti-scraping methods. Therefore, some crawl processes might take a longer time.

Also to avoid detection, we are using rotating proxies (with the [scrapy-rotating-proxies](https://github.com/TeamHG-Memex/scrapy-rotating-proxies) middleware). These are free proxies available at [https://free-proxy-list.net/](https://free-proxy-list.net/) and scraped by the `proxies` spider.

Sites using JavaScript to lazy-load sections of their pages (Immowelt, for example), need to be accessed with a Selenium webdriver, which runs all the JS on the page, before returning a response with the required HTML for parsing.

### Example flow

As an example, let's take a look at the WG-Gesucht spider. This is what happens when you run it:

1) It visits the first page of results
2) It gets pagination info: links to all pages in the pagination links at the bottom of the page
3) It get all links to offers displayed on the current page
4) One by one, it visits each of the offers, parses its contents, save it to parsed items
5) Repeats 3 and 4 for all pagination links

## Installation

To install this package, you'll have to fork it and install its dependencies with:

`pip install`

## Usage

You can run a spider by entering the command in the terminal:

```scrapy crawl [spider name]```

To get a list of all spider names currently in the project, type:

```scrapy list```

So, if you want to run the `wg-gesucht` spider, you'll type:

```scrapy crawl wg-gesucht```

## Proxies

This project uses the scrapy-rotating-proxies middleware. It uses a list of free proxies scraped from [free-proxy-list.net](https://free-proxy-list.net/). Although it works most of the time, it is good practice to refresh this list once in a while to make sure you always have fresh, working proxies to work with.

To generate a new list of proxies, simply run the `proxies` spider. It will scrape [free-proxy-list.net](https://free-proxy-list.net/) and create a `proxies.txt` file, which is then used by the other spiders. In a terminal, type:

```scrapy crawl proxies```