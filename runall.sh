> result.log

find music -name '*.mp3' | sort | while read file; do
# find music -name '*Twisted*.mp3' | while read file; do
    mpg123 -q -w sample.wav "$file"
    bpm=`python bpm.py --file sample.wav`

    result="$bpm\t$file"
    echo -e $result
    echo -e $result >> result.log
done
