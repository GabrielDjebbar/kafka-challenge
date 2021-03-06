# kafka-challenge

## Setup : 
### Install and then launch kafka :
bin/zookeeper-server-start.sh config/zookeeper.properties

bin/kafka-server-start.sh config/server.properties

## Populate topic with jsonl data:
Your_path_to/kafka-console-producer.sh --broker-list localhost:9092 --topic user-timeline < stream.jsonl

### Install python and libs :
apt install python3  
apt install python3-pip  
pip3 install -r requirements.txt

### Launch the python script (to see the kafka records being consumed and results of counting printed to stdin):
python3 prototype_simple.py  
or  
python3 prototype_probabilistic.py  


## First solution using sets
### Algorithm & Datastructue
My first basic approach was to have a dictionary of sets where each set corresponded to a time window of 1 minute.
Basically my solution transforms each record timestamp into a timestamp without seconds (I do this by dividing the timestamp by 60 and now records with the same modified timestamp belongs to the same window of 60 seconds). We can then remultiply 60 to get a coherent modified timestamp. 
#### Example 
With {"ts":1468244384,"uid":"9bfcae2f7c3a4ec2add" }
We take integer part of 1468244384/60 which is 24470739 and then remutiply by 60  to get 1468244340 (that's the same as doing 1468244384 - 1468244384 % 60). This modified timestamp will be used to count unique user id inside a 60 seconds window.

### When to send output data :
When I read the statement about the need to have the counts available as soon as possible I assumed that the data was ordered inside the kafka topic. Therefore I thought that each time I got a modifiedRecord which is different from the previous modifiedRecord it means we are onto a new time window and we can print right away the number of unique id in the previous time window (as since the data is supposedly ordered there is no way subsquent records again end up being belonging to a previous minute later on ).
![alt tag](https://github.com/GabrielDjebbar/kafka-challenge/blob/master/visual_explanation_sending_output_stdin.jpg)
![alt tag](https://github.com/GabrielDjebbar/kafka-challenge/blob/master/sending_output_stdin.jpg)



## Second approach : Probabilistic Counting
The second thing I did was to build on to my basic solution by adding a LPC (Linear probabilistic Counter, which use a bit array, instead of using a simple set). This algorithm allows to have a trade-off between memory and couting error. I tried to see what was the evolution of the counting error depending on the size of the bit array as I thought it might be useful to think a memory usage reduction for a more scalable solution with records of 2 years worth of data and not just 15 minutes.

After running my first solution (dictionary of sets) I found that the number of unique users per minute is roughly 45000. 
In python, a set of roughly 45 000 uid elements is 210 Kb. Therefore I used 210Kb as my baseline for testing the evolution of the approximation error. Below is an analysis of the performance error versus the memory gain. 



## Benchmark (Memory consumption, approximation error)
Comparison of HashSet and Linear probabilistic counting.
![alt tag](https://github.com/GabrielDjebbar/kafka-challenge/blob/master/counting_error.jpg)

For 20KB I got 0.5 % error at most, which mean we can gain 10 time more space in memory for a perhaps negligeable tradeoff in accuracy (well this depends on the buisiness requirement of course).


## How to scale (Throughput) :
### Step 1.Using Kafka Streams and its Stafeful States
 After some research I saw that Kafka Streams API (Faust in python) that allows you to do stateful operations across several consumers, like *counting*, on your streams by using Store States.
So if I wanted some thing that could scale, by using more than one Consumer and naturally more than one partition on the source topic,  I would definitly need to use this API.

### Step 2. More consumers.
Having an app that use Kafka Streams would naturally allow me to to launch multiple Consumers and speed up throughput (given the input topic is partionned accordingly).

## Edge case : in case of late arrival

### When to output data ?
#### 1.	Previous approach not working
If the data is supposedly **not ordered by their timestamp** then there is no way to apply a strategy using flags. As data records corresponding to different minutes could be intermingled (like this data stream: 12h15, 12h15,12h16, 12h16, 12h17, 12h15, 12h16). 
In this case I could very simply output the new updated count for a given minute after each processing of a new record of the stream (as Ktable is a changelog of updated key value). But this is not what buisiness want (I don’t think they would want to deal with a stream of intermdiate results). 
For example with the above data stream we could output :  
12h15 1  
12h15 2  
12h16 1  
12h17 1  
12h15 3  
12h16 2

#### 2.	A possible solution that answers buisiness: using time out.
However if we suppose the data is **roughly ordered** (and that the bulk, say 99% of one given timestamp minute should be roughly processed by the consumer in a small interval of time, say within 2 seconds ), we could perhaps have a *screening mechanism onto the KTable* (containing the updated count after each new record processed) that would somehow check when was the record updated for the last time inside the KTable and output the record if the time the record was last updated is above a certain time threshold (for example say 2 seconds). This way we would get the bulk of the data for a given minute and ignore the records that are really too late. 
This timeout/screening mechanism is something that should probably implemented with Kafka **punctuate()** function (from what I checked on internet ). 

![alt tag](https://github.com/GabrielDjebbar/kafka-challenge/blob/master/scale_and_edge_case.jpg)

https://stackoverflow.com/questions/51631413/timeout-for-aggregated-records-in-kafka-table
https://stackoverflow.com/questions/47125764/timeouts-for-kafka-streams

## If I could do it again : 
I would try going for Java instead of Python as documentation around Kafka Stream seems to be a lot more complete (moreover not all functionalities have been ported to Python it seems, punctuate amongst other). But mostly, not having dealt with Kafka streams beforehand held me back for wrapping my head around a scalable approach that worked as buisiness intended.
