import datetime
from django.utils import timezone
from ..models import *
from .auth_controller import *

# ユーザーのデータから
def get_timedata(data):
    r_time = None
    if data.updatedAt == None: # TODO:ここの部分はハード側の編集を行う必要がある 例えば、20分経過していない状態でタッチすると20分未満の時間でラズパイが記録してします
        r_time = (data.createdAt+datetime.timedelta(minutes=20))-data.createdAt
    else:
        # 2回目以降のタッチと初回のタッチの差分をとる
        r_time = data.updatedAt-data.createdAt
    r_time = r_time.total_seconds()
    year = data.createdAt.year
    month = data.createdAt.month
    day = data.createdAt.day
    hours, minutes = get_hm(r_time) # 総秒数を時間と分に変換する
    return year, month, day, hours, minutes, r_time

# 現在が前期なのか後期なのかのサーチ
def get_fiscal():
    date = timezone.now()
    ft = None 
    fy = date.year
    # 0: 前期, 1: 後期
    if (date.month < 9) and (date.month >= 4):
        ft = 0
    else:
        ft = 1
    # 年度の年の判定
    if (date.month <= 3) and (date.month >= 1):
        fy = (date.year - 1)
    return fy, ft # 年度, 前期or後期

def get_goal_time(u_id, focus_term): # 前期、後期のゴールラインの取得
    # ユーザーの学科、専攻を取得
    user = StudentModel.objects.get(u_id=u_id)
    major = user.major

    gt = None # 目標時間
    if (u_id[1] == 'm') or (u_id[1] == 'd'): # 大学院生の場合、通年の目標時間の取得
        gt = (MajorModel.objects.get(m_name=major)).total_term
        return gt
    
    # 前期・後期の目標時間を取得
    if focus_term == 0: #前期
        gt = (MajorModel.objects.get(m_name=major)).first_half_term
    else: # 後期
        gt = (MajorModel.objects.get(m_name=major)).second_half_term
    return gt    

# 総秒数を時間、分に変換
def get_hm(times):
    # 分に変換
    minutes = int(times%3600)
    minutes = int(minutes//60)
    # 時間に変換
    hours = int(times//3600)
    return hours, minutes # 時間、分

# 目標時間と現在の在室時間の差分を返す
def time_remainder(goal, total):
    remainder = goal - total
    if remainder <= 0:
        remainder = 0
    hours, minutes = get_hm(remainder)
    return hours, minutes

# 学生データの取得
def get_student_timedata(uds, u_id, kind=None):
    # ユーザーのデータの取得
    user_data = {}
    total_seconds = 0
    each_total = {}
    for ud in uds:
        # ユーザーの時間データの取得
        year, month, day, hours, minutes, t_seconds = get_timedata(ud)
        if not (month in user_data.keys()):
            user_data[month] = []
            each_total[month] = 0
        core_time_judge = None
        if kind == None:
            core_time_judge = judge_core_time(u_id=u_id, ud=ud)
        user_data[month].append({
            'year':year, 'day':day,
            'hours':make_same_size(hours), 'minutes':make_same_size(minutes),
            'memo': ud.memo, 'r_id': ud.id, 'comment': ud.comment,
            's_notice': ud.s_notice, 't_notice': ud.t_notice, 
            'core_time_judge':core_time_judge
        })
        each_total[month] += t_seconds # 各月のトータルの在室時間(秒)をまとめる
        total_seconds += t_seconds # 在室時間の総秒数を集計
    return user_data, total_seconds, each_total

def get_core_time(u_id=None, t_id=None, kind=0):
    if (u_id == None and t_id == None):
        return [None, None]
    if t_id == None:
        t_id = (StudentModel.objects.get(u_id=u_id)).t_id
    core_time = []
    if kind == 0:
        for i in LaboratoryModel.objects.filter(t_id=t_id):
            if u_id[1] == 'd':
                core_time.append(i.d_core_time_start)
                core_time.append(i.d_core_time_end)
            elif u_id[1] == 'm':
                core_time.append(i.m_core_time_start)
                core_time.append(i.m_core_time_end)
            else:
                core_time.append(i.s_core_time_start)
                core_time.append(i.s_core_time_end)
    else:
        for i in LaboratoryModel.objects.filter(t_id=t_id):
            # 博士のコアタイム
            core_time.append(i.d_core_time_start)
            core_time.append(i.d_core_time_end)
            # 修士のコアタイム
            core_time.append(i.m_core_time_start)
            core_time.append(i.m_core_time_end)
            # 学部のコアタイム
            core_time.append(i.s_core_time_start)
            core_time.append(i.s_core_time_end)
    return core_time

def judge_core_time(u_id, ud):
    # Tコアタイムの時間内に学生が在室しているかを判定
    core_time = get_core_time(u_id=u_id)
    core_time_judge = [None, None]
    if core_time[0] != None: # 出勤時間のチェック
        ct = (ud.createdAt.hour*3600+ud.createdAt.minute*60)
        jts = (ct - (core_time[0].hour*3600+core_time[0].minute*60))
        jth = jts//3600
        jtm = jts//60
        if jtm > 0 and jth >= 0:
            core_time_judge[0] = True
    tn = timezone.now()
    if core_time[1] != None: # 退勤時間のチェック
        if  ud.updatedAt != None:
            ut = (ud.updatedAt.hour*3600+ud.updatedAt.minute*60)
            jts = ((core_time[1].hour*3600+core_time[1].minute*60) - ut)
            jth = jts//3600
            jtm = jts//60
            if jtm > 0 and jth >= 0:
                core_time_judge[1] = True
    return core_time_judge

def make_same_size(data):
    if data < 10 and 0 <= data:
        rs = '0{}'.format(data)
        return rs
    return str(data)
