''' https://github.com/scaperot/the-BPM-detector-python '''
import numpy
import pywt
import scipy.signal


def peak_detect(data):
    max_val = numpy.amax(abs(data))
    peak_ndx = numpy.where(data == max_val)
    if len(peak_ndx[0]) == 0:  # if nothing found then the max must be negative
        peak_ndx = numpy.where(data == -max_val)
    return peak_ndx


def detect(data, fs):
    levels = 4
    max_decimation = 2 ** (levels - 1)  # 8
    min_ndx = 60. / 220 * (fs / max_decimation)
    max_ndx = 60. / 40 * (fs / max_decimation)

    for loop in range(0, levels):
        cD = []
        # 1) DWT
        if loop == 0:
            cA, cD = pywt.dwt(data, 'db4')
            cD_minlen = len(cD) / max_decimation + 1
            cD_sum = numpy.zeros(cD_minlen)
        else:
            cA, cD = pywt.dwt(cA, 'db4')

        # 2) Filter
        cD = scipy.signal.lfilter([0.01], [1 - 0.99], cD)

        # 4) Subtractargs.filename out the mean.

        # 5) Decimate for reconstruction later.
        cD = abs(cD[::(2 ** (levels - loop - 1))])

        cD = cD - numpy.mean(cD)
        # 6) Recombine the signal before ACF
        #    essentially, each level I concatenate
        #    the detail coefs (i.e. the HPF values)
        #    to the beginning of the array
        cD_sum = cD[0:cD_minlen] + cD_sum

    # adding in the approximate data as well...
    cA = scipy.signal.lfilter([0.01], [1 - 0.99], cA)
    cA = abs(cA)
    cA = cA - numpy.mean(cA)
    cD_sum = cA[0:cD_minlen] + cD_sum

    # ACF
    correl = numpy.correlate(cD_sum, cD_sum, 'full')

    midpoint = len(correl) / 2
    correl_midpoint_tmp = correl[midpoint:]
    peak_ndx = peak_detect(correl_midpoint_tmp[min_ndx:max_ndx])
    peak_ndx_adjusted = peak_ndx[0] + min_ndx
    bpm = 60. / peak_ndx_adjusted * (fs / max_decimation)

    return float(bpm)


if __name__ == '__main__':
    # Option
    bar_shape = [1, 1, 8, 1]
    bpm = 166
    framerate = 1000
    window = 3

    # Generate bar data
    bar_time = 60. / bpm
    bar_frame = int(bar_time * framerate)
    bar_multi = bar_frame / len(bar_shape)
    bar_data = []
    for x in bar_shape:
        bar_data += [x] * bar_multi

    # Padding
    pad = bar_frame - len(bar_data)
    bar_data += [0] * pad

    # Generate
    wdata = bar_data * int(window / bar_time)

    # Detect
    bpm = detect(wdata, framerate)

    print '      window: %d' % window
    print '   framerate: %d' % framerate
    print '   data size: %d' % len(wdata)
    print 'generate BPM: %d' % bpm
    print 'detector BPM: %.2f' % bpm
