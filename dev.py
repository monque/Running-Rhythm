from datetime import timedelta
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
    data, wf_src = wav_load('sample.wav')
    # data, wf_src = parse_wav('sample.wav')

    # write
    wf_dst = wave.open('dst.wav', 'w')
    wf_dst.setnchannels(2)
    wf_dst.setframerate(44100)
    wf_dst.setsampwidth(2)

    track = ''
    for x in range(0, 10 * 44100):
        fdata = data[x * 4:x * 4 + 4]
        # fval, = struct.unpack('<h', fdata)
        # print '%5d' % (fval),

        # reduce bit-depth
        # fval = fval / 256 + 128

        # fdata = struct.pack('<B', fval)
        track += fdata

        # dval, = struct.unpack('<b', fdata)
        # print '%5d' % (dval)

    wf_dst.writeframes(track)
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


def test_detector():
    import numpy
    from detector_dwt import detect

    bpms = []
    window = 3

    wf = wave.open('dst.wav', 'r')
    nchannels, sampwidth, framerate, nframes = wf.getparams()[:4]

    start = 0
    step = window * framerate
    while start < nframes:
        data = wf.readframes(step)
        wdata = numpy.fromstring(data, dtype='<i')
        bpms.append(detect(wdata, framerate))
        start += step

    wf.close()

    print numpy.median(bpms)


test_detector()
