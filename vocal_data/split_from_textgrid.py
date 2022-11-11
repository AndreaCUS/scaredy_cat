
"""
This script will split longer .wav audio files into mulltiple .wav files,
using a TextGrid files where each individual vocalization or segment has been labelled.

How to run the script:

python3 split_from_textgrid.py folder_path label

...where 'folder_path' is the full path to a directory which contains a series of
.wav files and their corresponding .TextGrid files.
... where 'label' is the label used to tag the vocalizations or segments of interest
in the TextGrid

Expected outcome:
For each .wav + textgrid pairing, a new folder will be writen which will contain
 a .wav clip for each segment that was labelled in the TextGrid

Notes:
Occasionally you'll get an error saying something about failing to parse.
This usually means there's a TextGrid file that starts with a non utf-8 characer.
You can simply open that TextGrid file with a text editor and delete the
offending character.

I also sometimes get an error saying
"RuntimeWarning: Couldn't find ffmpeg or avconv - defaulting to ffmpeg, but may
not work"
This appears to be inoffensive.

"""

import sys
import os
from pydub import AudioSegment

def split_wav_file(folder, filename, start_s, end_s, split_filename):
    """
    Make a new audio file from a longer audio file, using start and end timestamp
    """

    start_ms = start_s * 1000
    end_ms = end_s * 1000
    audio = AudioSegment.from_wav(folder + "/" + filename)
    split_audio = audio[start_ms:end_ms]
    split_audio.export(
        folder + "/" + filename.rstrip(".wav") + "/" + split_filename,
        format="wav",
    )


def read_textgrid(filepath, label):
    """
    Read TextGrid file, return timestamps of individual vocalizations of interest.

    Args:
        filepath (str): File path of the Textgrid.

    Returns:
        time_list: A list of dictionaries, containing start and end time
                    for each tagged vocalization that was found.

    Raises:
        Exception: Occasionally there may be an error due to failure to parse the TextGrid.
        This usually means there's a file that starts with a non utf-8 characer.
        You can simply open that TextGrid file with a text editor and delete the
        offending character (it was so rare that I just handled it by hand).

    """
    # print("Processing file ", filepath)
    time_list = []

    with open(filepath) as file:
        try:
            content = file.readlines()
        except:
            print(
                "**** Problem processing file {}. Check first characters of file.".format(
                    filepath
                )
            )
    for index, line in enumerate(content):
        # each vocalization of interest was marked "m" in the TextGrid
        if ("intervals [" in line) and ('text = "{}"'.format(label) in content[index + 3]):
            start = float(content[index + 1].lstrip("xmin = ").strip(" \n"))
            end = float(content[index + 2].lstrip("xmax = ").strip(" \n"))
            times = {"start_time": start, "end_time": end}
            time_list.append(times)
    return time_list


def extract_files_from_grid(folder, file, label):
    """
    Given one .wav and one .TextGrid file, extract all segments of interest
    to new audio files.

    Args:
        folder (str): folder where audio and TextGrid files are
        file (str): filename of audio file to split
        label (str): label used to identify sounds of interest in TextGrid
    """

    textgrid_filename = folder + "/" + file.strip(".wav") + ".TextGrid"
    time_list = read_textgrid(textgrid_filename, label)
    for index, segment in enumerate(time_list):
        new_name = file.strip(".wav") + "_" + str(index) + ".wav"
        split_wav_file(folder, file, segment["start_time"], segment["end_time"], new_name)


def main():
    folder = sys.argv[1]
    label = sys.argv[2]
    for file in os.listdir(folder):
        if file.endswith(".wav"):
            os.makedirs(folder + "/" + file.strip(".wav"), exist_ok=True)
            extract_files_from_grid(folder, file, label)


if __name__ == "__main__":
    main()
