import os
import requests

REQUIRED_GB = 35
BASE_URL = "https://lfs.aminer.cn/misc/moocdata/data/mooccube2/"

FILES = [
    "entities/course.json",
    "entities/problem.json",
    "entities/user.json",
    "relation/exercise-problem.txt",
    "relation/user-problem.json",
    "relations/user-video.json",
    "relations/concept-course.txt"
    "relations/video_id-ccid.txt"
    "relations/concept-video.txt",
    "relations/concept-problem.txt"
    "entities/concept.json"
]


os.makedirs("entities", exist_ok=True)
os.makedirs("relations", exist_ok=True)

def download_file(filename):
    url = BASE_URL + filename
    print(f">>> Đang tải {filename} ...")

    try:
        with requests.get(url, stream=True, timeout=60) as r:
            r.raise_for_status()

            with open(filename, "wb") as f:
                for chunk in r.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        f.write(chunk)

        print(f"✓ Hoàn thành: {filename}")

    except Exception as e:
        print(f"✗ Lỗi khi tải: {filename}")
        print(e)

    print("----------------------------------------")
    
for file in FILES:
    download_file(file)

print("Tất cả file đã được xử lý!")