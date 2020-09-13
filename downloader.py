import requests
from bs4 import BeautifulSoup
from utils import *
import py7zr


class Stack_Exchange_Downloader():

    def __init__(self, name):
        """
        :param name: name of stackexchange site to download. If all, will download all stackexchanges & metas.
        """
        sitesmap = requests.get("https://ia600107.us.archive.org/27/items/stackexchange/Sites.xml").content
        self.name = name.replace("http://", "").replace("https://", "").replace(".com", "").replace(".net", "")
        self.sites = {}
        self.parse_sitesmap(sitesmap)

    def parse_sitesmap(self, sitesmap):
        soup = BeautifulSoup(sitesmap, "lxml")
        for site in soup.find_all("row"):
            url = site['url'].replace("https://", "")
            site_name = url.replace(".com", "").replace(".net", "")
            download_link = "https://archive.org/download/stackexchange/" + url + ".7z"
            if url == "stackoverflow.com":
                download_link = "https://archive.org/download/stackexchange/stackoverflow.com-Posts.7z"
            self.sites[site_name] = {"url" : url, "download" : download_link}

    def download(self):
        if self.name == "all":
            for k in self.sites:
                command = "wget {} -P dumps".format(self.sites[k]["download"])
                print(command)
                if os.system(command):
                    print('Download for {} failed!'.format(k))
        else:
            command = "wget {} -P dumps".format(self.sites[self.name]["download"])
            print(command)
            if os.system(command):
                print('Download for {} failed!'.format(self.name))

    def extract(self):
        if self.name == "all":
            for k in self.sites:
                # archive = py7zr.SevenZipFile('dumps/{}'.format(self.sites[k]["download"].replace("https://archive.org/download/stackexchange/", "")
                #                                                , mode='r'))
                # archive.extractall()
                # archive.close()
                command = "py7zr x dumps/{} dumps/{}".format(self.sites[k]["download"].replace("https://archive.org/download/stackexchange/", ""),
                                                       k)
                print(command)
                if os.system(command):
                    print('Extraction for {} failed!'.format(k))
        else:
            # archive = py7zr.SevenZipFile(
            #     'dumps/{}'.format(self.sites[self.name]["download"].replace("https://archive.org/download/stackexchange/", "")
            #                       , mode='r'))
            # archive.extractall()
            # archive.close()
            command = "py7zr x dumps/{} dumps/{}".format(self.sites[self.name]["download"].replace("https://archive.org/download/stackexchange/", ""),
                                                      self.name)
            print(command)
            if os.system(command):
                print('Extraction for {} failed!'.format(self.name))
