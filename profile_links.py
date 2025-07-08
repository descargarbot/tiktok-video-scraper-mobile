import requests
import string
import random
import time
import re
import json
import sys
import itertools
from urllib.parse import urlencode

##################################################################

def get_sec_uid(username):
    
    headers = {            
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36',
                'Referer': 'https://www.tiktok.com/'
            }    
    tt_url = 'https://www.tiktok.com/@' + username

    try:
        html_tiktok_web_data = requests.get(tt_url, headers=headers).text
    except Exception as e:
        print(e, "\nError on line {}".format(sys.exc_info()[-1].tb_lineno))
        raise SystemExit('error getting html web data')

    matches = re.findall(
        r'<script\s+[^>]*id="__UNIVERSAL_DATA_FOR_REHYDRATION__"[^>]*>\s*(.*?)\s*</script>',
        html_tiktok_web_data,
        re.DOTALL
    )

    if matches:
        text_user_data = matches[0].strip()
    else:
        raise SystemExit('__UNIVERSAL_DATA_FOR_REHYDRATION__ error')

    try:
        json_user_data = json.loads(text_user_data)
    except json.JSONDecodeError as e:
        print(e, "\nError on line {}".format(sys.exc_info()[-1].tb_lineno))
        raise SystemExit('error getting json web data')

    try:
        secUid = json_user_data['__DEFAULT_SCOPE__']['webapp.user-detail']['userInfo']['user']['secUid']
    except Exception as e:
        print(e, "\nError on line {}".format(sys.exc_info()[-1].tb_lineno))
        raise SystemExit('error getting html web video')

    print(secUid)
    return secUid

##################################################################

def build_request(sec_uid, cursor):
    params = {
            'aid': '1988',
            'app_language': 'en',
            'app_name': 'tiktok_web',
            'browser_language': 'en-US',
            'browser_name': 'Mozilla',
            'browser_online': 'true',
            'browser_platform': 'Win32',
            'browser_version': '5.0 (Windows)',
            'channel': 'tiktok_web',
            'cookie_enabled': 'true',
            'count': '15',
            'cursor': cursor,
            'device_id': '7290321599863826609',
            'device_platform': 'web_pc',
            'focus_state': 'true',
            'from_page': 'user',
            'history_len': '2',
            'is_fullscreen': 'false',
            'is_page_visible': 'true',
            'language': 'en',
            'os': 'windows',
            'priority_region': '',
            'referer': '',
            'region': 'US',
            'screen_height': '1080',
            'screen_width': '1920',
            'secUid': sec_uid,
            'type': '1',
            'tz_name': 'UTC',
            'verifyFp': f'verify_{"".join(random.choices(string.hexdigits, k=7))}',
            'webcast_language': 'en',
        }

    return '?' + urlencode(params)

##################################################################

def get_profile_items(username):
    tiktok_user_items_endpoint = 'https://www.tiktok.com/api/creator/item_list/'

    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36'} 

    sec_uid = get_sec_uid(username)
    cursor = int(time.time() * 1E3)
    items_id = []
    old_cursor = 0

    for page in itertools.count(1):
        query_string = build_request(sec_uid, cursor)
        url = f"{tiktok_user_items_endpoint}{query_string}"
        try:
            tiktok_user_items_json = requests.get(url, headers=headers).json()
        except Exception as e:
            print(e, "\nError on line {}".format(sys.exc_info()[-1].tb_lineno))
            raise SystemExit('error getting item_list page' + page)

        if 'itemList' in tiktok_user_items_json:
            for tt_video_id in tiktok_user_items_json['itemList']:
                if tt_video_id['id'] in items_id:
                    continue
                
                video_photo = 'video' # by default is video
                if 'video' in tt_video_id:
                    if 'PlayAddrStruct' in tt_video_id['video']:
                        video_photo = "video"
                    else:
                        video_photo = "photo"
                else:
                    continue
                items_id.append(f'https://www.tiktok.com/@{username}/{video_photo}/{tt_video_id['id']}')

                cursor = int(int(tt_video_id['createTime']) * 1E3)
        else:
           old_cursor = cursor

        if not cursor or old_cursor == cursor:
            # User may not have posted within this ~1 week lookback, so manually adjust cursor (based on yt-dlp extractor)
            cursor = old_cursor - 7 * 86_400_000
            if cursor < 1472706000000:
                break

        if 'hasMorePrevious' in tiktok_user_items_json:
            if tiktok_user_items_json['hasMorePrevious'] != True:
                break
        else:
            break
   
    return items_id

##################################################################
# put the user name and get all tt links from the acc (dont use the @ sign, just the username)
if __name__ == "__main__":
    username = ''
    item_list = get_profile_items(username)
    print(len(item_list))
    for link in item_list:
        print(link)
