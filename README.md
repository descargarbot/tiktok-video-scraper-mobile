# tiktok video scraper (mobile)
<div align="center">
  
![DescargarBot](https://www.descargarbot.com/v/download-github_tiktok.png)
  
[![TikTok](https://img.shields.io/badge/on-descargarbot?logo=github&label=status&color=green
)](https://github.com/descargarbot/tiktok-video-scraper-mobile/issues "TikTok Mobile")
</div>

<h2>dependencies</h2>
<code>Python 3.9+</code>
<code>requests</code>
<br>
<br>
<h2>install dependencies</h2>
<ul>
<li><h3>requests</h3></li>
  <code>pip install requests</code><br>
  <code>pip install -U 'requests[socks]'</code>
  <br>
<br>
</ul>
<h2>use case example</h2>

    #import the class TikTokVideoScraperMobile
    from tiktok_video_scraper_mobile_v2 import TikTokVideoScraperMobile

    # set tiktok url
    tiktok_url = 'your tiktok post'

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

  > [!NOTE]\
  > you can use the CLI
  <br><br>
  > <code>python3 tiktok_video_scraper_mobile_v2.py TIKTOK_URL</code><br>or<br>
  > <code>python3 tiktok_carrusel_scraper_mobile.py TIKTOK_URL</code><br>or<br>
  > <code>python3 tiktok_video_scraper_mobile.py TIKTOK_URL</code>
  
<br>
<h2>online</h2>
<ul>
  ⤵
  <li> web 🤖 <a href="https://descargarbot.com" >  DescargarBot.com</a></li>
  <li> <a href="https://t.me/xDescargarBot" > Telegram Bot 🤖 </a></li>
  <li> <a href="https://discord.gg/gcFVruyjeQ" > Discord Bot 🤖 </a></li>
</ul>

