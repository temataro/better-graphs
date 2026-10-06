"""M8: shared-row evidence tables. Statistics, data and layout stay separate.

Historical inputs are numeric transcriptions of R datasets/sleep.R and
UCBAdmissions.R; references and interpretation boundaries are in the curriculum.
"""
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
import house_style as hs

SLEEP_1 = np.array([.7, -1.6, -.2, -1.2, -.1, 3.4, 3.7, .8, 0., 2.])
SLEEP_2 = np.array([1.9, .8, 1.1, .1, -.1, 4.4, 5.5, 1.6, 4.6, 3.4])
# Male admitted, male rejected, female admitted, female rejected; departments A-F.
BERKELEY = np.array([[512,313,89,19], [353,207,17,8], [120,205,202,391],
                     [138,279,131,244], [53,138,94,299], [22,351,24,317]])


def mean_ci10(values):
    """Two-sided 95% t interval, df=9; intentionally limited to n=10."""
    values = np.asarray(values, dtype=float)
    if values.shape != (10,) or not np.isfinite(values).all():
        raise ValueError('This historical calculation requires ten finite values')
    mean = values.mean()
    half = 2.2621571628540993 * values.std(ddof=1) / np.sqrt(10)
    return float(mean), float(mean-half), float(mean+half)


def table_column(ax, x, heading, values, *, align='right', size=11, accent_rows=()):
    """Column x uses axes fraction; row y uses shared data coordinates."""
    transform = ax.get_yaxis_transform()
    ax.text(x, -1., heading, transform=transform, ha=align, va='center',
            fontsize=size-1, weight='bold', color=hs.MUTED, linespacing=1.3)
    for row, value in enumerate(values):
        ax.text(x, row, str(value), transform=transform, ha=align, va='center',
                fontsize=size, color=hs.ACCENT if row in accent_rows else hs.INK)


def evidence_frame(rows, *, title, dek, source, widths=(2.2,4.2,3.6), height=6.2,
                   register='read'):
    """Three axes INSIDE one figure: label stub, plot, exact-value table."""
    hs.theme(register)
    fig = plt.figure(figsize=(12,height), facecolor=hs.PAPER)
    grid = fig.add_gridspec(1,3,left=.045,right=.97,bottom=.22,top=.70,
                           width_ratios=widths,wspace=.09)
    labels = fig.add_subplot(grid[0,0])
    plot = fig.add_subplot(grid[0,1],sharey=labels)
    numbers = fig.add_subplot(grid[0,2],sharey=labels)
    for ax in (labels,plot,numbers):
        ax.set_facecolor(hs.PAPER)
        ax.set_ylim(rows-.4,-1.6)
        ax.tick_params(axis='y',left=False,labelleft=False)
        for spine in ax.spines.values():
            spine.set_visible(False)
        ax.axhline(-.55,color=hs.HAIRLINE,lw=1)
    for ax in (labels,numbers):
        ax.set_xlim(0,1)
        ax.set_xticks([])
    plot.tick_params(axis='x',labelsize=10,length=0,pad=8)
    fig.text(.045,.94,'M8 / EVIDENCE TABLES',fontsize=10,weight='bold',color=hs.ACCENT)
    fig.text(.045,.865,title,fontsize=23,family=hs.DISPLAY_STACK,color=hs.INK)
    fig.text(.045,.795,dek,fontsize=11,color=hs.MUTED)
    fig.text(.045,.055,source,fontsize=10,color=hs.MUTED,linespacing=1.5)
    return fig,labels,plot,numbers


def export(fig, stem):
    target = Path(__file__).resolve().parents[1] / 'outputs'
    target.mkdir(exist_ok=True)
    for ext in ('png','svg'):
        fig.savefig(target / f'{stem}.{ext}',dpi=160,facecolor=hs.PAPER)
    return fig


def sleep_glance():
    mean,lo,hi = mean_ci10(SLEEP_2-SLEEP_1)
    fig,labels,ax,table = evidence_frame(1,height=4.9,register='glance',
        title='More sleep in this small paired sample',
        dek='Drug 2 minus drug 1 · ten people, each measured twice · hours',
        source='R sleep data; historical teaching example, not treatment advice.\n95% paired t interval; independent persons and approximately normal differences assumed.')
    table_column(labels,.02,'Comparison',['Within-person\ndifference'],align='left',size=13)
    ax.axvline(0,color=hs.MUTED,lw=1,ls='--')
    ax.errorbar(mean,0,xerr=[[mean-lo],[hi-mean]],fmt='o',color=hs.ACCENT,markersize=10,capsize=5,lw=2)
    ax.set_xlim(-.3,3)
    ax.set_xticks([0,1,2,3])
    ax.set_xlabel('Difference in extra sleep (hours)',fontsize=11,labelpad=9)
    table_column(table,.17,'Pairs',['10'],size=13)
    table_column(table,.98,'Mean [95% CI], h',[f'{mean:.2f} [{lo:.2f}, {hi:.2f}]'],size=13)
    return export(fig,'m8_sleep_glance')


def sleep_read():
    summaries = [mean_ci10(v) for v in (SLEEP_1,SLEEP_2,SLEEP_2-SLEEP_1)]
    fig,labels,ax,table = evidence_frame(3,
        title='A comparison needs its own estimate',
        dek='The first two rows describe conditions; the last estimates their paired difference.',
        source='R sleep data · n = 10 paired people · hours relative to control.\nAll intervals: 95% t, df = 9. Compare the difference row, not overlap of the condition intervals.')
    table_column(labels,.02,'Quantity',['Drug 1','Drug 2','Drug 2 − drug 1'],align='left',accent_rows=(2,))
    ax.axvline(0,color=hs.MUTED,ls='--',lw=1)
    for row,(mean,lo,hi) in enumerate(summaries):
        ax.errorbar(mean,row,xerr=[[mean-lo],[hi-mean]],color=hs.ACCENT if row==2 else hs.MUTED,
                    fmt='D' if row==2 else 'o',markersize=7,capsize=4,lw=1.8)
    ax.set_xlim(-1,4)
    ax.set_xlabel('Extra sleep / paired difference (hours)',fontsize=10,labelpad=9)
    table_column(table,.35,'Mean, h',[f'{v[0]:.2f}' for v in summaries],accent_rows=(2,))
    table_column(table,.98,'95% CI, h',[f'[{v[1]:.2f}, {v[2]:.2f}]' for v in summaries],accent_rows=(2,))
    return export(fig,'m8_sleep_read')


def sleep_study():
    fig,labels,ax,table = evidence_frame(10,height=8.2,widths=(1.3,4.8,3.9),
        title='Keep the person attached to the number',
        dek='Circles = drug 1; squares = drug 2. A connecting segment preserves each pair.',
        source='R sleep data · original ID order, not sorted to dramatize change · no missing pairs.\nRaw values are extra hours versus control; Change = drug 2 − drug 1. Lines show pairing, not time trajectories.')
    table_column(labels,.02,'Person',[f'{i:02d}' for i in range(1,11)],align='left')
    ax.axvline(0,color=hs.HAIRLINE,lw=1)
    for i,(a,b) in enumerate(zip(SLEEP_1,SLEEP_2)):
        ax.plot([a,b],[i,i],color=hs.CONTEXT,lw=2)
        ax.plot(a,i,'o',color=hs.MUTED,markersize=6)
        ax.plot(b,i,'s',color=hs.ACCENT,markersize=6)
    ax.set_xlim(-2.2,6)
    ax.set_xlabel('Extra sleep compared with control (hours)',fontsize=11,labelpad=10)
    for x,heading,values in [(.28,'Drug 1, h',SLEEP_1),(.61,'Drug 2, h',SLEEP_2),(.98,'Change, h',SLEEP_2-SLEEP_1)]:
        table_column(table,x,heading,[f'{v:+.1f}' for v in values])
    return export(fig,'m8_sleep_study')


def sleep_before():
    """A deliberately mediocre, but numerically honest, starting point."""
    hs.theme('read')
    fig,ax = plt.subplots(figsize=(10,5))
    fig.subplots_adjust(left=.10,right=.95,top=.82,bottom=.31)
    ax.bar(['Drug 1','Drug 2'],[SLEEP_1.mean(),SLEEP_2.mean()],color=[hs.MUTED,hs.ACCENT])
    ax.set_ylabel('Mean extra sleep (hours)')
    ax.set_title('Before: two bars, a grid, no paired difference',fontsize=16)
    tab=ax.table(cellText=[[f'{SLEEP_1.mean():.2f}',f'{SLEEP_2.mean():.2f}'],['10','10']],
                 rowLabels=['Mean, h','People'],colLabels=['Drug 1','Drug 2'],cellLoc='center',bbox=[0,-.70,1,.50])
    tab.auto_set_font_size(False)
    tab.set_fontsize(11)
    fig.text(.1,.025,'Deliberate anti-example: R sleep data. The columns are the same ten people.',fontsize=10)
    return export(fig,'m8_sleep_before')


def berkeley_records():
    totals=np.vstack([BERKELEY.sum(axis=0),BERKELEY])
    mn=totals[:,0]+totals[:,1]
    fn=totals[:,2]+totals[:,3]
    return totals,mn,fn,totals[:,0]/mn*100,totals[:,2]/fn*100


def berkeley_figure():
    totals,mn,fn,mr,fr=berkeley_records()
    fig,labels,ax,table=evidence_frame(7,height=7.6,widths=(1.5,3.8,4.7),
        title='The denominator changes the story',
        dek='Berkeley, six largest departments, 1973 · circles = male; squares = female (source labels)',
        source='R UCBAdmissions; Bickel, Hammel & O’Connell (1975). Admissions counts, not randomized trials.\nAll-six row is a mixture, not an adjusted effect. These counts alone cannot settle questions of discrimination.')
    table_column(labels,.02,'Department',['All six','A','B','C','D','E','F'],align='left')
    for i,(m,f) in enumerate(zip(mr,fr)):
        ax.plot([m,f],[i,i],color=hs.CONTEXT,lw=2)
        ax.plot(m,i,'o',color=hs.MUTED,markersize=6)
        ax.plot(f,i,'s',color=hs.ACCENT,markersize=6)
    for a in (labels,ax,table):
        a.axhline(.5,color=hs.HAIRLINE,lw=1.2)
    ax.set_xlim(0,100)
    ax.set_xticks([0,25,50,75,100])
    ax.set_xlabel('Admitted (%)',fontsize=11,labelpad=9)
    table_column(table,.47,'Male admitted / N',[f'{a:,} / {n:,}' for a,n in zip(totals[:,0],mn)])
    table_column(table,.99,'Female admitted / N',[f'{a:,} / {n:,}' for a,n in zip(totals[:,2],fn)])
    return export(fig,'m8_berkeley')


def synthetic_trials(seed=20261006,draws=12000):
    """Independent two-arm illustrative trials, not published observations.

    Means are deliberately centered to specified effects. The bootstrap illustrates
    conditional sampling uncertainty, not calibration of this data-generation scheme.
    """
    rng=np.random.default_rng(seed)
    records=[]
    for label,setting,n,effect in [('A','Lab / novice',40,6.),('B','Lab / practiced',120,3.),('C','Field / mixed',60,1.)]:
        control=rng.normal(50,10,n)
        treatment=rng.normal(50-effect,10,n)
        control+=50-control.mean()
        treatment+=(50-effect)-treatment.mean()
        boot=control[rng.integers(0,n,(draws,n))].mean(1)-treatment[rng.integers(0,n,(draws,n))].mean(1)
        lo,hi=np.quantile(boot,[.025,.975])
        records.append(dict(trial=label,setting=setting,n=n,effect=float(control.mean()-treatment.mean()),
                            lo=float(lo),hi=float(hi),boot=boot,control=control,treatment=treatment))
    return records,np.quantile(records[0]['boot']-records[1]['boot'],[.025,.975])


def trials_figure():
    records,interval=synthetic_trials()
    fig,labels,ax,table=evidence_frame(4,height=7.4,widths=(2.7,3.7,3.6),
        title='Compare effects, not significance labels',
        dek='Synthetic task-completion experiments · positive = faster with the new interface · seconds',
        source='Synthetic, seed 20261006; 12,000 independent-arm percentile bootstrap draws per trial; nominal 95% intervals.\nA − B is an exploratory between-trial contrast, not an effect of expertise. No pooled effect is estimated.')
    table_column(labels,.02,'Experiment / estimand',[f"Trial {r['trial']} / {r['setting']}" for r in records]+['A − B effect contrast'],align='left',size=10)
    effects=[r['effect'] for r in records]+[records[0]['effect']-records[1]['effect']]
    intervals=[(r['lo'],r['hi']) for r in records]+[interval]
    ax.axvline(0,color=hs.MUTED,ls='--',lw=1)
    for i,(mean,(lo,hi)) in enumerate(zip(effects,intervals)):
        ax.errorbar(mean,i,xerr=[[mean-lo],[hi-mean]],fmt='D' if i==3 else 'o',
                    color=hs.ACCENT if i==3 else hs.INK,markersize=7,capsize=4,lw=1.8)
    for a in (labels,ax,table):
        a.axhline(2.5,color=hs.HAIRLINE,lw=1.3)
    ax.set_xlim(-5,12)
    ax.set_xticks([-5,0,5,10])
    ax.set_xlabel('Mean time saved (seconds)',fontsize=11,labelpad=10)
    table_column(table,.26,'n / arm',[str(r['n']) for r in records]+['—'],size=10)
    table_column(table,.99,'Effect [95% CI], s',[f'{m:.1f} [{lo:.1f}, {hi:.1f}]' for m,(lo,hi) in zip(effects,intervals)],size=10)
    return export(fig,'m8_trials')


def markdown_table(headers,rows):
    """Companion HTML table after Pandoc, generated from the same numeric records."""
    print('| '+' | '.join(headers)+' |')
    print('| '+' | '.join(['---']*len(headers))+' |')
    for row in rows:
        print('| '+' | '.join(map(str,row))+' |')
    print()
