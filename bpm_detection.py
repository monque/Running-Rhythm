#!/usr/bin/env python
''' https://github.com/scaperot/the-BPM-detector-python '''
import argparse
import array
import wave

from scipy import signal
import numpy
import pywt
# import pdb
# import matplotlib.pyplot as plt

from datetime import timedelta


def read_wav(filename):

    # open file, get metadata for audio
    try:
        wf = wave.open(filename, 'rb')
    except IOError, e:
        print e
        return

    # typ = choose_type( wf.getsampwidth() ) #TODO: implement choose_type
    nsamps = wf.getnframes()
    assert(nsamps > 0)

    fs = wf.getframerate()
    assert(fs > 0)

    # calculate time length
    tlength = timedelta(0, seconds=float(nsamps) / fs)

    data = wf.readframes(nsamps)

    # manual parse
    # import struct
    # frame_ndx = 44100 * 5
    # frame_offset = frame_ndx * 4
    # val, = struct.unpack('<i', data[frame_offset:frame_offset + 4])
    # print 'unpack: %d' % val

    if False:
        samps = []
        for x in xrange(0, len(data), 4):
            val, = struct.unpack('<h', data[x:x + 2])
            samps.append(val)
    else:
        # read entire file and make into an array
        samps = list(array.array('i', data))

    # print ' samps: %d' % samps[frame_ndx]

    print 'Read', nsamps, 'samples from', filename
    try:
        assert(nsamps == len(samps))
    except AssertionError, e:
        print nsamps, "not equal to", len(samps)

    return samps, fs


# simple peak detection
def peak_detect(data):
    max_val = numpy.amax(abs(data))
    peak_ndx = numpy.where(data == max_val)
    if len(peak_ndx[0]) == 0:  # if nothing found then the max must be negative
        peak_ndx = numpy.where(data == -max_val)
    return peak_ndx


def bpm_detector(data, fs):
    cA = []
    cD = []
    correl = []
    cD_sum = []
    levels = 4
    max_decimation = 2**(levels-1)  # 8
    min_ndx = 60. / 220 * (fs / max_decimation)
    max_ndx = 60. / 40 * (fs / max_decimation)

    for loop in range(0, levels):
        cD = []
        # 1) DWT
        if loop == 0:
            [cA, cD] = pywt.dwt(data, 'db4')
            cD_minlen = len(cD)/max_decimation+1
            cD_sum = numpy.zeros(cD_minlen)
        else:
            [cA, cD] = pywt.dwt(cA, 'db4')

        # 2) Filter
        cD = signal.lfilter([0.01], [1 - 0.99], cD)

        # 4) Subtractargs.filename out the mean.

        # 5) Decimate for reconstruction later.
        cD = abs(cD[::(2**(levels-loop-1))])

        cD = cD - numpy.mean(cD)
        # 6) Recombine the signal before ACF
        #    essentially, each level I concatenate
        #    the detail coefs (i.e. the HPF values)
        #    to the beginning of the array
        cD_sum = cD[0:cD_minlen] + cD_sum

    # adding in the approximate data as well...
    cA = signal.lfilter([0.01], [1 - 0.99], cA)
    cA = abs(cA)
    cA = cA - numpy.mean(cA)
    cD_sum = cA[0:cD_minlen] + cD_sum

    # ACF
    correl = numpy.correlate(cD_sum, cD_sum, 'full')

    midpoint = len(correl) / 2
    correl_midpoint_tmp = correl[midpoint:]
    peak_ndx = peak_detect(correl_midpoint_tmp[min_ndx:max_ndx])
    peak_ndx_adjusted = peak_ndx[0]+min_ndx
    bpm = 60. / peak_ndx_adjusted * (fs / max_decimation)
    print bpm
    return bpm, correl


def dplay(samps, fs):
    group_flen = fs / 5
    group_left = group_flen
    group_cur = []
    group_data = []

    for s in samps:
        group_left -= 1
        group_cur.append(s)
        if group_left <= 0:
            avg = sum(group_cur) / len(group_cur)
            avg = abs(avg)
            group_data.append(avg)
            group_left = group_flen
            group_cur = []

    width = 120
    size = max(group_data) / width

    for s in group_data:
        bnum = s / size
        print '#' * bnum
    fuck


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Process .wav file to determine the Beats Per Minute.')
    parser.add_argument('--filename', required=True,
                        help='.wav file for processing')
    parser.add_argument('--window', type=float, default=3,
                        help='size of the the window (seconds) that will be scanned to determine the bpm.  Typically less than 10 seconds. [3]')

    args = parser.parse_args()
    samps, fs = read_wav(args.filename)
    # dplay(samps, fs)

    bpm, dummy = bpm_detector([0, 0, 200, 100, 0, 100] * 300, 150)
    fuck

    data = []
    correl = []
    bpm = 0
    nsamps = len(samps)
    window_samps = int(args.window*fs)
    window_ndx = int(1)  # current window we are processing
    samps_ndx = 0  # first sample in window_ndx
    max_window_ndx = nsamps / window_samps
    bpms = numpy.zeros(max_window_ndx)

    # iterate through all windows
    while window_ndx < max_window_ndx:

        # get a new set of samples
        data = samps[samps_ndx:samps_ndx+window_samps]
        if not ((len(data) % window_samps) == 0):
            raise AssertionError(str(len(data)))

        bpms[window_ndx], correl = bpm_detector(data, fs)

        # iterate at the end of the loop
        window_ndx = window_ndx + 1
        samps_ndx = samps_ndx+window_samps

    bpm = numpy.median(bpms)
    print 'Completed.  Estimated Beats Per Minute:', bpm

    # Plot display, but we dont need it
    # n = range(0, len(correl))
    # plt.plot(n, abs(correl))
    # plt.show(False); # plot non-blocking
    # time.sleep(10)
    # plt.close()
