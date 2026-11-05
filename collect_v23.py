import argparse,statistics,time
from collections import defaultdict
from common import *

def main():
    p=argparse.ArgumentParser(description='Four independent trials per phrase, fresh v2.3 dataset')
    p.add_argument('--port',default='COM7');p.add_argument('--audit',action='store_true');p.add_argument('--redo',nargs='+',choices=LABELS);p.add_argument('--samples',type=int,default=25)
    args=p.parse_args()
    if args.samples<25:p.error('At least 25 samples per trial')
    if args.redo and DATA.exists():
        import shutil,datetime,csv
        backup=ROOT/('phrase_data_v23_backup_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S')+'.csv')
        shutil.copy2(DATA,backup);print('Backup:',backup.name)
        remaining=[r for r in read_csv() if r['label'] not in args.redo]
        with DATA.open('w',newline='',encoding='utf-8') as f:
            w=csv.DictWriter(f,fieldnames=FIELDS);w.writeheader();w.writerows(remaining)
    existing=read_csv();trials=defaultdict(set)
    for r in existing:trials[r['label']].add(r['trial'])
    print('\nFLEXVOICE 2.3 | separate FLEX + POT | 4 trials each')
    for label in LABELS:print(f'{label:13s} {min(4,len(trials[label]))}/4')
    if args.audit:return
    print('\nClose Arduino Serial Monitor before starting. Ctrl+C keeps completed trials.')
    try:ser=serial_open(args.port)
    except Exception as e:raise SystemExit(f'Cannot open {args.port}: {e}')
    try:
        with ser:
            time.sleep(1.5)
            for label in LABELS:
                if args.redo and label not in args.redo:continue
                n=len(trials[label]);attempts=0
                while n<4:
                    attempts+=1
                    if attempts>20:raise SystemExit(f'Too many failed attempts for {label}. Check sensor response.')
                    print(f'\n{label} | valid trial {n+1}/4\nAction: {HOW[label]}')
                    input('Return to REST and press Enter...')
                    input('Make gesture, HOLD STILL, press Enter to capture...')
                    samples=collect_samples(ser,args.samples)
                    if len(samples)<args.samples:
                        print(f'Only {len(samples)}/{args.samples} CSV readings. Check port/firmware.');continue
                    flex=statistics.median(x['flex'] for x in samples)
                    pot=statistics.median(x['pot'] for x in samples)
                    flexspread=max(x['flex'] for x in samples)-min(x['flex'] for x in samples)
                    potspread=max(x['pot'] for x in samples)-min(x['pot'] for x in samples)
                    accelspread=max(max(x[k] for x in samples)-min(x[k] for x in samples) for k in ('ax','ay','az'))
                    print(f'FLEX={flex:.0f}, POT={pot:.0f}, flex spread={flexspread:.0f}, pot spread={potspread:.0f}, accel spread={accelspread:.2f}')
                    # Conservative starting bounds based on user's observed ranges.
                    if label=='REST':good=flex<=235 and pot<=1400
                    elif KIND[label]=='FLEX':good=flex>=245 and pot<=1400
                    else:good=flex<=235 and pot>=2400
                    if not good or flexspread>90 or potspread>450 or accelspread>0.30:
                        print('WARNING: wrong control state or unstable hold.')
                        if input('Save anyway as diagnostic only? [y/N]: ').strip().lower()!='y':continue
                        # Never contaminate training with invalid examples.
                        diagnostic=ROOT/'diagnostic_v23.txt'
                        with diagnostic.open('a',encoding='utf-8') as f:f.write(f'{label}: flex={flex}, pot={pot}, flexspread={flexspread}, potspread={potspread}, accelspread={accelspread}\n')
                        print('Diagnostic saved separately; NOT counted.');continue
                    trial=f'{label}_{int(time.time()*1000)}_{n+1}'
                    append(label,trial,samples);n+=1
                    print(f'SAVED {label} trial {n}/4')
    except KeyboardInterrupt:print('\nStopped; completed trials remain saved.')
    print('\nRun: py collect_v23.py --audit')
if __name__=='__main__':main()