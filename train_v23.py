from collections import defaultdict
import numpy as np,pandas as pd,joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score,balanced_accuracy_score,classification_report
from common import *

def main():
    if not DATA.exists():raise SystemExit('No v2.3 data yet. Run collect_v23.py first.')
    df=pd.read_csv(DATA)
    trials={label:list(df[df.label==label].trial.drop_duplicates()) for label in LABELS}
    missing=[f'{label} ({len(trials[label])}/4)' for label in LABELS if len(trials[label])<4]
    if missing:raise SystemExit('Need four trials each: '+', '.join(missing))
    # Use exactly four complete trials for each class; never split samples within a trial.
    df=df[df.apply(lambda r:r['trial'] in trials[r['label']][:4],axis=1)].copy()
    for label in LABELS:
        for trial in trials[label][:4]:
            if len(df[(df.label==label)&(df.trial==trial)])<25:raise SystemExit(f'Incomplete trial: {trial}')
    median=df.groupby('label')[['flex','pot']].median()
    for label in LABELS:
        f,p=median.loc[label]
        if KIND[label]=='REST' and not(f<=235 and p<=1400):raise SystemExit(f'Bad REST median: {f}, {p}')
        if KIND[label]=='FLEX' and not(f>=245 and p<=1400):raise SystemExit(f'Bad FLEX median for {label}: {f}, {p}')
        if KIND[label]=='POT' and not(f<=235 and p>=2400):raise SystemExit(f'Bad POT median for {label}: {f}, {p}')
    X=df[FEATURES];y=df.label
    predictions=[];actual=[];fold_scores=[]
    for fold in range(4):
        held={trials[label][fold] for label in LABELS}
        test=df.trial.isin(held)
        m=RandomForestClassifier(n_estimators=200,min_samples_leaf=2,class_weight='balanced_subsample',random_state=42,n_jobs=-1)
        m.fit(X[~test],y[~test]);pred=m.predict(X[test]);predictions.extend(pred);actual.extend(y[test]);fold_scores.append(accuracy_score(y[test],pred))
    report=classification_report(actual,predictions,labels=LABELS,zero_division=0)
    score=accuracy_score(actual,predictions);balanced=balanced_accuracy_score(actual,predictions)
    final=RandomForestClassifier(n_estimators=250,min_samples_leaf=2,class_weight='balanced_subsample',random_state=42,n_jobs=-1)
    final.fit(X,y)
    joblib.dump({'model':final,'features':FEATURES,'labels':LABELS,'version':'2.3'},ROOT/'phrase_model_v23.joblib')
    txt=f'FlexVoice 2.3: trial-separated four-fold evaluation\nAccuracy: {score:.1%}\nBalanced accuracy: {balanced:.1%}\nFold scores: {fold_scores}\n\n{report}\n'
    (ROOT/'training_report_v23.txt').write_text(txt,encoding='utf-8');print(txt)
    print('Saved phrase_model_v23.joblib. Validate on new, unseen gestures before relying on results.')
if __name__=='__main__':main()