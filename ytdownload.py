import os
from pytube import YouTube, Playlist
from moviepy.editor import *
import argparse


def mp4_to_mp3(mp4, mp3):
    converter = AudioFileClip(mp4)
    converter.write_audiofile(mp3)
    converter.close()


def download_playlist_audio(link, playlistname="download"):
    try:
        ytPlaylist = Playlist(link)
        if ytPlaylist.length() == 0:
            print('>Not a playlist')
            return False

    except Exception as err:
        print('>Could not load playlist...')
        print(f'>{err}')
        return False

    path = os.path.join(os.getcwd(), playlistname)
    try:
        os.mkdir(path)
    except FileExistsError:
        pass

    downloaded = []
    failed = []
    for video in ytPlaylist.videos:
        try:
            print(f'>Downloading: "{video.title}" from "{video.embed_url}"')
            video.streams.filter()
            stream = video.streams.get_audio_only(subtype='mp4')
            stream.download(output_path=path,
                            skip_existing=True, max_retries=2)
            mp4 = os.path.join(path, stream.default_filename)
            mp3 = os.path.join(path, os.path.splitext(
                stream.default_filename)[0] + '.mp3')
            print(f'>Converting "{mp4}" to "{mp3}"')
            mp4_to_mp3(mp4, mp3)
            print('>Success!')
        except Exception as err:
            print(f'>Failed! {err}')
            failed.append(video)
    print(
        f'>Failed to download {len(failed)}/{len(ytPlaylist.videos)} videos:')
    for video in failed:
        print(video.embed_url)
    return True


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
        print('>Success!')
    except:
        print(">Failed!")
    return True


parser = argparse.ArgumentParser(
    description='Youtube Video or Playlist downloader')
parser.add_argument('--link', action='store',
                    help='Link to a video or playlist')
parser.add_argument('--out', action='store', default='download',
                    help='Directory, where to store downloaded files')
args = parser.parse_args()
link = args.link or input("Enter the YouTube playlist/video URL: ")
download_playlist_audio(link, args.out) or download_video(link, args.out)
