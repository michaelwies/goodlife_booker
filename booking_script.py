import os
import argparse
import logging

from time import sleep
from datetime import datetime, timedelta

from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, ElementNotInteractableException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.firefox.options import Options 

class BookingException(Exception):
    pass

logging.basicConfig(level=logging.INFO)

load_dotenv()
GOODLIFE_USERNAME = os.getenv('GOODLIFE_USERNAME')
GOODLIFE_PASSWORD = os.getenv('GOODLIFE_PASSWORD')

if not GOODLIFE_USERNAME or not GOODLIFE_PASSWORD:
    logging.error('username/password not defined in .env file')
    exit(1)

def wait_for_element_by(browser, element_name, element_type, waitsecs):
    try:
        WebDriverWait(browser, waitsecs).until(EC.presence_of_element_located((element_type, element_name)))
    except TimeoutException:
        print ("Loading {element_name} took too much time!")

def book_gym_session(browser, day, time, slot):
    # navigate to login page
    browser.get('https://www.goodlifefitness.com/member-details.html')

    # LOGIN
    # 1. Username
    logging.info(f'Logging in with username {GOODLIFE_USERNAME}')
    wait_for_element_by(browser, 'js-login-email', By.CLASS_NAME, 10)
    emailIn = browser.find_elements_by_class_name('js-login-email')
    emailIn[1].send_keys(GOODLIFE_USERNAME)
    # 2. Password
    wait_for_element_by(browser, 'js-login-password', By.CLASS_NAME, 10)
    passwordIn = browser.find_elements_by_class_name('js-login-password')
    passwordIn[1].send_keys(GOODLIFE_PASSWORD)
    sleep(1)
    # 3. Submit
    submitButton = browser.find_elements_by_class_name('js-login-submit')
    submitButton[1].click()
    # Allow for some laginess during peak hours for login to complete
    sleep(10)

    # navigate to workout booking page
    browser.get('https://www.goodlifefitness.com/book-workout.html#no-redirect')
    sleep(2) #arbitrary pause for page load

    # select date x days from now
    days_from_now = datetime.now() + timedelta(days=day)
    days_from_now = days_from_now.strftime('%Y-%m-%d')
    dayIndex = day
    slotIndex = slot-1
    logging.info(f'Selecting date {days_from_now} ({day} days from now).')
    
    # Wait for tabs to show up
    wait_for_element_by(browser, 'js-class-weekday', By.CLASS_NAME, 10)
    # Load the tabs element
    dateTabLinks = browser.find_elements_by_class_name('js-class-weekday')
    print("# of DateTabLinks: "+str(len(dateTabLinks)))
    # Click the n-th tab (zero-indexed)
    dateTabLinks[dayIndex].click()

    # select appropriate session to book
    logging.info(f'Selecting 0th Workout on {days_from_now}')
    dayDivID = 'day-number-'+str(day+1)
    wait_for_element_by(browser, dayDivID, By.ID, 10)
    dayDiv =  browser.find_element_by_id(dayDivID)
    print("======   dayDiv   =====")
    print('class: '+dayDiv.get_attribute('class'))
    print('data-index: '+dayDiv.get_attribute('data-index'))
    print("=======================")
    wait_for_element_by(browser, 'class-action', By.CLASS_NAME, 10)
    RegistrationButtons = dayDiv.find_elements_by_class_name('class-action')
    print("======   RegistrationButton   =====")
    print('class: '+RegistrationButtons[slotIndex].get_attribute('class'))
    print('data-workout-id: '+RegistrationButtons[slotIndex].get_attribute('data-workout-id'))
    print("=======================")
    print("# Registration Buttons Found: "+str(len(RegistrationButtons)))

    # Stay in this loop while the "data-class-action" of the button is something other than cancel.
    # Once it's 'cancel-class' that means the class is booked, so we'll skip the loop and exit
    dataClassAction = RegistrationButtons[slotIndex].get_attribute('data-class-action')
    attempt = 0
    while dataClassAction != 'cancel-class' and attempt < 5:
        logging.info(f'Attempting to book slot {slot} on {days_from_now}')
        attempt = attempt + 1
        #Click the register button
        RegistrationButtons[slotIndex].click()
        # accept code of conduct
        logging.info(f'Agreeing to terms')
        wait_for_element_by(browser, 'js-workout-booking-agreement-input', By.ID, 10)
        browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        browser.find_element_by_id('js-workout-booking-agreement-input').click()
        sleep(1)

        # Confirm Booking
        confirm_button = browser.find_element_by_class_name('js-terms-agreement-cta')
        confirm_button.click()
        logging.info(f'Confirmation Button Clicked')
        # Wait 60 seconds, then reload the page and try again (will exit if booked)
        sleep(60)
        browser.refresh()
        sleep(5)

        # Wait for the weekday tabs, and click the one indicated in input variable 'day'
        wait_for_element_by(browser, 'js-class-weekday', By.CLASS_NAME, 10)
        dateTabLinks = browser.find_elements_by_class_name('js-class-weekday')
        while len(dateTabLinks)<7:
            dateTabLinks = browser.find_elements_by_class_name('js-class-weekday')
        dateTabLinks[dayIndex].click()
        # identify the container for the selected 'day'
        wait_for_element_by(browser, dayDivID, By.ID, 10)
        dayDiv =  browser.find_element_by_id(dayDivID)
        # Wait for the registration buttons, and get the 'data-class-action' of the one we're trying to register for
        wait_for_element_by(browser, 'class-action', By.CLASS_NAME, 10)
        RegistrationButtons = dayDiv.find_elements_by_class_name('class-action')
        dataClassAction = RegistrationButtons[slotIndex].get_attribute('data-class-action')

    logging.info('Booking confirmed')



if __name__ == '__main__':
    # setup arguments
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--headless', action='store_true',
        help='run in headless browser mode'
    )
    parser.add_argument(
        '--time_slot', type=str, default='6:00AM - 7:00AM',
        help='desired time-slot. str format ex: "6:00AM - 7:00AM"'
    )
    parser.add_argument(
        '--days', type=int, default=6,
        help='how many days in the future to book (0 to 6)'
    )
    parser.add_argument(
        '--slot', type=int, default=1,
        help='Which slot to book (1 to n)'
    )
    args = parser.parse_args()


    ####### NOT USING CHROME BROWSER #######
    '''
    # setup browser with chrome webdriver 
    options = Options()
    options.headless = args.headless
#    browser = webdriver.Chrome(options=options)
    '''
    #########################################
    
    # A Firefox profile was created manually in the browser and saved to this location
    ## Profile pre-approves location permissions on goodlife.com
    profilePath = 'C:/Users/mwies/Documents/git/goodlife_booker/firefox_profile'
    
    #Create profile from profile path and use to instantiate firefox browser
    profile = webdriver.FirefoxProfile(profilePath) 
    browser = webdriver.Firefox(firefox_profile=profile)

    # book session
    try:
        book_gym_session(browser, args.days, args.time_slot, args.slot)
        success = True
    except BookingException as e:
        logging.error(e)
        success = False

    # close browser & exit
    #browser.close()
    #browser.quit()

    logging.info('Exiting')
    exit(int(not success))
