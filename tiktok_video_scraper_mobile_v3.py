import requests
import re
import sys
import random

#https://github.com/is-L7N/SignerPy
from SignerPy import sign, get

##################################################################
class TikTokVideoScraperMobile:

    def __init__(self):
        """ Initialize """

        self.headers = {
            'Accept': 'application/json',
            "User-Agent": "com.zhiliaoapp.musically/2023501030 (Linux; U; Android 14; en_US; Pixel 8 Pro; Build/TP1A.220624.014;tt-ok/3.12.13.4-tiktok)",
            "content-type": "application/x-www-form-urlencoded",
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
    

    def get_video_data_by_video_id(self, video_id: str) -> tuple:
        """ get video url """

        tiktok_video_data_endpoint = 'https://api16-normal-c-useast1a.tiktokv.com/aweme/v1/multi/aweme/detail/'
        
        params = {
            '_rticket': '1746881769000',
            'ab_version': '39.8.2',
            'ac': 'wifi',
            'ac2': 'wifi5g',
            'aid': '1233',
            'app_language': 'en',
            'app_name': 'musical_ly',
            'app_type': 'normal',
            'build_number': '39.8.2',
            'carrier_region': 'US',
            'cdid': '6fafd62a-ec86-4ae9-a900-92335a266645',
            'channel': 'googleplay',
            'current_region': 'US',
            'device_brand': 'Google',
            'device_id': '7290321599863826609',
            'device_platform': 'android',
            'device_type': 'Pixel 7',
            'dpi': '420',
            'host_abi': 'armeabi-v7a',
            'iid': '7322695348128516797',
            'is_pad': '0',
            'language': 'en',
            'last_install_time': '1746518062',
            'locale': 'en',
            'manifest_version_code': '2023508030',
            'openudid': '00eafece6f7ae014',
            'os': 'android',
            'os_api': '29',
            'os_version': '13',
            'region': 'US',
            'residence': 'US',
            'resolution': '1080*2400',
            'ssmix': '0',
            'timezone_name': 'America/New_York',
            'timezone_offset': '-14400',
            'ts': '1746881769',
            'uoo': '1',
            'update_version_code': '2023508030',
            'version_code': '390802',
            'version_name': '39.8.2',
        }

        data = {
            'aweme_ids': f"[{video_id}]",
            'request_source': '0',
        }

        signed_params = get(params)
        signed_headers = sign(
            params=signed_params,
            payload=data,
        )
        self.headers.update(signed_headers)

        # contains music url and image urls from post / or single video
        tiktok_video_urls = []

        try:
            json_video_data = self.tiktok_session.post(tiktok_video_data_endpoint, params=signed_params, headers=self.headers, data=data, proxies=self.proxies, timeout=60).json()
        except Exception as e:
            print(e, "\nError on line {}".format(sys.exc_info()[-1].tb_lineno))
            raise SystemExit('error getting post data')

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
                    path_filename = f'{video_id}___{count}.mp4'
            
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
    #tiktok_video.set_proxies('', '')

    # get video id from url
    video_id = tiktok_video.get_video_id_by_url(tiktok_url)
    
    # get video url from video id
    tiktok_video_urls, video_thumbnail = tiktok_video.get_video_data_by_video_id(video_id)

    # get the video filesize
    videos_filesize = tiktok_video.get_video_filesize(tiktok_video_urls)
    [print('filesize: ~' + filesize + ' bytes') for filesize in videos_filesize]

    # download video by url
    downloaded_video_list = tiktok_video.download(tiktok_video_urls, video_id)
 
    tiktok_video.tiktok_session.close()
