
import time
import sys
import os
import urllib, urllib2
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from datetime import datetime, timedelta
from BeautifulSoup import BeautifulSoup


class MfpExtractor(object):

    def __init__(self, username, password):
        
        # url for website
        self.base_url = 'http://www.myfitnesspal.com'

        # user provided username and password
        self.username = username
        self.password = password

        # only want to access a page once every 2 seconds 
        #so we don't thrash the mfp server too much
        self.earliest_query_time = time.time()
        self.query_interval = 2

        #selenium driver
        self.driver = webdriver.Firefox()

    # method to do login
    def login(self):
        self.driver.get(self.base_url)

        elem = self.driver.find_element_by_link_text("Log In")
        elem.click()

        elem = self.driver.find_element_by_name("username")
        elem.send_keys(self.username)

        elem = self.driver.find_element_by_name("password")
        elem.send_keys(self.password)

        elem.send_keys(Keys.RETURN)
        self.driver.implicitly_wait(10)

    def access_page(self, path, username, params):

        # go to sleep for as long as necessary to avoid making more than 
        # one call to the website every 2 seconds
        while time.time() < self.earliest_query_time:
            sleep_dur = self.earliest_query_time - time.time()
            time.sleep(sleep_dur)

        # strip the path
        path = path.lstrip('/')
        path = path.rstrip('/')

        # construct the url
        url = self.base_url + '/' + path + '/' + username + '?' + urllib.urlencode( params )

        self.driver.get(url)

        page = self.driver.find_element_by_tag_name("html")

        return self.driver.page_source


    def get_daily_food_data_from_mfp(self, username, date):

        diary_path = '/food/diary/'
        params = {'date' : date}

        return self.access_page(diary_path, username, params)

    def get_daily_exercise_data_from_mfp(self, username, date):

        diary_path = '/exercise/diary'
        params = {'date' : date}

        return self.access_page(diary_path, username, params)

    def finish(self):
        self.driver.close()


if __name__ == "__main__":

    args = sys.argv

    # check for username and password and optional number of days to get
    if len(args) not in [3,4]:
        print "Incorrect number of arguments"
        print "Argument pattern: username password [days]"
        exit(1)

    username = args[1]
    password = args[2]

    # check how many days to retrieve
    if len(args) == 4:
        # we've been specified a number of days
        num_days = timedelta(days=float(args[3]))
    else:
        # we haven't, go back 4 weeks
        num_days = timedelta(days=28.0)
    
    print 'Retrieving food and exercise data for %s days' % num_days.days

    # the date we want to go back to in the history
    start_date = datetime.now() - num_days

    # create list of days to get
    dates_to_check = []
    date_to_check = datetime.now()
    one_day = timedelta(days=1)
    while date_to_check - one_day > start_date:
        date_to_check = date_to_check - one_day
        dates_to_check.append(date_to_check)

    # initialise an MfpExtractor to login to the website
    mfp = MfpExtractor(username, password)
    mfp.login()

 # want to store downloaded html files for later processing. Check to see 
    # if the directories already exist, if not then make them.
    cwd = os.getcwd()
    exercise_dirname = os.path.join(username, 'exercise')
    food_dirname = os.path.join(username, 'food')

    exercise_dir = os.path.join(cwd, exercise_dirname)
    food_dir = os.path.join(cwd, food_dirname)

    if not os.path.isdir(exercise_dir):
        os.mkdir(exercise_dir)
    if not os.path.isdir(food_dir):
        os.mkdir(food_dir)

    for date_to_check in dates_to_check:
        fmt_date = date_to_check.strftime('%Y-%m-%d')
        exer_file = os.path.join(exercise_dir, 'exercise_diary_%s.html' % fmt_date)
        if not os.path.isfile(exer_file):
            print 'Exercise file for %s not found, fetching from mfp' % fmt_date
            html = mfp.get_daily_exercise_data_from_mfp(username, fmt_date)
            print 'Exercise file for %s retrieved' % fmt_date
            soup = BeautifulSoup(html)
            out_file = open(exer_file, 'w')
            out_file.write(soup.prettify())
        else:
            print 'Exercise file for %s already downloaded' % fmt_date
        food_file = os.path.join(food_dir, 'food_diary_%s.html' % fmt_date)
        if not os.path.isfile(food_file):
            print 'Food file for %s not found, fetching from mfp' % fmt_date
            html = mfp.get_daily_food_data_from_mfp(username, fmt_date)
            print 'Food file for %s retrieved' % fmt_date
            soup = BeautifulSoup(html)
            out_file = open(food_file, 'w')
            out_file.write(soup.prettify())
        else:
            print 'Food file for %s already downloaded' % fmt_date


    mfp.finish()