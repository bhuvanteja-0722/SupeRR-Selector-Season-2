import sys
from pathlib import Path
root=Path(__file__).resolve().parent
sys.path.insert(0,str(root))
import numpy as np
from sklearn.ensemble import RandomForestClassifier, ExtraTreesClassifier, HistGradientBoostingClassifier
from sklearn.metrics import roc_auc_score, brier_score_loss
from train_model import load_deliveries, aggregate, combine, season_bounds, build_frame, FEATURES, fit_models, predictions

data=root/'work'/'data'
sma_raw=load_deliveries(data/'sma_csv2.zip'); ipl_raw=load_deliveries(data/'ipl_csv2.zip')
reg,display=__import__('train_model').load_name_registry(data/'people.csv',data/'names.csv')
sma_b,sma_dates=aggregate(sma_raw,'bat',reg); sma_w,_=aggregate(sma_raw,'bowl',reg)
ipl_b,ipl_dates=aggregate(ipl_raw,'bat',reg); ipl_w,_=aggregate(ipl_raw,'bowl',reg)
frame=build_frame(combine(sma_b,sma_w),season_bounds(sma_dates),combine(ipl_b,ipl_w),season_bounds(ipl_dates))
seasons=sorted({r['domestic_season'] for r in frame},key=lambda s:season_bounds(sma_dates)[s][1])
constructors={
 'logistic':lambda:fit_models,
 'random_forest':lambda:RandomForestClassifier(n_estimators=300,min_samples_leaf=10,max_features=.8,random_state=17,n_jobs=-1),
 'extra_trees':lambda:ExtraTreesClassifier(n_estimators=300,min_samples_leaf=10,max_features=.8,random_state=17,n_jobs=-1),
 'hist_gradient':lambda:HistGradientBoostingClassifier(learning_rate=.05,max_iter=100,max_leaf_nodes=15,l2_regularization=5,random_state=17)
}
rows=[]
for idx,season in enumerate(seasons):
 if idx<4: continue
 train=[r for r in frame if r['domestic_season'] in seasons[:idx]]
 test=[r for r in frame if r['domestic_season']==season]
 if len({r['ipl_next_appearance'] for r in train})<2: continue
 X=np.asarray([[r[f] for f in FEATURES] for r in train]); y=np.asarray([r['ipl_next_appearance'] for r in train])
 Xt=np.asarray([[r[f] for f in FEATURES] for r in test]); yt=np.asarray([r['ipl_next_appearance'] for r in test])
 regfit=fit_models(train)[1]
 impact=np.maximum(0,np.expm1(regfit.predict(Xt)))
 for name,ctor in constructors.items():
  if name=='logistic': clf=fit_models(train)[0]
  else: clf=ctor().fit(X,y)
  p=clf.predict_proba(Xt)[:,1]
  top=np.argsort(-(p*impact))[:10]
  rows.append((name,season,roc_auc_score(yt,p) if len(set(yt))==2 else float('nan'),brier_score_loss(yt,p),float(yt[top].mean())))
for name in constructors:
 rs=[r for r in rows if r[0]==name]
 print(name,'mean_auc',round(float(np.nanmean([r[2] for r in rs])),3),'mean_brier',round(float(np.mean([r[3] for r in rs])),3),'mean_p10',round(float(np.mean([r[4] for r in rs])),3),'folds',[(r[1],round(r[2],3),round(r[3],3),round(r[4],2)) for r in rs])
