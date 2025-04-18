import time
import random
from flask import Flask, render_template, request, jsonify
import yt_dlp
import undetected_chromedriver as uc
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

app = Flask(__name__)

video_queue = []
driver = None
currently_playing = None

def random_sleep(min_sleep=2, max_sleep=5):
    time.sleep(random.uniform(min_sleep, max_sleep))

def run_browser_with_profile(profile_dir):
    options = Options()
    options.add_argument(f"user-data-dir={profile_dir}")
    options.add_argument("profile-directory=Profile 1")
    driver = uc.Chrome(options=options)
    return driver

def get_video_details(video_url):
    try:
        with yt_dlp.YoutubeDL() as ydl:
            info = ydl.extract_info(video_url, download=False)
            title = info.get("title", "Unknown title")
            uploader = info.get("uploader", "Unknown uploader")
            return title, uploader
    except Exception as e:
        print(f"Error fetching video details: {e}")
        return None, None

def close_previous_tab():
    all_tabs = driver.window_handles
    if len(all_tabs) > 1:
        driver.switch_to.window(all_tabs[0])
        driver.close()
        driver.switch_to.window(all_tabs[1])

def open_video_in_fullscreen(driver, video_url):
    driver.get(video_url)
    time.sleep(0.1)
    try:
        fullscreen_button = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, 'button.ytp-fullscreen-button'))
        )
        fullscreen_button.click()

        play_button = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, 'button.ytp-play-button'))
        )
        random_sleep(1, 3)
    except Exception as e:
        print(f"Error: {e}")
        print("Trying JavaScript to click elements.")
        driver.execute_script("arguments[0].click();", play_button)
        driver.execute_script("arguments[0].click();", fullscreen_button)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/add_video', methods=['POST'])
def add_video():
    video_url = request.form['url']
    node = request.form.get('node', '').strip()

    if video_url:
        title, uploader = get_video_details(video_url)
        if title and uploader:
            video_queue.append({
                'url': video_url,
                'title': title,
                'uploader': uploader,
                'node': node
            })
            return jsonify({'status': 'success', 'title': title, 'uploader': uploader})
        else:
            return jsonify({'status': 'error', 'message': 'Failed to fetch video details'})
    return jsonify({'status': 'error', 'message': 'Invalid URL'})

@app.route('/get_queue', methods=['GET'])
def get_queue():
    return jsonify({
        'queue': video_queue,
        'currently_playing': currently_playing
    })

@app.route('/play_next_video', methods=['POST'])
def play_next_video():
    global currently_playing
    if not video_queue:
        return jsonify({'status': 'error', 'message': 'No videos in the queue'})

    video = video_queue.pop(0)
    video_url = video['url']
    currently_playing = video

    open_video_in_fullscreen(driver, video_url)

    return jsonify({'status': 'success', 'title': video['title'], 'uploader': video['uploader']})

@app.route('/start_browser', methods=['GET'])
def start_browser():
    global driver
    if driver is None:
        driver = run_browser_with_profile(r"C:\Users\<USER>\AppData\Local\Google\Chrome\User Data")
        close_previous_tab()
        return jsonify({'status': 'success', 'message': 'Browser started'})
    else:
        return jsonify({'status': 'error', 'message': 'Browser already running'})

@app.route('/delete_video/<int:index>', methods=['DELETE'])
def delete_video(index):
    if 0 <= index < len(video_queue):
        removed = video_queue.pop(index)
        return jsonify({'status': 'success', 'removed': removed})
    return jsonify({'status': 'error', 'message': 'Invalid index'})

@app.route('/stop_browser', methods=['GET'])
def stop_browser():
    global driver
    if driver is not None:
        driver.quit()
        driver = None
        return jsonify({'status': 'success', 'message': 'Browser stopped'})
    else:
        return jsonify({'status': 'error', 'message': 'No browser to stop'})



if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
