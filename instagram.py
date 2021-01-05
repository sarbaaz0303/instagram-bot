from utils import *
from typing import *

import os
import time
import json
import random
import shutil
import requests
from functools import partial
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from multiprocessing.dummy import Pool
from concurrent.futures import ThreadPoolExecutor


Image = NewType('Image', str)
Video = NewType('Video', str)
Link = NewType('Link', str)
AnyPath = NewType('AnyPath', os.PathLike[str])
Function = NewType('Function', Any)


class Instagram:
    MAX_WORKERS: int = 6
    N_PROCESSES: int = 6

    BASE_URL: str = "https://www.instagram.com/"
    BASE_PATH: AnyPath = "./Instagram"

    """initialize driver, set position and creates session"""

    def __init__(self, username: str, password: str) -> None:
        self.username = username
        self.password = password
        self.http_base = requests.Session()
        self.chrome_options = Options().add_argument(
            '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36')
        self.driver = webdriver.Chrome(
            r"./chrome-driver-v87/chromedriver.exe", options=self.chrome_options)

        self.driver.set_window_position(330, 30)
        self.driver.set_window_size(750, 800)

        self.data_href: List = []
        self.data_users: List = []
        self.images: List = []
        self.videos: List = []

    '''entry point'''

    def __enter__(self):
        return self

    '''exit the session and close the browser '''

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.http_base.close()
        self.driver.quit()

    '''exit the session and close the browser '''

    def exit(self):
        self.http_base.close()
        self.driver.quit()

    '''clear data'''

    def clean(self) -> None:
        self.data_href = []
        self.data_users = []
        self.images = []
        self.videos = []

    """login to instagram using username and password setting cookies and disabling notifications"""

    def login(self) -> None:
        driver = self.driver

        # login to instagram
        driver.get(self.BASE_URL)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "loginForm")))

        driver.find_element_by_xpath(
            '//input[@name="username"]').send_keys(self.username)
        driver.find_element_by_xpath(
            '//input[@name="password"]').send_keys(self.password)
        driver.find_element_by_id("loginForm").submit()

        # invalid credentials
        try:
            WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.ID, "slfErrorAlert")))
            raise ValueError("Invalid Credentials")
        except TimeoutException:
            pass

        # don't save notification
        try:
            WebDriverWait(driver, 5).until(
                EC.presence_of_element_located(
                    (By.XPATH, '//button[text()="Not Now"]'))
            ).click()
        except TimeoutException:
            pass

        # close notification
        try:
            WebDriverWait(driver, 5).until(
                EC.presence_of_element_located(
                    (By.XPATH, '//button[text()="Not Now"]'))
            ).click()
        except TimeoutException:
            pass

        # set cookies
        cookies = {
            cookie["name"]: cookie["value"] for cookie in self.driver.get_cookies()
        }

        self.http_base.cookies.update(cookies)

        # create base folder
        create_folder(self.BASE_PATH)

        with open(f'{self.BASE_PATH}/cookies.json', 'w') as file:
            file.write(json.dumps(cookies))

    """scroll down window; break when num is reached"""

    def scroll_down(self, scroll: int, function: Function) -> None:
        driver = self.driver

        i, last_height = (1, 0)
        while True:
            current_height = driver.execute_script(
                "window.scrollTo(0,document.body.scrollHeight); return document.body.scrollHeight"
            )
            time.sleep(3)
            function()
            if i == scroll:
                break
            i += 1
            if last_height == current_height:
                break
            last_height = current_height

    '''scroll down popup; break when num is reached'''

    def scroll_popup(self, scroll: int, function: Function) -> None:
        driver = self.driver
        scroll_box = driver.find_element_by_class_name('isgrP')
        i, last_height = (1, 0)
        while True:
            current_height = driver.execute_script(
                'arguments[0].scrollTo(0, arguments[0].scrollHeight);return arguments[0].scrollHeight;', scroll_box
            )
            time.sleep(3)
            if i == scroll:
                break
            i += 1
            if last_height == current_height:
                break
            last_height = current_height
        function(scroll_box)

    '''scroll down popup; until action is done'''

    def scroll_popup_action(self, num: int, function: Function) -> None:
        driver = self.driver
        scroll_box = driver.find_element_by_class_name('isgrP')
        i, last_height = (1, 0)
        while True:
            current_height = driver.execute_script(
                'arguments[0].scrollTo(0, arguments[0].scrollHeight);return arguments[0].scrollHeight;', scroll_box
            )
            time.sleep(3)
            i = function(scroll_box, i, num)
            if i == num:
                break
            if last_height == current_height:
                break
            last_height = current_height

    '''likes an image or a video per 5 seconds'''

    def like_post(self) -> None:
        try:
            get_post = self.driver.find_element_by_class_name('QBXjJ')
            if get_post.find_elements_by_class_name('FFVAD') or get_post.find_elements_by_class_name('tWeCl'):
                like_post = get_post.find_element_by_css_selector(
                    '.ltpMr.Slqrh')
                if like_post.find_element_by_class_name('_8-yf5').get_attribute('aria-label') == "Like":
                    like_post.find_element_by_class_name('wpO6b ').click()
                else:
                    print('[*] Post already liked'.title())
        except:
            print('[!] something went wrong Like'.title())
        finally:
            time.sleep(5)

    '''follow user in every 6 minutes'''

    def follow_user(self) -> None:
        try:
            follow_user = self.driver.find_element_by_css_selector(
                '.sqdOP.yWX7d.y3zKF')
            if follow_user.text == "Follow":
                follow_user.click()
            else:
                print('[*] user already followed'.title())
        except:
            print('[!] something went wrong Follow'.title())
        finally:
            time.sleep(30)
            # time.sleep(random.randint(350, 365))

    '''unfollow user every 30-45 seconds'''

    def unfollow_user(self) -> None:
        try:
            unfollow_user = self.driver.find_element_by_css_selector(
                '.sqdOP.L3NKy._8A5w5')
            if unfollow_user.text == "Following":
                unfollow_user.click()
                WebDriverWait(self.driver, 2).until(
                    EC.presence_of_element_located(
                        (By.CSS_SELECTOR, '.aOOlW.-Cab_'))
                ).click()
            else:
                print('[*] user already unfollowed'.title())
        except:
            print('[!] something went wrong Unfollow'.title())
        finally:
            time.sleep(random.randint(30, 40))

    '''get images and videos from link'''

    def fetch_url(self, url: str) -> Link:
        data = self.http_base.get(url, params={'__a': 1}).json()[
            'graphql']['shortcode_media']
        if data['__typename'] == 'GraphImage':
            image_url = data['display_url']
            self.images.append(image_url)
        elif data['__typename'] == 'GraphVideo':
            video_url = data['video_url']
            self.videos.append(video_url)
        elif data['__typename'] == 'GraphSidecar':
            for sidecar in data['edge_sidecar_to_children']['edges']:
                if sidecar['node']['__typename'] == 'GraphImage':
                    image_url = sidecar['node']['display_url']
                    self.images.append(image_url)
                elif sidecar['node']['__typename'] == 'GraphVideo':
                    video_url = sidecar['node']['video_url']
                    self.videos.append(video_url)
        else:
            print(f"Warning {url}: has unknown type of {data['__typename']}")

    '''downloads image'''

    def download_image(self, image_link: tuple, path: AnyPath, image_name) -> Image:
        num, image = image_link
        with open(f'{path}/{image_name}_{num}.jpg', 'wb') as file:
            res = self.http_base.get(image, stream=True)
            shutil.copyfileobj(res.raw, file)

    '''downloads video'''

    def download_video(self, video_link: tuple, path: AnyPath, video_name) -> Video:
        num, video = video_link
        with open(f'{path}/{video_name}_{num}.mp4', 'wb') as file:
            res = self.http_base.get(video, stream=True)
            shutil.copyfileobj(res.raw, file)

    '''using thread the link is fetched by workers in batch and also processed in batch'''

    def fast_download(self, links: list, path: AnyPath, name=None) -> Any:

        if name:
            image_name = name
            video_name = name
        else:
            image_name = 'image'
            video_name = 'video'

        print('[+] Ready for videos - images'.title())
        print(f'[*] Extracting {len(links)} posts , please wait...'.title())

        with ThreadPoolExecutor(max_workers=self.MAX_WORKERS) as executor:
            for link in links:
                executor.submit(self.fetch_url, link)

        print('[*] ready for saving images and videos!'.title())

        images_data = enumerate(self.images)
        videos_data = enumerate(self.videos)

        pool = Pool(self.N_PROCESSES)
        pool.map(partial(self.download_image, path=path,
                         image_name=image_name), images_data)
        pool.map(partial(self.download_video, path=path,
                         video_name=video_name), videos_data)

        print('[+] Done')
        print('== '*20)

    '''get basic profile data of a user'''

    def basic_profile_data_user(self, username: str) -> dict:
        search = self.http_base.get(
            f'{self.BASE_URL}{username}/', params={'__a': 1})
        search.raise_for_status()

        data = search.json()['graphql']['user']
        username = data['username']
        full_name = data['full_name']
        profile_pic_url_hd = data['profile_pic_url_hd']
        post_count = data['edge_owner_to_timeline_media']['count']
        is_private = data['is_private']
        followed_by_viewer = data['followed_by_viewer']
        follows_viewer = data['follows_viewer']
        edge_follow = data['edge_follow']['count']
        edge_followed_by = data['edge_followed_by']['count']

        return {
            'username': username,
            'full_name': full_name,
            'profile_pic_url': profile_pic_url_hd,
            'post_count': post_count,
            'following': edge_follow,
            'followers': edge_followed_by,
            'followed_by_viewer': followed_by_viewer,
            'is_following': follows_viewer,
            'is_private': is_private
        }

    '''get username of a profile from data'''

    def get_username_and_append_data(self, data: Any) -> None:
        if self.BASE_URL in data:
            username = self.http_base.get(f'{data}', params={'__a': 1}).json()[
                'graphql']['shortcode_media']['edge_media_to_parent_comment']['edges'][0]['node']['owner']['username']
        else:
            username = data
        self.data_users.append(self.basic_profile_data_user(username))

    '''is account private'''

    def is_private(self, data: dict) -> None:
        if username != self.username:
            if data['is_private'] and not data['followed_by_viewer']:
                raise Exception('Account is private')

    '''remove duplicate json'''

    def remove_dublicate_data(self) -> None:
        data_username = [data['username'] for data in self.data_users]
        self.data_users = [data for num, data in enumerate(
            self.data_users) if data['username'] not in data_username[num+1:]]

    '''write json data to the file'''

    def write_json(self, links: list, path: str = './json_data.json') -> None:
        print(
            f'[*] Extracting {len(links)} tags data and writing, please wait...'.title())
        with ThreadPoolExecutor(max_workers=self.MAX_WORKERS) as executor:
            for data in links:
                executor.submit(self.get_username_and_append_data, data)
        with open(f'{path}', 'a+') as file:
            if file.tell() != 0:
                file.seek(0)
                self.data_users += json.load(file)
                file.seek(0)
                file.truncate()
                self.remove_dublicate_data()
            file.write(json.dumps(self.data_users))
        print('[+] Done')
        print('== '*20)

    '''write simple json'''

    def write_simple_json(self, path):
        print(f'[*] writing data, please wait...'.title())
        with open(f'{path}', 'a+') as file:
            if file.tell() != 0:
                file.seek(0)
                self.data_users += json.load(file)
                file.seek(0)
                file.truncate()
                self.remove_dublicate_data()
            file.write(json.dumps(self.data_users))
        print('[+] Done')
        print('== '*20)

    '''click followers to open pop up'''

    def open_followers_popup(self, username: str) -> None:
        try:
            WebDriverWait(self.driver, 5).until(EC.presence_of_element_located(
                (By.XPATH, f'//a[@href="/{username}/followers/"]'))
            ).click()
            time.sleep(2)
        except TimeoutException:
            raise('Element Not found')

    '''click following to open pop up'''

    def open_following_popup(self, username: str) -> None:
        try:
            WebDriverWait(self.driver, 5).until(EC.presence_of_element_located(
                (By.XPATH, f'//a[@href="/{username}/following/"]'))
            ).click()
            time.sleep(2)
        except TimeoutException:
            raise('Element Not found')

    '''close followers/following pop up'''

    def close_popup(self) -> None:
        try:
            WebDriverWait(self.driver, 5).until(EC.presence_of_all_elements_located(
                (By.CLASS_NAME, 'wpO6b'))
            )[1].click()
            time.sleep(2)
        except TimeoutException:
            raise('Element Not found')

    '''scroll function posts links'''

    def posts_links(self, test: str) -> None:
        post_section = self.driver.find_element_by_class_name('_2z6nI')
        post_links = post_section.find_elements_by_xpath('//a[@href]')
        [self.data_href.append(data.get_attribute('href')) for data in post_links if test in data.get_attribute(
            'href') and data.get_attribute('href') not in self.data_href]

    '''scroll function tag links'''

    def tag_links(self):
        tag_section = self.driver.find_element_by_class_name('KC1QD')
        tag_links = tag_section.find_elements_by_xpath('//a[@href]')
        [self.data_href.append(data.get_attribute('href')) for data in tag_links if '.com/p/' in data.get_attribute(
            'href') and data.get_attribute('href') not in self.data_href]

    '''scroll popup function get names'''

    def util_names(self, scroll_box: Function) -> None:
        link_tag = scroll_box.find_elements_by_class_name('FPmhX')
        [self.data_href.append(href.text)
         for href in link_tag if href.text not in self.data_href]

    '''scroll popup function get names of follow'''

    def util_follow_names(self, scroll_box: Function, i, num: int) -> int:
        li_tags = scroll_box.find_elements_by_class_name('wo9IH')
        for li in li_tags:
            if li.find_elements_by_css_selector('.sqdOP.L3NKy.y3zKF'):
                self.data_href.append(
                    li.find_element_by_class_name('FPmhX').text)
                if i == num:
                    break
                i += 1
        return i

    '''scroll popup function follow of follow followers'''

    def util_follow_followers(self, scroll_box: Function, i, num: int) -> int:
        li_tags = scroll_box.find_elements_by_class_name('wo9IH')
        for li in li_tags:
            if li.find_elements_by_css_selector('.sqdOP.L3NKy.y3zKF'):
                li.find_element_by_css_selector('.sqdOP.L3NKy.y3zKF').click()
                self.data_href.append(
                    li.find_element_by_class_name('FPmhX').text)
                if i == num:
                    break
                i += 1
                time.sleep(random.randint(30, 60))
        return i

    '''scroll popup function unfollow following'''

    def util_unfollow_following(self, scroll_box: Function, i, num: int) -> int:
        li_tags = scroll_box.find_elements_by_class_name('wo9IH')
        for li in li_tags:
            if li.find_elements_by_css_selector('.sqdOP.L3NKy._8A5w5'):
                li.find_element_by_css_selector('.sqdOP.L3NKy._8A5w5').click()
                time.sleep(5)
                try:
                    WebDriverWait(self.driver, 5).until(EC.presence_of_element_located(
                        (By.CSS_SELECTOR, '.aOOlW.-Cab_'))
                    ).click()
                except TimeoutException:
                    print('[!] there was a problem in unfollowing'.title())
                self.data_href.append(
                    li.find_element_by_class_name('FPmhX').text)
                if i == num:
                    break
                i += 1
                time.sleep(random.randint(20, 40))
        return i

    '''scroll popup function unfollow non followers'''

    def util_unfollow_non_followers(self, scroll_box: Function, i, num: int, non_followers) -> int:
        li_tags = scroll_box.find_elements_by_class_name('wo9IH')
        for li in li_tags:
            if li.find_element_by_class_name('FPmhX').text in non_followers:
                li.find_element_by_css_selector('.sqdOP.L3NKy._8A5w5').click()
                time.sleep(5)
                try:
                    WebDriverWait(self.driver, 5).until(EC.presence_of_element_located(
                        (By.CSS_SELECTOR, '.aOOlW.-Cab_'))
                    ).click()
                except TimeoutException:
                    print('[!] there was a problem in unfollowing'.title())
                self.data_href.append(
                    li.find_element_by_class_name('FPmhX').text)
                if i == num:
                    break
                i += 1
                # time.sleep(random.randint(20, 40))
        return i

    '''MAIN FUNCTIONS'''

    '''scrape a user profile and like, download its data'''

    def profile_scrape(self, profile_name: str, post_no: Any = 50, like: bool = False, download: bool = False, scrape: str = 'posts') -> Any:
        driver = self.driver

        data = self.basic_profile_data_user(profile_name)
        self.is_private(data)

        post_no = str_all_to_num(post_no, data['post_count'], 300)

        path = f'{self.BASE_PATH}/{profile_name}'
        create_folder(path)

        test: str = '.com/p/'
        reels = ['reels', 'reel']
        channel = ['channel', 'igtv', 'tv']
        tagged = ['tagged', 'tag']

        if scrape in reels:
            driver.get(f'{self.BASE_URL}{profile_name}/reels/')
            path = f'{self.BASE_PATH}/{profile_name}/reels'
            create_folder(path)
            test = '.com/reel/'
        elif scrape in channel:
            driver.get(f'{self.BASE_URL}{profile_name}/channel/')
            path = f'{self.BASE_PATH}/{profile_name}/channel'
            create_folder(path)
            test = '.com/tv/'
        elif scrape in tagged:
            driver.get(f'{self.BASE_URL}{profile_name}/tagged/')
            path = f'{self.BASE_PATH}/{profile_name}/tagged'
            create_folder(path)
        else:
            driver.get(f'{self.BASE_URL}{profile_name}')
            path = f'{self.BASE_PATH}/{profile_name}/posts'
            create_folder(path)

        time.sleep(2)

        if scrape in (reels + channel):
            scroll = num_to_scroll(post_no, 24, 12)
        else:
            scroll = num_to_scroll(post_no, 36, 12)

        self.scroll_down(scroll, partial(self.posts_links, test=test))

        links = self.data_href[:post_no]
        print(len(self.data_href), len(links), 'profile_scrape')

        if like:
            for link in links:
                driver.get(link)
                time.sleep(2)
                self.like_post()
            print('[+] Done')

        if download:
            self.fast_download(links, path, profile_name)

        self.clean()

    '''explore tag'''

    def explore_tags(self, hashtag: str, posts_no: Any = 50, like: bool = False, follow: bool = False, download: bool = False, write: bool = False) -> Any:
        driver = self.driver
        driver.get(f'{self.BASE_URL}explore/tags/{hashtag}/')
        time.sleep(2)

        scroll = num_to_scroll(posts_no, 45, 12)
        self.scroll_down(scroll, self.tag_links)

        links = self.data_href[:posts_no]
        print(len(links), 'explore_tags')

        path = f'{self.BASE_PATH}/#{hashtag}'

        if download or write:
            create_folder(path)

        if write:
            self.write_json(links, path=f'{path}/{hashtag}.json')

        if download:
            path = f'{path}/posts'
            create_folder(path)
            self.fast_download(links, path, hashtag)

        if like or follow:
            if follow:
                print(
                    '[!] due to instagram policy you can only follow 10 users per hour'.title())

            for link in links:
                driver.get(link)
                time.sleep(3)

                if like and follow:
                    self.follow_user()
                    self.like_post()
                elif like:
                    self.like_post()
                elif follow:
                    self.follow_user()
            print('[+] Done')
            print('== '*20)

        self.clean()

    '''get followers following name'''

    def get_names(self, username, num: Any, write: bool, names: str, temp: bool = False) -> Any:
        driver = self.driver
        if not username:
            username = self.username

        data = self.basic_profile_data_user(username)
        self.is_private(data)

        if not(driver.current_url == f'{self.BASE_URL}{username}/'):
            driver.get(f'{self.BASE_URL}{username}/')
            time.sleep(3)

        path = f'{self.BASE_PATH}/{username}'
        create_folder(path)

        if temp:
            path = f'{path}/temp'
            create_folder(path)

        num = str_all_to_num(num, data[names], 500)

        if names == 'followers':
            self.open_followers_popup(username)
        if names == 'following':
            self.open_following_popup(username)
        scroll = num_to_scroll(num, 24, 12)
        self.scroll_popup(scroll, self.util_names)
        self.close_popup()
        self.data_href = self.data_href[:num]
        print(len(self.data_href), num, 'get_names')

        if write:
            self.write_json(self.data_href, path=f'{path}/{names}.json')

    '''action on name'''

    def get_action(self, username, num: Any, write: bool, names: str, function: Function, file: str = None, temp: bool = False) -> Any:
        driver = self.driver
        if not username:
            username = self.username

        data = self.basic_profile_data_user(username)
        self.is_private(data)

        if not(driver.current_url == f'{self.BASE_URL}{username}/'):
            driver.get(f'{self.BASE_URL}{username}/')
            time.sleep(3)

        path = f'{self.BASE_PATH}/{username}'
        create_folder(path)

        if temp:
            path = f'{path}/temp'
            create_folder(path)

        if not file:
            file = names

        num = str_all_to_num(num, data[names], 500)

        if names == 'followers':
            self.open_followers_popup(username)
        if names == 'following':
            self.open_following_popup(username)

        self.scroll_popup_action(num, function)

        self.close_popup()
        self.data_href = self.data_href[:num]
        print(len(self.data_href), num, 'get_action')

        if write:
            self.write_json(self.data_href, path=f'{path}/{file}.json')

    '''get followers data from a username'''

    def get_followers(self, username=None, num: Any = 'all', write: bool = False) -> Any:
        self.get_names(username, num, write, 'followers')
        self.clean()

    '''get following data from a username'''

    def get_following(self, username=None, num: Any = 'all', write: bool = False) -> Any:
        self.get_names(username, num, write, 'following')
        self.clean()

    '''get non followers i.e user follow but doesnt get a follow back'''

    def get_non_followers(self, username=None, num: Any = 'all', write: bool = False) -> Any:
        self.get_names(username, num, write, 'followers', temp=True)
        self.clean()

        self.get_names(username, num, write, 'following', temp=True)
        self.clean()

        if not username:
            username = self.username

        path = f'{self.BASE_PATH}/{username}'

        with open(f'{path}/temp/followers.json', 'r') as file:
            get_followers = json.load(file)

        with open(f'{path}/temp/following.json', 'r') as file:
            get_following = json.load(file)

        self.data_users = [
            following for following in get_following if following not in get_followers]
        print(len(self.data_users), len(get_followers),
              len(get_following), 'get_non_followers')

        if write:
            self.write_simple_json(f'{path}/non-followers.json')

        if os.path.isdir(f'{path}/temp'):
            os.remove(f'{path}/temp/followers.json')
            os.remove(f'{path}/temp/following.json')
            os.rmdir(f'{path}/temp')
        self.clean()

    '''followers that user is not following'''

    def get_followers_not_following(self, username=None, num: Any = 'all', write: bool = False) -> Any:
        self.get_action(username, num, write, 'followers',
                        file='followers_not_following', function=self.util_follow_names)
        self.clean()

    '''follow followers'''

    def follow_followers(self, username=None, num: Any = 'all', write: bool = False) -> Any:
        self.get_action(username, num, write, 'followers',
                        file='follow_followers', function=self.util_follow_followers)
        self.clean()

    '''follow following'''

    def follow_following(self, username=None, num: Any = 'all', write: bool = False) -> Any:
        self.get_action(username, num, write, 'following',
                        file='follow_following', function=self.util_follow_followers)
        self.clean()

    '''unfollow following'''

    def unfollow_following(self, username=None, num: Any = 'all', write: bool = False) -> Any:
        self.get_action(username, num, write, 'following',
                        file='unfollow_following', function=self.util_unfollow_following)
        self.clean()

    '''unfollow followers'''

    def unfollow_followers(self, username=None, num: Any = 'all', write: bool = False) -> Any:
        self.get_action(username, num, write, 'followers',
                        file='unfollow_followers', function=self.util_unfollow_following)
        self.clean()

    '''unfollow not follow back'''

    def unfollow_non_followers(self, username=None, num: Any = 'all', write: bool = False) -> Any:
        self.get_names(username, num, write, 'followers', temp=True)
        self.clean()

        self.get_names(username, num, write, 'following', temp=True)
        self.clean()

        if not username:
            username = self.username

        path = f'{self.BASE_PATH}/{username}'

        with open(f'{path}/temp/followers.json', 'r') as file:
            get_followers = json.load(file)

        with open(f'{path}/temp/following.json', 'r') as file:
            get_following = json.load(file)

        self.data_users = [
            following for following in get_following if following not in get_followers]
        print(len(self.data_users), len(get_followers),
              len(get_following), 'unfollow_non_followers')

        self.write_simple_json(f'{path}/temp/non-followers.json')
        self.clean()

        with open(f'{path}/temp/non-followers.json', 'r') as file:
            non_followers = json.load(file)

        non_followers = [non['username'] for non in non_followers]

        self.get_action(username, num, write, 'following', file='unfollow_non_followers', function=partial(
            self.util_unfollow_non_followers, non_followers=non_followers))

        if os.path.isdir(f'{path}/temp'):
            os.remove(f'{path}/temp/followers.json')
            os.remove(f'{path}/temp/following.json')
            os.remove(f'{path}/temp/non-followers.json')
            os.rmdir(f'{path}/temp')
        self.clean()

    '''download from link'''

    def download(self, link: str) -> Any:
        path = f'{self.BASE_PATH}/downloads'
        create_folder(path)

        try:
            with open(f'{self.BASE_PATH}/cookies.json', 'r') as file:
                cookies = json.load(file)

            self.http_base.cookies.update(cookies)
            username = self.http_base.get(f'{link}', params={'__a': 1}).json()[
                'graphql']['shortcode_media']['edge_media_to_parent_comment']['edges'][0]['node']['owner']['username']

            self.fetch_url(link)
            while self.images:
                filename = datetime.strftime(
                    datetime.now(), '%Y-%m-%d-%H-%M-%S')
                image = self.images.pop()
                with open(f'{path}/{username}-{filename}.jpg', 'wb') as file:
                    res = self.http_base.get(image, stream=True)
                    shutil.copyfileobj(res.raw, file)
                time.sleep(1)
            while self.videos:
                filename = datetime.strftime(
                    datetime.now(), '%Y-%m-%d-%H-%M-%S')
                video = self.videos.pop()
                with open(f'{path}/{username}-{filename}.mp4', 'wb') as file:
                    res = self.http_base.get(video, stream=True)
                    shutil.copyfileobj(res.raw, file)
                time.sleep(1)
        except:
            print(
                '[!] oops! it look like cookies have expired. please login to instagram'.title())
        finally:
            self.clean()

    """DM everyone in the list"""

    def direct_message(self, message: List = [], targets: list = [], target_path: AnyPath = '', num='all') -> Any:
        driver = self.driver
        driver.get(f"{self.BASE_URL}direct/inbox/")
        targets_user: list = []
        try:
            if target_path:
                with open(f'{target_path}', 'r') as file:
                    target = json.load(file)
                [targets_user.append(username['username']) for username in target if username['username'] not in targets_user]

            if targets:
                targets_user += targets

            if num == 'all':
                num = len(targets_user)
            print(f'Sending Dm\'s to {num} people')

        except Exception:
            print('File Not Found')
        try:
            for name in targets_user[num]:
                try:
                    WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located(
                            (By.CSS_SELECTOR, ".wpO6b.ZQScA"))
                    ).click()
                    new_dm = WebDriverWait(driver, 5).until(
                        EC.presence_of_element_located(
                            (By.CLASS_NAME, "_1XyCr"))
                    )
                    input_tag = WebDriverWait(new_dm, 5).until(
                        EC.presence_of_element_located(
                            (By.CLASS_NAME, "j_2Hd"))
                    )
                    input_tag.click()
                    input_tag.send_keys(name)
                    time.sleep(2)
                    WebDriverWait(new_dm, 5).until(
                        EC.presence_of_element_located(
                            (By.CLASS_NAME, "dCJp8"))
                    ).click()
                    WebDriverWait(new_dm, 5).until(
                        EC.presence_of_element_located(
                            (By.CSS_SELECTOR, ".sqdOP.yWX7d.y3zKF.cB_4K")
                        )
                    ).click()
                    time.sleep(3)
                    textarea = driver.find_element_by_tag_name('textarea')
                    textarea.click()
                    textarea.send_keys(random.choice(message))
                    time.sleep(2)
                    WebDriverWait(driver, 5).until(
                        EC.presence_of_element_located(
                            (By.XPATH, '//button[contains(text(), "Send")]')
                        )
                    ).click()
                    time.sleep(5)
                except:
                    print(f"There was a problem sending message to {name}")
        except Exception:
            print("Unknown Error")


if __name__ == "__main__":
    username = ""
    password = ""

    insta_bot = Instagram(username, password)
    # insta_bot.login()
    # insta_bot.profile_scrape()
    # insta_bot.explore_tags()
    # insta_bot.get_followers()
    # insta_bot.get_following()
    # insta_bot.get_non_followers()
    # insta_bot.get_followers_not_following()
    # insta_bot.follow_followers()
    # insta_bot.follow_following()
    # insta_bot.unfollow_followers()
    # insta_bot.unfollow_following()
    # insta_bot.unfollow_non_followers()
    # insta_bot.download()
    # insta_bot.direct_message()
    insta_bot.exit()
