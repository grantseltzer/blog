counter=1
mkdir test
for file in *.jpg
do
	cp $file ./test/$counter.jpg
	counter=$((counter + 1))
done
