from ..models import *
from django.http import HttpResponse
from django.contrib.auth.hashers import make_password, check_password
from django.utils import timezone
from .time_controller import *
from .ldap_auth import *
import os

LDAP_USE = False

# Login処理
"""
student:
    学生のログイン処理

teacher:
    教員のログイン処理
"""

# ログイン処理の共通部分
def common_login(data, request, kind, ldap_id=None):
    # ユーザーの検索 TODO: 別の関数にするか検討中
    error_message = None
    rt_code = None
    if data is None:
        error_message = 'ユーザーが見つかりません'
        return error_message

    if ldap_id != None:
        rt_code, error_message = ldap_auth_login(ldap_id, request.POST['password'], 0, []) # debug_mode=0, debug_user=[]で本番環境
    else:
        rt_code = 1

    #ログイン処理
    if rt_code:
        if kind == 0: # 学生のセッション処理
            request.session['id'] = data.u_id
            request.session['name'] = data.u_name
            request.session['target'] = kind
        if kind == 1: # 教員のセッション処理
            request.session['id'] = data.t_id
            request.session['name'] = data.t_name
            request.session['target'] = kind
        if kind == 2:
            if check_password(request.POST['password'], data.password):
                request.session['id'] = data.admin_id
                request.session['target'] = kind
            error_message = ''
        request.session.set_expiry(3600) # セッションの有効期限をセット
        error_message = None
    else:
        error_message = 'ユーザーIDまたは、パスワードが間違っています'
        return error_message
    return error_message # Noneを返せば、ログインは正常に行われたと判定

def not_ldap_common(data, request, kind):
    error_message = None
    if data is None:
        error_message = "ユーザーが見つかりません"
        return error_message
    if check_password(request.POST['password'], data.password):
        if kind == 0:
            request.session['id'] = data.u_id
            request.session['name'] = data.u_name
            request.session['target'] = kind
        if kind == 1:
            request.session['id'] = data.t_id
            request.session['name'] = data.t_name
            request.session['target'] = kind
        if kind == 2:
            request.session['id'] = data.admin_id
            request.session['target'] = kind
        request.session.set_expiry(3600)
        error_message = None
    else:
        error_message = 'ユーザーIDまたは、パスワードが間違っています'
    return error_message

# ログイン処理
def auth_login(request, kind): #Id, pwd, target):
    error_message=None
    data = None
    fy, _ = get_fiscal() # 注目年度を取得
    student_id_app = None
    student_id_ldap = None
    if kind == 2:
        student_id_app = (request.POST['admin_id']).lower()
    if kind == 0: # 学生
        student_id_app = None
        student_id_ldap = None
        try:
            student_id_app = (request.POST['user_id']).lower()
            student_id_ldap = student_id_app
            if 's' == student_id_app[0] or 'm' == student_id_app[0]:
                student_id_ldap = student_id_app
                student_id_app = student_id_app[1:]
            else:
                if student_id_app[1] == 'm':
                    student_id_ldap = ('m'+student_id_app)
                else:
                    student_id_ldap = ('s'+student_id_app)
        except:
            print('happen error.')
        for i in StudentModel.objects.filter(u_id=student_id_app, updatedAt__year='{}'.format(fy)):
            data = i
        #error_message = common_login(data, request, kind, student_id_ldap)
    if kind == 1: # 教員
        for i in TeacherModel.objects.filter(t_id=request.POST['user_id'], updatedAt__year='{}'.format(fy)):
            data = i
        #error_message = common_login(data, request, kind, student_id_ldap)
    if kind == 2: # admin
        for i in AdminModel.objects.filter(admin_id=student_id_app):
             data = i
        #error_message = common_login(data, request, kind)
    if os.environ['DEBUG'] == 'True':
        student_id_ldap = None

    if not LDAP_USE:
        error_message = not_ldap_common(data, request, kind)
    else:
        error_message = common_login(data, request, kind, student_id_ldap)
    return error_message

# ログアウト処理
def auth_logout(request):
    request.session.flush() # セッションの削除

# パスワード変更をデータベースへ適応
def common_reset_pwd(obj, new_pwd):
    obj.password = make_password(new_pwd)
    obj.updatedAt = timezone.now()
    obj.save()

# パスワード変更処理
"""def reset_password(request):
    if request.POST['confirm_password'] != request.POST['new_password']: # 確認欄と入力が同じであるかをチェック
            return '確認用と一致していません同じ入力を行なってください'
    if request.session['target'] == 0:
        common_reset_pwd(StudentModel.objects.get(u_id=request.session['id']), 
        request.POST['new_password'])
    
    if request.session['target'] == 1:
        common_reset_pwd(TeacherModel.objects.get(t_id=request.session['id']), 
        request.POST['new_password'])
    return True"""

def get_student_data(u_id, focus_term, fiscal_year):
    uds = None
    if (u_id[1] == 'm') or (u_id[1] == 'd'): # 修士、博士の判定とデータ取得
        # 年度データを取得
        uds = RecordModel.objects.filter(u_id=u_id, createdAt__range=['{}-04-01'.format(fiscal_year), '{}-03-31'.format(fiscal_year+1)]).order_by('createdAt').reverse()
    else:
        # 学部生の前期後期の判定と取得
        if focus_term == 0:
            uds = RecordModel.objects.filter(u_id=u_id, createdAt__range=['{}-04-01'.format(fiscal_year), '{}-08-31'.format(fiscal_year)]).order_by('createdAt').reverse()
        else:
            uds = RecordModel.objects.filter(u_id=u_id, createdAt__range=['{}-09-30'.format(fiscal_year), '{}-03-31'.format(fiscal_year+1)]).order_by('createdAt').reverse()
    return uds

# ユーザーのデータの取得
def get_home_datalist(u_id, context, fiscal_year, focus_term):
    uds = None
    uds = get_student_data(u_id, focus_term, fiscal_year)
    if uds != None:
        user_data, total_seconds, each_total = get_student_timedata(uds, u_id)
        context['user_data'] = user_data
        context['total_time'] = [make_same_size(i) for i in get_hm(total_seconds)]
        # 各月のトータルの在室時間(秒)を時間、分に変換
        each_total_hm = {}
        for key, value in each_total.items(): # 月別のデータを変換し格納
            if not (key in each_total_hm.keys()):
                each_total_hm[key] = [make_same_size(i) for i in get_hm(value)]
        context['each_total'] = each_total_hm
        # 学科、専攻別の制限時間を取得
        goal_time = get_goal_time(u_id, focus_term)
        context['goal_time'] = goal_time # 目標時間の取得
        context['remainder'] = [make_same_size(i) for i in time_remainder(goal_time*3600, total_seconds)] # 合計時間と目標時間の差を取得
        context['core_time'] = get_core_time(u_id=u_id) # コアタイムの取得
    else: # まだ記録がない場合
        context['user_data'] = None
        goal_time = get_goal_time(u_id, focus_term)
        context['goal_time'] = goal_time
        context['total_time'] = ['00', '00']
        context['each_total'] = None
        context['remainder'] = [goal_time, '00']
        context['core_time'] = [None, None]
    return context

# 教員の担当する学生のデータを取得
def get_home_datalist_t(request, context, fiscal_year, focus_term):
    context['teacher_data'] = TeacherModel.objects.get(t_id=request.session['id'])
    students = StudentModel.objects.filter(t_id=request.session['id'])
    s_list = {}
    m_list = {}
    d_list = {}
    result = {}
    if students != None:
        for sd in students:
            if sd.u_id[1] == 'm': # 修士の場合
                if not (sd.u_id in m_list.keys()):
                    m_list[sd.u_id] = []
                uds = get_student_data(sd.u_id, focus_term, fiscal_year) # ユーザーデータの取得
                goal_time = get_goal_time(sd.u_id, focus_term) # 目標時間の取得
                if uds != None:
                    user_data, total_seconds, _ = get_student_timedata(uds, sd.u_id) # ユーザーのデータと現在の合計在室時間を秒単位で取得
                    th, tm = get_hm(total_seconds) # 合計秒数を時間と分に変換
                    rh, rm = time_remainder(goal_time*3600, total_seconds) # 目標時間と合計時間の差を時間、分で取得
                    m_list[sd.u_id] = [sd.u_name, make_same_size(th), make_same_size(tm), goal_time, make_same_size(rh), make_same_size(rm)]
                else: # ユーザーの記録がまだない場合
                    m_list[sd.u_id] = [sd.u_name, '00', '00', goal_time, goal_time, '00']
            elif sd.u_id[1] == 'd': # 博士の場合
                if not (sd.u_id in d_list.keys()):
                    d_list[sd.u_id] = []
                uds = get_student_data(sd.u_id, focus_term, fiscal_year)
                goal_time = get_goal_time(sd.u_id, focus_term)
                if uds != None:
                    user_data, total_seconds, _ = get_student_timedata(uds, sd.u_id)
                    th, tm = get_hm(total_seconds)
                    rh, rm = time_remainder(goal_time*3600, total_seconds)
                    d_list[sd.u_id] = [sd.u_name, make_same_size(th), make_same_size(tm), goal_time, make_same_size(rh), make_same_size(rm)]
                else:
                    d_list[sd.u_id] = [sd.u_name, '00', '00', goal_time, goal_time, '00']
            else: # 学部の場合
                if not (sd.u_id in s_list.keys()):
                    s_list[sd.u_id] = []
                uds = get_student_data(sd.u_id, focus_term, fiscal_year)
                goal_time = get_goal_time(sd.u_id, focus_term)
                if uds != None:
                    user_data, total_seconds, _ = get_student_timedata(uds, sd.u_id)
                    th, tm = get_hm(total_seconds)
                    rh, rm = time_remainder(goal_time*3600, total_seconds)
                    s_list[sd.u_id] = [sd.u_name, make_same_size(th), make_same_size(tm), goal_time, make_same_size(rh), make_same_size(rm)]
                else:
                    s_list[sd.u_id] = [sd.u_name, '00', '00', goal_time, goal_time, '00']
        student_list = {'s_list': s_list, 'm_list': m_list, 'd_list': d_list}
    else:
        # 受けもちの学生がいない場合の処理
        student_list = None
    context['student_list'] = student_list
    context['core_time'] = get_core_time(t_id=request.session['id'], kind=1) # 設定しているコアタイムの取得
    return context

def get_student_datalist(request, context, fiscal_year, focus_term, u_id=None):
    if request.session['target'] == 0:
        context = get_home_datalist(request.session['id'], context, fiscal_year, focus_term)
    # 担当学生の現在状況と目標時間の差分の状況を取得する
    if request.session['target'] == 1:
        if u_id != None:
            context = get_home_datalist(u_id, context, fiscal_year, focus_term)
        else:
            context = get_home_datalist_t(request, context, fiscal_year, focus_term)
    return context
        
# 学生、教員データの一括登録処理
def auto_register_users(data, data_type):
    result_message = ''
    kind = None
    try:
        # 学生データの処理
        if data_type == 'student':
            for d in data:
                # 新規データであれば、作成
                if (StudentModel.objects.filter(u_id=d[0]).first()) == None:
                    StudentModel.objects.create(
                        u_id=d[0], u_name=d[1], password=make_password('password'),
                        t_id=d[2], email=d[3], major=d[4], 
                        createdAt=timezone.now(),
                        updatedAt=timezone.now()
                    )
                # 既存データの更新
                else:
                    StudentModel.objects.filter(u_id=d[0]).update(
                        u_name=d[1], t_id=d[2], email=d[3], major=d[4], 
                        updatedAt=timezone.now()
                    )
        # 教員データの処理
        if data_type == 'teacher':
            for d in data:
                # 新規の場合作成
                if (TeacherModel.objects.filter(t_id=d[0]).first()) == None:
                    TeacherModel.objects.create(
                        t_id=d[0], t_name=d[1], password=make_password('password'),
                        email=d[2],
                        createdAt=timezone.now(),
                        updatedAt=timezone.now()
                    )
                    LaboratoryModel.objects.create(
                        t_id=d[0], lab_name=(d[1].split(' '))[0]+'研究室',
                        createdAt=timezone.now(),
                        updatedAt=timezone.now()
                    )
                # 既存データの更新
                else:
                    TeacherModel.objects.filter(t_id=d[0]).update(
                        t_name=d[1], email=d[2],
                        updatedAt=timezone.now()
                    )
                    LaboratoryModel.objects.filter(t_id=d[0]).update(
                        lab_name=(d[1].split(' '))[0]+'研究室',
                        updatedAt=timezone.now()
                    )
        result_message = '正常にデータの登録が成功しました'
        kind = 0
    except:
        result_message = 'エラーが発生しました'
        kind = 1
    return kind, result_message

# 手動でのユーザー登録のための関数
def manual_register(request):
    result_message = None
    try:
        if request.POST['data-type'] == 'student': # 登録データが学生の場合
            if StudentModel.objects.filter(u_id=request.POST['user_id']).first() == None: # ユーザーが存在しなければ、新規で追加
                if TeacherModel.objects.filter(t_id=request.POST['t_id']).first() == None: # 入力された教員IDがない場合
                    result_message = ('教員ID:{}は存在しません').format(request.POST['t_id'])
                elif MajorModel.objects.filter(m_id=get_major_id(request.POST['user_id'])).first() == None: # 入力された学科・専攻が存在しない場合
                    result_message = ('{}の所属する学科・専攻は存在しません').format(request.POST['user_id'])
                else: # 新規で追加
                    StudentModel.objects.create(
                        u_id=request.POST['user_id'], password=make_password('password'),
                        u_name=request.POST['name'], email=request.POST['email'],
                        t_id=request.POST['t_id'], major=request.POST['major'],
                        createdAt=timezone.now(), updatedAt=timezone.now()
                    )
            else: # 入力されたユーザーが既存の場合
                result_message = ('{}はすでに存在します'.format(request.POST['user_id']))
            
        if request.POST['data-type'] == 'teacher': # 教員の場合
            # 上記同様にまだないデータであれば、新規で登録すると共に、研究室情報も登録
            if TeacherModel.objects.filter(t_id=request.POST['user_id']).first() == None:
                TeacherModel.objects.create(
                    t_id=request.POST['user_id'], #password=make_password('test'),
                    t_name=request.POST['name'],
                    email=request.POST['email'], createdAt=timezone.now(),
                    updatedAt=timezone.now()
                )
                LaboratoryModel.objects.create(
                    t_id=request.POST['user_id'],
                    lab_name=request.POST['lab_name'],
                    createdAt=timezone.now(), updatedAt=timezone.now()
                )
            else:
                result_message = ('{}はすでに存在します'.format(request.POST['user_id']))          
    except:
        result_message = 'エラーが発生しました'
    return result_message

# 各ユーザー個人のデータの取得
def edit_each_infomation(request, kind, user_id):
    result = None
    message = None
    try:
        if kind == 'student': # 学生の場合
            if TeacherModel.objects.filter(t_id=request.POST['t_id']).first() == None:
                return None, ('教員ID:{}は存在しません').format(request.POST['t_id'])
            elif MajorModel.objects.filter(m_name=request.POST['major']).first() == None:
                return None, ('{}という学科・専攻は存在しません').format(request.POST['major'])
            else: # 学生個人のデータの取得
                StudentModel.objects.filter(u_id=user_id).update(
                    u_id=request.POST['u_id'], u_name=request.POST['u_name'],
                    email=request.POST['email'], t_id=request.POST['t_id'],
                    major=request.POST['major'], updatedAt=timezone.now()
                )
                result = True
        if kind == 'teacher': # 教員の場合
            TeacherModel.objects.filter(t_id=user_id).update(
                t_id=request.POST['t_id'], t_name=request.POST['t_name'],
                email=request.POST['email'], updatedAt=timezone.now()
            )
        result = True
        message = '正常に更新されました'
    except:
        message = 'エラーが発生しました'
    return result, message

# 学科・専攻のid取得を行う
def get_major_id(user_id):
    if user_id[1] == 'm' or user_id[1] == 'd': # 修士、博士のIDの取得
        return user_id[0:2]
    else: # 学科のIDの取得
        return user_id[2]
    
def get_teacher_recodetime(t_id):
    trds = RecordModel.objects.filter(u_id=t_id)
    return get_student_timedata(trds, t_id, 1)


# グラフ描画用のデータ取得のための関数
def get_graph_all_total(t_id=None, focus_term=None, fiscal_year=None, kind=None): # 全ユーザーの合計在室時間とユーザー名の取得
    if t_id == None or focus_term == None or fiscal_year == None:
        return None, None
    student_list = []
    teacher_recode_data = RecordModel.objects.filter(u_id=t_id)
    if teacher_recode_data.first() != None:
        _, t_total, _ = get_teacher_recodetime(t_id)
        t_total = round((t_total/3600), 1)
        student_list.append([t_id, t_total])
    else:
        student_list.append([t_id, 0])
    students = StudentModel.objects.filter(t_id=t_id)
    each_goal_time = {'S':0, 'M':0}
    count = 0
    if students != None:
        for sd in students:
            if sd.u_id[1] == 'm': # 修士の場合
                uds = get_student_data(sd.u_id, focus_term, fiscal_year) # ユーザーデータの取得
                if each_goal_time['M'] == 0:
                    each_goal_time['M'] = get_goal_time(sd.u_id, focus_term) # 目標時間の取得
                if uds != None:
                    user_data, total_seconds, _ = get_student_timedata(uds, sd.u_id) # ユーザーのデータと現在の合計在室時間を秒単位で取得
                    total_seconds = round((total_seconds/3600), 1) # 合計秒数を時間と分に変換
                    student_list.append([sd.u_id, total_seconds])
                else: # ユーザーの記録がまだない場合
                    student_list.append([sd.u_id, 0])
            elif sd.u_id[1] == 'd': # 博士の場合
                pass
            else: # 学部の場合
                uds = get_student_data(sd.u_id, focus_term, fiscal_year)
                if each_goal_time['S'] == 0:
                    each_goal_time['S'] = get_goal_time(sd.u_id, focus_term)
                if uds != None:
                    user_data, total_seconds, _ = get_student_timedata(uds, sd.u_id)
                    total_seconds = round((total_seconds/3600), 1)
                    student_list.append([sd.u_id, total_seconds])
                else:
                    student_list.append([sd.u_id, 0])
    return student_list, each_goal_time

def get_graph_each_month(): # ユーザー毎の各月のデータを取得
    return

