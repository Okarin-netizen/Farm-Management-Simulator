import random, statistics as st, json, sys
from sim import *
CFG['pest_base']={'default':0.20,'cabbage':0.40,'potato':0.10}
CFG['pest_out']={'default':0.50,'cabbage':0.70,'potato':0.25}
CFG['pest_cost']['net']=1
CFG.update({"house_cost":8,"house_net_factor":0.25,"direct_unsold":[0,0.2,0.5,0.8]})
S=dict(pa=0,pb=2,ea=75,eb=0.8,ra=40,rb=2)
def sc(pr,e,r):
    P=max(0,min(100,S['pa']+S['pb']*pr)); E=max(0,min(100,S['ea']+S['eb']*e)); R=max(0,min(100,S['ra']+S['rb']*r)); return P,E,R,P+E+R
def pf(spring,autumn,pm,fert,ships,hn=0,hs='winter'):
    def pol(season,money,houses):
        plan=[]
        for i in range(3):
            build=(season==hs and i<hn and i>=houses)
            crop={'spring':spring,'summer':'tomato','autumn':autumn,'winter':'spinach'}[season]
            if season=='winter' and i<hn and i<max(houses,hn): crop='strawberry'
            pest='none' if season=='winter' else pm.get(crop,'none')
            plan.append((crop,pest,fert,ships[i],build))
        return plan
    return pol
pols={
 '利益重視：農薬＋化学肥料＋市場':pf('cabbage','cabbage',{'cabbage':'chem','tomato':'chem'},'chem',('market',)*3),
 '利益重視＋ハウス1（夏）＋いちご':pf('cabbage','cabbage',{'cabbage':'chem','tomato':'chem'},'chem',('market',)*3,1,'summer'),
 '環境重視：ネット＋堆肥＋直売3':pf('cabbage','cabbage',{'cabbage':'net','tomato':'net','spinach':'net','potato':'net'},'compost',('direct',)*3),
 '環境・地域：無対策＋堆肥＋直売1加工2':pf('potato','spinach',{},'compost',('direct','process','process')),
 'バランス：キャベツだけ農薬＋堆肥＋市場/直売/加工':pf('potato','cabbage',{'cabbage':'chem'},'compost',('market','direct','process')),
 'バランス：ネット＋堆肥＋契約/直売/加工＋ハウス1':pf('potato','cabbage',{'cabbage':'net','tomato':'net'},'compost',('contract','direct','process'),1,'summer'),
 '何もしない：無対策・無肥料・市場':pf('potato','spinach',{},'none',('market',)*3),
}
N=5000
dist={}
for k,p in pols.items():
    rng=random.Random(3); xs=[]
    for _ in range(N):
        xs.append(sc(*play(p,rng,None)))
    c=list(zip(*xs)); dist[k]=c[3]
    print(f"| {k} | {st.mean(c[0]):.0f} | {st.mean(c[1]):.0f} | {st.mean(c[2]):.0f} | {st.mean(c[3]):.0f} | {sorted(c[3])[N//10]:.0f}〜{sorted(c[3])[9*N//10]:.0f} |")
# random player
rng=random.Random(5); xs=[]
for _ in range(N):
    xs.append(sc(*play(random_policy,random.Random(rng.random()),None)))
c=list(zip(*xs)); print('random', [round(st.mean(x)) for x in c], sorted(c[3])[N//10], sorted(c[3])[9*N//10])
keys=list(pols)
a=dist[keys[0]]; 
for k in keys[1:]:
    b=dist[k]; print('P(',k,'> 利益重視)=', sum(1 for x,y in zip(b,a) if x>y)/N)
