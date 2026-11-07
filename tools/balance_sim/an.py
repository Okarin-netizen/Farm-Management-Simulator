import pickle, sys, json
res=pickle.load(open(sys.argv[1],'rb'))
S=json.loads(sys.argv[2])
def sc(m):
    pr,e,r=m
    P=max(0,min(100,S['pa']+S['pb']*pr)); E=max(0,min(100,S['ea']+S['eb']*e)); R=max(0,min(100,S['ra']+S['rb']*r))
    t=P+E+R+S.get('bal',0)*min(P,E,R)
    return t,P,E,R
def fam(k):
    sp,au,pc,pt,ps,fert,ships,hn,hs=k
    eco = sum(s in('direct','process') for s in ships)
    if fert=='chem' and pt=='chem' and (pc=='chem' or 'cabbage' not in (sp,au)) and eco==0: return '化学・市場型'
    if fert=='compost' and 'chem' not in (pc,pt,ps) and eco>=2: return '環境・地域型'
    if fert=='none' and pc=='none' and pt=='none' and ps=='none' and eco==0 and hn==0: return '何もしない型'
    return 'その他'
rows=[(sc(m),k,m) for k,m,sd in res]
rows.sort(key=lambda x:-x[0][0])
top=rows[0][0][0]
print('TOP10')
for s,k,m in rows[:10]: print(f"{s[0]:6.1f} P{s[1]:4.0f} E{s[2]:4.0f} R{s[3]:4.0f} | {m[0]:5.1f}万 env{m[1]:5.1f} reg{m[2]:5.1f}",fam(k),k)
fams={}
for s,k,m in rows: fams.setdefault(fam(k),[]).append((s,k,m))
for f,l in fams.items():
    s,k,m=l[0]; import statistics as st
    print(f"{f}: best {s[0]:.1f} ({s[0]/top*100:.0f}%) P{s[1]:.0f} E{s[2]:.0f} R{s[3]:.0f} median {st.median(x[0][0] for x in l):.1f} n={len(l)}", k)
print('rank of best per family:', {f: next(i for i,r in enumerate(rows) if fam(r[1])==f) for f in fams})
# count how many policies within 5% of top
print('within5%:', sum(1 for r in rows if r[0][0]>=0.95*top), 'within10%:', sum(1 for r in rows if r[0][0]>=0.9*top))
# diversity in top 50
from collections import Counter
t50=rows[:50]
print('top50 fert',Counter(r[1][5] for r in t50),'cabbage pest',Counter(r[1][2] for r in t50),'tomato pest',Counter(r[1][3] for r in t50),'house',Counter((r[1][7],r[1][8]) for r in t50))
print('top50 ships',Counter(s for r in t50 for s in r[1][6]))
