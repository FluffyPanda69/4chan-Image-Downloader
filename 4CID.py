import ctypes
import os
import platform
import threading
import requests
import time
import textwrap
from bs4 import BeautifulSoup
from os import path
from multiprocessing import Pool
import urllib.error
import urllib.request

# constants
basedir = "4ch"
savepath = ""
boards = []
exits = ["exit", "e", "quit", "q", ":q", ":q?", "q!", "wq", "kill"]

api_url1 = "https://a.4cdn.org"
api_url2 = "threads.json"
http = "http:"
url4chan = "https://boards.4channel.org"
urlthread = "thread/"

# thread filters
minreplies = 0
maxthreadage = 86400 * 7
maxthreadtime = int(time.time()) - maxthreadage


# check if file is a format we can download, skip it if we have it
def filename_check(filename):
    name = str(filename)
    if path.exists(savepath + filename):
        return False
    good_formats = [".bmp", ".ico", ".jpeg", ".jpg", ".png", ".gif"]
    for form in good_formats:
        if name.endswith(form):
            return True
    return False


def board_check(boardname):
    if boardname in boards:
        return boardname
    else:
        return ""


def board_slash(boardname):
    if not boardname.startswith("/"):
        boardname = "/" + boardname
    if not boardname.endswith("/"):
        boardname = boardname + "/"
    return boardname


def get_threads(board):
    global minreplies

    queryurl = api_url1 + board_slash(board) + api_url2
    time.sleep(1)
    result = requests.get(queryurl)
    result.raise_for_status()
    jsonresponse = result.json()
    threadlist = []

    for page in jsonresponse:
        for thread in page["threads"]:
            if thread["last_modified"] > maxthreadtime:
                if thread["replies"] > minreplies:
                    threadlist.append(int(thread["no"]))

    return threadlist


def get_boards():
    queryurl = "https://a.4cdn.org/boards.json"
    time.sleep(1)
    result = requests.get(queryurl)
    result.raise_for_status()
    jsonresponse = result.json()
    boardlist = []

    for board in jsonresponse["boards"]:
        boardlist.append(str(board["board"]))

    return boardlist


def f_exit():
    print("Exiting...")
    exit(0)


def save_links(board, thread_number):
    # request build
    board = board_slash(board)
    fullurl = url4chan + board + urlthread + str(thread_number)
    result = requests.get(fullurl)

    # page soup
    if result.status_code == 200:
        soup = BeautifulSoup(result.content, "html.parser")
    else:
        return 1

    # save images to board name folder
    global savepath
    savepath = basedir + board

    # create folder if not present
    try:
        os.makedirs(savepath)
    except FileExistsError:
        pass
    except IOError:
        f_exit()

    image_links = []

    # get all image links
    for image in soup.find_all('a', {'class': 'fileThumb'}):
        # take full res version
        image = image.get('href')
        # strip url for filename
        filename = str(image).rpartition("/")[2]
        # skip weird formats
        if not (filename_check(filename)):
            continue
        # rebuild valid link
        image = http + image
        image_links.append((image, filename))

    if len(image_links) > 0:
        return image_links


def download_link(b, i, f):
    global savepath
    savepath = basedir + board_slash(b)
    try:
        with open(savepath + f, 'wb') as file:
            im = urllib.request.urlopen(i)
            file.write(im.read())
        file.close()
        print(f + " saved\n")
    except urllib.error.HTTPError:
        print(f + " not saved (404)\n")
        pass
    except urllib.error.URLError:
        print(f + "not saved (???)\n")
        pass


def main():
    global exits

    print("4chan image saver\nConnecting to 4chan API...")
    global boards
    boards = get_boards()
    if len(boards) > 0:
        print("\nFound the following boards:")
        print(textwrap.fill(str(boards), 80))
    else:
        f_exit()
    print("\nReady to go\n")

    try:
        os.makedirs(basedir)
    except FileExistsError:
        pass

    while True:
        currentboard = str(input("Enter board (or exit): "))
        if currentboard.lower() in exits:
            f_exit()

        currentboard = board_check(currentboard)
        if len(currentboard) == 0:
            print("Invalid board, try again")
            continue

        threads = get_threads(currentboard)
        print("\nGot the thread numbers\n")

        tuples = []
        for thread in threads:
            tuples.append((currentboard, thread))

        with Pool(60) as p:
            res_links = p.starmap(save_links, tuples)
        p.close()

        file_links = []
        for res in res_links:
            if res is not None:
                for link in res:
                    file_links.append((currentboard, link[0], link[1]))

        print("Got all image links, starting download...\n")

        dl_threads = []

        for fl in file_links:
            t = threading.Thread(target=download_link, args=fl)
            dl_threads.append(t)
            t.start()

        for t in dl_threads:
            t.join()

        print("Got all images currently on board " + board_slash(currentboard) + "\n")

        if platform.system().lower() == "windows":
            ctypes.windll.user32.FlashWindow(ctypes.windll.kernel32.GetConsoleWindow(), True)


if __name__ == "__main__":
    main()
