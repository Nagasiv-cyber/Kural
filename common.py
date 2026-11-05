from pathlib import Path
import csv, math, time
ROOT=Path(__file__).resolve().parent
DATA=ROOT/'phrase_data_v23.csv'
FIELDS=['label','trial','flex','pot','ax','ay','az','gx','gy','gz']
FEATURES=['flex','pot','ax','ay','az']
GESTURES=[
 ('INTRO','FLEX','LEFT','Point toward yourself: FLEX bent, POT low, wrist left'),
 ('HUNGRY','FLEX','UP','FLEX bent, POT low, wrist up'),
 ('NEED_REST','FLEX','DOWN','FLEX bent, POT low, wrist down'),
 ('COME_HERE','FLEX','RIGHT','FLEX bent, POT low, wrist right'),
 ('FEEL_GOOD','FLEX','CENTER','FLEX bent, POT low, wrist neutral'),
 ('FEEL_UNWELL','POT','LEFT','FLEX straight, POT high, wrist left'),
 ('YES','POT','UP','FLEX straight, POT high, wrist up'),
 ('NO','POT','DOWN','FLEX straight, POT high, wrist down'),
 ('ASK_NAME','POT','RIGHT','FLEX straight, POT high, wrist right'),
 ('ASK_FROM','POT','CENTER','FLEX straight, POT high, wrist neutral'),
]
LABELS=['REST']+[g[0] for g in GESTURES]
HOW={'REST':'FLEX straight, POT low, wrist neutral',**{g[0]:g[3] for g in GESTURES}}
KIND={'REST':'REST',**{g[0]:g[1] for g in GESTURES}}
PHRASES={'INTRO':'Hello, my name is {name}.','HUNGRY':"I'm hungry. I need something to eat.", 'NEED_REST':'I need some rest.','COME_HERE':'Please come here.','FEEL_GOOD':"I'm feeling good.",'FEEL_UNWELL':"I'm not feeling well.",'YES':'Yes, please.','NO':'No, thank you.','ASK_NAME':'What is your name?','ASK_FROM':'Where are you from?'}

def parse(line):
    parts=line.strip().split(',')
    if len(parts)!=9 or parts[-1]!='OK': return None
    try: vals=[float(x) for x in parts[:-1]]
    except ValueError: return None
    if not all(math.isfinite(x) for x in vals) or not (0<vals[0]<4095 and 0<=vals[1]<=4095):return None
    return dict(zip(FIELDS[2:],vals))

def read_csv():
    if not DATA.exists():return []
    with DATA.open(newline='',encoding='utf-8') as f:return list(csv.DictReader(f))

def append(label,trial,readings):
    new=not DATA.exists()
    with DATA.open('a',newline='',encoding='utf-8') as f:
        writer=csv.DictWriter(f,fieldnames=FIELDS)
        if new:writer.writeheader()
        for r in readings:writer.writerow({'label':label,'trial':trial,**r})

def serial_open(port):
    import serial
    return serial.Serial(port,115200,timeout=0.3)

def collect_samples(ser,count=25,timeout=8):
    ser.reset_input_buffer();end=time.monotonic()+timeout;out=[]
    while len(out)<count and time.monotonic()<end:
        row=parse(ser.readline().decode('utf-8',errors='replace'))
        if row:out.append(row)
    return out