import argparse
import wave

import numpy

from detector_dwt import detect


def cal_file(filename, window=3):
    bpm_table = {}

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

        # detect
        try:
            bpm = detect(wdata, framerate)
        except:
            continue
        if bpm in bpm_table:
            bpm_table[bpm] += 1
        else:
            bpm_table[bpm] = 1

    wf.close()

    # result
    tolerance = 3
    result = None
    for key, val in bpm_table.items():
        if key > 200:
            continue

        total = 0
        for k in range(key - tolerance, key + tolerance + 1):
            if k in bpm_table:
                la = 1. * abs(key - k) / (tolerance + 1)
                la = 1 - la
                total += 1. * bpm_table[k] * la
        if result is None or result['freq'] < total:
            result = {
                'bpm': key,
                'freq': int(total),
            }
    result['ratio'] = 100. * result['freq'] / sum(bpm_table.values())

    return result['bpm'], int(result['ratio'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Process .wav file to determine the Beats Per Minute.')
    parser.add_argument('--file', required=True,
                   help='.wav file for processing')
    parser.add_argument('--window', type=float, default=3,
                   help='size of the the window (seconds) that will be scanned to determine the bpm.  Typically less than 10 seconds. [3]')
    args = parser.parse_args()

    filename = args.file
    bpm, ratio = cal_file(filename)
    print bpm, ratio
