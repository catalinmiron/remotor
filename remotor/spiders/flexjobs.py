# -*- coding: utf-8 -*-
"""Scrape jobs from flexjobs.com.
"""
from urlparse import urljoin

from scrapy import Request, Selector
import scrapy

from remotor.items import JobItem


class FlexjobsSpider(scrapy.Spider):
    """Spider for flexjobs.com

    This is a two-layer site with a pagination page, with links to the ads from
    the numbered pages.

    """
    name = "flexjobs"
    root = "https://www.flexjobs.com"
    allowed_domains = ["www.flexjobs.com"]
    start_urls = [
        'https://www.flexjobs.com/search?search=python&location=remote']

    job_selector = (
        '//div[@id="joblistarea"]//a[starts-with(@href, "/publicjobs/")]/@href')

    def parse(self, response):
        """Get the pagination links and hand them off.
        """
        s = Selector(response)
        pagination = s.css('.pagination')
        pagelinks = pagination.xpath(
            '//a[contains(@href, "&page=")]/@href').extract()
        for pagelink in pagelinks:
            request = Request(
                urljoin(self.root, pagelink),
                callback=self.parse_jobspage,
                dont_filter=True,
                )
            yield request

    def parse_jobspage(self, response):
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
#        inspect_response(response, self)
        s = Selector(response)
        item = JobItem()
        item['url'] = response.url
        item['site'] = 'FlexJobs'
        item['title'] = s.css('h1::text').extract_first()
        item['html'] = s.css('#job-description p').extract()
        item['html'].extend(s.css('td, th').extract())
        item['text'] = s.css('#job-description p::text').extract()
        item['text'].extend(s.css('td::text, th::text').extract())
        yield item
