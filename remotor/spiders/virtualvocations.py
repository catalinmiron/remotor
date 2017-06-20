# -*- coding: utf-8 -*-
"""Scrape jobs from virtualvocations.com.
"""
import datetime
from urlparse import urljoin

from scrapy import FormRequest, Request, Selector
import scrapy

from remotor.items import JobItem
from scrapy.shell import inspect_response


class VirtualvocationsSpider(scrapy.Spider):
    """Spider for virtualvocations.com

    This is a two-layer site with a pagination page, with links to the ads from
    the numbered pages. The first query is a POST request which means we use
    start_requests() rather than start_urls.

    """
    name = "virtualvocations"
    root = "https://www.virtualvocations.com"
    allowed_domains = ["www.virtualvocations.com"]

    job_selector = (
        '//a[starts-with(@href, "{0}/job/")]/@href'.format(root))

    def start_requests(self):
        """Submit a POST request with our query parameters.
        """
        return [
            FormRequest("https://www.virtualvocations.com/jobs/",
                formdata={'search': 'python', 'location': 'remote'},
                callback=self.parse)
                ]

    def parse(self, response):
        """Get the pagination links and hand them off.
        """
        s = Selector(response)
        pagination = s.css('.pagination')
        pagelinks = [response.url]
        pagelinks.extend(pagination.xpath(
            '//a[contains(@href, "l-remote/p-")]/@href').extract())
        for pagelink in pagelinks[:1]:
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
        for joblink in joblinks[:1]:
            request = Request(
                urljoin(self.root, joblink),
                callback=self.parse_job,
                )
            yield request

    def parse_job(self, response):
        """Parse a joblink into a JobItem.
        """
        s = Selector(response)
        inspect_response(response, self)
        item = JobItem()
        item['url'] = response.url
        item['site'] = 'VirtualVocations'
        item['title'] = s.css('h1::text').extract_first()
        item['text'] = s.xpath('//div[@id="job_details"]//text()').extract()
        posted = s.xpath('//div[@class="col-sm-6"]/p//text()').extract()[3]
        item['date_added'] = parse_date(posted).isoformat()
        yield item


def parse_date(text, now=None):
    """Parse a date in the format 'Posted: Monday, June 19, 2017'."""
    text = text.replace("Posted:", '').strip()
    if not now:
        now = datetime.datetime.now()
    parsed = datetime.datetime.strptime(text, '%A, %B %d, %Y')
    if (parsed.month, parsed.day) == (now.month, now.day):
        parsed = now  # we are seeing this soon after posting
    return parsed


def test_parse_time():
    now = datetime.datetime(2017, 6, 20, 6, 30)
    tests = [('Posted: Monday, June 19, 2017', datetime.datetime(2017, 6, 19)),
             ('Posted: Monday, June 20, 2017', now),
             ]
    for test in tests:
        assert parse_date(test[0], now) == test[1]

