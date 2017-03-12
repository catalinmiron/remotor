# -*- coding: utf-8 -*-
from urlparse import urljoin

from scrapy import Request, Selector
import scrapy

from remotor.items import JobItem


class CareerbuilderSpider(scrapy.Spider):
    root = 'http://www.careerbuilder.com'
    name = "careerbuilder"
    allowed_domains = ["www.careerbuilder.com"]
    start_urls = ['http://www.careerbuilder.com/jobs-remote-python']

    job_selector = '//a[starts-with(@href, "/job/")]/@href'

    def parse(self, response):
        """Get the joblinks and hand them off.
        """
        s = Selector(response)
        joblinks = s.xpath(self.job_selector).extract()
        for joblink in joblinks:
            request = Request(
                urljoin(self.root, joblink),
                callback=self.parse_job,
                )
            yield request

    def parse_job(self, response):
        """Parse a joblink into a JobItem.
        """
        s = Selector(response)
        item = JobItem()
        item['url'] = response.url.split('?')[0]
        item['title'] = s.css('h1::text').extract_first()
        item['text'] = s.css('.job-facts::text').extract()
        item['text'].extend(s.css('.item').css('.tag::text').extract())
        item['text'].extend(s.css('.description::text').extract())
        yield item