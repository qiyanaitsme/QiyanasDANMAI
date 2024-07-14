import requests
import os
import time
from loguru import logger
from datetime import datetime
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE_URL = "https://danbooru.donmai.us/posts.json"

logger.remove()
logger.add(lambda message: sys.stdout.write(message) and sys.stdout.flush(),
           format="{time:YYYY-MM-DD} | {level} | {message}")

if "SUCCESS" not in logger._core.levels:
    logger.level("SUCCESS", no=33, color="<green>")

def download_image(post, index, downloaded_count, SAVE_FOLDER):
    if 'file_url' in post:
        file_url = post['file_url']
        file_name = os.path.basename(file_url)
        file_path = os.path.join(SAVE_FOLDER, file_name)

        logger.info(f"Начато скачивание - картинка {downloaded_count + index} - ссылка {file_url}")
        with requests.get(file_url, stream=True) as r:
            r.raise_for_status()
            with open(file_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        logger.log("SUCCESS", f"Завершено скачивание - картинка {downloaded_count + index} - {file_name}")
    else:
        logger.warning(f"No file URL found for post {post['id']}")


def download_images(tags, limit, downloaded_count, SAVE_FOLDER):
    params = {
        'tags': tags,
        'limit': min(200, limit - downloaded_count)
    }

    response = requests.get(BASE_URL, params=params)

    if response.status_code == 200:
        data = response.json()
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = []
            for index, post in enumerate(data, start=1):
                futures.append(executor.submit(download_image, post, index, downloaded_count, SAVE_FOLDER))
            for future in as_completed(futures):
                future.result()
    else:
        logger.error(f"Failed to retrieve data: {response.status_code}")


if __name__ == "__main__":
    tags = input("Введите теги для поиска (через запятую): ")
    limit = int(input("Введите количество изображений для скачивания: "))
    SAVE_FOLDER = datetime.now().strftime('%Y-%m-%d') + '_' + tags.replace(',', '_').replace(' ', '_')
    if not os.path.exists(SAVE_FOLDER):
        os.makedirs(SAVE_FOLDER)
    logger.info("Начинаю скачивание.")

    downloaded_count = 0
    while downloaded_count < limit:
        download_images(tags, limit, downloaded_count, SAVE_FOLDER)
        downloaded_count += min(200, limit - downloaded_count)
        logger.info("Конец.")
        time.sleep(2)