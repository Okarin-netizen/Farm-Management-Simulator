import itertools, random, statistics as st, sys, json, pickle, time
import sim
from sim import *
CFG['pest_base']={'default':0.20,'cabbage':0.40,'potato':0.10}
CFG['pest_out']={'default':0.50,'cabbage':0.70,'potato':0.25}
CFG['direct_unsold']=[0,0.10,0.40,0.70]
CFG['pest_cost']['net']=1
CFG.update(json.loads(sys.argv[1]))
out=sys.argv[2]
def pol_factory(spring, autumn, winter_berry_n, pestmap, fert, ships, house_n, house_season):
    def pol(season, money, houses):
        plan=[]
        for i in range(3):
            build = (season==house_season and i<house_n and i>=houses)
            crop={'spring':spring,'summer':'tomato','autumn':autumn,'winter':'spinach'}[season]
            if season=='winter' and i<winter_berry_n and i<max(houses,house_n): crop='strawberry'
            pest = 'none' if season=='winter' else pestmap[crop]
            plan.append((crop,pest,fert,ships[i],build))
        return plan
    return pol
ship_sets=list(itertools.combinations_with_replacement(['market','direct','contract','process'],3))
pests=['chem','net','none']
res=[]
t=time.time()
for spring in ['cabbage','potato']:
  for autumn in ['cabbage','spinach']:
    for pc in pests:
      for pt in pests:
        for ps in ['none','chem']:
          if spring!='cabbage' and autumn!='cabbage' and pc!='none': continue
          pm={'cabbage':pc,'tomato':pt,'spinach':ps,'potato':ps,'strawberry':'none'}
          for fert in ['chem','compost','none']:
            for ships in ship_sets:
              for hn,hs in [(0,'winter'),(1,'winter'),(3,'winter'),(1,'summer')]:
                key=(spring,autumn,pc,pt,ps,fert,ships,hn,hs)
                p=pol_factory(spring,autumn,hn,pm,fert,ships,hn,hs)
                rng=random.Random(11); acc=[]
                for _ in range(200): acc.append(play(p,rng,None))
                c=list(zip(*acc)); res.append((key,[st.mean(x) for x in c],[st.pstdev(x) for x in c]))
pickle.dump(res,open(out,'wb')); print(len(res), time.time()-t)
