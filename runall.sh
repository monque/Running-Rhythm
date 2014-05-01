if [ ! -d "$1" ]; then
    echo "error starting dir"
    exit 1
fi

> wav/result.log
tmpfile="wav/tmp.wav"
find "$1" -name '*.mp3' | sort | while read file; do
    mpg123 -q -w $tmpfile "$file"

    bpm=`./bpm.py --downsample 4 --invertmix $tmpfile`

    result="$bpm\t$file"
    echo -e $result
    echo -e $result >> wav/result.log
done
