from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

import math
import os
import json
import time
import requests

URL = input('Введите URL: ')
HEADERS = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
zipcode = "28277"

options = webdriver.ChromeOptions()
options.add_extension('plugin.crx')
options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36")

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options)

driver.get(URL)
time.sleep(2)

wait = WebDriverWait(driver, 10)

cookies_file_path = "cookies.json"
try:
    with open(cookies_file_path, "r") as file:
        cookies = json.load(file)
    for cookie in cookies:
        if 'expiry' in cookie:
            cookie['expiry'] = int(cookie['expiry'])
        driver.add_cookie(cookie)
    driver.refresh()
except FileNotFoundError:
    print("Cookies file не найден.")
    driver.refresh()

title = ""
description = ""
price = ""
brand = ""
url = str(URL)

def parse(URL):
    global title, description, price, brand
    try:
        title = driver.find_element(By.XPATH, "//span[@id='productTitle']").text
        whole_price_element = driver.find_element(By.XPATH, "//span[@class='a-price-whole']")
        fraction_price_element = driver.find_element(By.XPATH, "//span[@class='a-price-fraction']")
        list_items = driver.find_elements(By.XPATH, "//ul[@class='a-unordered-list a-vertical a-spacing-mini']//span[@class='a-list-item']")
        brand = driver.find_element(By.XPATH, "//span[@class='a-size-base po-break-word']").text
        
        whole_price = whole_price_element.text
        fraction_price = fraction_price_element.text
        price_float = float(f"{whole_price}.{fraction_price}")
        price_ceil = math.ceil(price_float)
        price = str(price_ceil)
        description = '\n'.join(item.text for item in list_items)

        lis = driver.find_elements(By.CSS_SELECTOR, 'li.item.imageThumbnail.a-declarative')
        output_dir = 'images'
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        for i, li in enumerate(lis):
            img = li.find_element(By.TAG_NAME, 'img')
            src = img.get_attribute('src')
            marker = '_AC'
            index = src.find(marker)
            if index != -1:
                src = src[:index + len(marker)] + src[src.rfind('.'):]

            try:
                response = requests.get(src, timeout=10)
                if response.status_code == 200:
                    file_path = os.path.join(output_dir, f'image_{i}.jpg')
                    with open(file_path, 'wb') as f:
                        f.write(response.content)
                    print(f'Скачано изображение {file_path}')
                else:
                    print(f'Не удалось скачать изображение {src}')
            except requests.RequestException as e:
                print(f'Ошибка при скачивании изображения {src}: {e}')

        print(title)
        print(f'The description is: {description}') 
        print(f"The price is: {price}")
        print(f"Url: {url}")
        print(f"Brand: {brand}")

    except Exception as e:
        print(f"Ошибка при парсинге страницы: {e}")

category = 'appliances'
def handle_warning_and_continue():
    try:
        if driver.find_element(By.XPATH, "//strong[text()='Warning - phone number in posting description']"):
            driver.find_element(By.XPATH, "//button[@name='continue' and @value='continue' and contains(@class, 'pickbutton')]").click()
        else:
            return
    except Exception as e:
        print(f"Ошибка при обработке предупреждения: {e}")
        return
    
def post_create(category):
    global title, description, price, brand
    try:

        driver.execute_script("window.open('https://charlotte.craigslist.org/', '_blank');")
        
        windows = driver.window_handles
        driver.switch_to.window(windows[1])

        wait.until(EC.element_to_be_clickable((By.ID, 'post'))).click()
        wait.until(EC.element_to_be_clickable((By.XPATH, "//span[@class='right-side' and contains(text(), 'for sale by owner')]"))).click()

        category_xpath = f"//span[@class='option-label' and text()='{category}']"
        wait.until(EC.element_to_be_clickable((By.XPATH, category_xpath))).click()

        action = ActionChains(driver)
        driver.find_element(By.XPATH, "//span[@class='ui-selectmenu-button ui-widget ui-state-default ui-corner-all' and @role='combobox']").click()

        try:
            new_option = wait.until(EC.element_to_be_clickable((By.XPATH, "//li[@role='option' and text()='new']")))
            action.move_to_element(new_option).click().perform()


        except Exception as e:
            print(f"Ошибка при выборе опции: {e}")
        

        delivery_option = wait.until(EC.element_to_be_clickable((By.XPATH, '//span[text()="delivery available"]')))
        delivery_option.click()

        input_title = wait.until(EC.presence_of_element_located((By.XPATH, "//input[@id='PostingTitle']")))
        input_price = driver.find_element(By.XPATH, "//input[@type='number' and @name='price']")
        input_zipcode = driver.find_element(By.XPATH, "//input[@id='postal_code']")
        input_description = driver.find_element(By.XPATH, "//textarea[@id='PostingBody']")
        input_email = driver.find_element(By.XPATH, "//input[@class='json-form-input' and @placeholder='Your email address']")
        continue_btn = driver.find_element(By.XPATH, '//button[@type="submit" and @name="go" and @value="continue"]')

        action.click(input_title).send_keys(title).perform()
        action.click(input_price).send_keys(price).perform()
        action.click(input_zipcode).send_keys(zipcode).perform()
        action.click(input_description).send_keys(description).perform()
        action.click(input_email).send_keys("lalalal@gmail.com").perform()
        action.click(continue_btn).perform()

        handle_warning_and_continue()

        driver.find_element(By.XPATH, "//button[contains(@class, 'continue') and contains(@class, 'bigbutton') and @type='submit']").click()

        file_input = wait.until(EC.presence_of_element_located((By.XPATH, '//input[@type="file"]')))
        images_folder = 'D:/Amazon/images'
        images = [os.path.abspath(os.path.join(images_folder, f)) for f in os.listdir(images_folder) if os.path.isfile(os.path.join(images_folder, f))]
        file_input.send_keys('\n'.join(images))
        time.sleep(5)

        done_button_xpath = "//button[@id='doneWithImages']"
        done_with_images_button = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.XPATH, done_button_xpath))
        )
        done_with_images_button.click()
        print("Пост создан.")


    except Exception as e:
        print(f"Ошибка при создании поста: {e}")

parse(URL)
post_create(category)

time.sleep(1000)

driver.quit()
