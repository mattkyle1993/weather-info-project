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
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import accuracy_score
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

def keep_retrying(zip_list,driver,max_retry=3,):
    failed_zip = []
    for zip in zip_list:
        # if grab_weather_info(zip,driver) != True:
        a = 0
        if a == 0:
            answer = grab_weather_info(zip,driver)
            if answer == True:
                pass
            else:
                a = 1
        if a == 1:
            print("this zip failed, sending back for retry:",zip)
            failed_zip.append(zip)
    # Retry the failed strings
    for retry_zip in failed_zip:
        retry = 0
        while retry <= max_retry:
            retry += 1
            if grab_weather_info(retry_zip,driver):
                failed_zip.remove(retry_zip)
    print("number of failed zips:",len(failed_zip))

def find_the_elements(xpath,driver,elements = True,max_tries=3,sleep_seconds=0):

    """
    https://stackoverflow.com/questions/42683692/python-selenium-keep-refreshing-until-item-found-chromedriver
    """
        
    # max_tries = 3

    for t in range(max_tries):
        element = ""
        try:
            if elements == True:
                element = driver.find_elements(By.XPATH, xpath)
                time.sleep(sleep_seconds)
                # break                  # break out of the inner loop if we succeeded
            else:
                element = driver.find_element(By.XPATH, xpath)
                time.sleep(sleep_seconds)
                # break
        except:
            if t < max_tries-1:
                print("failed to load link. retrying...")
            else:
                print('giving up')
                # quit()
            
    return element, driver


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
    driver.maximize_window()
    return driver


def zco(x):
    search = SearchEngine()
    city = search.by_zipcode(x).major_city
    return city if city else 'None'        

def get_zipcodes(kc=False,top_num_zips = 0):
    
    xpaths = [
        "/html/body/table/tbody/tr/td[2]/div/div[7]/table/tbody/tr[{zip_count}]/td[1]/a",
        "/html/body/div[1]/div/section/div/div/div[1]/table/tbody/tr[{zip_count}]/td[2]"
    ]
    zip_urls = [
        "https://www.zip-codes.com/city/mo-kansas-city.asp",
        "https://247wallst.com/special-report/2019/06/26/the-most-populated-zip-codes-in-america/"
                ]
    
    if kc == True:
        zip_url = zip_urls[0]
        # xpath = xpaths[0]
        if top_num_zips == 0:
            NUM_ZIPS = 72
        else:
            NUM_ZIPS = top_num_zips
    else:
        zip_url = zip_urls[1]
        # xpath = xpaths[1]
        if top_num_zips == 0:
            NUM_ZIPS = 50
        else:
            NUM_ZIPS = top_num_zips
    
    driver = get_selenium_driver()
    # driver.get(zip_url)
    driver = try_except_get(driver,zip_url)
    drivr = [driver]
    for d in drivr:
        if d == None:
            break
    driver.implicitly_wait(1) 
    
    zip_list = []
    for i in range(NUM_ZIPS):
        # print("i here", [i])
        if i > 0:
            if kc == False:
                xpath= f"/html/body/div[1]/div/section/div/div/div[1]/table/tbody/tr[{i}]/td[2]"
            else:
                xpath = f"/html/body/table/tbody/tr/td[2]/div/div[7]/table/tbody/tr[{i}]/td[1]/a"
            # zip_count = i
            # xpath = f"/html/body/div[1]/div/section/div/div/div[1]/table/tbody/tr[{zip_count}]/td[2]"
            xpath = xpath.format(zip_count=i)
            # elem = driver.find_elements(By.XPATH, xpath) 
            elem, driver = find_the_elements(xpath,driver,elements=True)
            for el in elem:
                string = el.text
                temp = re.findall(r'\d+', string)
                res = list(map(int, temp))
                res = f"{res[0]}"
                # print(res)
                zip_list.append(res)        
    # print(zip_list)
    return zip_list, driver

def try_except_get(driver, url):
    try:
        driver.get(url)
        return driver
    except Exception as error:
        print("ERROR::",Exception)
        return None

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

def grab_weather_info(zip,driver):

    SHRT_SLEEP = 3
    LONG_SLEEP = 5

    # kc_zips, driver = get_zipcodes()
    # ct = 0
    # for zip in kc_zips:
    # print("zip here::",zip)
    XPTHS = [
        "/html/body/div/div[7]/div[1]/div[1]/div[2]/div[3]/div[3]/div[2]", # wind speed
        "/html/body/div/div[7]/div[1]/div[1]/div[2]/div[3]/div[10]/div[2]", # cloud ceiling
        "/html/body/div/div[7]/div[1]/div[1]/div[2]/div[3]/div[6]/div[2]", # dew point
        "/html/body/div/div[7]/div[1]/div[1]/div[2]/div[2]/div[1]/div[1]/div/div",# temperature in F
        "/html/body/div/div[7]/div[1]/div[1]/div[2]/div[3]/div[4]/div[2]", # humidity
        "/html/body/div/div[7]/div[1]/div[1]/div[2]/div[3]/div[7]/div[2]" # air pressure
        # "/html/body/div/div[7]/div[1]/div[1]/div[2]/div[2]/div[1]/div[2]" # whats_on
        # "/html/body/div[1]/div[7]/div[1]/div[1]/div[4]/div[2]/div[2]/div[1]/p[4]/span", # day_precip_chance
        # "/html/body/div[1]/div[7]/div[1]/div[1]/div[5]/div[2]/div[2]/div[1]/p[3]/span" # night_precip_chance
        # "/html/body/div[1]/main/div[2]/main/div[1]/section/div[2]/div[2]/details[1]/div/div[2]/ul/li[2]/div/span[2]" # UV Index
            ]
    
    
    forecast_url_4_srch="https://www.accuweather.com/en/search-locations?query={zipcode}"

    driver = try_except_get(driver,forecast_url_4_srch.format(zipcode=zip))
    drivr = [driver]
    for d in drivr:
        if d == None:
            break
    time.sleep(SHRT_SLEEP)
    search_element, driver = find_the_elements("/html/body/div/div[6]/div[1]/div[1]/div[2]/a[1]",driver,elements=False)
    
    time.sleep(SHRT_SLEEP)
    search_element.click()
    time.sleep(LONG_SLEEP)
    # print("test 3")
    
    grabbed = [
        "wind_speed",
        "cloud_ceiling",
        "dew_point",
        "temperature_in_F",
        "humidity",
        "air_pressure",
        # "weather_conditions",
        # "day_precip_chance",
        # "night_precip_chance"
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
    expand_details, driver = find_the_elements("/html/body/div[1]/div[7]/div[1]/div[1]/a[1]/div[2]/span[2]/span",driver,elements=False)
    
    # print("test 2")
    try:
        expand_details.click()
    except:
        for e in expand_details:
            e.click()  
    time.sleep(SHRT_SLEEP)
    # driver = close_ads(driver) # close ads
    # time.sleep(SHRT_SLEEP)


    idx = 0
    error_ct = 0
    for X in XPTHS:
        # try:
        # if driver:
        if idx <= len(XPTHS):
            elem, driver = find_the_elements(xpath=X,driver=driver,sleep_seconds=1)
        else:
            break
        # print("test 1")
        # elem = driver.find_elements(By.XPATH, X) 
        if elem:
            for el in elem:
                string = el.text
                temp = re.findall(r'\d+', string)
                res = list(map(int, temp))
                if idx != 5:
                    print(f"{grabbed[idx]}::",res[0])
                    weather_dict[f'{grabbed[idx]}'] = res
                if idx == 5:
                    print(f"{grabbed[idx]}::",res[0])
                    weather_dict[f'{grabbed[idx]}'] = res[0]
                time.sleep(SHRT_SLEEP)
            idx += 1
        else:
            error_ct += 1
    if error_ct > 0:
        # print("failed on grabbing weather data. sending zip to back of the line.")
        return False    
    # print("test 4")
    now = datetime.now()
    formatted_date = now.strftime("%m_%d_%Y_%H_%M_%S")
        
    weather_dict['timestamp'] = formatted_date
    weather_new = pd.DataFrame(data=weather_dict)
    # print("test 6")
    try:
        weather_old = pd.read_csv("weather_data.csv")
        weather_together = pd.concat([weather_old, weather_new], ignore_index=True)
        weather_together.to_csv("weather_data.csv",index=False)
        # print("test 7")
    except:
        weather_new.to_csv("weather_data.csv",index=False)   
        # print("test 8")
    time.sleep(SHRT_SLEEP)     
    return True

def predict_model():
    
    data = pd.read_csv("weather_data.csv")

    # Split data into features and target
    X = data.drop(['temperature_in_F',"zipcode","city","timestamp"], axis=1)  # Replace 'target_column' with the actual target column name
    y = data['temperature_in_F']

    # Split data into training and testing sets
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Create and train the Decision Tree model
    model = DecisionTreeClassifier()
    model.fit(X_train, y_train)

    # Make predictions on the test set
    y_pred = model.predict(X_test)

    # Evaluate the model
    accuracy = accuracy_score(y_test, y_pred)
    print(f'Accuracy: {accuracy:.2f}')

    # Get a list of the most important features
    feature_importances = model.feature_importances_
    feature_names = X.columns
    important_features = sorted(zip(feature_names, feature_importances), key=lambda x: x[1], reverse=True)
    print('Most important features:')
    for feature, importance in important_features:
        print(f'{feature}: {importance:.4f}')

    # Create a timestamp for the output CSV file
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')

    # Write the important features to a CSV file
    output_filename = f'important_features_{timestamp}.csv'
    important_features_df = pd.DataFrame(important_features, columns=['Feature', 'Importance'])
    important_features_df.to_csv(output_filename, index=False)

    print(f'Important features saved to {output_filename}')
    
if __name__ == "__main__":
    zip_list, driver = get_zipcodes(top_num_zips=15)
    keep_retrying(zip_list=zip_list,driver=driver)
    predict_model()
