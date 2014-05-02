# coding=utf-8
from datetime import timedelta
import struct
import wave

import numpy
import scipy.signal


def load_wav(filename):
    attr = {
        'filename': filename,
    }

    wf = wave.open(filename, 'rb')

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


def test_select_bpm():
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
    result = bpm.select_bpm(blist, verbose=True)
    print result


def dev_process(file_in, file_out, func_process):
    # Read
    print 'Read input file %s' % file_in
    data_in, wf_in = load_wav(file_in)

    # Process
    data_out = func_process(data_in)
    print 'Process done'

    # Write
    wf_out = wave.open(file_out, 'wb')
    wf_out.setnchannels(2)
    wf_out.setframerate(44100)  # 44.1khz
    wf_out.setsampwidth(2)  # 16bit
    wf_out.writeframes(data_out)
    wf_out.close()
    print 'Write output file %s' % file_out


def process_rmvocal(data_in):
    w_in = numpy.fromstring(data_in, dtype='<i2')
    left, right = w_in[::2], w_in[1::2]
    w_out = (left - right) / 2

    data_out = ''
    for x in w_out:
        data_out += struct.pack('<h', x)

    return data_out


def process_treble_cut(data_in):
    w_in = numpy.fromstring(data_in, dtype='<i2')

    # Cut
    unit = 44100 * 2
    s_begin = 30 * unit
    s_end = 40 * unit
    w_in = w_in[s_begin:s_end]

    # Create Filter
    f = scipy.signal.firwin(numtaps=20, cutoff=4, nyq=20)
    print type(f), f

    # Do filter
    w_out = scipy.signal.lfilter(f, [1.0], w_in)

    data_out = ''
    for x in w_out:
        if x > 32767:
            x = 32767
        try:
            data_out += struct.pack('<h', x)
        except struct.error as e:
            print 'value:', x, 'error:', e
            raise e

    return data_out


if __name__ == '__main__':
    # 115_30_陈奕迅 - 29.阿士匹灵.wav
    # 117_70_I Saved the World Today - Eurythmics.wav
    # 122_76_Only This Moment - Röyksopp.wav
    # 136_66_Geri Halliwell - 10.It's Raining Men.wav
    # 140_66_The Cure - 07.Lovesong.wav
    # 163_33_陈奕迅 - 44.忘记歌词.wav
    # 164_41_孙燕姿 - 01.世说心语.wav
    # 165_50_Hoobastank - 08.The Reason.wav
    # 170_24_Tears For Fears - 01.Sowing the seeds of love.wav
    # 192_52_Blur - 01.For Tomorrow.mp3.wav

    dev_process('wav/164_41_孙燕姿 - 01.世说心语.wav', 'wav/dev.wav', process_treble_cut)
