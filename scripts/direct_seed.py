"""
FlowSync Direct Seeder — standalone, no external deps beyond psycopg2.
Run inside container: python /app/scripts/direct_seed.py
Run from host:       DATABASE_URL=postgresql://flowsync:...@localhost:5432/flowsync_bi python scripts/direct_seed.py
"""
import os, sys, uuid, random
from datetime import date, datetime, timedelta
from psycopg2.extras import execute_values

DATABASE_URL = os.getenv("DATABASE_URL",
    "postgresql://flowsync:flowsync_secret_change_me@postgres:5432/flowsync_bi")
N_ACCOUNTS = int(os.getenv("SEED_ACCOUNTS", "200"))
N_MONTHS   = int(os.getenv("SEED_MONTHS",   "24"))
random.seed(int(os.getenv("SEED_RANDOM_SEED", "42")))

PLANS = [
    {"id":"starter",      "name":"Starter",      "mrr":99.0,   "seats":5},
    {"id":"professional", "name":"Professional",  "mrr":299.0,  "seats":15},
    {"id":"business",     "name":"Business",      "mrr":799.0,  "seats":50},
    {"id":"enterprise",   "name":"Enterprise",    "mrr":1999.0, "seats":200},
]
PW = [0.35, 0.30, 0.22, 0.13]
REGIONS    = ["North America","Europe","APAC","LATAM"]
INDUSTRIES = ["Technology","Finance","Healthcare","Retail","Manufacturing","Education"]
SIZES      = ["SMB","Mid-Market","Enterprise"]
CHANNELS   = ["Organic","Paid Search","Referral","Partner","Direct Sales","Content"]
COUNTRIES  = {"North America":["United States","Canada"],"Europe":["United Kingdom","Germany","France"],
               "APAC":["Australia","Japan","Singapore"],"LATAM":["Brazil","Mexico","Colombia"]}
PFXS = ["Acme","Apex","Atlas","Beacon","Blue","Cedar","Cloud","Core","Delta","Echo",
        "Edge","Falcon","Forge","Gem","Globe","Harbor","Helix","Horizon","Iris","Iron",
        "Jade","Kite","Lark","Leaf","Lynx","Maple","Mesa","Mint","Nexus","Nova",
        "Oak","Onyx","Orbit","Peak","Pine","Pixel","Prism","Pulse","Quest","Raven",
        "Ridge","River","Sage","Scout","Shift","Shore","Signal","Silver","Sky","Slate",
        "Solar","Spark","Sphere","Star","Steel","Stone","Storm","Summit","Swift","Terra",
        "Tide","Titan","Tower","Trek","Vault","Vega","Vibe","Vista","Volt","Wave"]
SFXS = ["AI","Analytics","Apps","Cloud","Co","Corp","Data","Digital","Dynamics",
        "Edge","Flow","Force","Forge","Group","Hub","Inc","Insights","IO","Labs",
        "Logic","Media","Networks","Nexus","One","Ops","Platform","Pro","Scale",
        "Solutions","Systems","Tech","Technologies","Works"]

def uid(): return str(uuid.uuid4())
def co():  return f"{random.choice(PFXS)} {random.choice(SFXS)}"

def add_months(d, n):
    m = d.month - 1 + n
    y = d.year + m // 12
    mo = m % 12 + 1
    dim = [31,28+int(y%4==0 and(y%100!=0 or y%400==0)),31,30,31,30,31,31,30,31,30,31]
    return date(y, mo, min(d.day, dim[mo-1]))

def fom(d): return d.replace(day=1)
def mbetween(d1,d2): return (d2.year-d1.year)*12+(d2.month-d1.month)

def gen_accounts(end_month):
    start = add_months(end_month, -N_MONTHS)
    accs = []
    for i in range(N_ACCOUNTS):
        reg  = random.choice(REGIONS)
        plan = random.choices(PLANS, weights=PW)[0]
        cm   = add_months(start, random.randint(0, N_MONTHS-1))
        cat  = datetime(cm.year, cm.month, 1, 9, 0)
        churn = None
        if random.random() < 0.25:
            cm2 = add_months(cm, random.randint(3, N_MONTHS))
            if cm2 < end_month: churn = cm2
        accs.append({"id":uid(),"name":co(),"industry":random.choice(INDUSTRIES),
                     "region":reg,"country":random.choice(COUNTRIES[reg]),
                     "size":random.choices(SIZES,weights=[0.5,0.35,0.15])[0],
                     "emp":random.randint(10,5000),"year":random.randint(2005,2022),
                     "channel":random.choice(CHANNELS),"plan":plan,
                     "created":cat,"churned":churn})
    return accs

def insert_accounts(conn, accs):
    rows = [(a["id"],a["name"],a["industry"],a["region"],a["country"],
             a["size"],a["emp"],a["year"],f"https://co-{i}.io",
             a["channel"],a["created"],a["created"])
            for i,a in enumerate(accs)]
    with conn.cursor() as c:
        execute_values(c,
            "INSERT INTO staging.stg_accounts"
            "(account_id,company_name,industry,region,country,company_size,"
            "employee_count,founded_year,website,acquisition_channel,created_at,updated_at)"
            " VALUES %s ON CONFLICT(account_id) DO NOTHING", rows)
    conn.commit()
    print(f"  [OK] stg_accounts: {len(rows)}")

def insert_subscriptions(conn, accs, end_month):
    sub_map = {}
    rows = []
    for a in accs:
        sid  = uid()
        p    = a["plan"]
        st   = fom(a["created"].date())
        ed   = fom(a["churned"]) if a["churned"] and a["churned"]<end_month else None
        stat = "cancelled" if ed else "active"
        su   = max(1, int(p["seats"]*random.uniform(0.3,0.95)))
        sub  = {"sid":sid,"aid":a["id"],"plan_id":p["id"],"plan_name":p["name"],
                "status":stat,"mrr":p["mrr"],"seats":p["seats"],"seats_used":su,
                "start":st,"end":ed,"created":a["created"]}
        sub_map[a["id"]] = sub
        rows.append((sid,a["id"],p["id"],p["name"],stat,p["mrr"],p["mrr"]*12,
                     random.choice(["monthly","annual"]),p["seats"],su,
                     None,None,st,ed,
                     datetime(ed.year,ed.month,1) if ed else None,
                     a["created"],a["created"]))
    with conn.cursor() as c:
        execute_values(c,
            "INSERT INTO staging.stg_subscriptions"
            "(subscription_id,account_id,plan_id,plan_name,status,mrr_amount,arr_amount,"
            "billing_cycle,seats_licensed,seats_used,trial_start_date,trial_end_date,"
            "start_date,end_date,cancelled_at,created_at,updated_at)"
            " VALUES %s ON CONFLICT(subscription_id) DO NOTHING", rows)
    conn.commit()
    print(f"  [OK] stg_subscriptions: {len(rows)}")
    return sub_map

def insert_invoices(conn, accs, sub_map, end_month):
    start = add_months(end_month, -N_MONTHS)
    rows = []
    for a in accs:
        s  = sub_map[a["id"]]
        cm = max(s["start"], start)
        se = s["end"] or end_month
        while cm < se:
            dd = cm.replace(day=15)
            fail = random.random() < 0.04
            rows.append((uid(),a["id"],s["sid"],s["mrr"],"USD",
                         "failed" if fail else "paid",dd,
                         dd+timedelta(days=2) if not fail else None,
                         dd if fail else None,
                         "Card declined" if fail else None,
                         cm, datetime(cm.year,cm.month,1)))
            cm = add_months(cm,1)
    with conn.cursor() as c:
        for i in range(0,len(rows),500):
            execute_values(c,
                "INSERT INTO staging.stg_invoices"
                "(invoice_id,account_id,subscription_id,amount,currency,status,"
                "due_date,paid_date,failed_date,failure_reason,invoice_date,created_at)"
                " VALUES %s ON CONFLICT(invoice_id) DO NOTHING", rows[i:i+500])
    conn.commit()
    print(f"  [OK] stg_invoices: {len(rows)}")

def insert_tickets(conn, accs, end_month):
    start = add_months(end_month, -N_MONTHS)
    cats  = ["billing","technical","feature_request","onboarding","general"]
    pris  = ["low","medium","high","urgent"]
    rows  = []
    for a in accs:
        for _ in range(random.randint(0,8)):
            dt = datetime(start.year,start.month,1)+timedelta(days=random.randint(0,N_MONTHS*30))
            if dt.date()>end_month: continue
            res = random.random()<0.75
            rdt = dt+timedelta(hours=random.randint(2,72)) if res else None
            rows.append((uid(),a["id"],uid(),f"Issue with {random.choice(cats)}",
                         random.choice(cats),random.choice(pris),
                         "resolved" if res else "open",
                         round(random.uniform(2.5,5.0),1) if res else None,
                         dt,rdt,dt+timedelta(hours=random.randint(1,8))))
    with conn.cursor() as c:
        execute_values(c,
            "INSERT INTO staging.stg_support_tickets"
            "(ticket_id,account_id,user_id,subject,category,priority,status,"
            "csat_score,created_at,resolved_at,first_response_at)"
            " VALUES %s ON CONFLICT(ticket_id) DO NOTHING", rows)
    conn.commit()
    print(f"  [OK] stg_support_tickets: {len(rows)}")

def insert_leads_funnel(conn, accs, end_month):
    start  = add_months(end_month, -N_MONTHS)
    stages = ["lead","qualified","trial","paid"]
    lr, fr = [], []
    for a in accs:
        lid = uid()
        cat = a["created"]-timedelta(days=random.randint(14,90))
        ts  = (cat+timedelta(days=random.randint(1,7))).date()
        te  = ts+timedelta(days=14)
        d2p = (a["created"].date()-cat.date()).days
        lr.append((lid,a["name"],"Contact","c@ex.com",a["industry"],a["size"],
                   a["channel"],a["channel"],"converted",ts,te,a["created"],a["id"],
                   a["plan"]["mrr"],cat,cat))
        fr.append((lid,"paid",a["channel"],a["industry"],a["size"],
                   True,d2p,a["plan"]["mrr"],fom(cat.date()),ts,te,a["created"]))
    for i in range(int(N_ACCOUNTS*1.5)):
        lid = uid()
        dt  = datetime(start.year,start.month,1)+timedelta(days=random.randint(0,N_MONTHS*30))
        if dt.date()>end_month: dt=datetime(end_month.year,end_month.month,1)
        stg = random.choices(stages,weights=[0.40,0.25,0.20,0.15])[0]
        ch  = random.choice(CHANNELS)
        ind = random.choice(INDUSTRIES)
        sz  = random.choices(SIZES,weights=[0.5,0.35,0.15])[0]
        pl  = random.choices(PLANS,weights=PW)[0]
        cv  = stg=="paid"
        ts  = (dt+timedelta(days=random.randint(1,14))).date() if stg in("trial","paid") else None
        te  = ts+timedelta(days=14) if ts else None
        d2p = random.randint(14,90) if cv else None
        lr.append((lid,co(),"Contact",f"l{i}@ex.com",ind,sz,ch,ch,stg,ts,te,
                   dt if cv else None,None,pl["mrr"] if cv else 0.0,dt,dt))
        fr.append((lid,stg,ch,ind,sz,cv,d2p,pl["mrr"] if cv else None,
                   fom(dt.date()),ts,te,dt if cv else None))
    with conn.cursor() as c:
        execute_values(c,
            "INSERT INTO staging.stg_leads"
            "(lead_id,company_name,contact_name,contact_email,industry,company_size,"
            "acquisition_channel,lead_source,status,trial_start_date,trial_end_date,"
            "converted_at,account_id,estimated_mrr,created_at,updated_at)"
            " VALUES %s ON CONFLICT(lead_id) DO NOTHING", lr)
        execute_values(c,
            "INSERT INTO marts.fct_sales_conversion"
            "(lead_id,funnel_stage,acquisition_channel,industry,company_size,"
            "is_paid_conversion,days_lead_to_paid,converted_mrr,"
            "lead_created_month,trial_start_date,trial_end_date,converted_at)"
            " VALUES %s", fr)
    conn.commit()
    print(f"  [OK] stg_leads: {len(lr)}, fct_sales_conversion: {len(fr)}")

def compute_mrr_movements(conn, accs, sub_map, end_month):
    start = add_months(end_month, -N_MONTHS)
    rows  = []
    prev  = {}
    cm    = start
    while cm < end_month:
        for a in accs:
            aid = a["id"]
            s   = sub_map[aid]
            mrr = s["mrr"]
            act = s["start"]<=cm and (s["end"] is None or s["end"]>cm)
            was = aid in prev
            if act and not was:
                mt="new"; nm=mrr; ex=co2=ch=re=0.0; end=mrr
            elif act and was:
                d=mrr-prev[aid]
                if d>5:   mt="expansion";   ex=d;       nm=co2=ch=re=0.0
                elif d<-5: mt="contraction"; co2=abs(d); nm=ex=ch=re=0.0
                else:      mt="retained";    nm=ex=co2=ch=re=0.0
                end=mrr
            elif not act and was:
                mt="churn"; ch=prev[aid]; nm=ex=co2=re=0.0; end=0.0; mrr=0.0
            else:
                continue
            net=nm+ex+re-co2-ch
            rows.append((aid,cm,end,mt,nm,ex,co2,ch,re,net,
                         s["plan_name"],a["region"],a["industry"],a["size"],a["channel"]))
        for a in accs:
            aid=a["id"]; s=sub_map[aid]
            act=s["start"]<=cm and(s["end"] is None or s["end"]>cm)
            if act: prev[aid]=s["mrr"]
            elif aid in prev: del prev[aid]
        cm=add_months(cm,1)
    with conn.cursor() as c:
        for i in range(0,len(rows),1000):
            execute_values(c,
                "INSERT INTO marts.fct_mrr_movements"
                "(account_id,month_key,mrr,mrr_movement_type,"
                "new_mrr,expansion_mrr,contraction_mrr,churned_mrr,"
                "reactivation_mrr,net_mrr_contribution,"
                "plan_name,region,industry,company_size,acquisition_channel)"
                " VALUES %s ON CONFLICT(account_id,month_key) DO NOTHING", rows[i:i+1000])
    conn.commit()
    print(f"  [OK] fct_mrr_movements: {len(rows)}")

def compute_health(conn, accs, sub_map, end_month):
    start = add_months(end_month, -N_MONTHS)
    rows  = []
    for a in accs:
        s  = sub_map[a["id"]]
        ss = s["start"]
        se = s["end"] or end_month
        cm = max(ss, start)
        while cm < min(se, end_month):
            seats = s["seats"]
            au    = max(1, int(seats*random.uniform(0.2,0.95)))
            fu    = random.randint(2,12)
            ot    = random.randint(0,5)
            csat  = round(random.uniform(2.5,5.0),1)
            dl    = random.randint(0,30)
            pf    = random.randint(0,2)
            sess  = random.randint(10,300)
            us    = min(100.0,(sess/150.0)*100)
            ss2   = (au/seats)*100
            fs    = (fu/12.0)*100
            sups  = max(0.0,100.0-ot*20)
            cs2   = ((csat-1)/4.0)*100
            ps    = max(0.0,100.0-pf*40)
            hs    = round((us*0.25+ss2*0.20+fs*0.20+sups*0.15+cs2*0.10+ps*0.10),2)
            tier  = "healthy" if hs>=70 else ("at_risk" if hs>=50 else "critical")
            risk  = "low" if hs>=70 else ("medium" if hs>=50 else "high")
            rsc   = round(100-hs,2)
            flags = []
            if dl>14:    flags.append("no_login_14d")
            if ot>=2:    flags.append("support_overload")
            if pf>0:     flags.append("payment_failure")
            if csat<3:   flags.append("low_csat")
            if au/seats<0.25: flags.append("low_seat_util")
            ten   = mbetween(ss,cm)
            usage_drop = random.random() < 0.15
            rows.append((
                a["id"],cm,a["name"],s["plan_name"],s["mrr"],
                hs,tier,risk,rsc,len(flags),flags,
                a["size"],a["region"],a["industry"],a["channel"],
                sess,au,seats,s["seats_used"],fu,ot,csat,dl,ten,
                round(us,2),round(ss2,2),round(fs,2),round(sups,2),round(ps,2),round(ten/24*100,2),
                usage_drop,dl>14,ot>=2,pf>0,csat<3,au/seats<0.25
            ))
            cm=add_months(cm,1)
    with conn.cursor() as c:
        for i in range(0,len(rows),500):
            execute_values(c,
                "INSERT INTO marts.fct_account_monthly_health"
                "(account_id,month_key,company_name,plan_name,mrr,"
                "health_score,health_tier,churn_risk_level,churn_risk_score,risk_flag_count,risk_reasons,"
                "company_size,region,industry,acquisition_channel,"
                "monthly_sessions,active_users,seats_licensed,seats_used,features_used,"
                "open_tickets,avg_csat,days_since_login,tenure_months,"
                "usage_score,seat_utilization_score,feature_adoption_score,"
                "support_score,payment_score,tenure_score,"
                "flag_usage_drop,flag_no_login,flag_support_overload,"
                "flag_payment_failure,flag_low_csat,flag_low_seat_util)"
                " VALUES %s ON CONFLICT(account_id,month_key) DO NOTHING", rows[i:i+500])
    conn.commit()
    print(f"  [OK] fct_account_monthly_health: {len(rows)}")

def run_sql_file(conn, path):
    with open(path) as f:
        sql = f.read()
    with conn.cursor() as c:
        c.execute(sql)
    conn.commit()
    print(f"  [OK] ran {path}")

def main():
    import psycopg2
    print(f"Connecting to: {DATABASE_URL[:40]}...")
    conn = psycopg2.connect(DATABASE_URL)
    end_month = date.today().replace(day=1)

    print("\n[1/7] Generating accounts...")
    accs = gen_accounts(end_month)

    print("[2/7] Inserting staging.stg_accounts...")
    insert_accounts(conn, accs)

    print("[3/7] Inserting staging.stg_subscriptions...")
    sub_map = insert_subscriptions(conn, accs, end_month)

    print("[4/7] Inserting staging.stg_invoices...")
    insert_invoices(conn, accs, sub_map, end_month)

    print("[5/7] Inserting staging.stg_support_tickets...")
    insert_tickets(conn, accs, end_month)

    print("[6/7] Inserting staging.stg_leads + marts.fct_sales_conversion...")
    insert_leads_funnel(conn, accs, end_month)

    print("[7/7] Computing marts.fct_mrr_movements...")
    compute_mrr_movements(conn, accs, sub_map, end_month)

    print("[8/8] Computing marts.fct_account_monthly_health...")
    compute_health(conn, accs, sub_map, end_month)

    # Run SQL aggregations
    sql_path = os.path.join(os.path.dirname(__file__), "seed_sql.sql")
    if os.path.exists(sql_path):
        print("[9/9] Running aggregation SQL (exec summary, cohorts, customer success)...")
        run_sql_file(conn, sql_path)
    else:
        print(f"  [WARN] {sql_path} not found — skipping aggregations")

    conn.close()
    print("\nSeed complete!")

    # Print row counts
    import psycopg2
    conn2 = psycopg2.connect(DATABASE_URL)
    tables = [
        "staging.stg_accounts","staging.stg_subscriptions","staging.stg_invoices",
        "staging.stg_support_tickets","staging.stg_leads",
        "marts.fct_mrr_movements","marts.fct_account_monthly_health",
        "marts.fct_customer_cohorts","marts.fct_sales_conversion",
        "marts.mart_exec_revenue_summary","marts.mart_customer_success_summary",
    ]
    print("\nRow counts:")
    with conn2.cursor() as c:
        for t in tables:
            c.execute(f"SELECT COUNT(*) FROM {t}")
            n = c.fetchone()[0]
            print(f"  {t}: {n:,}")
    conn2.close()

if __name__ == "__main__":
    main()
