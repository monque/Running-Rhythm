> result.log

find music -name '*.mp3' | while read file; do
    echo "$file"
    mpg123 -q -w sample.wav "$file"
    bpm=`python bpm.py --file sample.wav`
    echo -e "$file\x1F$bpm" >> result.log
done
