from __const__ import *
import argparse
import yt_dlp
import os
import signal
from pathlib import Path

download_archive: Path = None
archive_existed: bool = False
EXITED_N_TIMES = 0

def cleaner():
    args = cli_argument_parser()
    check_for_new_video(args.channel_url, args.name, args.download_all_matches, args.directory, download=False)

def signal_handler(sig, frame):
    global EXITED_N_TIMES
    EXITED_N_TIMES += 1
    print('Received SIGINT, cleaning up ...')
    if EXITED_N_TIMES < 10:
        cleaner()
    os._exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGHUP, signal_handler)

def get_downloads_info(url: str) -> tuple[str, str]:
    """Get the downloads targets channel and id from the given url"""

    with yt_dlp.YoutubeDL(YDL_OPTS_DOWNLOADS_INFO) as ydl:
        info = ydl.extract_info(url, download=False)

        # ℹ️ ydl.sanitize_info makes the info json-serializable
        info_dict = ydl.sanitize_info(info)
        return info_dict.get('channel', url).lower(), info_dict.get('id', "")

def validate_path(path: str) -> str:
    """Replace invalid characters in path"""

    for char in set('/\?%*:|"<>~= '):
        path = path.replace(char, "")
    return path

def _download_all_latest(url: str, filter: str, download_archive: Path, latest: bool = True) -> None:
    """Downloads every video not processing and matching the regex filter or check if last N videos match the filter."""

    global YDL_OPTS_BULK_DOWNLOAD
    YDL_OPTS_BULK_DOWNLOAD['download_archive'] = download_archive.__str__()
    YDL_OPTS_BULK_DOWNLOAD['match_filter'] = yt_dlp.match_filter_func(f"{filter} & !is_post_live_dvr")
    YDL_OPTS_BULK_DOWNLOAD['outtmpl'] = {
        'default': f'{download_archive.parent}/%(title)s.%(ext)s',
        'description': f'{download_archive.parent}/%(title)s/%(title)s.%(ext)s',
        'infojson': f'{download_archive.parent}/%(title)s/%(title)s.%(ext)s',
        'thumbnail': f'{download_archive.parent}/%(title)s/%(title)s.%(ext)s'}

    if latest:
        YDL_OPTS_BULK_DOWNLOAD['playlistend'] = SCAN_LAST_N_VIDEOS
        YDL_OPTS_BULK_DOWNLOAD['playlistreverse'] = True
        YDL_OPTS_BULK_DOWNLOAD['outtmpl']['default'] = f'{download_archive.parent}/%(title)s-%(id)s".%(ext)s'
        YDL_OPTS_BULK_DOWNLOAD['match_filter'] = yt_dlp.match_filter_func(filter)

    with yt_dlp.YoutubeDL(YDL_OPTS_BULK_DOWNLOAD) as ydl:
        ydl.download(url)

def redownload_vid(id: str, path: Path) -> bool:
    """Downloads a video that is fully processed by youtube from given `id` and returns whether file was actually downloaded or not"""

    global YDL_OPTS_SINGLE_DOWNLOAD
    YDL_OPTS_SINGLE_DOWNLOAD['outtmpl'] = {'default': f'{path}/%(title)s.%(ext)s', 'pl_thumbnail': ''}
    with yt_dlp.YoutubeDL(YDL_OPTS_SINGLE_DOWNLOAD) as ydl:
        info_dict = ydl.extract_info(id, download=True)
        file_name = Path(ydl.prepare_filename(info_dict))
        return file_name.exists()

def check_for_new_video(url: str, regex: str = "title ~=.*", download_all: bool = False, dir: Path = None, download: bool = True) -> None:
    """Downloads all videos matching the desired filter, even if video is still being processed by Youtube.
       Uses the download archive file from yt-dlp to safe states if video is still being processed.
       Every video is downloaded in the first place, to have a (lower quality) version of the video even if Youtube deletes the video some time after its been uploaded.
       When file is done processing, it downloads the video again, now in better quality and deletes the old version.
       @param download_all use it when you want to download every file matching the regex and was not downloaded already.\n
       Note: Dont delete the archive txt file because it safes state which videos are already downloaded and which have already best quality available"""

    global download_archive, archive_existed
    channel_name, yt_id  = get_downloads_info(url)
    file_name = validate_path(f"{channel_name}_{yt_id}")
    download_archive = Path(f"{file_name if not dir else dir}/{file_name}.txt")

    # downloads all videos that match the regex if no files were downloaded
    # if there were already files downloaded, only the latest few videos are checked whether they match the regex
    if download:
        archive_existed = download_archive.exists()
        _download_all_latest(url, regex, download_archive, latest=archive_existed if not download_all else False)

    if not download_archive.exists():
        return
    
    with open(download_archive, "r") as fp:
        ids = fp.readlines()

    i = 0
    while i < len(ids):
        if i + 1 < len(ids) and ids[i + 1].startswith(POST_PROCESSING_DONE):
            i += 2
            continue
        if not archive_existed or download_all:
            ids.insert(i + 1, f"{POST_PROCESSING_DONE}\n")
            i += 2
            continue

        real_id = ids[i].rpartition(" ")[2].replace("\n", "")
        # check if video is now fully processed by Youtube and if so download it again and delete old video file
        if redownload_vid(real_id, download_archive.parent):
            for file in os.listdir(download_archive.parent):
                if file.find(real_id) != -1:
                    os.remove(f"{download_archive.parent}/{file}")
                    break
            ids.insert(i + 1, f"{POST_PROCESSING_DONE}\n")
            i += 1
        i += 1

    with open(download_archive, "w") as file:
        file.writelines(ids)

def cli_argument_parser():
    """`Returns` a ArgumentParser instance with specific arguments necessary for the program."""

    argParser = argparse.ArgumentParser(description='A script to automatically download YouTube Videos which match given filters.')
    argParser.add_argument("channel_url", type=str, help="The url of the video(s) source")
    argParser.add_argument("-n", "--name", default="title ~=.*", type=str, help="Match video's title with given Regex")
    argParser.add_argument("-a", "--download-all-matches", action="store_true", help="Download all videos that match the given regex")
    argParser.add_argument("-d", "--directory", type=Path, help="Directory where videos are safed to")
    argParser.add_argument("--skip-download", action="store_true", help="No files get downloaded")

    return argParser.parse_args()

def main():
    args = cli_argument_parser()
    if args.skip_download:
        return
    check_for_new_video(args.channel_url, args.name, args.download_all_matches, args.directory)

if __name__ == "__main__":
    main()