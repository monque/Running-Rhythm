#! /usr/bin/env python
import argparse
import random
import wave

import numpy
import scipy.signal

from detector_dwt import detect


BPM_MIN = 100
BPM_MAX = 200
BTABLE = {x: 0 for x in range(BPM_MIN, BPM_MAX + 1)}


def select_bpm(blist, tolerance=3, verbose=False):
    if not blist:
        raise ValueError('empty BPM list')

    # Duplicate with multiple
    blen = len(blist)
    for bpm in blist[:]:
        blist.append(bpm * 2)
        blist.append(bpm / 2)

    # Convert to table
    btable = BTABLE.copy()
    for bpm in blist:
        if bpm in btable:
            btable[bpm] += 1

    final_bpm = final_weight = 0
    for bpm in sorted(btable.keys()):
        # Calculate weight
        wlist = []
        for b in range(bpm - tolerance, bpm + tolerance + 1):
            if b not in btable:
                continue
            factor = 1 - 1. * abs(bpm - b) / (tolerance + 1)
            wlist.append(factor * btable[b])
        weight = sum(wlist)

        # Set final
        if weight > final_weight:
            final_bpm = bpm
            final_weight = weight

        if verbose and weight > 0:
            print '%3d %5.2f %s' % (bpm, weight, wlist)

    final_proportion = int(100 * final_weight / blen)
    return final_bpm, final_proportion


def detect_wav(filename, window=3, overlap=0, rmvocal=False, lowpass=False,
               down_factor=1, skip_window=0, verbose=False):
    wf = wave.open(filename, 'rb')
    nchannels, sampwidth, framerate, nframes = wf.getparams()[:4]

    # Options init
    if overlap > 0:
        odata = []
    if lowpass:
        f = scipy.signal.firwin(numtaps=20, cutoff=8, nyq=20)

    blist = []
    window_nframes = window * framerate
    window_count = nframes / window_nframes
    for window_id in range(0, window_count):
        # Skip window
        if skip_window > 0 and random.randrange(skip_window) == 0:
            continue

        # Read window then convert
        wdata = numpy.fromstring(wf.readframes(window_nframes), dtype='<i%d' % sampwidth)

        # Mix into one channel
        if rmvocal and nchannels == 2:
            # remove vocal by mixing invert channel
            wdata = (wdata[::2] - wdata[1::2]) / 2
        else:
            # only first channel
            wdata = wdata[::nchannels]

        # Break if sample too short
        if len(wdata) < window_nframes:
            break

        # Overlap
        if overlap > 0:
            wdata = numpy.concatenate((odata, wdata))
            odata = wdata[-(overlap * framerate):]

        # Downsample
        if down_factor > 1:
            wdata = wdata[::down_factor]

        # Low pass filter
        if lowpass:
            wdata = scipy.signal.lfilter(f, [1.0], wdata)

        # Detect
        try:
            bpm = detect(wdata, framerate / down_factor)
        except ValueError as e:
            print '%5.1f%% error: %s' % (100. * window_id / window_count, e)
            continue
        else:
            blist.append(bpm)
            if verbose:
                print '%5.1f%% %d' % (100. * window_id / window_count, bpm)

    wf.close()
    return blist


if __name__ == '__main__':
    # Argument
    parser = argparse.ArgumentParser(description='Process .wav file to determine the Beats Per Minute.')
    parser.add_argument('file', type=str, nargs='+', help='.wav file for processing')
    parser.add_argument('--verbose', '-v', action='store_true')
    # Detect
    parser.add_argument('--window', '-w', type=int, default=3, metavar='S', help='size of the window (seconds) that will be scanned to determine the bpm. Default: 3')
    parser.add_argument('--overlap', '-o', type=int, default=0, metavar='S', help='size of the overlap of window (seconds). Default: 0')
    parser.add_argument('--rmvocal', action='store_true', help='remove vocal by mixing left with inverted right channel. Default: False')
    parser.add_argument('--lowpass', action='store_true', help='use Low Pass Filter to cut treble sound. Default: False')
    parser.add_argument('--downsample', type=int, default=1, metavar='N', help='downsample by an integer factor that will increase speed. Default: 1')
    parser.add_argument('--skipwindow', type=int, default=0, metavar='N', help='skip window detecting every N times. Default: 0')
    # Select
    parser.add_argument('--tolerance', '-t', type=int, default=3, metavar='N', help='tolerance using in select final BPM. Default: 3')
    args = parser.parse_args()

    # Process file list
    op_showfile = len(args.file) > 1
    for filename in args.file:
        if args.verbose:
            print 'process %s' % filename

        # Detect
        options = {
            'window': args.window,
            'overlap': args.overlap,
            'rmvocal': args.rmvocal,
            'lowpass': args.lowpass,
            'down_factor': args.downsample,
            'skip_window': args.skipwindow,
            'verbose': args.verbose,
        }
        blist = detect_wav(filename, **options)

        # Select
        bpm, proportion = select_bpm(blist, args.tolerance, args.verbose)

        if op_showfile:
            print '%3d %3d %s' % (bpm, proportion, filename)
        else:
            print '%3d %3d' % (bpm, proportion)
