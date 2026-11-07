import random, itertools, statistics as st, sys

SEASONS = ['spring', 'summer', 'autumn', 'winter']
CROPS = {
    'spinach':   dict(seasons={'spring','autumn','winter'}, cost=2, sales=5, house=False),
    'potato':    dict(seasons={'spring'}, cost=2, sales=5, house=False),
    'cabbage':   dict(seasons={'spring','autumn'}, cost=3, sales=7, house=False),
    'tomato':    dict(seasons={'summer'}, cost=4, sales=10, house=False),
    'strawberry':dict(seasons={'winter'}, cost=6, sales=15, house=True),
}
CFG = dict(
    start=30, house_cost=10, heat_cost=2, heat_env=-1,
    pest_base={'default':0.20,'cabbage':0.30,'potato':0.10},   # no-measure loss outside winter
    pest_out={'default':0.50,'cabbage':0.70,'potato':0.25},
    net_factor=0.5,
    pest_cost={'chem':1,'net':2,'none':0}, pest_env={'chem':-2,'net':0,'none':0},
    fert={'chem':(1,0.20,-1),'compost':(1,0.10,1),'none':(0,0,0)},
    direct_bonus=1.2, direct_unsold=[0,0.20,0.35,0.50], direct_unsold_mult=0.7,
    proc_price=0.8, proc_recover=0.5,
    school_money=3, school_region=2,
)
# event deck weights per season
DECK = {
 'spring': dict(typhoon=0, heat=0, rain=1, pest=2, high=1, crash=1, super_=1, school=1, normal=2),
 'summer': dict(typhoon=2, heat=2, rain=2, pest=2, high=1, crash=1, super_=1, school=0, normal=1),
 'autumn': dict(typhoon=2, heat=0, rain=1, pest=1, high=1, crash=2, super_=1, school=1, normal=2),
 'winter': dict(typhoon=0, heat=0, rain=0, pest=0, high=2, crash=1, super_=1, school=2, normal=3),
}
def draw(season, rng):
    d = DECK[season]; ks=list(d); ws=[d[k] for k in ks]
    return rng.choices(ks, ws)[0]

def weather_loss(ev, crop, house):
    loss = 0
    if ev=='typhoon': loss=0.5; hf=0.5
    elif ev=='heat': loss = 0.5 if crop=='spinach' else 0.1; hf=0.5
    elif ev=='rain': loss = 0.5 if crop=='tomato' else 0; hf=0.0
    else: return 0
    if crop=='potato': loss*=0.5
    if house: loss*=hf
    return loss

def pest_loss(ev, season, crop, pest):
    if season=='winter': return 0
    tbl = CFG['pest_out'] if ev=='pest' else CFG['pest_base']
    l = tbl.get(crop, tbl['default'])
    if pest=='chem': return 0
    if pest=='net': return l*CFG['net_factor']
    return l

def play(policy, rng, score_fn):
    money=CFG['start']; env=0; region=0; houses=0
    for si,season in enumerate(SEASONS):
        plan = policy(season, money, houses)  # list of 3 (crop|None, pest, fert, ship, build_house)
        cost=0
        anyb=False
        for p in plan:
            crop,pest,fert,ship,build = p
            if build:
                anyb=True
                if not CFG.get('house_all'): cost+=CFG['house_cost']
            if crop:
                cost+=CRAPS(crop)+CFG['pest_cost'][pest]+CFG['fert'][fert][0]
        # houses: plots 0..houses-1 are houses (+ new builds)
        newh = houses + sum(1 for p in plan if p[4])
        if CFG.get('house_all') and anyb and houses==0: cost+=CFG['house_cost']; newh=3
        cost += sum(CFG['heat_cost'] for i,p in enumerate(plan) if p[0] and season=='winter' and i<newh)
        if cost>money:  # fallback: plant nothing
            plan=[(None,'none','none','market',False)]*3; cost=0; newh=houses
        houses=newh
        money-=cost
        ev = draw(season, rng)
        ndirect = sum(1 for p in plan if p[0] and p[3]=='direct')
        unsold = (ev!='super_') and rng.random() < CFG['direct_unsold'][ndirect]
        sales=0
        for i,p in enumerate(plan):
            crop,pest,fert,ship,_=p
            if not crop: continue
            house = i<houses
            fc,fy,fe = CFG['fert'][fert]
            env+=fe+CFG['pest_env'][pest]
            if season=='winter' and house: env+=CFG['heat_env']
            y0 = 1+fy
            y = y0*(1-weather_loss(ev,crop,house))*(1-pest_loss(ev,season,crop,pest))
            base=CROPS[crop]['sales']
            if ship=='market':
                m = 1.5 if ev=='high' else 0.6 if ev=='crash' else 1.0
                sales+=base*y*m
            elif ship=='direct':
                sales+=base*y*CFG['direct_bonus']*(CFG['direct_unsold_mult'] if unsold else 1); region+=1
            elif ship=='contract':
                sales+=base*y
            elif ship=='process':
                sales+=base*CFG['proc_price']*(y+(y0-y)*CFG['proc_recover']); region+=1
        if ev=='school' and any(p[0] for p in plan):
            sales+=CFG['school_money']; region+=CFG['school_region']
        money+=sales
    profit=money-CFG['start']
    return profit, env, region

def CRAPS(c): return CROPS[c]['cost']

def best_crop(season, houses_after, i, winter_berry):
    if season=='summer': return 'tomato'
    if season=='winter':
        return 'strawberry' if (i<houses_after and winter_berry) else 'spinach'
    return 'cabbage'

def make_policy(pest, fert, ships, nhouse=0, house_season='summer', winter_berry=True, crop_mode='best'):
    # ships: tuple of 3 ship methods per plot
    def pol(season, money, houses):
        plan=[]
        for i in range(3):
            build = (season==house_season and i<nhouse and i>=houses)
            ha = max(houses, nhouse if SEASONS.index(season)>=SEASONS.index(house_season) else houses)
            if crop_mode=='best': crop=best_crop(season, ha, i, winter_berry)
            elif crop_mode=='safe':
                crop={'spring':'potato','summer':'tomato','autumn':'spinach','winter':'spinach'}[season]
                if season=='winter' and i<ha and winter_berry: crop='strawberry'
            else:
                crop=best_crop(season, ha, i, winter_berry)
            p = pest if season!='winter' else 'none'
            plan.append((crop,p,fert,ships[i],build))
        return plan
    return pol

def random_policy(season, money, houses):
    rng=random
    plan=[]
    for i in range(3):
        opts=[c for c,d in CROPS.items() if season in d['seasons'] and (not d['house'] or i<houses)]
        crop=rng.choice(opts+[None]) if rng.random()<0.9 else None
        crop = crop or (opts[0] if rng.random()<0.7 else None)
        plan.append((crop, rng.choice(['chem','net','none']), rng.choice(['chem','compost','none']),
                     rng.choice(['market','direct','contract','process']), False))
    return plan

def norm(profit, env, region, S):
    P = max(0,min(100, profit/S['pmax']*100))
    E = max(0,min(100, (env-S['emin'])/(S['emax']-S['emin'])*100))
    R = max(0,min(100, region/S['rmax']*100))
    return P,E,R

def total(P,E,R,S):
    t=P+E+R
    if S.get('bal'): t += S['bal']*min(P,E,R)
    return t

def evaluate(policy, S, n=3000, seed=1):
    rng=random.Random(seed)
    out=[]
    for _ in range(n):
        pr,e,r=play(policy,rng,None)
        P,E,R=norm(pr,e,r,S)
        out.append((pr,e,r,P,E,R,total(P,E,R,S)))
    cols=list(zip(*out))
    return [st.mean(c) for c in cols], st.pstdev(cols[6]), cols[6]
