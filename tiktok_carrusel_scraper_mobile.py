import requests
import re
import sys
import random

##################################################################
class TikTokCarruselScraperMobile:

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

        self.tiktok_regex = r'https?://www\.tiktok\.com/(?:embed|@([\w\.-]+)?/photo)/(\d+)'

        self.tiktok_session = requests.Session()
    
    def set_proxies(self, http_proxy: str, https_proxy: str) -> None:
        """ set proxy  """

        self.proxies['http'] = http_proxy 
        self.proxies['https'] = https_proxy
    

    def get_carrusel_id_by_url(self, tiktok_url: str) -> str:
        """ get carrusel id """

        # If the url is a short url, get web url
        if 'vm.' in tiktok_url or 'vt.' in tiktok_url or '/t/' in tiktok_url:
            try:
                tiktok_url = self.tiktok_session.get(tiktok_url, headers=self.headers, proxies=self.proxies, timeout=60).url
            except Exception as e:
                print(e, "\nError on line {}".format(sys.exc_info()[-1].tb_lineno))
                raise SystemExit('error getting web url')

        try:
            carrusel_id = re.match(self.tiktok_regex, tiktok_url).group(2)
        except Exception as e:
            print(e, "\nError on line {}".format(sys.exc_info()[-1].tb_lineno))
            raise SystemExit('error getting id')

        return carrusel_id 
    

    def get_carrusel_data_by_id(self, carrusel_id: str) -> tuple:
        """ get carrusel urls """

        # get iid-device_id from jsdelivr cdn
        try:
            iid_did = requests.get('https://cdn.jsdelivr.net/gh/descargarbot/tiktok-video-scraper-mobile@main/ids.json').json()
        except Exception as e:
            print(e, "\nError on line {}".format(sys.exc_info()[-1].tb_lineno))
            raise SystemExit('error getting tiktok ids')

        tiktok_carrusel_data_endpoint = 'https://api16-normal-c-useast1a.tiktokv.com/aweme/v1/multi/aweme/detail/'
        
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
        payload = {"aweme_ids": f"[{carrusel_id}]"}


        running = True
        try_count = 1
        try_iid_did = random.choice(iid_did)
        params['iid'] = try_iid_did['iid']
        params['device_id'] = try_iid_did['device_id']
        iid_did.remove(try_iid_did)
        
        while running:
            if iid_did:
                try:
                    json_carrusel_data = self.tiktok_session.post(tiktok_carrusel_data_endpoint, data=payload, headers=self.headers, params=params, proxies=self.proxies, timeout=60).json()
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

        # contains music url and image urls from post
        tiktok_carrusel_urls = []

        try:
            if 'added_sound_music_info' in json_carrusel_data["aweme_details"][0]:
                tiktok_carrusel_music = json_carrusel_data["aweme_details"][0]["added_sound_music_info"]["play_url"]["url_list"][0]
                tiktok_carrusel_urls.append(tiktok_carrusel_music)

            thumbnail = json_carrusel_data["aweme_details"][0]["image_post_info"]["image_post_cover"]["display_image"]["url_list"][0]

            if 'images' in json_carrusel_data["aweme_details"][0]["image_post_info"]:
                for image in json_carrusel_data["aweme_details"][0]["image_post_info"]["images"]:
                    image_url = image["display_image"]["url_list"][0]
                    tiktok_carrusel_urls.append(image_url)

        except Exception as e:
            print(e, "\nError on line {}".format(sys.exc_info()[-1].tb_lineno))
            raise SystemExit('error getting url')

        # return tuple with list, str
        return tiktok_carrusel_urls, thumbnail 


    def download(self, tiktok_carrusel_url: list, carrusel_id: str) -> list:
        """ download the items from the carrusel
            carrusel_id is just to name the files """

        counter = 0
        downloaded_list = []
        for item_url in tiktok_carrusel_url:
            try:
                item = self.tiktok_session.get(item_url, headers=self.headers, proxies=self.proxies, stream=True)
            except Exception as e:
                print(e, "\nError on line {}".format(sys.exc_info()[-1].tb_lineno))
                raise SystemExit('error downloading')

            if '.mp3' in item_url:
                path_filename = f'{carrusel_id}.mp3'
            else:
                path_filename = f'{carrusel_id}_{counter}.webp'
            
            try:
                with open(path_filename, 'wb') as f:
                    for chunk in item.iter_content(chunk_size=1024):
                        if chunk:
                            f.write(chunk)
                            f.flush()
                            
                downloaded_list.append(path_filename)

            except Exception as e:
                print(e, "\nError on line {}".format(sys.exc_info()[-1].tb_lineno))
                raise SystemExit('error writting')

            counter = counter + 1

        return downloaded_list

##################################################################

if __name__ == "__main__":

    # use case example

    # set tiktok carrusel url
    tiktok_url = ''
    if tiktok_url == '':
        if len(sys.argv) < 2:
            print('you must provide a tiktok carrusel url')
            exit()
        tiktok_url = sys.argv[1]
    
    # create scraper carrusel object
    tiktok_carrusel = TikTokCarruselScraperMobile()

    # set the proxy (optional, u can run it with ur own ip)
    #tiktok_carrusel.set_proxies('socks5://157.230.250.185:2144', 'socks5://157.230.250.185:2144')

    # get carrusel id from url
    carrusel_id = tiktok_carrusel.get_carrusel_id_by_url(tiktok_url)
    
    # get carrusel url from carrusel id
    tiktok_carrusel_urls, thumbnail = tiktok_carrusel.get_carrusel_data_by_id(carrusel_id)

    # download carrusel by url
    downloaded_carrusel_list = tiktok_carrusel.download(tiktok_carrusel_urls, carrusel_id)

    tiktok_carrusel.tiktok_session.close()

