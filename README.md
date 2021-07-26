# 4chan-Image-Downloader
Python script that downloads images off 4chan one board at a time. I mostly made this to create my own image datasets for machine learning, but it can have other uses.

## Usage
Place in desired location and run. The script will create it's own folder and subfolders as needed. Simply enter the board you want to download and wait/repeat. Most common quit commands work for a clean exit.

### Performance
All image names and links and gathered and then downloaded in bulk. I'm not sure if 4chan itself throttles downloads to some extent, but it seems it can serve files at a reliable 100Mbps. During testing it reached a sustained peak of about 250Mbps, downloading all images on /g/ in less than 3 minutes.

### Warning
Download images from the NSFW boards at your own risk, there's plenty of content of questionable legality, depending on where you live.
