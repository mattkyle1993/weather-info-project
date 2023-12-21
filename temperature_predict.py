from base64 import encode
from concurrent.futures import thread
import requests
import json
import html_to_json
from bs4 import BeautifulSoup
import psutil    
import os
import glob
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
import pandas as pd
from datetime import datetime
import time
from fuzzywuzzy import fuzz, process
import math
from html.parser import HTMLParser
from html.entities import name2codepoint
import codecs
import urllib.request, urllib.error, urllib.parse
import pathlib
import mysql.connector
import sys
import re
import random
# from service_schedule import AppServerSvc
import win32serviceutil
import win32service
import win32event
import servicemanager
import socket
from uszipcode import SearchEngine, SimpleZipcode, ComprehensiveZipcode
from selenium.webdriver import ActionChains
from selenium.common.exceptions import TimeoutException
    from selenium.common.exceptions import NoSuchElementException

import time
from datetime import datetime

# https://stackoverflow.com/questions/2031111/in-python-how-can-i-put-a-thread-to-sleep-until-a-specific-time
# Comment from author: "Here's a half-ass solution that doesn't account for clock jitter or adjustment of the clock. See comments for ways to get rid of that.""


# if for some reason this script is still running
# after a year, we'll stop after 365 days
# for i in range(0,365):
#     # sleep until 2AM
#     t = datetime.datetime.today()
#     future = datetime.datetime(t.year,t.month,t.day,2,0)
#     if t.hour >= 2:
#         future += datetime.timedelta(days=1)
#     time.sleep((future-t).total_seconds())
    
# https://stackoverflow.com/questions/32404/how-do-you-run-a-python-script-as-a-service-in-windows
    
class AppServerSvc (win32serviceutil.ServiceFramework):
    _svc_name_ = "WeatherKCMOsvc"
    _svc_display_name_ = "WEATHER IN KCMO"

    def __init__(self,args):
        win32serviceutil.ServiceFramework.__init__(self,args)
        self.hWaitStop = win32event.CreateEvent(None,0,0,None)
        socket.setdefaulttimeout(60)

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.hWaitStop)

    def SvcDoRun(self):
        servicemanager.LogMsg(servicemanager.EVENTLOG_INFORMATION_TYPE,
                            servicemanager.PYS_SERVICE_STARTED,
                            (self._svc_name_,''))
        self.main()

    def main(self):
        pass

def StartUpService():
    print("starting service:")
    win32serviceutil.HandleCommandLine(AppServerSvc)

WEBDRIVER_PATH = "C:\\Users\mattk\Desktop\streaming_data_experiment\chromedriver_win32\chromedriver.exe"

def get_selenium_driver():
    """
    returns webdriver so selenium can be implemented more easily
    """
    webdriver_path = WEBDRIVER_PATH
    service = Service(executable_path=webdriver_path)
    options = webdriver.ChromeOptions()
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--ignore-ssl-errors')
    # driver = webdriver.Chrome(chrome_options=options)
    driver = webdriver.Chrome(service=service, options=options)    
    return driver


def zco(x):
    search = SearchEngine()
    city = search.by_zipcode(x).major_city
    return city if city else 'None'        

def get_zipcodes(kc=True,):
    
    if kc == True:
        zip_url = "https://www.zip-codes.com/city/mo-kansas-city.asp"
        driver = get_selenium_driver()
        driver.get(zip_url)
        driver.implicitly_wait(1) 
        zip_list = []
        for i in range(72):
            if i > 0:
                zip_count = i
                xpath = f"/html/body/table/tbody/tr/td[2]/div/div[7]/table/tbody/tr[{zip_count}]/td[1]/a"
                # elem = driver.find_elements(By.XPATH, xpath) 
                elem = find_the_elements(xpath,driver)
                for el in elem:
                    string = el.text
                    temp = re.findall(r'\d+', string)
                    res = list(map(int, temp))
                    res = f"{res[0]}"
                    # print(res)
                    zip_list.append(res)
    else:
        zip_url = "https://247wallst.com/special-report/2019/06/26/the-most-populated-zip-codes-in-america/"
        driver = get_selenium_driver()
        driver.get(zip_url)
        driver.implicitly_wait(1) 
        zip_list = []
        for i in range(50):
            if i > 0:
                zip_count = i
                xpath = f"/html/body/div[1]/div/section/div/div/div[1]/table/tbody/tr[{zip_count}]/td[2]"
                # elem = driver.find_elements(By.XPATH, xpath) 
                elem = find_the_elements(xpath,driver)
                for el in elem:
                    string = el.text
                    temp = re.findall(r'\d+', string)
                    res = list(map(int, temp))
                    res = f"{res[0]}"
                    # print(res)
                    zip_list.append(res)        
    return zip_list

def find_the_elements(xpath,driver,elements = True,):

    """
    https://stackoverflow.com/questions/42683692/python-selenium-keep-refreshing-until-item-found-chromedriver
    """
    
    max_tries = 3

    for t in range(max_tries):
        element = ""
        try:
            if elements == True:
                element = driver.find_elements(By.XPATH, xpath)
                break                  # break out of the inner loop if we succeeded
            else:
                element = driver.find_element(By.XPATH, xpath)
                break
        except:
            print("failed to load link. retrying..." if t < max_tries-1 else "giving up.")
            exit()
    return element, driver


# def close_ads(driver):
#     """
#     Source for this:
#     https://stackoverflow.com/questions/41460265/hide-remove-ads-with-selenium-python
#     """
#     all_iframes = driver.find_elements(By.TAG_NAME,"iframe")
#     if len(all_iframes) > 0:
#         print("Ad Found\n")
#         driver.execute_script("""
#             var elems = document.getElementsByTagName("iframe"); 
#             for(var i = 0, max = elems.length; i < max; i++)
#                 {
#                     elems[i].hidden=true;
#                 }
#                             """)
#         print('Total Ads: ' + str(len(all_iframes)))
#     else:
#         print('No frames found')
#     return driver

def grab_weather_info():

    SHRT_SLEEP = 3
    LONG_SLEEP = 7

    kc_zips = get_zipcodes(kc=False)
    ct = 0
    for zip in kc_zips:
        XPTHS = [
            "/html/body/div/div[7]/div[1]/div[1]/div[2]/div[3]/div[3]/div[2]", # wind speed
            "/html/body/div/div[7]/div[1]/div[1]/div[2]/div[3]/div[10]/div[2]", # cloud ceiling
            "/html/body/div/div[7]/div[1]/div[1]/div[2]/div[3]/div[6]/div[2]", # dew point
            "/html/body/div/div[7]/div[1]/div[1]/div[2]/div[2]/div[1]/div[1]/div/div",# temperature in F
            "/html/body/div/div[7]/div[1]/div[1]/div[2]/div[3]/div[4]/div[2]", # humidity
            "/html/body/div/div[7]/div[1]/div[1]/div[2]/div[3]/div[7]/div[2]" # air pressure
            # "/html/body/div/div[7]/div[1]/div[1]/div[2]/div[2]/div[1]/div[2]" # whats_on
            "/html/body/div/div[7]/div[1]/div[1]/div[4]/div[2]/div[2]/div[1]/p[4]/span", # day_precip_chance
            "/html/body/div/div[7]/div[1]/div[1]/div[5]/div[2]/div[2]/div[1]/p[3]/span" # night_precip_chance
            # "/html/body/div[1]/main/div[2]/main/div[1]/section/div[2]/div[2]/details[1]/div/div[2]/ul/li[2]/div/span[2]" # UV Index
                ]
        if ct == 0:
            # if ct < 1:
            driver = get_selenium_driver()
            try:
                driver.set_page_load_timeout(LONG_SLEEP)
                driver.get("https://www.accuweather.com") 
                time.sleep(SHRT_SLEEP)
                # driver = close_ads(driver)
                # time.sleep(SHRT_SLEEP)
            except TimeoutException as ex:
                isrunning = 0 # can be used later when this project is at a sophisticated level
                print("Exception has been thrown. " + str(ex))
                driver.close()
                break
            # search_element = driver.find_element(By.XPATH, ) 
            search_element, driver = find_the_elements("/html/body/div[1]/div[1]/div[3]/div/div[1]/div[1]/form/input",driver,elements=False)
            # action.move_to_element(search_element).click().send_keys(f"{zip}").perform()        
            time.sleep(SHRT_SLEEP)
            search_element.send_keys(f"{zip}") 
            time.sleep(SHRT_SLEEP)
            search_element.send_keys(Keys.ENTER)
        if ct > 0: # shorten the algorithm 
            driver.set_page_load_timeout(LONG_SLEEP)
            forecast_url_4_srch = driver.current_url
            driver.get(forecast_url_4_srch) 
            time.sleep(SHRT_SLEEP)
            # driver = close_ads(driver)
            # time.sleep(SHRT_SLEEP)
            # search_element = driver.find_element(By.XPATH, "/html/body/div[1]/div[1]/div[2]/div/div/div/div[1]/form/input") 
            search_element = find_the_elements("/html/body/div[1]/div[1]/div[2]/div/div/div/div[1]/form/input",driver,elements=False)
            # action.move_to_element(search_element).click().send_keys(f"{zip}").perform()        
            time.sleep(SHRT_SLEEP)
            search_element.send_keys(f"{zip}") 
            time.sleep(SHRT_SLEEP)
            search_element.send_keys(Keys.ENTER)
        ct += 1
        # "/html/body/div[1]/div[1]/div[2]/div/div/div/div[1]" # search bar for weather_forecast page
        # driver = close_ads(driver)
        # time.sleep(SHRT_SLEEP)
        url_ = driver.current_url
        
        grabbed = [
            "wind_speed",
            "cloud_ceiling",
            "dew_point",
            "temperature_in_F",
            "humidity",
            "air_pressure",
            # "weather_conditions",
            "day_precip_chance",
            "night_precip_chance"
        ]
        # time.sleep(30)
        weather_dict = {}
        weather_dict['zipcode'] = [zip]
        
        print("working on zipcode::",zip)

        try:
            city_name = zco(zip,)
        except:
            city_name = "failed_to_get_city_name"
        print("city name::", city_name)
        weather_dict['city'] = [city_name]
        if "search-locations" in url_:
            time.sleep(SHRT_SLEEP)
            srch_elmt, driver = find_the_elements("/html/body/div/div[7]/div[1]/div[1]/div[2]/a[1]/p[1]",driver,elements=False)
            # srch_elmt = driver.find_element(By.XPATH, "/html/body/div/div[7]/div[1]/div[1]/div[2]/a[1]/p[1]")
            srch_elmt.click()
        else:
            driver.get(url=url_)
        time.sleep(SHRT_SLEEP)
        # driver = close_ads(driver) # close ads
        # time.sleep(SHRT_SLEEP)
        # expand_details = driver.find_element(By.XPATH, "/html/body/div/div[7]/div[1]/div[1]/a[1]/div[2]/span[2]/span") # click to expand details
        expand_details, driver = find_the_elements("/html/body/div/div[7]/div[1]/div[1]/div[2]/a[1]/p[1]",driver,elements=False)
        expand_details.click()
        time.sleep(SHRT_SLEEP)
        # driver = close_ads(driver) # close ads
        # time.sleep(SHRT_SLEEP)


        idx = 0
        for X in XPTHS:
            # try:
            # if driver:
            elem = driver.find_elements(By.XPATH, X) 
            if elem:
                for el in elem:
                    string = el.text
                    temp = re.findall(r'\d+', string)
                    res = list(map(int, temp))
                    print(f"{grabbed[idx]}::",res[0])
                    weather_dict[f'{grabbed[idx]}'] = [res]
                idx += 1
            else:
                print("z")
            

        now = datetime.now()
        formatted_date = now.strftime("%m_%d_%Y_%H_%M_%S")
            
        weather_dict['timestamp'] = formatted_date
        weather_new = pd.DataFrame(data=weather_dict)
        try:
            weather_old = pd.read_csv("weather_data.csv")
            weather_together = pd.concat([weather_old, weather_new], ignore_index=True)
            weather_together.to_csv("weather_data.csv",index=False)
        except:
            weather_new.to_csv("weather_data.csv",index=False)   
        time.sleep(SHRT_SLEEP)     
        
if __name__ == "__main__":
    # StartUpService()
    # minutes_to_sleep = 15
    # for i in range(3):
        # print(i)
    # driver = get_selenium_driver()
    grab_weather_info()
        # print(f"sleeping {minutes_to_sleep} minutes until next scrape")
        # time.sleep(minutes_to_sleep * 60)
