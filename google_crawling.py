from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import time
import yaml
import logging

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

def load_queries():
    with open("backend/config.yaml", "r", encoding="utf-8") as file:
        config = yaml.safe_load(file)
    return config["query"]

def create_driver():
    options = webdriver.ChromeOptions()
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    return webdriver.Chrome(options=options)

def crawl_google_maps(queries, max_results=1):
    driver = create_driver()
    results = []

    for idx, query in enumerate(queries[:max_results]):
        logging.info(f"[{idx+1}/{max_results}] Google Maps에서 검색 중: {query}")
        driver.get("https://www.google.com/maps/")
        time.sleep(2)

        try:
            searchbox = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "searchboxinput"))
            )
            searchbox.clear()
            searchbox.send_keys(query)
            searchbutton = driver.find_element(By.ID, "searchbox-searchbutton")
            searchbutton.click()

            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.tAiQdd"))
            )
            driver.find_element(By.CSS_SELECTOR, "div.tAiQdd").click()
            time.sleep(3)

            title = driver.find_element(By.CSS_SELECTOR, "h1.DUwDvf").text
            try:
                rating = driver.find_element(By.CSS_SELECTOR, "#QA0Szd > div > div > div.w6VYqd > div:nth-child(2) > div > div.e07Vkf.kA9KIf > div > div > div.TIHn2 > div > div.lMbq3e > div.LBgpqf > div > div.fontBodyMedium.dmRWX > div.F7nice > span:nth-child(1) > span:nth-child(1)").text
            except:
                rating = "N/A"
            try:
                review_count = driver.find_element(By.CSS_SELECTOR, "#QA0Szd > div > div > div.w6VYqd > div:nth-child(2) > div > div.e07Vkf.kA9KIf > div > div > div.TIHn2 > div > div.lMbq3e > div.LBgpqf > div > div.fontBodyMedium.dmRWX > div.F7nice > span:nth-child(2) > span > span").text
            except:
                review_count = "N/A"

            try:
                price = driver.find_element(By.CSS_SELECTOR, "#QA0Szd > div > div > div.w6VYqd > div:nth-child(2) > div > div.e07Vkf.kA9KIf > div > div > div.TIHn2 > div > div.lMbq3e > div.LBgpqf > div > div.fontBodyMedium.dmRWX > span > span > span > span:nth-child(2) > span > span").text
            except:
                price = "N/A"
            try:
                category = driver.find_element(By.CSS_SELECTOR, "#QA0Szd > div > div > div.w6VYqd > div:nth-child(2) > div > div.e07Vkf.kA9KIf > div > div > div.TIHn2 > div > div.lMbq3e > div.LBgpqf > div > div:nth-child(2) > span:nth-child(1) > span > button").text
            except:
                category = "N/A"
            # 이미지 URL 
            try:
                image_element = driver.find_element(By.CSS_SELECTOR, "#QA0Szd > div > div > div.w6VYqd > div:nth-child(2) > div > div.e07Vkf.kA9KIf > div > div > div.ZKCDEc > div.RZ66Rb.FgCUCc > button > img")
                image_url = image_element.get_attribute("src")
            except:
                image_url = "N/A"

            results.append({
                "restaurant_name": query,
                "googlemap_name": title,
                "rating": rating,
                "review_count": review_count,
                "price": price,
                "category": category,
                "image": image_url
            })
            logging.info(f"크롤링 성공: {title}")

        except Exception as e:
            logging.error(f"검색 결과 크롤링 중 오류 발생: {e}")

        time.sleep(2)

    driver.quit()
    return results

def save_to_csv(data, filename):
    df = pd.DataFrame(data)
    
    # review_count 컬럼에서 '-', '(', ')' 제거 및 숫자로 변환
    if 'review_count' in df.columns:
        df['review_count'] = (
            df['review_count']
            .str.replace("-", "", regex=False)   # '-' 기호 제거
            .str.replace(",", "", regex=False)  # 쉼표 제거
            .str.replace("(", "", regex=False)  # '(' 제거
            .str.replace(")", "", regex=False)  # ')' 제거
            .fillna("0")                        # 결측값을 '0'으로 대체
            .astype(int)                        # 정수형으로 변환
        )
    
    df.to_csv(filename, index=False, encoding="utf-8-sig")
    logging.info(f"크롤링 결과가 {filename}에 저장되었습니다.")


if __name__ == "__main__":
    queries = load_queries()
    output_file = "google_maps_results.csv"

    logging.info("크롤링 시작")
    search_results = crawl_google_maps(queries, max_results=1)
    save_to_csv(search_results, output_file)
    logging.info("크롤링 완료")
