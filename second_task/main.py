from typing import List, Dict, Union
import json

from scrapy.crawler import CrawlerProcess
from itemadapter import ItemAdapter
from scrapy.item import Item, Field
import scrapy


class QuoteItem(Item):
    """Class representing a quote item."""
    quote = Field()
    author = Field()
    tags = Field()


class AuthorItem(Item):
    """Class representing an author item."""
    fullname = Field()
    born_date = Field()
    born_location =Field()
    description =Field()


class DataPipline:
    """Pipeline class to process scraped items."""
    quotes: List[Dict[str, Union[str, List[str]]]] = []
    authors: List[Dict[str, str]] = []

    def process_item(self, item: Item, spider: scrapy.Spider) -> None:
        """Process each scraped item.

        Parameters:
            item (scrapy.Item): The scraped item.
            spider (scrapy.Spider): The spider which scraped the item.
        """
        adapter = ItemAdapter(item)
        if "fullname" in adapter.keys():
            self.authors.append(dict(adapter))
        if "quote" in adapter.keys():
            self.quotes.append(dict(adapter))

    def close_spider(self, spider: scrapy.Spider) -> None:
        """Close the spider and save the scraped data to JSON files.

        Parameters:
            spider (scrapy.Spider): The spider which was closed.
        """
        with open("quotes.json", "w", encoding="utf-8") as fd:
            json.dump(self.quotes, fd, ensure_ascii=False, indent=2)
        with open("authors.json", "w", encoding="utf-8") as fd:
            json.dump(self.authors, fd, ensure_ascii=False, indent=2)


class QuotesSpider(scrapy.Spider):
    """Spider to scrape quotes and authors from 'quotes.toscrape.com'."""

    name: str = "get_quotes"
    allowed_domains: List[str] = ["quotes.toscrape.com"]
    start_urls: List[str] = ["https://quotes.toscrape.com/"]
    custom_settings: Dict[str, Dict[str, int]] = {"ITEM_PIPELINES": {DataPipline: 300}}

    def parse(self, response: scrapy.http.Response, **kwargs):
        """Parse quotes from the response.

        Parameters:
            response (scrapy.http.Response): The response object from the request.
            **kwargs: Additional keyword arguments.
        """
        for q in response.xpath("/html//div[@class='quote']"):
            quote: str = q.xpath("span[@class='text']/text()").get().strip()
            author: str = q.xpath("span/small[@class='author']/text()").get().strip()
            tags: List[str] = q.xpath("div[@class='tags']/a/text()").extract()
            yield QuoteItem(quote=quote, author=author, tags=tags)
            yield response.follow(url=self.start_urls[0] + q.xpath("span/a/@href").get(), callback=self.parse_author)

        next_link: str = response.xpath("/html//li[@class='next']/a/@href").get()
        if next_link:
            yield scrapy.Request(url=self.start_urls[0] + next_link)

    @classmethod
    def parse_author(cls, response: scrapy.http.Response, **kwargs):
        """Parse author details from the response.

        Parameters:
            response (scrapy.http.Response): The response object from the request.
            **kwargs: Additional keyword arguments.
        """
        content = response.xpath("/html//div[@class='author-details']")
        fullname: str = content.xpath("h3[@class='author-title']/text()").get().strip()
        born_date: str = content.xpath("p/span[@class='author-born-date']/text()").get().strip()
        born_location: str = content.xpath("p/span[@class='author-born-location']/text()").get().strip()
        description: str = content.xpath("div[@class='author-description']/text()").get().strip()
        yield AuthorItem(fullname=fullname, born_date=born_date, born_location=born_location, description=description)


if __name__ == "__main__":
    process = CrawlerProcess()
    process.crawl(QuotesSpider)
    process.start()
