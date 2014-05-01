from datetime import timedelta
import numpy
import scipy.signal
import struct
import wave


def wav_load(filename):
    attr = {
        'filename': filename,
    }

    wf = wave.open(filename, 'r')

    if wf.getnchannels() == 1:
        attr['channel'] = 'mono'
    else:
        attr['channel'] = 'stereo'

    # The standard audio file format for CDs, for example, is LPCM-encoded,
    # containing two channels of 44,100 samples per second, 16 bits per sample
    # http://en.wikipedia.org/wiki/WAV
    attr['samp_width'] = '%d bit' % (wf.getsampwidth() * 8)
    attr['frame_rate'] = wf.getframerate()
    attr['frame_count'] = wf.getnframes()
    attr['comp_type'] = wf.getcomptype()
    attr['comp_name'] = wf.getcompname()
    attr['time_length'] = timedelta(0, seconds=wf.getnframes() / wf.getframerate())

    for key in sorted(attr.keys()):
        val = attr[key]
        print key.ljust(20), val

    data = wf.readframes(attr['frame_count'])

    return data, wf


def main_readwrite():
    data, wf_src = wav_load('wav/wjgc.wav')
    # data, wf_src = parse_wav('sample.wav')

    # write
    wf_dst = wave.open('wav/dev.wav', 'w')
    wf_dst.setnchannels(1)
    wf_dst.setframerate(44100)
    wf_dst.setsampwidth(2)

    wdata = numpy.fromstring(data, dtype='<h')
    left = wdata[::2]
    right = wdata[1::2]
    wdata = (left - right) / 2
    wdata = scipy.signal.lfilter([0.01], [1 - 0.90], wdata)

    data = ''
    for x in wdata:
        data += struct.pack('<h', x)

    wf_dst.writeframes(data)
    wf_dst.close()


def parse_wav(filename):
    wf = open(filename, 'r')

    ck_id = wf.read(4)
    ck_len, = struct.unpack('<I', wf.read(4))
    subck_id = wf.read(4)
    print ck_id, ck_len, subck_id

    ck_id = wf.read(4)
    ck_len, = struct.unpack('<I', wf.read(4))
    ck_data = wf.read(ck_len)
    # Field             Length  Contents
    # wFormatTag        2       Format code
    # nChannels         2       Number of interleaved channels
    # nSamplesPerSec    4       Sampling rate (blocks per second)
    # nAvgBytesPerSec   4       Data rate
    # nBlockAlign       2       Data block size (bytes)
    # wBitsPerSample    2       Bits per sample
    # http://www-mmsp.ece.mcgill.ca/Documents/AudioFormats/WAVE/WAVE.html
    print struct.unpack('<HHIIHH', ck_data)
    print ck_id, ck_len

    ck_id = wf.read(4)
    ck_len, = struct.unpack('<I', wf.read(4))
    ck_data = wf.read(ck_len)
    print ck_id, ck_len

    return ck_data, wf


def write_fixfreq():
    wf_dst = wave.open('dst.wav', 'w')
    wf_dst.setnchannels(1)
    wf_dst.setframerate(44100)
    wf_dst.setsampwidth(1)

    def gen(freq, second, rate):
        track = ''

        interval = rate / freq
        sig_low = struct.pack('<B', 0)
        sig_flat = struct.pack('<B', 128)
        sig_high = struct.pack('<B', 255)

        i = 0
        sig_next = sig_high
        for x in xrange(0, second * rate):
            if i == 0:
                i = interval
                track += sig_next
                if sig_next == sig_high:
                    sig_next = sig_low
                else:
                    sig_next = sig_high
            else:
                i -= 1
                track += sig_flat
        return track


    wf_dst.writeframes(gen(10000, 5, 44100))
    wf_dst.close()


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
        print bpm
        bpms.append(bpm)

    wf.close()

    return numpy.median(bpms)


blist = [
    93, 65, 96, 60, 115, 69, 218, 183, 66, 105, 145,
    136, 98, 60, 68, 206, 82, 111, 105, 71, 65, 68,
    163, 74, 133, 100, 151, 96, 158, 100, 108, 176,
    74, 141, 203, 110, 80, 116, 95, 92, 99, 206,
    65, 151, 161, 74, 108, 68, 130, 161, 218, 219,
    84, 184, 70, 208, 140, 69, 68, 141, 135, 157,
    143, 108, 107, 202, 218, 220, 93, 65, 95, 60,
    117, 69, 92, 219, 93, 106, 111, 180, 92, 84,
    68, 186, 176, 70, 79, 219, 121, 66, 209, 110,
    70, 138, 135, 79, 162, 154, 128, 116, 64, 139,
    139, 140, 125, 114, 123, 63, 93, 139, 199, 139,
    122, 70, 151, 70, 60, 186, 78, 218, 184, 143,
    141, 140, 139, 193, 133, 168, 188, 82, 83, 62,
    93, 96, 219, 217
]
import bpm
print bpm.blist_analyze(blist, verbose=True)
