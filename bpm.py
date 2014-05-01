#! /usr/bin/env python
import argparse
import wave

import numpy

from detector_dwt import detect


BPM_MIN = 100
BPM_MAX = 200
BTABLE = {x: 0 for x in range(BPM_MIN, BPM_MAX + 1)}


def blist_analyze(blist, tolerance=3, verbose=False):
    if not blist:
        raise ValueError('Empty BPM list')

    # Convert to dict
    btable = BTABLE.copy()
    for bpm in blist:
        for b in [bpm, bpm * 2, bpm / 2]:  # Multiple
            if b in btable:
                btable[b] += 1

    # Calculate weight
    final_bpm = final_weight = 0
    for bpm in sorted(btable.keys()):
        # Tolerance
        wlist = []
        for b in range(bpm - tolerance, bpm + tolerance + 1):
            if b not in btable:
                continue
            factor = 1 - 1. * abs(bpm - b) / (tolerance + 1)
            wlist.append(factor * btable[b])
        weight = sum(wlist)

        if verbose and weight > 0:
            print '%3d %5.2f %s' % (bpm, weight, wlist)

        if weight > final_weight:
            final_bpm = bpm
            final_weight = weight

    final_weightp = 100. * final_weight / len(blist)
    return final_bpm, int(final_weightp)


def detect_wav(filename, window=3, downsample=1, invertmix=False, verbose=False):
    wf = wave.open(filename, 'rb')
    nchannels, sampwidth, framerate, nframes = wf.getparams()[:4]

    # Data type
    if sampwidth == 2:
        dtype  = '<h'
    elif sampwidth == 4:
        dtype  = '<i'

    # Process by window
    blist = []
    step = window * framerate
    for x in range(0, nframes, step):
        wdata = numpy.fromstring(wf.readframes(step), dtype=dtype)
        if invertmix and nchannels == 2:  # try to remove vocal
            left = wdata[::2]
            right = wdata[1::2]
            wdata = (left - right) / 2
        else:
            wdata = wdata[::nchannels]  # only detect first channel

        # Break when wdata too short
        if len(wdata) < step:
            break

        # Downsample
        if downsample > 1:
            # wdata = scipy.signal.decimate(wdata, downsample)
            wdata = wdata[::downsample]

        # Detect
        try:
            bpm = detect(wdata, framerate / downsample)
        except ValueError as e:
            print '%5.1f%% error: %s' % (100. * x / nframes, e)
            continue
        else:
            blist.append(bpm)
            if verbose:
                print '%5.1f%% %d' % (100. * x / nframes, bpm)

    wf.close()
    return blist


if __name__ == '__main__':
    # Arguments
    parser = argparse.ArgumentParser(description='Process .wav file to determine the Beats Per Minute.')
    parser.add_argument('file', type=str, nargs='+',
        help='.wav file for processing')
    parser.add_argument('--window', '-w', type=int, default=3, metavar='S',
        help='size of the the window (seconds) that will be scanned to determine the bpm. Default: 3')
    parser.add_argument('--tolerance', '-t', type=int, default=3, metavar='N',
        help='tolerance using in window BPM result analyze. Default: 3')
    parser.add_argument('--invertmix', action='store_true',
        help='[EXPERIMENTAL] mix left channel with inverted right channel, it will remove vocal to improve detect. Default: False')
    parser.add_argument('--downsample', type=int, default=1, metavar='Q',
        help='[EXPERIMENTAL] downsample to RATE to improve speed. Default: 1')
    parser.add_argument('--verbose', '-v', action='store_true')
    args = parser.parse_args()

    # Loop file list
    op_showfile = len(args.file) > 1
    for filename in args.file:
        if args.verbose:
            print 'process %s' % filename

        # Detect
        blist = detect_wav(filename, args.window, args.downsample, False, args.verbose)
        if args.invertmix:
            blist += detect_wav(filename, args.window, args.downsample, True, args.verbose)

        # Analyze
        bpm, weightp = blist_analyze(blist, args.tolerance, args.verbose)

        if op_showfile:
            print '%3d %3d %s' % (bpm, weightp, filename)
        else:
            print '%3d %3d' % (bpm, weightp)
