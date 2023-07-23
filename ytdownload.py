import os
from time import sleep
from pytube import YouTube, Playlist
from moviepy.editor import *
import argparse
from multiprocessing import Process, Queue, cpu_count, freeze_support

processes = {}
max_proccesses = cpu_count()
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
