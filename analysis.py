"""Synthetic evidence experiment; no real treatment or patient data."""
from pathlib import Path
import json,hashlib,platform
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'results'
TRUTH=-.08

def generate(n=10000,seed=42,randomised=False):
    rng=np.random.default_rng(seed)
    severity=rng.random(n)<.3
    treated=rng.random(n)<(np.full(n,.5) if randomised else np.where(severity,.8,.2))
    probability=np.where(severity,np.where(treated,.25,.4),np.where(treated,.05,.1))
    event=rng.random(n)<probability
    return pd.DataFrame({'person_id':np.arange(n),'severe':severity.astype(int),'treated':treated.astype(int),'adverse_event':event.astype(int)})

def estimate(data,severity='severe'):
    rates=data.groupby([severity,'treated']).adverse_event.mean().unstack()
    if rates.shape!=(2,2) or rates.isna().any().any():return np.nan,np.nan
    marginal=data.groupby('treated').adverse_event.mean()
    return float(marginal[1]-marginal[0]),float(.7*(rates.loc[0,1]-rates.loc[0,0])+.3*(rates.loc[1,1]-rates.loc[1,0]))

def main():
    OUT.mkdir(exist_ok=True)
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'axes.spines.top':False,'axes.spines.right':False,'axes.facecolor':'#fffdf7','figure.facecolor':'#fffdf7','savefig.facecolor':'#fffdf7'})
    d=generate();assert d.person_id.is_unique and not d.isna().any().any()
    d.to_csv(OUT/'synthetic-population.csv',index=False)
    groups=d.groupby(['severe','treated']).adverse_event.agg(['size','mean'])
    groups.to_csv(OUT/'group-audit.csv')
    primary=estimate(d)
    rng=np.random.default_rng(123)
    boot=np.array([estimate(d.iloc[rng.integers(0,len(d),len(d))]) for _ in range(500)])
    invalid=int((~np.isfinite(boot).all(axis=1)).sum())
    valid=boot[np.isfinite(boot).all(axis=1)]
    if len(valid)<450:raise RuntimeError('Too many undefined bootstrap samples')
    intervals=np.percentile(valid,[2.5,97.5],axis=0)
    est=pd.DataFrame({'estimator':['Crude comparison','Severity standardisation'],'risk_difference':primary,'lower':intervals[0],'upper':intervals[1],'true_effect':TRUTH})
    est.to_csv(OUT/'primary-estimates.csv',index=False)
    pd.DataFrame(boot,columns=['crude','standardised']).to_csv(OUT/'bootstrap-estimates.csv',index=False)
    repeats=[]
    for n in (1000,10000):
        for j in range(100):
            seed=100000+n+j
            a,b=estimate(generate(n,seed))
            repeats.append({'n':n,'replicate':j,'seed':seed,'crude':a,'standardised':b})
    rep=pd.DataFrame(repeats);rep.to_csv(OUT/'repeated-estimates.csv',index=False)
    summary=[]
    for n,g in rep.groupby('n'):
        for method in ('crude','standardised'):
            error=g[method]-TRUTH
            summary.append({'n':int(n),'estimator':method,'mean_error':error.mean(),'rmse':np.sqrt(np.mean(error**2))})
    pd.DataFrame(summary).to_csv(OUT/'sampling-summary.csv',index=False)
    rand=estimate(generate(seed=43,randomised=True))
    # Extension: keep latent severity fixed and perturb only the measured covariate.
    noisy=[]
    # Standardise to the known distribution of the recorded covariate.
    for q in (0.,.1,.3):
        temp=d.copy();rngn=np.random.default_rng(777)
        temp['recorded_severity']=np.logical_xor(temp.severe,rngn.random(len(temp))<q).astype(int)
        r=temp.groupby(['recorded_severity','treated']).adverse_event.mean().unstack()
        w1=.3*(1-q)+.7*q
        value=float((1-w1)*(r.loc[0,1]-r.loc[0,0])+w1*(r.loc[1,1]-r.loc[1,0]))
        noisy.append({'flip_probability':q,'adjusted_using_recorded_severity':value,'oracle_using_true_severity':primary[1],'target_recorded_severe_share':w1})
    pd.DataFrame(noisy).to_csv(OUT/'measurement-error.csv',index=False)
    fig,axes=plt.subplots(1,2,figsize=(12,4.8))
    imbalance=d.groupby('treated').severe.mean()*100
    axes[0].bar(['Untreated','Treated'],imbalance,color=['#537c8e','#d47c46'],width=.55)
    axes[0].set(ylabel='Severe illness (%)',ylim=(0,100),title='The groups start in different places')
    for k,x in enumerate(imbalance):axes[0].text(k,x+2,f'{x:.1f}%',ha='center')
    for k,row in est.iterrows():
        axes[1].errorbar(row.risk_difference*100,k,xerr=[[100*(row.risk_difference-row.lower)],[100*(row.upper-row.risk_difference)]],fmt='o',ms=9,color=['#d47c46','#537c8e'][k],capsize=5)
    axes[1].axvline(TRUTH*100,color='#304d3d',ls='--',label='Known simulated effect')
    axes[1].axvline(0,color='#b3b3ad',lw=.8)
    axes[1].set(yticks=[0,1],yticklabels=est.estimator,xlabel='Adverse-event risk difference (percentage points)',title='Same data, different comparison',ylim=(-.5,1.5))
    axes[1].legend(fontsize=9,loc='upper center');fig.tight_layout();fig.savefig(OUT/'the-reversal.png',dpi=170);plt.close(fig)
    fig,axes=plt.subplots(1,2,figsize=(11,4.5),sharex=True,sharey=True)
    for ax,(n,g) in zip(axes,rep.groupby('n')):
        for method,color in [('crude','#d47c46'),('standardised','#537c8e')]:ax.hist(g[method]*100,bins=16,alpha=.65,label=method,color=color)
        ax.axvline(TRUTH*100,color='#304d3d',ls='--');ax.set(title=f'{n:,} people × 100 experiments',xlabel='Estimated risk difference (percentage points)');ax.legend(frameon=False)
    axes[0].set_ylabel('Experiments');fig.suptitle('More data reduces spread, not confounding',fontsize=15);fig.tight_layout();fig.savefig(OUT/'more-data.png',dpi=170);plt.close(fig)
    result={'synthetic':True,'true_risk_difference':TRUTH,'limiting_crude_difference':(.14*.05+.24*.25)/.38-(.56*.1+.06*.4)/.62,'primary_crude':primary[0],'primary_standardised':primary[1],'randomised_crude':rand[0],'randomised_standardised':rand[1],'bootstrap_repetitions':500,'undefined_bootstrap_samples':invalid,'seeds':{'primary':42,'bootstrap':123,'randomised':43,'measurement_error':777},'python':platform.python_version(),'numpy':np.__version__,'pandas':pd.__version__,'matplotlib':matplotlib.__version__,'analysis_sha256':hashlib.sha256((ROOT/'analysis.py').read_bytes()).hexdigest()}
    (OUT/'run.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2));print(est.to_string(index=False));print(pd.DataFrame(summary).to_string(index=False));return est
if __name__=='__main__':main()
