import abc

class Scraper:
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def scrape_channel(self, channel, day):
        pass

    @abc.abstractmethod
    def scrape_description(self, uuid):
        pass
