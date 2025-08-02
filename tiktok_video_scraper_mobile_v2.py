import requests
import re
import sys
import random
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from queue import Queue
import time

##################################################################
class TikTokVideoScraperMobile:

    def __init__(self):
        """ Initialize """

        self.headers = {
            "content-type": "application/x-www-form-urlencoded",
            "User-Agent": "com.zhiliaoapp.musically/2023501030 (Linux; U; Android 14; en_US; Pixel 8 Pro; Build/TP1A.220624.014;tt-ok/3.12.13.4-tiktok)",
            "x-argus": "",
        }

        self.proxies = {
            'http': '',
            'https': '',
        }

        self.tiktok_regex = r'https?://www\.tiktok\.com/(?:embed|@([\w\.-]+)?/(video|photo))/(\d+)'

        self.tiktok_session = requests.Session()
    
    def set_proxies(self, http_proxy: str, https_proxy: str) -> None:
        """ set proxy  """

        self.proxies['http'] = http_proxy 
        self.proxies['https'] = https_proxy
    

    def get_video_id_by_url(self, tiktok_url: str) -> str:
        """ get video id """

        # If the url is a short url, get web url
        if 'vm.' in tiktok_url or 'vt.' in tiktok_url or '/t/' in tiktok_url:
            try:
                tiktok_url = self.tiktok_session.get(tiktok_url, headers=self.headers, proxies=self.proxies, timeout=60).url
            except Exception as e:
                print(e, "\nError on line {}".format(sys.exc_info()[-1].tb_lineno))
                raise SystemExit('error getting web url')

        try:
            video_id = re.match(self.tiktok_regex, tiktok_url).group(3)
        except Exception as e:
            print(e, "\nError on line {}".format(sys.exc_info()[-1].tb_lineno))
            raise SystemExit('error getting video id')

        return video_id 
    

    def get_video_data_by_video_id(self, video_id: str, max_workers: int = 5) -> tuple:
        """ get video url with threading optimization """
        
        # get iid-device_id from github repo file
        try:
            iid_did = requests.get('https://cdn.jsdelivr.net/gh/descargarbot/tiktok-video-scraper-mobile@main/ids.json').json()
        except Exception as e:
            print(e, "\nError on line {}".format(sys.exc_info()[-1].tb_lineno))
            raise SystemExit('error getting tiktok ids')

        tiktok_video_data_endpoint = 'https://api16-normal-c-useast1a.tiktokv.com/aweme/v1/multi/aweme/detail/'
        
        base_params = {
            "channel": "googleplay",
            "aid": "1233",
            "app_name": "musical_ly",
            "version_code": "350103",
            "version_name": "35.1.3",
            "device_platform": "android",
            "device_type": "Pixel 8 Pro",
            "os_version": "14",
        }
        payload = {"aweme_ids": f"[{video_id}]"}

        result_queue = Queue()
        stop_event = threading.Event()
        
        def try_request(iid_did_pair, attempt=1):
            """exec threads"""
            if stop_event.is_set():
                return None
                
            params = base_params.copy()
            params['iid'] = iid_did_pair['iid']
            params['device_id'] = iid_did_pair['device_id']
            
            max_retries = 3
            for retry in range(max_retries):
                if stop_event.is_set():
                    return None
                    
                try:
                    response = self.tiktok_session.post(
                        tiktok_video_data_endpoint, 
                        data=payload, 
                        headers=self.headers, 
                        params=params, 
                        proxies=self.proxies, 
                        timeout=30
                    )
                    json_video_data = response.json()
                    
                    if self._is_valid_response(json_video_data):
                        print(f"Éxito con iid: {params['iid']}, device_id: {params['device_id']}")
                        result_queue.put(json_video_data)
                        stop_event.set()
                        return json_video_data
                    else:
                        break
                        
                except Exception as e:
                    if retry < max_retries - 1:
                        print(f"Error, retry {retry + 1} with iid: {params['iid']}, device_id: {params['device_id']} - {str(e)}")
                        time.sleep(0.5)
                    else:
                        print(f"Fail with {max_retries} retrys - iid: {params['iid']}, device_id: {params['device_id']}")
            
            return None

        random.shuffle(iid_did)
        iid_did = iid_did[:400]
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            batch_size = max_workers * 2
            
            for i in range(0, len(iid_did), batch_size):
                if stop_event.is_set():
                    break
                    
                batch = iid_did[i:i + batch_size]
                futures = [executor.submit(try_request, pair) for pair in batch]
                
                for future in as_completed(futures):
                    if stop_event.is_set():
                        break
                    try:
                        result = future.result(timeout=5)
                        if result:
                            for f in futures:
                                f.cancel()
                            break
                    except Exception as e:
                        continue
                
                if stop_event.is_set():
                    break
                    
                print(f"trying next batch... ({i + batch_size}/{len(iid_did)})")

        if not result_queue.empty():
            json_video_data = result_queue.get()
        else:
            raise SystemExit('Error with all iid/device_id')

        return self._process_video_data(json_video_data)
    
    def _is_valid_response(self, json_data):
        try:
            return (json_data and 
                    'aweme_details' in json_data and 
                    len(json_data['aweme_details']) > 0 and
                    json_data['aweme_details'][0] is not None)
        except:
            return False
    
    def _process_video_data(self, json_video_data):
        tiktok_video_urls = []
        thumbnail = None
        
        try:
            # for singles videos
            tiktok_video_url = json_video_data["aweme_details"][0]["video"]["bit_rate"][0]["play_addr"]["url_list"][0]
            thumbnail = json_video_data["aweme_details"][0]["video"]["dynamic_cover"]["url_list"][0]
            tiktok_video_urls.append(tiktok_video_url)
        except Exception as e:
            try:
                # for carousel
                if 'added_sound_music_info' in json_video_data["aweme_details"][0]:
                    tiktok_carrusel_music = json_video_data["aweme_details"][0]["added_sound_music_info"]["play_url"]["url_list"][0]
                    tiktok_video_urls.append(tiktok_carrusel_music)

                thumbnail = json_video_data["aweme_details"][0]["image_post_info"]["image_post_cover"]["display_image"]["url_list"][0]

                if 'images' in json_video_data["aweme_details"][0]["image_post_info"]:
                    for image in json_video_data["aweme_details"][0]["image_post_info"]["images"]:
                        image_url = image["display_image"]["url_list"][0]
                        tiktok_video_urls.append(image_url)

            except Exception as e:
                print(e, "\nError on line {}".format(sys.exc_info()[-1].tb_lineno))
                raise SystemExit('error getting video url')
        
        return tiktok_video_urls, thumbnail


    def download(self, tiktok_video_urls: list, video_id: str) -> list:
        """ download the video
            video_is is just to name the file """

        path_filenames = []
        count = 0
        for tiktok_video_url in tiktok_video_urls:
            try:
                video = self.tiktok_session.get(tiktok_video_url, headers=self.headers, proxies=self.proxies, stream=True)
            except Exception as e:
                print(e, "\nError on line {}".format(sys.exc_info()[-1].tb_lineno))
                raise SystemExit('error downloading video')

            if len(tiktok_video_urls) == 1:
                path_filename = f'{video_id}.mp4'
            else:
                if '.webp' in tiktok_video_url:
                    path_filename = f'{video_id}___{count}.webp'
                else:
                    path_filename = f'{video_id}___{count}.mp3'
            
            try:
                with open(path_filename, 'wb') as f:
                    for chunk in video.iter_content(chunk_size=1024):
                        if chunk:
                            f.write(chunk)
                            f.flush()
                path_filenames.append(path_filename)
                count = count + 1
            except Exception as e:
                print(e, "\nError on line {}".format(sys.exc_info()[-1].tb_lineno))
                raise SystemExit('error writting video')

        return path_filenames


    def get_video_filesize(self, video_urls: list) -> list:
        """ get file size of requested video """
        filesizes = []

        for video_url in video_urls:
            try:
                video_size = self.tiktok_session.head(video_url, headers=self.headers, proxies=self.proxies)
                filesizes.append(video_size.headers['content-length'])
            except Exception as e:
                print(e, "\nError on line {}".format(sys.exc_info()[-1].tb_lineno))
                raise SystemExit('error getting video file size')

        return filesizes

##################################################################

if __name__ == "__main__":

    # use case example

    # set tiktok url
    tiktok_url = ''
    if tiktok_url == '':
        if len(sys.argv) < 2:
            print('you must provide a tiktok url')
            exit()
        tiktok_url = sys.argv[1]
    
    # create scraper video object
    tiktok_video = TikTokVideoScraperMobile()

    # set the proxy (optional, u can run it with ur own ip)
    #tiktok_video.set_proxies('socks5://157.230.250.185:2144', 'socks5://157.230.250.185:2144')

    # get video id from url
    video_id = tiktok_video.get_video_id_by_url(tiktok_url)
    
    # get video url from video id
    tiktok_video_urls, video_thumbnail = tiktok_video.get_video_data_by_video_id(video_id, max_workers=20)

    # get the video filesize
    videos_filesize = tiktok_video.get_video_filesize(tiktok_video_urls)
    [print('filesize: ~' + filesize + ' bytes') for filesize in videos_filesize]

    # download video by url
    downloaded_video_list = tiktok_video.download(tiktok_video_urls, video_id)
 
    tiktok_video.tiktok_session.close()
