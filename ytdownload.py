import os, re
from time import sleep
from pytube import YouTube, Playlist, cipher
from moviepy.editor import *
import argparse
from multiprocessing import Process, Queue, cpu_count, freeze_support


# Fix proposed by amckee & SamSpiri (see https://github.com/pytube/pytube/issues/1954#issuecomment-2227977322)
def get_throttling_function_name(js: str) -> str:
    """Extract the name of the function that computes the throttling parameter.

    :param str js:
        The contents of the base.js asset file.
    :rtype: str
    :returns:
        The name of the function used to compute the throttling parameter.
    """
    function_patterns = [
        # https://github.com/ytdl-org/youtube-dl/issues/29326#issuecomment-865985377
        # https://github.com/yt-dlp/yt-dlp/commit/48416bc4a8f1d5ff07d5977659cb8ece7640dcd8
        # var Bpa = [iha];
        # ...
        # a.C && (b = a.get("n")) && (b = Bpa[0](b), a.set("n", b),
        # Bpa.length || iha("")) }};
        # In the above case, `iha` is the relevant function name
        r'a\.[a-zA-Z]\s*&&\s*\([a-z]\s*=\s*a\.get\("n"\)\)\s*&&\s*' r"\([a-z]\s*=\s*([a-zA-Z0-9$]+)(\[\d+\])?\([a-z]\)",
        r"\([a-z]\s*=\s*([a-zA-Z0-9$]+)(\[\d+\])\([a-z]\)",
    ]
    # logger.debug('Finding throttling function name')
    for pattern in function_patterns:
        regex = re.compile(pattern)
        function_match = regex.search(js)
        if function_match:
            # logger.debug("finished regex search, matched: %s", pattern)
            if len(function_match.groups()) == 1:
                return function_match.group(1)
            idx = function_match.group(2)
            if idx:
                idx = idx.strip("[]")
                array = re.search(r"var {nfunc}\s*=\s*(\[.+?\]);".format(nfunc=re.escape(function_match.group(1))), js)
                if array:
                    array = array.group(1).strip("[]").split(",")
                    array = [x.strip() for x in array]
                    return array[int(idx)]

    raise re.RegexMatchError(caller="get_throttling_function_name", pattern="multiple")


cipher.get_throttling_function_name = get_throttling_function_name

processes = {}
max_proccesses = max(cpu_count() / 2, 1)
queue = Queue()


def cleanup_parallel_download(failed_downloads: list):
    event = None
    try:
        event = queue.get(False)
    except:
        pass

    if not event:
        return

    task_id, success, video_url = event
    if task_id in processes:
        print(f">Task {task_id}: download completed with success = {success}")
        if not success:
            failed_downloads.append(video_url)
        processes[task_id].join()
        del processes[task_id]


def start_parallel_download(task_id: str, video: YouTube, path: os.path):
    if len(processes) < max_proccesses:
        process = Process(target=download_run, args=(task_id, queue, video, path))
        process.start()
        processes[task_id] = process
        print(f">Task {task_id}: download started! (Maximum number of processes {max_proccesses})")
        return True
    return False


def mp4_to_mp3(mp4, mp3):
    converter = AudioFileClip(mp4)
    converter.write_audiofile(mp3, logger=None)
    converter.close()


def download_run(task_id: str, ipc: Queue, video: YouTube, path: os.path):
    try:
        print(f'>Task {task_id}: Downloading: "{video.title}" from "{video.embed_url}"')
        video.streams.filter()
        stream = video.streams.get_audio_only(subtype="mp4")
        stream.download(output_path=path, skip_existing=True, max_retries=2)
        mp4 = os.path.join(path, stream.default_filename)
        mp3 = os.path.join(path, os.path.splitext(stream.default_filename)[0] + ".mp3")
        print(f'>Task {task_id}: Converting "{mp4}" to "{mp3}"')
        mp4_to_mp3(mp4, mp3)
        print(f">Task {task_id}: Success!")
        ipc.put((task_id, True, video.embed_url))
    except Exception as err:
        print(f">Task {task_id}: Failed! {err}")
        ipc.put((task_id, False, video.embed_url))


def download_playlist_audio(link, playlistname="download"):
    try:
        ytPlaylist = Playlist(link)
        if ytPlaylist.length == 0:
            return False
    except Exception as err:
        print(">Could not load as playlist...")
        print(f">{err}, {type(ytPlaylist)}")
        return False

    path = os.path.join(os.getcwd(), playlistname)
    try:
        os.mkdir(path)
    except FileExistsError:
        pass

    failed = []
    downloading = 0
    while downloading < len(ytPlaylist.videos):
        video = ytPlaylist.videos[downloading]
        if start_parallel_download(str(downloading), video, path):
            downloading += 1
        else:
            sleep(1.0)
        cleanup_parallel_download(failed)

    print(">Waiting for all downloads to finish")
    while len(processes) > 0:
        cleanup_parallel_download(failed)
    print(f">Failed Downloads: {failed}")


def download_video(link, playlistname="download"):
    try:
        video = YouTube(link)
    except:
        return False

    path = os.path.join(os.getcwd(), playlistname)
    try:
        os.mkdir(path)
    except FileExistsError:
        pass

    try:
        stream = video.streams.get_highest_resolution()
        print(f'>Downloading: "{video.title}" from "{video.embed_url}"')
        stream.download(output_path=path, skip_existing=True, max_retries=3)
        print(">Success!")
    except:
        print(">Failed!")
    return True


if __name__ == "__main__":
    if sys.platform.startswith("win"):
        freeze_support()
    parser = argparse.ArgumentParser(description="Youtube Video or Playlist downloader")
    parser.add_argument("--link", action="store", help="Link to a video or playlist")
    parser.add_argument("--out", action="store", default="download", help="Directory, where to store downloaded files")
    args = parser.parse_args()
    link = args.link or input("Enter the YouTube playlist/video URL: ")
    download_playlist_audio(link, args.out) or download_video(link, args.out)
