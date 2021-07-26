import os
import threading
import requests
import time
from bs4 import BeautifulSoup
from os import path
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


# check if file is a format we can download, skip it if we have it
def filename_check(filename):
    name = str(filename)
    if path.exists(savepath + filename):
        return False
    good_formats = [".jpeg", ".jpg", ".png"]
    for form in good_formats:
        if name.endswith(form):
            return True
    return False


def board_check(boardname):
    if boardname in boards:
        return True
    return False


def board_slash(boardname):
    if not boardname.startswith("/"):
        boardname = "/" + boardname
    if not boardname.endswith("/"):
        boardname = boardname + "/"
    return boardname


def get_threads(board):
    queryurl = api_url1 + board_slash(board) + api_url2
    time.sleep(1)
    result = requests.get(queryurl)
    result.raise_for_status()
    jsonresponse = result.json()
    threadlist = []
    for page in jsonresponse:
        for thread in page["threads"]:
            threadlist.append(int(thread["no"]))
    return threadlist


def get_boards():
    queryurl = "https://a.4cdn.org/boards.json"
    time.sleep(1)
    result = requests.get(queryurl)
    result.raise_for_status()
    jsonresponse = result.json()
    boardlist = []
    print("\nFound the following boards:")
    for board in jsonresponse["boards"]:
        bname = str(board["board"])
        bdesc = str(board["title"])
        boardlist.append(bname)
        print(bname + " : " + bdesc)
    return boardlist


def f_exit():
    print("Exiting...\n")
    exit(0)


def save_links(board, thread_number, image_links):
    # request build
    board = board_slash(board)
    fullurl = url4chan + board + urlthread + thread_number
    result = requests.get(fullurl)
    # page soup
    if result.status_code == 200:
        soup = BeautifulSoup(result.content, "html.parser")
    else:
        return 1
    # save images to board name folder
    global savepath
    savepath = basedir + board
    # get all image links
    for image in soup.find_all('a', {'class': 'fileThumb'}):
        # take full res version
        image = image.get('href')
        # strip url for filename
        filename = str(image).rpartition("/")[2]
        # skip weird formats and already downloaded files
        if not (filename_check(filename)):
            continue
        # rebuild valid link
        image = http + image
        if len(image) > 32:
            image_links.append((image, filename))


def download_link(b, i, f):
    global savepath
    savepath = basedir + board_slash(b)
    try:
        with open(savepath + f, 'wb') as file:
            im = urllib.request.urlopen(i)
            file.write(im.read())
            file.close()
            im.close()
        print(f + " saved\n", flush=True, end="")
    except urllib.error.HTTPError:
        print(f + " not saved (404)\n", flush=True, end="")
        pass
    except urllib.error.URLError:
        print(f + "not saved (???)\n", flush=True, end="")
        pass


def main():
    global exits

    print("4chan image saver\nConnecting to 4chan API...")
    global boards
    boards = get_boards()
    if len(boards) == 0:
        f_exit()

    print("\nReady to go\n")

    try:
        os.makedirs(basedir)
    except FileExistsError:
        pass

    while True:
        currentboard = str(input("Enter board/exit: "))
        if currentboard.lower() in exits:
            f_exit()

        if not board_check(currentboard):
            print("Invalid board, try again")
            continue

        # create board folder if not present
        try:
            os.makedirs(basedir+board_slash(currentboard))
        except FileExistsError:
            pass
        except IOError:
            f_exit()

        threads = get_threads(currentboard)
        print("\nGot the thread numbers\n")

        res_links = []
        dl_threads = []

        tuples = []
        for thread in threads:
            tuples.append((currentboard, str(thread), res_links))

        for tu in tuples:
            t = threading.Thread(target=save_links, args=tu)
            dl_threads.append(t)
            t.start()

        for t in dl_threads:
            t.join()

        # print(res_links)
        # exit(1)

        file_links = []
        for res in res_links:
            if res is not None:
                file_links.append((currentboard, res[0], res[1]))

        print("Got all image links, starting download...\n")

        dl_threads = []

        for fl in file_links:
            t = threading.Thread(target=download_link, args=fl)
            dl_threads.append(t)
            t.start()

        for t in dl_threads:
            t.join()

        print("\nGot all images currently on board " + board_slash(currentboard) + "\n")


if __name__ == "__main__":
    main()
