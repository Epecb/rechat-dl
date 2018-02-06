#!/usr/bin/env python3
'''
    rechat-dl is a simple command-line tool
    to download the Chat Replay messages and metadata of Twitch VODs
    for archival purposes.
'''

import sys
import time
import json
import argparse
import requests


CHUNK_ATTEMPTS = 6
CHUNK_ATTEMPT_SLEEP = 10


def progress(count, total, status=''):
    '''
    The gist here: https://gist.github.com/vladignatyev/06860ec2040cb497f0f3
    '''

    bar_len = 60
    filled_len = int(round(bar_len * count / float(total)))

    percents = round(100.0 * count / float(total), 1)
    pbar = '=' * filled_len + '-' * (bar_len - filled_len)

    sys.stdout.write('[%s] %s%s ...%s\r' % (pbar, percents, '%', status))
    sys.stdout.flush()


def download(vod_id, file_name):
    '''
    get vod chat
    '''

    messages = []
    client_id = "isaxc3wjcarzh4vgvz11cslcthw0gw"
    headers = {
        "Client-ID": client_id,
        "User-Agent": "Mozilla/5.0"
        }

    vod_info = requests.get("https://api.twitch.tv/kraken/videos/v" +
                            vod_id, headers=headers).json()

    if "error" in vod_info:
        sys.exit("got an error in vod info response: " + str(vod_info))

    video_length = vod_info['length']

# we store the vod metadata in the first element of the message array
    messages.append(vod_info)

    response = {'_next': ''}

    print("Downloading chat messages for vod " + vod_id + "...")
    while '_next' in response:

        query = ('cursor=' + response['_next'])

        for i in range(CHUNK_ATTEMPTS):
            error = None
            try:
                response = requests.get("https://api.twitch.tv/v5/videos/" +
                                        vod_id + "/comments?" + query,
                                        headers=headers).json()
            except requests.exceptions.ConnectionError as err:
                error = str(err)
            else:
                if "errors" in response or "comments" not in response:
                    error = "error received in chat message response: " + \
                            str(response)

            if error is None:
                messages += response["comments"]
                break
            else:
                print("\nerror while downloading chunk: " + error)

                if i < CHUNK_ATTEMPTS - 1:
                    print("retrying in " +
                          str(CHUNK_ATTEMPT_SLEEP) +
                          " seconds ", end="")
                print("(attempt " + str(i + 1) +
                      "/" + str(CHUNK_ATTEMPTS) + ")")

                if i < CHUNK_ATTEMPTS - 1:
                    time.sleep(CHUNK_ATTEMPT_SLEEP)

        if error is not None:
            sys.exit("max retries exceeded.")

        comment_offset = response['comments'][len(
            response['comments'])-1]["content_offset_seconds"]
        progress(comment_offset, video_length, status="receiving...")

    print("\nsaving to " + file_name)

    with open(file_name, "w") as save_file:
        save_file.write(json.dumps(messages))

    print("done!")


if __name__ == '__main__':
    PARSER = argparse.ArgumentParser(description=__doc__)
    PARSER.add_argument('vod_id', metavar='VOD-ID', help='''
    can be found in the vod url like this:
    http://www.twitch.tv/streamername/v/{VOD-ID}
    ''')
    PARSER.add_argument('file_name', metavar='FILE', nargs='?', help='''
    FILE (optional): the file the chat messages will be saved into.
    if not set, it's rechat-{VOD-ID}.json
    ''')
    ARGS = PARSER.parse_args(args=None if len(sys.argv) > 1 else ['--help'])
    ARGS.file_name = ("rechat-" + ARGS.vod_id +
                      ".json") if ARGS.file_name is None else ARGS.file_name
    download(ARGS.vod_id, ARGS.file_name)
