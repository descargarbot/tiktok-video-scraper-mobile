import requests
import re
import sys
import random

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

        self.tiktok_regex = r'https?://www\.tiktok\.com/(?:embed|@([\w\.-]+)?/video)/(\d+)'

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
            video_id = re.match(self.tiktok_regex, tiktok_url).group(2)
        except Exception as e:
            print(e, "\nError on line {}".format(sys.exc_info()[-1].tb_lineno))
            raise SystemExit('error getting video id')

        return video_id 
    

    def get_video_data_by_video_id(self, video_id: str) -> tuple:
        """ get video url """

        # get iid-device_id from github repo file
        try:
            iid_did = requests.get('https://raw.githubusercontent.com/descargarbot/tiktok-video-scraper-mobile/main/ids.json').json()
        except Exception as e:
            print(e, "\nError on line {}".format(sys.exc_info()[-1].tb_lineno))
            raise SystemExit('error getting tiktok ids')

        tiktok_video_data_endpoint = 'https://api16-normal-c-useast1a.tiktokv.com/aweme/v1/multi/aweme/detail/'
        
        params = {
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


        running = True
        try_count = 1
        try_iid_did = random.choice(iid_did)
        params['iid'] = try_iid_did['iid']
        params['device_id'] = try_iid_did['device_id']
        iid_did.remove(try_iid_did)
        
        while running:
            if iid_did:
                try:
                    json_video_data = self.tiktok_session.post(tiktok_video_data_endpoint, data=payload, headers=self.headers, params=params, proxies=self.proxies, timeout=60).json()
                    running = False
                except Exception as e:
                    if try_count > 4: # 4 is the max retry per pair
                        print(f'failed pair:{params['iid']},{params['device_id']}')

                        try_iid_did = random.choice(iid_did)
                        params['iid'] = try_iid_did['iid']
                        params['device_id'] = try_iid_did['device_id']
                        iid_did.remove(try_iid_did)

                        try_count = 1
                    else:
                        print(f'error, retry: {try_count}')
                        try_count = try_count + 1
            else:
                raise SystemExit('user id and device id no longer works')

        try:
            tiktok_video_url = json_video_data["aweme_details"][0]["video"]["bit_rate"][0]["play_addr"]["url_list"][0]
            thumbnail = json_video_data["aweme_details"][0]["video"]["dynamic_cover"]["url_list"][0]
        except Exception as e:
            print(e, "\nError on line {}".format(sys.exc_info()[-1].tb_lineno))
            raise SystemExit('error getting video url')
        
        return tiktok_video_url, thumbnail


    def download(self, tiktok_video_url: str, video_id: str) -> list:
        """ download the video
            video_is is just to name the file """

        try:
            video = self.tiktok_session.get(tiktok_video_url, headers=self.headers, proxies=self.proxies, stream=True)
        except Exception as e:
            print(e, "\nError on line {}".format(sys.exc_info()[-1].tb_lineno))
            raise SystemExit('error downloading video')

        path_filename = f'{video_id}.mp4'
        
        try:
            with open(path_filename, 'wb') as f:
                for chunk in video.iter_content(chunk_size=1024):
                    if chunk:
                        f.write(chunk)
                        f.flush()
        except Exception as e:
            print(e, "\nError on line {}".format(sys.exc_info()[-1].tb_lineno))
            raise SystemExit('error writting video')

        return [path_filename]


    def get_video_filesize(self, video_url: str) -> str:
        """ get file size of requested video """

        try:
            video_size = self.tiktok_session.head(video_url, headers=self.headers, proxies=self.proxies)
        except Exception as e:
            print(e, "\nError on line {}".format(sys.exc_info()[-1].tb_lineno))
            raise SystemExit('error getting video file size')

        return video_size.headers['content-length']

##################################################################

if __name__ == "__main__":

    # use case example

    # set tiktok video url
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
    tiktok_video_url, video_thumbnail = tiktok_video.get_video_data_by_video_id(video_id)

    # get the video filesize
    video_size = tiktok_video.get_video_filesize(tiktok_video_url)
    print(f'filesize: ~{video_size} bytes')

    # download video by url
    downloaded_video_list = tiktok_video.download(tiktok_video_url, video_id)
 
    tiktok_video.tiktok_session.close()

