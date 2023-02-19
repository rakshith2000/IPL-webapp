from datetime import datetime
from . import db
from .models import User, Pointstable, Fixture
import os, csv
from werkzeug.security import generate_password_hash, check_password_hash
from flask import Blueprint, render_template, url_for, redirect, request, flash
from flask_login import login_required, current_user
from sqlalchemy import and_, or_

main = Blueprint('main', __name__)

pofs = {'Q1':'Qualifier 1', 'E':'Eliminator', 'Q2':'Qualifier 2', 'F':'Final'}

full_name = {'CSK':'Chennai Super Kings',
             'DC':'Delhi Capitals',
             'GT':'Gujarat Titans',
             'KKR':'Kolkata Knight Riders',
             'LSG':'Lucknow Super Giants',
             'MI':'Mumbai Indians',
             'PBKS':'Punjab Kings',
             'RCB':'Royal Challengers Bangalore',
             'RR':'Rajasthan Royals',
             'SRH':'Sunrisers Hydrabad',
             'TBA':'TBA'}

def oversAdd(a, b):
    A, B = round(int(a)*6 + (a-int(a))*10, 0), round(int(b)*6 + (b-int(b))*10, 2)
    S = int(A) + int(B)
    s = S//6 + (S%6)/10
    return s

def oversSub(a, b):
    A, B = round(int(a) * 6 + (a - int(a)) * 10, 0), round(int(b) * 6 + (b - int(b)) * 10, 2)
    S = int(A) - int(B)
    s = S // 6 + (S % 6) / 10
    return s

def ovToPer(n):
    return (int(n)+((n-int(n))*10)/6)

def updatePointsTable(a, A, b, B, wt, match_no):
    print(A, B)
    A[1] = 20 if A[2] == 10 else A[1]
    B[1] = 20 if B[2] == 10 else B[1]
    dataA = db.session.execute('select team_name,P,W,L,Points,For,Against,Win_List from pointstable where team_name=="{}"'.format(str(a)))
    print(dataA)
    for i in dataA:
        if i[0] == wt:
            P, W, L, Points = 1+i[1], 1+i[2], 0+i[3], i[4]+2
            wl = eval(i[7])
            wl[match_no] = 'W'
            wl = dict(sorted(wl.items()))
        else:
            P, W, L, Points = 1+i[1], 0+i[2], 1+i[3], i[4]+0
            wl = eval(i[7])
            wl[match_no] = 'L'
            wl = dict(sorted(wl.items()))
        forRuns = eval(i[5])['runs'] + A[0]
        forOvers = oversAdd(eval(i[5])['overs'], A[1])
        againstRuns = eval(i[6])['runs'] + B[0]
        againstOvers = oversAdd(eval(i[6])['overs'], B[1])
        NRR = round((forRuns/ovToPer(forOvers) - againstRuns/ovToPer(againstOvers)), 3)
        PT = Pointstable.query.filter_by(team_name=str(a)).first()
        PT.P, PT.W, PT.L, PT.Points, PT.NRR, PT.Win_List = P, W, L, Points, NRR, str(wl)
        PT.For = {"runs":forRuns, "overs":forOvers}
        PT.Against = {"runs":againstRuns, "overs":againstOvers}
        db.session.commit()

    dataB = db.session.execute('select team_name,P,W,L,Points,For,Against,Win_List from pointstable where team_name=="{}"'.format(str(b)))
    for i in dataB:
        print(i)
    for i in dataB:
        if i[0] == wt:
            P, W, L, Points = 1 + i[1], 1 + i[2], 0 + i[3], i[4] + 2
            wl = eval(i[7])
            wl[match_no] = 'W'
            wl = dict(sorted(wl.items()))
        else:
            P, W, L, Points = 1 + i[1], 0 + i[2], 1 + i[3], i[4] + 0
            wl = eval(i[7])
            wl[match_no] = 'L'
            wl = dict(sorted(wl.items()))
        forRuns = eval(i[5])['runs'] + B[0]
        forOvers = oversAdd(eval(i[5])['overs'], B[1])
        againstRuns = eval(i[6])['runs'] + A[0]
        againstOvers = oversAdd(eval(i[6])['overs'], A[1])
        NRR = round((forRuns/ovToPer(forOvers) - againstRuns/ovToPer(againstOvers)), 3)
        PT = Pointstable.query.filter_by(team_name=str(b)).first()
        PT.P, PT.W, PT.L, PT.Points, PT.NRR, PT.Win_List = P, W, L, Points, NRR, str(wl)
        PT.For = {"runs": forRuns, "overs": forOvers}
        PT.Against = {"runs": againstRuns, "overs": againstOvers}
        db.session.commit()

@main.route('/')
def index():
    if db.session.execute('select count() from user').scalar() == 0:
        user = User(email='adminipl2022@gmail.com', \
                    password=generate_password_hash('Admin@ipl2022', method='sha256'), \
                    name='AdminIPL2022')
        db.session.add(user)
        db.session.commit()
    if db.session.execute('select count() from pointstable').scalar() == 0:
        teams = ['CSK', 'DC', 'GT', 'KKR', 'LSG', 'MI', 'PBKS', 'RCB', 'RR', 'SRH']
        inter = os.getcwd()
        for i in teams:
            tm = Pointstable(team_name=i, P=0,W=0,L=0,NR=0,\
                    Points=0, NRR=0.0, Win_List=str({}),\
                logo_path='{}/IPL/static/images/{}.png'.format(inter,i),\
                For={'runs':0, 'overs':0.0}, Against={'runs':0, 'overs':0.0})
            db.session.add(tm)
            db.session.commit()
    if db.session.execute('select count() from fixture').scalar() == 0:
        df = open('IPL/IPL2022.csv', 'r')
        df = list(csv.reader(df))
        for i in df[1:]:
            mt = Fixture(Match_No=i[0], Date=(datetime.strptime(i[1],'%Y-%m-%d')).date(),\
                                    Team_A=i[2], Team_B=i[3], Venue=i[4],\
                                    A_info={'runs':0, 'overs':0.0, 'wkts':0},\
                                    B_info={'runs':0, 'overs':0.0, 'wkts':0})
            db.session.add(mt)
            db.session.commit()
    return render_template('index.html')

@main.route('/pointstable')
def displayPT():
    dataPT = Pointstable.query.order_by(Pointstable.Points.desc(),Pointstable.NRR.desc()).all()
    dt = [['Pos', 'Logo', 'Teams', 'Played', 'Won', 'Lost', 'No Result', 'Points', 'NRR', 'Last 5'], [i for i in range(1,11)],\
         [], [], [], [], [], [], [], [], []]
    for i in dataPT:
        img = "/static/images/{}.png".format(i.team_name)
        dt[2].append(img)
        dt[3].append(full_name[i.team_name])
        dt[4].append(i.P)
        dt[5].append(i.W)
        dt[6].append(i.L)
        dt[7].append(i.NR)
        dt[8].append(i.Points)
        I = '{0:+}'.format(i.NRR)
        dt[9].append(I)
        wl = eval(i.Win_List).values()
        wl = wl if len(wl)<5 else wl[-5:]
        wl = list(wl)[::-1]
        wl = ''.join(wl)
        dt[10].append(wl)
    return render_template('displayPT.html', PT=dt)

@main.route('/fixtures')
def displayFR():
    team = request.args.get('team','All',type=str)
    print(team)
    if team == 'All':
        dataFR = db.session.execute('select * from Fixture')\
            #Fixture.query.all()
        hint = 'All'
    else:
        dataFR = db.session.execute('select * from Fixture where Team_A=="{}" or Team_B=="{}"'.format(team, team)) \
            #Fixture.query.filter_by(or_(Fixture.Team_A == team, Fixture.Team_B == team)).all()
        hint = team
    dt = [['Match No', 'Date', 'Match B/W', 'Score', 'Venue', 'Result'], [], [], [], [], [], []]
    for i in dataFR:
        dt[1].append(i[1])
        dt[2].append(datetime.strptime(i[2],'%Y-%m-%d').strftime('%d-%b-%Y'))
        dt[3].append(full_name[i[3]]+'\nvs\n'+full_name[i[4]])
        A, B = eval(i[7]), eval(i[8])
        score = '{}/{} ({})\n\n{}/{} ({})'.format(str(A['runs']),str(A['wkts']),str(A['overs']),\
                                                str(B['runs']),str(B['wkts']),str(B['overs']))
        dt[4].append(score)
        dt[5].append(str(i[5]).replace(' St', '\nSt') if ' St' in str(i[5]) else i[5])
        if i[6] == None:
            txt = 'Upcoming'
        else:
            txt = i[6]
        dt[6].append(txt)
    length = len(dt[1])
    return render_template('displayFR.html', FR=dt, length=length, hint=hint)

@main.route('/update')
@login_required
def update():
    return render_template('update.html')

@main.route('/updatematch', methods=['POST'])
@login_required
def updatematch():
    hint = request.form.get('hint')
    if request.method == "POST" and hint == 'before':
        match = request.form.get('match')
        print(match)
        FR = Fixture.query.filter_by(Match_No=match).first()
        print(FR.Team_A)
        return render_template('updatematch.html', FR=FR, fn=full_name, match=match)
    if request.method == 'POST' and hint == 'after':
        A = [int(request.form['runsA']), float(request.form['oversA']), int(request.form['wktsA'])]
        B = [int(request.form['runsB']), float(request.form['oversB']), int(request.form['wktsB'])]
        wt, win_type, win_by = str(request.form['wt']).upper(), str(request.form['win_type']), str(request.form['win_by'])
        result = '{} won by {} {}'.format(full_name[wt], win_by, win_type)
        match_no = str(request.form['match'])
        FR = Fixture.query.filter_by(Match_No=match_no).first()
        a, b = FR.Team_A,  FR.Team_B
        FR.Result = result
        FR.Win_T = wt
        FR.A_info, FR.B_info = {'runs':A[0], 'overs':A[1], 'wkts':A[2]}, {'runs':B[0], 'overs':B[1], 'wkts':B[2]}
        db.session.commit()
        print(a, b)
        A[1] = 20 if A[2] == 10 else A[1]
        B[1] = 20 if B[2] == 10 else B[1]
        dataA = db.session.execute('select team_name,P,W,L,Points,For,Against,Win_List from pointstable where team_name=="{}"'.format(str(a)))

        for i in dataA:
            print('Hello')
            if i[0] == wt:
                P, W, L, Points = 1 + i[1], 1 + i[2], 0 + i[3], i[4] + 2
                wl = eval(i[7])
                wl[match_no] = 'W'
                wl = dict(sorted(wl.items()))
            else:
                P, W, L, Points = 1 + i[1], 0 + i[2], 1 + i[3], i[4] + 0
                wl = eval(i[7])
                wl[match_no] = 'L'
                wl = dict(sorted(wl.items()))
            forRuns = eval(i[5])['runs'] + A[0]
            forOvers = oversAdd(eval(i[5])['overs'], A[1])
            againstRuns = eval(i[6])['runs'] + B[0]
            againstOvers = oversAdd(eval(i[6])['overs'], B[1])
            NRR = round((forRuns / ovToPer(forOvers) - againstRuns / ovToPer(againstOvers)), 3)
        PT = Pointstable.query.filter_by(team_name=str(a)).first()
        PT.P, PT.W, PT.L, PT.Points, PT.NRR, PT.Win_List = P, W, L, Points, NRR, str(wl)
        PT.For = {"runs": forRuns, "overs": forOvers}
        PT.Against = {"runs": againstRuns, "overs": againstOvers}
        db.session.commit()

        dataB = db.session.execute('select team_name,P,W,L,Points,For,Against,Win_List from pointstable where team_name=="{}"'.format(str(b)))

        for i in dataB:
            if i[0] == wt:
                P, W, L, Points = 1 + i[1], 1 + i[2], 0 + i[3], i[4] + 2
                wl = eval(i[7])
                wl[match_no] = 'W'
                wl = dict(sorted(wl.items()))
            else:
                P, W, L, Points = 1 + i[1], 0 + i[2], 1 + i[3], i[4] + 0
                wl = eval(i[7])
                wl[match_no] = 'L'
                wl = dict(sorted(wl.items()))
            forRuns = eval(i[5])['runs'] + B[0]
            forOvers = oversAdd(eval(i[5])['overs'], B[1])
            againstRuns = eval(i[6])['runs'] + A[0]
            againstOvers = oversAdd(eval(i[6])['overs'], A[1])
            NRR = round((forRuns / ovToPer(forOvers) - againstRuns / ovToPer(againstOvers)), 3)
        PT = Pointstable.query.filter_by(team_name=str(b)).first()
        PT.P, PT.W, PT.L, PT.Points, PT.NRR, PT.Win_List = P, W, L, Points, NRR, str(wl)
        PT.For = {"runs": forRuns, "overs": forOvers}
        PT.Against = {"runs": againstRuns, "overs": againstOvers}
        db.session.commit()

        #updatePointsTable(a, A, b, B, wt, match_no)
        flash('Match result is updated successfully')
        return redirect(url_for('main.update'))
