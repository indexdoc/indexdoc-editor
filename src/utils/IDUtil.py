import uuid
from datetime import datetime

def get_long():
    return get_long_id_by_time()

def get_uuid():
    return uuid.uuid1().hex

#适合数据量不大的非集群应用，每秒插入不超过10000个
#如果需要作集群，需要将此服务独立出来单独作为一个ID生成器进程。也可以定义一个标志位作为集群ID。
from datetime import datetime
last_time_id = 21010100000000
def get_long_id_by_time():
    global last_time_id
    dt = datetime.now()
    new_id = datetime.strftime(dt,'%y%m%d%H%M%S0000')
    new_id = int(new_id) + int(dt.microsecond/100)
    if new_id <= last_time_id:
        new_id = last_time_id + 1
    last_time_id = new_id
    return new_id

#雪花算法，适合大数据量分布式应用
# import snowflake.client
# def get_long_id_by_snowflake():
#     snowflake.client.Generator
#     pass

# print(type(get_long_id_by_time()),get_long_id_by_time())