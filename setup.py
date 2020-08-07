# Automatically created by: shub deploy

from setuptools import setup, find_packages

setup(
    name         = 'rentDataScraping',
    version      = '1.0',
    packages     = find_packages(),
    entry_points = {'scrapy': ['settings = rentDataScraping.settings']},
)
