from kafka import KafkaConsumer
import time
from probabilistic_counter import LPCounter
import json
class DDict(dict):
    """
    Cusstom defaultdict to pass LPCounter with a parameter
    """
    def __missing__(self,key):
        res = self[key] = LPCounter(20)
        return res


def python_kafka_consumer():
    topic = 'user-timeline'
    consumer = KafkaConsumer(topic,bootstrap_servers='localhost:9092',auto_offset_reset='earliest',group_id=None)
    msg_consumed_count = 0
    consumer_start = time.time()
    count = DDict()
    timestamp_1 = None
    timestamp_2 = None
    for msg in consumer:
        msg_consumed_count += 1
        json_msg = json.loads(msg.value)
        count[int(int(json_msg['ts'])/60)*60].increment(json_msg['uid'])
        if timestamp_1 is None:
            timestamp_1 = int(int(json_msg['ts'])/60)*60
        else:
            timestamp_2 = timestamp_1
            timestamp_1 = int(int(json_msg['ts'])/60)*60
            if(timestamp_1!=timestamp_2):
                print(timestamp_2, count[timestamp_2].current_count())
                
    #print(msg_consumed_count/(time.time() - consumer_start ))

python_kafka_consumer()
