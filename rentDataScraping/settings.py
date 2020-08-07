# -*- coding: utf-8 -*-

import os
import pathlib
from scrapy.utils.project import data_path
from dotenv import load_dotenv
load_dotenv()



# Scrapy settings for rentDataScraping project
#
# For simplicity, this file contains only settings considered important or
# commonly used. You can find more settings consulting the documentation:
#
#     https://docs.scrapy.org/en/latest/topics/settings.html
#     https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
#     https://docs.scrapy.org/en/latest/topics/spider-middleware.html

BOT_NAME = 'rentDataScraping'

SPIDER_MODULES = ['rentDataScraping.spiders']
NEWSPIDER_MODULE = 'rentDataScraping.spiders'


# Crawl responsibly by identifying yourself (and your website) on the user-agent
#USER_AGENT = 'rentDataScraping (+http://www.yourdomain.com)'

# Obey robots.txt rules
ROBOTSTXT_OBEY = False

# Configure maximum concurrent requests performed by Scrapy (default: 16)
CONCURRENT_REQUESTS = 8

# Configure a delay for requests for the same website (default: 0)
# See https://docs.scrapy.org/en/latest/topics/settings.html#download-delay
# See also autothrottle settings and docs
DOWNLOAD_DELAY = 3
# The download delay setting will honor only one of:
#CONCURRENT_REQUESTS_PER_DOMAIN = 16
#CONCURRENT_REQUESTS_PER_IP = 16

# Disable cookies (enabled by default)
#COOKIES_ENABLED = False

# Disable Telnet Console (enabled by default)
#TELNETCONSOLE_ENABLED = False

# Override the default request headers:
#DEFAULT_REQUEST_HEADERS = {
#   'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
#   'Accept-Language': 'en',
#}

filename = 'proxies.txt'
proxy_path = data_path(filename)

ROTATING_PROXY_LIST_PATH = proxy_path # os.getcwd()+'/proxies.txt'

# Enable or disable spider middlewares
# See https://docs.scrapy.org/en/latest/topics/spider-middleware.html
#SPIDER_MIDDLEWARES = {
#    'rentDataScraping.middlewares.RentdatascrapingSpiderMiddleware': 543,
#}

# Enable or disable downloader middlewares
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
DOWNLOADER_MIDDLEWARES = {
    'rotating_proxies.middlewares.RotatingProxyMiddleware': 610,
    'rotating_proxies.middlewares.BanDetectionMiddleware': 620
}



# Enable or disable extensions
# See https://docs.scrapy.org/en/latest/topics/extensions.html
# EXTENSIONS = {
#    'scrapy_dotpersistence.DotScrapyPersistence': 0
# }
#
# DOTSCRAPY_ENABLED = True
#
# ADDONS_AWS_ACCESS_KEY_ID = os.environ.get('SCRAPY_ADDONS_AWS_ACCESS_KEY_ID')
# ADDONS_AWS_SECRET_ACCESS_KEY = os.environ.get('SCRAPY_ADDONS_AWS_SECRET_ACCESS_KEY')
# # ADDONS_AWS_USERNAME = 'username' // This is the folder path (optional)
# ADDONS_S3_BUCKET = 'berlin-rents-live'

# Configure item pipelines
# See https://docs.scrapy.org/en/latest/topics/item-pipeline.html
# TODO: cleaning should come here?
ITEM_PIPELINES = {
    # 'rentDataScraping.pipelines.pandasExportExcelPipeline': 300,
    'rentDataScraping.pipelines.pgPipeline': 300
}

# Enable and configure the AutoThrottle extension (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/autothrottle.html
AUTOTHROTTLE_ENABLED = True
# The initial download delay
#AUTOTHROTTLE_START_DELAY = 5
# The maximum download delay to be set in case of high latencies
#AUTOTHROTTLE_MAX_DELAY = 60
# The average number of requests Scrapy should be sending in parallel to
# each remote server
#AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
# Enable showing throttling stats for every response received:
#AUTOTHROTTLE_DEBUG = False

# Enable and configure HTTP caching (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html#httpcache-middleware-settings
#HTTPCACHE_ENABLED = True
#HTTPCACHE_EXPIRATION_SECS = 0
#HTTPCACHE_DIR = 'httpcache'
#HTTPCACHE_IGNORE_HTTP_CODES = []
#HTTPCACHE_STORAGE = 'scrapy.extensions.httpcache.FilesystemCacheStorage'
