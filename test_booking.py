# to change the Training lesson: change the "days=xx" in line 23, change the TARGET_TIME line 25 change the line 113 for the correct page.
print("Test")

import time
import os
import datetime
import pytz
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys

# Configuration
USER = os.environ.get('REITBUCH_USER')
PASS = os.environ.get('REITBUCH_PASS')
URL = "https://rfv-leonberg.reitbuch.com/weekplan.php"

# Targets (Update these for your specific lesson)
# TARGET_DATE = "12.02." 
TARGET_DATE = (datetime.datetime.now(pytz.timezone('Europe/Berlin')) + datetime.timedelta(days=34)).strftime("%d.%m.")
#TARGET_DATE = (datetime.datetime.now(pytz.timezone('Europe/Berlin')) + datetime.timedelta(days=35)).strftime("%d.%m.") #Sonntag
TARGET_TIME = "9:00 - 10:00"
#TARGET_TIME = "10:00 - 11:00"
TARGET_NAME = "Dressur Standard"
print(TARGET_DATE)

# Timing Trigger: Actual Booking Time (Midnight)
TRIGGER_HOUR = 0
TRIGGER_MINUTE = 0
TRIGGER_SECOND = 1

def run_test_booking():
    tz = pytz.timezone('Europe/Berlin')
    
    # --- SMART DAY-AWARE LOGIC ---
    now_temp = datetime.datetime.now(tz)
    target_booking_dt = now_temp.replace(hour=TRIGGER_HOUR, minute=TRIGGER_MINUTE, second=TRIGGER_SECOND, microsecond=0)
    
    # If the target time (00:00:02) is technically "earlier" than right now (e.g., 23:55),
    # it means we are aiming for midnight TONIGHT (which is the next calendar day).
    if target_booking_dt < now_temp:
        target_booking_dt += datetime.timedelta(days=1)
        
    # Now, subtracting 2 minutes will correctly land at 23:58:02 of "today"
    login_trigger_dt = target_booking_dt - datetime.timedelta(minutes=2)

    # 1. WAIT PHASE 1: LOGIN TRIGGER (23:58:02)
    print(f"Current time: {now_temp.strftime('%H:%M:%S')}")
    print(f"Target Booking: {target_booking_dt.strftime('%d.%m. %H:%M:%S')}")
    print(f"Login Trigger:  {login_trigger_dt.strftime('%d.%m. %H:%M:%S')}")
    print("---------------------------------------------------------")
    
    while True:
        now = datetime.datetime.now(tz)
        if now >= login_trigger_dt:
            print(f"LOGIN TRIGGER REACHED: {now.strftime('%H:%M:%S')}")
            break
        time.sleep(0.5)

    # 2. INITIALIZATION & LOGIN
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    # Set the window size to Full HD
    chrome_options.add_argument("--window-size=1920,1080")
    
    chrome_options.add_argument("--remote-debugging-port=9222")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36")
    
    driver = webdriver.Chrome(options=chrome_options)
    
    # Additional command to ensure the window is maximized
    driver.set_window_size(1920, 1080)
    
    wait = WebDriverWait(driver, 20)
    
    try:
        print("Logging in early to save time...")
        driver.get(URL)
        
        user_field = wait.until(EC.presence_of_element_located((
            By.XPATH, "//input[contains(@name, 'user') or contains(@id, 'user') or @type='text']"
        )))
        user_field.send_keys(USER)
        
        pass_field = wait.until(EC.presence_of_element_located((
            By.XPATH, "//input[@type='password' or contains(@name, 'pass')]"
        )))
        pass_field.send_keys(PASS)
        
        try:
            login_btn = driver.find_element(By.XPATH, "//input[@value='Anmelden'] | //button[contains(., 'Anmelden')] | //input[@type='submit']")
            login_btn.click()
        except:
            pass_field.send_keys(Keys.ENTER)
        
        print("Login complete. Standing by for Midnight...")

        # 3. WAIT PHASE 2: BOOKING TRIGGER (Wait for 00:00:02)
        while True:
            now = datetime.datetime.now(tz)
            if now >= target_booking_dt:
                print(f"BOOKING TRIGGER REACHED: {now.strftime('%H:%M:%S')}")
                break
            time.sleep(0.05) # Higher precision for the midnight jump

        # 4. DIRECT NAVIGATION & BOOK
        #driver.get("https://rfv-leonberg.reitbuch.com/weekplan.php?w=3&p=1")
        driver.get("https://rfv-leonberg.reitbuch.com/weekplan.php?w=4&p=1")
        
        lesson_xpath = (
            f"//td[descendant::*[contains(text(), '{TARGET_DATE}')]]"
            f"//div[contains(@class, 'wp_event') and "
            f".//div[contains(text(), '{TARGET_TIME}')] and "
            f".//div[contains(text(), '{TARGET_NAME}')]]"
        )
        
        lesson_div = wait.until(EC.presence_of_element_located((By.XPATH, lesson_xpath)))
        driver.execute_script("arguments[0].click();", lesson_div)
            
        confirm_xpath = "//*[contains(text(), 'Kostenpflichtig anmelden') or @value='Kostenpflichtig anmelden' or @name='opnevent_book']"
        confirm_btn = wait.until(EC.element_to_be_clickable((By.XPATH, confirm_xpath)))
        confirm_btn.click()
        
        time.sleep(3)
        driver.save_screenshot("test_success.png")
        print(f"Success! Booking completed at: {datetime.datetime.now(tz).strftime('%H:%M:%S')}")

    except Exception as e:
        print(f"Failed: {e}")
        driver.save_screenshot("test_error.png")
    finally:
        driver.quit()

if __name__ == "__main__":
    run_test_booking()
