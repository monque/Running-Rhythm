#! /usr/bin/env python
import argparse
import wave

import numpy

from detector_dwt import detect


def blist_analyze(blist, tolerance=3, verbose=False):
    if not blist:
        raise ValueError('Empty BPM list')

    # Convert to dict
    btable = {}
    for x in blist:
        if x in btable:
            btable[x] += 1
        else:
            btable[x] = 1

    # Sum by tolerance
    final_bpm = final_weight = 0
    for bpm in sorted(btable.keys()):
        occu = btable[bpm]
        wlist = []
        for b in range(bpm - tolerance, bpm + tolerance + 1):
            if b not in btable:
                continue
            factor = 1 - 1. * abs(bpm - b) / (tolerance + 1)
            wlist.append(factor * btable[b])
        weight = sum(wlist)

        if verbose:
            print '%3d %5.2f %s' % (bpm, weight, wlist)

        if weight > final_weight:
            final_bpm = bpm
            final_weight = weight

    final_weightp = 100. * final_weight / len(blist)
    return final_bpm, int(final_weightp)


def detect_wav(filename, window=3, invertmix=False, verbose=False):
    wf = wave.open(filename, 'rb')
    nchannels, sampwidth, framerate, nframes = wf.getparams()[:4]

    # Data type
    if sampwidth == 2:
        dtype  = '<h'
    elif sampwidth == 4:
        dtype  = '<i'

    # Scan data by window
    blist = []
    step = window * framerate
    for x in range(0, nframes, step):
        wdata = numpy.fromstring(wf.readframes(step), dtype=dtype)
        if invertmix and nchannels == 2:  # try to remove vocal by mixing left, invert right
            left = wdata[::2]
            right = wdata[1::2]
            wdata = left - right
        else:
            wdata = wdata[::nchannels]  # only detect first channel

        # Break when wdata too short
        if len(wdata) < step:
            break

        # Detect
        try:
            bpm = detect(wdata, framerate)
        except:
            continue
        blist.append(bpm)

        if verbose:
            print '%5.1f%% %d' % (100. * x / nframes, bpm)

    wf.close()
    return blist


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Process .wav file to determine the Beats Per Minute.')
    parser.add_argument('file', type=str, nargs='+',
        help='.wav file for processing')
    parser.add_argument('--window', '-w', type=int, default=3, metavar='S',
        help='size of the the window (seconds) that will be scanned to determine the bpm. Default: 3')
    parser.add_argument('--tolerance', '-t', type=int, default=3, metavar='N',
        help='tolerance using in window BPM result analyze. Default: 3')
    parser.add_argument('--invertmix', action='store_true',
        help='[EXPERIMENTAL] mix left channel with inverted right channel, it will remove vocal to improved detect. Default: False')
    parser.add_argument('--verbose', '-v', action='store_true')
    args = parser.parse_args()

    op_showfile = len(args.file) > 1
    for filename in args.file:
        if args.verbose:
            print 'process %s' % filename

        blist = detect_wav(filename, args.window, args.invertmix, args.verbose)
        bpm, weightp = blist_analyze(blist, args.tolerance, args.verbose)

        if op_showfile:
            print '%3d %3d %s' % (bpm, weightp, filename)
        else:
            print '%3d %3d' % (bpm, weightp)
