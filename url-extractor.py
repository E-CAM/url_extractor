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
import re
import shutil
import tempfile

import requests
import yaml
from bs4 import BeautifulSoup
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
        self.window_size = (1366, 768)  # the default
        self.read_settings()

    def read_settings(self, filename=None):
        """
        Read the default settings for the extractor from the given file.
        :param filename: optional path to settings file (defaults to 'settings.yml' in the current directory)
        """
        if filename is None:
            filename = os.path.join(os.path.dirname(os.path.realpath(__file__)), "config", "settings.yml")

        if not os.path.isfile(filename):
            self.logger.warning("No config file found at %s", filename)
            return

        try:
            with open(filename, 'r') as settingsfile:
                settings = yaml.safe_load(settingsfile) or {}
                if settings.get("window_size"):
                    self.window_size = tuple(settings.get("window_size"))
        except (IOError, yaml.YAMLError) as err:
            self.logger.error("Failed to read or parse %s as settings file: %s", filename, err)

        self.logger.debug("Read settings from %s: %s", filename, self.window_size)

    def check_message(self, connector, host, secret_key, resource, parameters):  # pylint: disable=unused-argument,too-many-arguments
        """Check if the extractor should download the file or ignore it."""
        if not resource['file_ext'] == '.jsonurl':
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

        self.read_settings()

        tempdir = tempfile.mkdtemp(prefix='clowder-url-extractor')

        try:
            with open(resource['local_paths'][0], 'r') as inputfile:
                urldata = json.load(inputfile)
                url = urldata['URL']
        except (IOError, ValueError, KeyError) as err:
            self.logger.error("Failed to read or parse %s as URL input file: %s", resource['local_paths'][0], err)

        if not re.match(r"^https?:\/\/", url):
            self.logger.error("Invalid url: %s", url)
            return

        url_metadata = {
            'URL': url,
            'date': datetime.datetime.now().isoformat(),
        }

        try:
            req = requests.get(url)
            req.raise_for_status()

            if req.headers.get("X-Frame-Options"):
                url_metadata['X-Frame-Options'] = req.headers['X-Frame-Options'].upper()

            try:
                soup = BeautifulSoup(req.text, "lxml")
                url_metadata['title'] = soup.find("title").string
            except AttributeError as err:
                self.logger.error("Failed to extract title from webpage %s: %s", url, err)
                url_metadata['title'] = ''

            if not url.startswith("https"):
                # check if we can upgrade to https
                req_https = requests.get(url.replace("http", "https", 1))
                # currently, we only check for a 200 return code, maybe also check if page is the same?
                if req_https.status_code == 200:
                    # we can upgrade!
                    url_metadata['tls'] = True
                else:
                    url_metadata['tls'] = False
            else:
                url_metadata['tls'] = True

        except requests.exceptions.RequestException as err:
            self.logger.error("Failed to fetch URL %s: %s", url, err)

        browser = None
        try:
            desired_capabilities = DesiredCapabilities.CHROME.copy()
            desired_capabilities['chromeOptions'] = {
                "args": ["--hide-scrollbars"],
            }
            browser = webdriver.Remote(command_executor=self.selenium, desired_capabilities=desired_capabilities)
            browser.set_script_timeout(30)
            browser.set_page_load_timeout(30)
            browser.set_window_size(self.window_size[0], self.window_size[1])

            browser.get(url)

            screenshot_png = browser.get_screenshot_as_png()
            with open(os.path.join(tempdir, "website.urlscreenshot"), 'wb') as f:
                f.write(screenshot_png)

            pyclowder.files.upload_preview(connector, host, secret_key, resource['id'], os.path.join(tempdir, "website.urlscreenshot"), None)
            # Also upload as a thumbnail
            pyclowder.files.upload_thumbnail(connector, host, secret_key, resource['id'], os.path.join(tempdir, "website.urlscreenshot"))
        except (TimeoutException, WebDriverException, RemoteDriverServerException, ErrorInResponseException, IOError) as err:
            self.logger.error("Failed to fetch %s: %s", url, err)
        finally:
            if browser:
                browser.quit()

        metadata = self.get_metadata(url_metadata, 'file', resource['id'], host)
        self.logger.debug("New metadata: %s", metadata)

        # upload metadata
        pyclowder.files.upload_metadata(connector, host, secret_key, resource['id'], metadata)

        shutil.rmtree(tempdir, ignore_errors=True)


if __name__ == "__main__":
    extractor = URLExtractor()
    extractor.start()
