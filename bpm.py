import argparse
import wave

import numpy

from detector_dwt import detect


def cal_file(filename, window=3):
    bpms = []

    wf = wave.open(filename, 'rb')
    nchannels, sampwidth, framerate, nframes = wf.getparams()[:4]

    # data type
    if sampwidth == 2:
        dtype  = '<h'
    elif sampwidth == 4:
        dtype  = '<i'

    step = window * framerate
    for x in range(0, nframes, step):
        wdata = numpy.fromstring(wf.readframes(step), dtype=dtype)[::nchannels]  # only detect first channel

        # break when wdata too short
        if len(wdata) < step:
            break

        bpm = detect(wdata, framerate)
        bpms.append(bpm)

    wf.close()

    return numpy.median(bpms)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Process .wav file to determine the Beats Per Minute.')
    parser.add_argument('--file', required=True,
                   help='.wav file for processing')
    parser.add_argument('--window', type=float, default=3,
                   help='size of the the window (seconds) that will be scanned to determine the bpm.  Typically less than 10 seconds. [3]')
    args = parser.parse_args()

    filename = args.file
    bpm = cal_file(filename)
    print bpm
