#! /usr/bin/env python
import argparse
import wave

import numpy

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


def detect_wav(filename, window=3, overlap=0, down_factor=1, rmvocal=False, verbose=False):
    wf = wave.open(filename, 'rb')
    nchannels, sampwidth, framerate, nframes = wf.getparams()[:4]

    odata = []
    blist = []
    step = window * framerate
    for x in range(0, nframes, step):
        # Read window then convert
        wdata = numpy.fromstring(wf.readframes(step), dtype='<i%d' % sampwidth)

        # Extract sample
        if rmvocal and nchannels == 2:
            # remove vocal by mix invert channel
            wdata = (wdata[::2] - wdata[1::2]) / 2
        else:
            # only detect first channel
            wdata = wdata[::nchannels]

        # Break when sample too short
        if len(wdata) < step:
            break

        # Overlap
        if overlap > 0:
            wdata = numpy.concatenate((odata, wdata))
            odata = wdata[-(overlap * framerate):]

        # Downsample
        if down_factor > 1:
            wdata = wdata[::down_factor]

        # Detect
        try:
            bpm = detect(wdata, framerate / down_factor)
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
    # Argument
    parser = argparse.ArgumentParser(description='Process .wav file to determine the Beats Per Minute.')
    parser.add_argument('file', type=str, nargs='+', help='.wav file for processing')
    parser.add_argument('--verbose', '-v', action='store_true')
    # Detect
    parser.add_argument('--window', '-w', type=int, default=3, metavar='S', help='size of the window (seconds) that will be scanned to determine the bpm. Default: 3')
    parser.add_argument('--overlap', '-o', type=int, default=0, metavar='S', help='size of the overlap of window (seconds). Default: 0')
    parser.add_argument('--rmvocal', action='store_true', help='[EXPERIMENTAL] try to remove vocal by mixing left channel with inverted right channel. Default: False')
    parser.add_argument('--downsample', type=int, default=1, metavar='N', help='[EXPERIMENTAL] downsample by an integer factor that will increase speed. Default: 1')
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
            'down_factor': args.downsample,
            'rmvocal': False,
            'verbose': args.verbose,
        }
        blist = detect_wav(filename, **options)
        if args.rmvocal:
            options['rmvocal'] = True
            blist += detect_wav(filename, **options)

        # Select
        bpm, proportion = select_bpm(blist, args.tolerance, args.verbose)

        if op_showfile:
            print '%3d %3d %s' % (bpm, proportion, filename)
        else:
            print '%3d %3d' % (bpm, proportion)
