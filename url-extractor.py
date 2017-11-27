#!/usr/bin/env python
"""
URL extractor for clowder. We fetch any metadata about the URL and
generate a screenshot.

Author Ward Poelmans <wpoely86@gmail.com>
"""

import datetime
import json
import logging
import os
import shutil
import tempfile

import pyclowder
from pyclowder.extractors import Extractor
from selenium import webdriver
from selenium.common.exceptions import TimeoutException, WebDriverException, RemoteDriverServerException, ErrorInResponseException
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities


class URLExtractor(Extractor):
    """Extract metadata about URL and generate screenshot"""
    def __init__(self):
        Extractor.__init__(self)

        # parse command line and load default logging configuration
        self.setup()

        # setup logging for the exctractor
        logging.getLogger('pyclowder').setLevel(logging.DEBUG)
        logging.getLogger('__main__').setLevel(logging.DEBUG)
        self.logger = logging.getLogger(__name__)

        self.selenium = os.getenv('SELENIUM_URI', 'http://localhost:4444/wd/hub')


    def check_message(self, connector, host, secret_key, resource, parameters):  # pylint: disable=unused-argument,too-many-arguments
        """Check if the extractor should download the file or ignore it."""
        if not resource['file_ext'] == '.url':
            if parameters.get('action', '') != 'manual-submission':
                self.logger.debug("Unknown filetype, skipping")
                return pyclowder.utils.CheckMessage.ignore
            else:
                self.logger.debug("Unknown filetype, but scanning by manuel request")

        return pyclowder.utils.CheckMessage.download  # or bypass

    def process_message(self, connector, host, secret_key, resource, parameters):  # pylint: disable=unused-argument,too-many-arguments
        """The actual extractor: we extract the URL from the JSON input and upload the results"""
        self.logger.debug("Clowder host: %s", host)
        self.logger.debug("Received resources: %s", resource)
        self.logger.debug("Received parameters: %s", parameters)

        tempdir = tempfile.mkdtemp(prefix='clowder-url-extractor')

        try:
            with open(resource['local_paths'][0], 'r') as inputfile:
                urldata = json.load(inputfile)
                url = urldata['URL']
        except (IOError, ValueError, KeyError) as err:
            self.logger.error("Failed to read or parse %s as URL input file: %s", resource['local_paths'][0], err)

        url_metadata = {
            'URL': url
        }

        try:
            desired_capabilities = DesiredCapabilities.CHROME.copy()
            desired_capabilities['chromeOptions'] = {
                "args": ["--hide-scrollbars"],
            }
            browser = webdriver.Remote(command_executor=self.selenium, desired_capabilities=desired_capabilities)
            browser.set_script_timeout(30)
            browser.set_page_load_timeout(30)
            browser.set_window_size(1920, 1080)

            browser.get(url)
            browser.get_screenshot_as_file(os.path.join(tempdir, "website.png"))
            pyclowder.files.upload_preview(connector, host, secret_key, resource['id'], os.path.join(tempdir, "website.png"), None)

            url_metadata['title'] = browser.title
            url_metadata['date'] = datetime.datetime.now().isoformat()
        except (TimeoutException, WebDriverException, RemoteDriverServerException, ErrorInResponseException) as err:
            self.logger.error("Failed to fetch %s: %s", url, err)
        finally:
            browser.quit()

        metadata = self.get_metadata(url_metadata, 'file', resource['id'], host)
        self.logger.debug("New metadata: %s", metadata)

        # upload metadata
        pyclowder.files.upload_metadata(connector, host, secret_key, resource['id'], metadata)

        shutil.rmtree(tempdir, ignore_errors=True)


if __name__ == "__main__":
    extractor = URLExtractor()
    extractor.start()
