from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import requests
import re
import time
import urllib.request
import os
import socket


def user_info():
    while True:
        try:
            with open("User_info.txt", "r+") as file:
                content = file.read()
                if content == "":
                    user_id = input("Enter your Pixiv's user_id: ")
                    user_pw = input("Enter your password: ")
                    file.write("ID:" + user_id + "\n")
                    file.write("Pw:" + user_pw)
            with open("User_info.txt", "r") as file:
                user_id = file.readline()[3:]
                user_pw = file.readline()[3:]
                return user_id, user_pw
        except FileNotFoundError:
            with open("User_info.txt", "w") as file:  # Create file
                pass


def search_info():
    search_term = input("Please enter the picture you want to search: ")
    while True:
        try:
            num_pic = int(input("\nPlease enter total number of picture you want to download: "))
            num_likes = int(input("\n## If 0 means download all pictures ##"
                                  "\nPlease enter the minimum number of likes received by the picture: "))
            break
        except ValueError:
            print("Only numbers are accepted\n")

    return search_term, num_pic, num_likes


def loading(driver):
    driver.implicitly_wait(5)


def login_page(driver, acc_info):
    user_id = acc_info[0]
    user_pw = acc_info[1]

    loading(driver)
    login = driver.find_element_by_link_text("Login")
    login.click()

    loading(driver)
    username = driver.find_element_by_xpath('//*[@id="LoginComponent"]/form/div[1]/div[1]/input')
    username.send_keys(user_id)
    password = driver.find_element_by_xpath('//*[@id="LoginComponent"]/form/div[1]/div[2]/input')
    password.send_keys(user_pw)
    time.sleep(0.5)
    login_button = driver.find_element_by_xpath('/html/body/div[4]/div[3]/div/form/button')
    driver.execute_script('arguments[0].click()', login_button)

    loading(driver)
    proceed = driver.find_element_by_xpath('//*[@id="app-mount-point"]/div/div[2]/div/div[2]/a[2]')
    proceed.click()


def search(driver, search_term):
    loading(driver)
    search_bar = driver.find_element_by_xpath('//*[@id="root"]/div[2]/div[1]/div[1]/div[1]/div/div[2]/form/div/input')
    search_bar.clear()
    search_bar.send_keys(search_term)
    search_bar.send_keys(Keys.RETURN)


def page_calculate(driver):
    total_num_of_pic = int(float("".join(re.findall('([0-9]*?)', driver.find_element_by_xpath(
        '/html/body/div[1]/div[2]/div[2]/div/div[1]/div[1]/div[2]/span[1]').text))))
    total_num_of_page = round_dec(total_num_of_pic / 60)
    return total_num_of_page


def round_dec(num):
    rounded = int(num) if round(num) == num else int(num) + 1
    return rounded


def find_pic(driver, search_term, user_num_pic, user_num_likes):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                             'Chrome/93.0.4577.82 Safari/537.36 Edg/93.0.961.52'}

    loading(driver)
    time.sleep(1)
    picture_urls = []
    total_num_of_page = page_calculate(driver)
    print(type(total_num_of_page), total_num_of_page)
    page_counter = 1

    while page_counter <= total_num_of_page and len(picture_urls) < user_num_pic :
        driver.execute_script(f"window.open('https://www.pixiv.net/en/tags/{search_term}/artworks?p={page_counter}&s_mode=s_tag');")
        loading(driver)
        page_counter += 1
        pic_counter = 1
        while pic_counter < 61 and len(picture_urls) < user_num_pic:
            loading(driver)
            pic = driver.find_element_by_xpath(
                f'//*[@id="root"]/div[2]/div[2]/div/div[4]/div/section/div[2]/ul/li[{pic_counter}]/div/div[1]/div/a')
            pic_counter += 1
            pic_url = pic.get_attribute("href")  # Get the artwork's link

            pic_page = requests.get(pic_url, headers=headers).text  # Get into artwork's page and obtain the html text from the artwork's link
            pic_num_likes = re.findall('"likeCount":([0-9]+),', pic_page)  # Obtain the number of likes
            pic_num_likes = int("".join(pic_num_likes))  # Convert into int form
            if pic_num_likes >= user_num_likes:
                picture_urls.append(pic_url)
            print(len(picture_urls))

    print(picture_urls)
    return picture_urls


def create_folder():
    folder_name = input("\nEnter folder name: ")
    path = f'D://Pixiv//{folder_name}'
    if not os.path.exists(path):
        os.makedirs(path)
        print(f"{folder_name} folder created.")
    else:
        print(f"{folder_name} folder already exists.")


def download(links, search_term, user_num_likes):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                             'Chrome/93.0.4577.82 Safari/537.36 Edg/93.0.961.52'}
    for url in links:
        pic_page = requests.get(url, headers=headers).text
        pic_num_likes = re.findall('"likeCount":([0-9]+),', pic_page)  # Obtain the number of likes
        pic_num_likes = int("".join(pic_num_likes))  # Convert into int form

        if pic_num_likes >= user_num_likes:
            download_link = re.findall('"original":"(.*?)"', pic_page)  # Obtain the download link
            download_link = "".join(download_link)  # Convert into str form

            opener = urllib.request.build_opener()
            opener.addheaders = [('Referer', url)]
            urllib.request.install_opener(opener)
            print(f"Link: {url}")

            file_name = f'{url.split("/")[-1]}.jpg'
            print(f"File name: {file_name}")

            time.sleep(3)  # Set timer to avoid getting ban
            requests.DEFAULT_RETRIES = 100
            s = requests.session()
            s.keep_alive = False

            """Avoid error from urllib"""
            socket.setdefaulttimeout(5)
            try:
                urllib.request.urlretrieve(download_link, (f"D://Pixiv//{search_term}//" + str(file_name)))  # Download picture into folder
                print(f"{file_name} downloaded.\n")
            except socket.timeout:
                counter = 1
                while counter <= 3:
                    try:
                        urllib.request.urlretrieve(download_link, (f"D://Pixiv//{search_term}//" + str(file_name)))  # Download picture into folder
                        print(f"{file_name} downloaded.\n")
                        break
                    except socket.timeout:
                        error_info = f"Retrying to download for {counter} time" if counter == 1 else f"Retrying to download for {counter} times"
                        print(error_info)
                        counter += 1
                print(f"{file_name} failed to download.\n")
        else:
            continue


def main():
    search_infos = search_info()
    create_folder()

    driver_path = "C:\Program Files (x86)\chromedriver.exe"
    browser = webdriver.Chrome(driver_path)
    website = "https://www.pixiv.net/"
    browser.get(website)
    acc_info = user_info()
    login_page(browser, acc_info)
    search(browser, search_infos[0])
    pic_links = find_pic(browser, search_infos[0], search_infos[1], search_infos[2])
    browser.quit()
    download(pic_links, search_infos[0], search_infos[1])

if __name__ == "__main__":
    main()
