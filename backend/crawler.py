import re
import time
import pandas as pd
import urllib.request
from bs4 import BeautifulSoup
import json
import yaml
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os
from typing import List, Union, Callable
import logging  # 추가: 로깅 모듈 임포트
from selenium.webdriver.firefox.service import Service as FirefoxService

class Crawler:
    def __init__(self) -> None:
        # config.yaml 파일에서 기본 설정 읽기
        config_path = os.path.join(os.path.dirname(__file__), 'config.yaml')  # 변경: config.yaml 경로 수정
        with open(config_path, 'r', encoding='utf-8') as file:
            config = yaml.safe_load(file)

        self.default_queries: List[str] = config['query']  # 기존 Union[str, List[str]]에서 List[str]로 변경
        self.max_posts: int = config['max_posts']
        self.client_id: str = 'yxVAM1FtMsLm6a3peK_0'
        self.client_secret: str = '_YEIleXvQ9'
        self.driver = self.create_driver()  # 브라우저 인스턴스 생성
        logging.info("브라우저 인스턴스가 생성되었습니다.")

    # def __del__(self):
    #     self.driver.quit()  # 클래스가 소멸될 때 브라우저 닫기

    def create_driver(self) -> webdriver.Firefox:
        options = webdriver.FirefoxOptions()
        options.add_argument("--headless")  # headless 모드 추가
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")  # 추가: GPU 비활성화
        # options.add_argument("--remote-debugging-port=9222")  # 제거: 지원되지 않는 인자

        # GeckoDriver의 경로를 환경 변수에서 가져오도록 수정
        geckodriver_path = os.environ.get('GECKODRIVER', '/usr/local/bin/geckodriver')
        try:
            driver = webdriver.Firefox(service=FirefoxService(geckodriver_path), options=options)
            logging.info("Firefox WebDriver가 정상적으로 생성되었습니다.")
            return driver
        except Exception as e:
            logging.error(f"Firefox WebDriver 생성 실패: {e}")
            raise e

    def fetch_urls_from_api(self, query: str, max_posts: int = None) -> List[str]:
        print(f"\nAPI를 사용해 '{query}' 관련 게시물 URL을 수집합니다.")
        naver_urls: List[str] = []
        display: int = 10  # 한 번에 가져올 게시물 수
        max_posts = max_posts or self.max_posts

        for start in range(1, max_posts + 1, display):
            url = (f"https://openapi.naver.com/v1/search/blog?query={urllib.parse.quote(query)}&start={start}"
                   f"&display={display}&sort=sim")
            request = urllib.request.Request(url)
            request.add_header("X-Naver-Client-Id", self.client_id)
            request.add_header("X-Naver-Client-Secret", self.client_secret)
            response = urllib.request.urlopen(request)
            if response.getcode() == 200:
                data = json.loads(response.read().decode('utf-8'))['items']
                for row in data:
                    if 'blog.naver' in row['link'] and row['link'] not in naver_urls:
                        naver_urls.append(row['link'])
                    if len(naver_urls) >= max_posts:
                        break
            else:
                print(f"Error fetching data: {response.getcode()}")
            time.sleep(1)  # API 호출 간 대기
        return naver_urls

    def crawl_blog_contents(self, urls: List[str]) -> pd.DataFrame:
        driver = self.create_driver()
        writers, post_dates, titles, contents, tags_list, sympathies, ad_images_list, ad_status = [], [], [], [], [], [], [], []

        for url in urls:
            driver.get(url)
            time.sleep(2)

            try:
                # mainFrame iframe 대기 및 전환
                iframe = WebDriverWait(driver, 20).until(
                    EC.presence_of_element_located((By.ID, "mainFrame"))
                )
                driver.switch_to.frame(iframe)

                # 페이지 소스 가져오기
                html = BeautifulSoup(driver.page_source, "html.parser")

                # 제목 크롤링
                title_element = html.select_one("div.se-module.se-module-text.se-title-text > p > span")
                titles.append(title_element.text.strip() if title_element else "unknown")

                # 본문 내용 크롤링
                main_content = html.select("div.se-main-container > div")

                # 본문에서 동영상 콘텐츠 제거
                for video_div in html.select("div.se-module.se-module-video.__se-component"):
                    video_div.decompose()

                # 본문에서 __se-hash-tag 태그 제거
                for hash_tag_span in html.select("span.__se-hash-tag"):
                    hash_tag_span.decompose()

                # 텍스트만 추출하여 content에 저장
                content = ' '.join(div.get_text(strip=True) for div in main_content)
                contents.append(content)

                # 게시물 작성 날짜
                post_date_element = html.select_one("span.se_publishDate")
                post_dates.append(post_date_element.text.strip() if post_date_element else "unknown")

                # 작성자 정보
                writer_element = html.select_one("span.nick > a.link")
                writers.append(writer_element.text.strip() if writer_element else "unknown")

                # 태그 크롤링
                tag_elements = html.select("div.wrap_tag span.ell")
                tags = [tag.text.strip() for tag in tag_elements]
                tags_list.append(", ".join(tags))

                # 공감 수 크롤링
                sympathy_element = html.select_one("span.u_likeit_list_btn._button.btn_sympathy.pcol2.off > em.u_cnt._count")
                sympathy_text = sympathy_element.text.strip() if sympathy_element else "0"
                try:
                    sympathy = int(sympathy_text)
                except ValueError:
                    sympathy = 0
                sympathies.append(sympathy)

                # 광고성 이미지 크롤링
                ad_images = html.select("img[src*='firebasestorage']")
                dinnerqueen_ad_images = html.select("img[src*='dinnerqueen']")
                revu_ad_images = html.select("img[src*='revu']")
                cloudfront_ad_images = html.select("img[src*='cloudfront']")

                # 광고 이미지 URL 리스트 생성
                if ad_images or dinnerqueen_ad_images or revu_ad_images or cloudfront_ad_images:
                    ad_image_urls = [img.get("src") for img in ad_images if img.get("src")]
                    dinnerqueen_ad_image_urls = [img.get("src") for img in dinnerqueen_ad_images if img.get("src")]
                    revu_ad_image_urls = [img.get("src") for img in revu_ad_images if img.get("src")]
                    cloudfront_ad_image_urls = [img.get("src") for img in cloudfront_ad_images if img.get("src")]
                    all_ad_images = ad_image_urls + dinnerqueen_ad_image_urls + revu_ad_image_urls + cloudfront_ad_image_urls

                    ad_images_list.append(", ".join(all_ad_images))
                    ad_status.append("O")  # 광고가 있으면 'O'
                else:
                    ad_images_list.append("")
                    ad_status.append("X")  # 광고가 없으면 'X'

                # 메인 프레임으로 돌아가기
                driver.switch_to.default_content()

            except Exception as e:
                print(f"{url}에서 크롤링 중 오류 발생: {e}")
                titles.append("error")
                contents.append("error")
                post_dates.append("unknown")
                writers.append("unknown")
                tags_list.append("unknown")
                sympathies.append(0)
                ad_images_list.append("")
                ad_status.append("X")

        driver.quit()

        # DataFrame 생성 및 반환
        return pd.DataFrame({
            'writer': writers,
            'date': post_dates,
            'title': titles,
            'content': contents,
            'tags': tags_list,
            'sympathy': sympathies,
            'post_url': urls,
            'ad_images': ad_images_list,
            '광고': ad_status
        })

    def crawl_blog_content(self, url: str) -> dict:
        data = {}
        try:
            self.driver.get(url)
            logging.info(f"URL 접근 중: {url}")
            time.sleep(2)

            # mainFrame iframe 대기 및 전환
            iframe = WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.ID, "mainFrame"))
            )
            self.driver.switch_to.frame(iframe)

            # 페이지 소스 가져오기
            html = BeautifulSoup(self.driver.page_source, "html.parser")

            # 데이터 수집 로직
            # 제목 크롤링
            title_element = html.select_one("div.se-module.se-module-text.se-title-text > p > span")
            title = title_element.text.strip() if title_element else "unknown"

            # 본문 내용 크롤링
            main_content = html.select("div.se-main-container > div")
            for video_div in html.select("div.se-module.se-module-video.__se-component"):
                video_div.decompose()
            for hash_tag_span in html.select("span.__se-hash-tag"):
                hash_tag_span.decompose()
            content = ' '.join(div.get_text(strip=True) for div in main_content)

            # 게시물 작성 날짜
            post_date_element = html.select_one("span.se_publishDate")
            post_date = post_date_element.text.strip() if post_date_element else "unknown"

            # 작성자 정보
            writer_element = html.select_one("span.nick > a.link")
            writer = writer_element.text.strip() if writer_element else "unknown"

            # 태그 크롤링
            tag_elements = html.select("div.wrap_tag span.ell")
            tags = ", ".join([tag.text.strip() for tag in tag_elements])

            # 공감 수 크롤링
            sympathy_element = html.select_one("span.u_likeit_list_btn._button.btn_sympathy.pcol2.off > em.u_cnt._count")
            sympathy_text = sympathy_element.text.strip() if sympathy_element else "0"
            try:
                sympathy = int(sympathy_text)
            except ValueError:
                sympathy = 0

            # 광고성 이미지 크롤링
            ad_images = html.select("img[src*='firebasestorage']")
            dinnerqueen_ad_images = html.select("img[src*='dinnerqueen']")
            revu_ad_images = html.select("img[src*='revu']")
            cloudfront_ad_images = html.select("img[src*='cloudfront']")
            if ad_images or dinnerqueen_ad_images or revu_ad_images or cloudfront_ad_images:
                ad_image_urls = [img.get("src") for img in ad_images if img.get("src")]
                dinnerqueen_ad_image_urls = [img.get("src") for img in dinnerqueen_ad_images if img.get("src")]
                revu_ad_image_urls = [img.get("src") for img in revu_ad_images if img.get("src")]
                cloudfront_ad_image_urls = [img.get("src") for img in cloudfront_ad_images if img.get("src")]
                all_ad_images = ad_image_urls + dinnerqueen_ad_image_urls + revu_ad_image_urls + cloudfront_ad_image_urls
                ad_images_str = ", ".join(all_ad_images)
                ad_status = "O"
            else:
                ad_images_str = ""
                ad_status = "X"

            # 수집한 데이터를 data 딕셔너리에 저장
            data = {
                'writer': writer,
                'date': post_date,
                'title': title,
                'content': content,
                'tags': tags,
                'sympathy': sympathy,
                'post_url': url,
                'ad_images': ad_images_str,
                '광고': ad_status
            }

            logging.info(f"데이터 수집 성공: {url}")

            # 메인 프레임으로 돌아가기
            self.driver.switch_to.default_content()

        except Exception as e:
            logging.error(f"{url}에서 크롤링 중 오류 발생: {e}")
            data = {
                'writer': 'unknown',
                'date': 'unknown',
                'title': 'error',
                'content': 'error',
                'tags': 'unknown',
                'sympathy': 0,
                'post_url': url,
                'ad_images': '',
                '광고': 'X'
            }

        return data

    def crawl_blog_contents_with_callback(self, urls: List[str], callback: Callable[[str], None]) -> pd.DataFrame:
        driver = self.create_driver()
        writers, post_dates, titles, contents, tags_list, sympathies, ad_images_list, ad_status = [], [], [], [], [], [], [], []

        for url in urls:
            driver.get(url)
            time.sleep(2)

            try:
                # mainFrame iframe 대기 및 전환
                iframe = WebDriverWait(driver, 20).until(
                    EC.presence_of_element_located((By.ID, "mainFrame"))
                )
                driver.switch_to.frame(iframe)

                # 페이지 소스 가져오기
                html = BeautifulSoup(driver.page_source, "html.parser")

                # 제목 크롤링
                title_element = html.select_one("div.se-module.se-module-text.se-title-text > p > span")
                titles.append(title_element.text.strip() if title_element else "unknown")

                # 본문 내용 크롤링
                main_content = html.select("div.se-main-container > div")

                # 본문에서 동영상 콘텐츠 제거
                for video_div in html.select("div.se-module.se-module-video.__se-component"):
                    video_div.decompose()

                # 본문에서 __se-hash-tag 태그 제거
                for hash_tag_span in html.select("span.__se-hash-tag"):
                    hash_tag_span.decompose()

                # 텍스트만 추출하여 content에 저장
                content = ' '.join(div.get_text(strip=True) for div in main_content)
                contents.append(content)

                # 실시간으로 크롤링된 콘텐츠 전송
                callback(content)

                # 게시물 작성 날짜
                post_date_element = html.select_one("span.se_publishDate")
                post_dates.append(post_date_element.text.strip() if post_date_element else "unknown")

                # 작성자 정보
                writer_element = html.select_one("span.nick > a.link")
                writers.append(writer_element.text.strip() if writer_element else "unknown")

                # 태그 크롤링
                tag_elements = html.select("div.wrap_tag span.ell")
                tags = [tag.text.strip() for tag in tag_elements]
                tags_list.append(", ".join(tags))

                # 공감 수 크롤링
                sympathy_element = html.select_one("span.u_likeit_list_btn._button.btn_sympathy.pcol2.off > em.u_cnt._count")
                sympathy_text = sympathy_element.text.strip() if sympathy_element else "0"
                try:
                    sympathy = int(sympathy_text)
                except ValueError:
                    sympathy = 0
                sympathies.append(sympathy)

                # 광고성 이미지 크롤링
                ad_images = html.select("img[src*='firebasestorage']")
                dinnerqueen_ad_images = html.select("img[src*='dinnerqueen']")
                revu_ad_images = html.select("img[src*='revu']")
                cloudfront_ad_images = html.select("img[src*='cloudfront']")

                # 광고 이미지 URL 리스트 생성
                if ad_images or dinnerqueen_ad_images or revu_ad_images or cloudfront_ad_images:
                    ad_image_urls = [img.get("src") for img in ad_images if img.get("src")]
                    dinnerqueen_ad_image_urls = [img.get("src") for img in dinnerqueen_ad_images if img.get("src")]
                    revu_ad_image_urls = [img.get("src") for img in revu_ad_images if img.get("src")]
                    cloudfront_ad_image_urls = [img.get("src") for img in cloudfront_ad_images if img.get("src")]
                    all_ad_images = ad_image_urls + dinnerqueen_ad_image_urls + revu_ad_image_urls + cloudfront_ad_image_urls

                    ad_images_list.append(", ".join(all_ad_images))
                    ad_status.append("O")  # 광고가 있으면 'O'
                else:
                    ad_images_list.append("")
                    ad_status.append("X")  # 광고가 없으면 'X'

                # 메인 프레임으로 돌아가기
                driver.switch_to.default_content()

            except Exception as e:
                print(f"{url}에서 크롤링 중 오류 발생: {e}")
                titles.append("error")
                contents.append("error")
                post_dates.append("unknown")
                writers.append("unknown")
                tags_list.append("unknown")
                sympathies.append(0)
                ad_images_list.append("")
                ad_status.append("X")

        driver.quit()

        # DataFrame 생성 및 반환
        return pd.DataFrame({
            'writer': writers,
            'date': post_dates,
            'title': titles,
            'content': contents,
            'tags': tags_list,
            'sympathy': sympathies,
            'post_url': urls,
            'ad_images': ad_images_list,
            '광고': ad_status
        })