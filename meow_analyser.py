"""
This script will loop through a folder that contains subfolders with wav files,
analyze each of the .wav files, and output the data to a single .csv file

Run this script like so:
python3 vocal.py "/dir/where/folders_are"

"""

import os
import sys
import csv
import parselmouth
from parselmouth.praat import call

# Set min/max pitch for analysis
MIN_F0_ANALYSIS = 300
MAX_F0_ANALYSIS = 1500


class MeowAnalyser(object):
    def __init__(self, file_path):
        self.file_path = file_path
        self.file_name = os.path.basename(self.file_path)
        self.meow = parselmouth.Sound(self.file_path)
        self.f0min = MIN_F0_ANALYSIS
        self.f0max = MAX_F0_ANALYSIS

    def analyse_meow(self):
        pitch = call(self.meow, "To Pitch", 0.0, self.f0min, self.f0max)
        mean_f0 = call(pitch, "Get mean", 0, 0, "Hertz")
        max_f0 = call(pitch, "Get maximum", 0, 0, "Hertz", "Parabolic")
        min_f0 = call(pitch, "Get minimum", 0, 0, "Hertz", "Parabolic")
        diff_f0 = max_f0 - min_f0
        stdev_f0 = call(pitch, "Get standard deviation", 0, 0, "Hertz")
        duration = call(pitch, "Get end time")
        return [self.file_name, mean_f0, max_f0, min_f0, diff_f0, stdev_f0, duration]


def loop_meow_files(directory, results_file):
    """
    Loops through a directory of directories, analyses the .wav files within.
    Appends results of each analysed sound to a file.

    Args:
        directory (str): dir containing subfolders of sound files
        results_file (str): .csv results file
    """

    for root, d_names, f_names in os.walk(directory):
        for subdir in d_names:
            for file in os.listdir(os.path.join(root, subdir)):
                filename = file
                file_parent_path = os.path.join(root, subdir)
                file = os.path.join(file_parent_path, file)

                if filename.endswith(".wav"):
                    meow = MeowAnalyser(file)
                    file_results = meow.analyse_meow()
                    write_to_file(results_file, file_results)


def write_to_file(file_path, row):
    """
    Writes a row to a .csv file

    Args:
        file_path (str): path of file
        row (list): data to write to new row
    """

    with open(file_path, "a") as file:
        writer = csv.writer(file)
        writer.writerow(row)


def main():
    directory = sys.argv[1]
    results_file = directory + "/" + "meow_results.csv"

    file_header = [
        "filename",
        "meanF0Hz",
        "maxF0Hz",
        "minF0Hz",
        "diffF0Hz",
        "stdevF0Hz",
        "duration",
    ]
    write_to_file(results_file, file_header)

    loop_meow_files(directory, results_file)


if __name__ == "__main__":
    main()
