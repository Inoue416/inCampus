from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.views.generic import TemplateView, RedirectView
from .models import *
from .controller.auth_controller import *
from django.urls import reverse_lazy
from django.contrib.auth.hashers import make_password
from django.utils import timezone
from django.contrib import messages
import datetime
from .controller.time_controller import *
import json

class LoginView(TemplateView):
    # urlのパラメータを変数kindにセットし、生徒か教員のどちらの処理をするのかを判別
    template_name = 'auth/login.html'

    def get(self, request, kind):
        if 'id' in request.session:
            return redirect('incampusApp:home')
        return super().get(request, kind)#render(request, self.template_name)
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        kind = self.kwargs.get('kind') # URLパラメータの取得
        context['kind'] = kind
        return context

    def post(self, request, kind):
        login_result = auth_login(request, kind) # 認証処理
        if login_result is None: # 認証に問題なければ、ホームへリダイレクト
            return redirect('incampusApp:home')
        # フラッシュメッセージの追加
        messages.add_message(request, messages.ERROR, login_result)
        return self.get(request, kind)
    
class LogoutView(TemplateView): # TODO: admin用のlogout処理を作る, 各月の畳み込みを行う
    template_name = 'home.html'
    # アクセス時に呼び出され、ログアウト処理を行い、homeへリダイレクト
    def get(self, request):
        auth_logout(request)
        return redirect('incampusApp:home')

"""class ResetPasswordView(TemplateView):
    template_name = 'auth/reset_password.html'
    def get(self, request):
        if not ('id' in request.session):
            return redirect('incampusApp:home')
        return super().get(self, request)#render(request, self.template_name)

    def post(self, request):
        result = reset_password(request)
        if result == True:
            auth_logout(request)
            return redirect('incampusApp:home')
        messages.add_message(request, messages.ERROR, result)
        return super().get(self, request)"""

class HomeView(TemplateView):
    template_name = 'home.html'
    def get(self, request):
        if 'id' in request.session:
            if request.session['target'] == 0:
                return redirect('incampusApp:each_student_data', u_id=request.session['id'])
        return super().get(self, request)#render(request, self.template_name, self.get_context_data())
    def get_context_data(self):
        context = super().get_context_data()
        fiscal_year, focus_term = get_fiscal() # 前期・後期判定、年度の取得
        if 'id' in self.request.session:
            # ユーザーのデータ取得
            context = get_student_datalist(self.request, context, fiscal_year, focus_term)
            ttd, egt = get_graph_all_total(t_id=self.request.session['id'], focus_term=focus_term, fiscal_year=fiscal_year) 
            context['ttd'] = json.dumps(ttd)
            context['egt'] = json.dumps(egt)
            context['fiscal_year'] = fiscal_year
            context['focus_term'] = focus_term
        return context
    
class StudentDateDetailView(TemplateView):
    template_name = 'student/student_date_detail.html'
    def get(self, request, r_id):
        if not('id' in request.session): # ログイン状態でなければ、ホームへリダイレクト
            return redirect('incampusApp:home')
        # 通知をオフに
        if request.session['target'] == 0:
            RecordModel.objects.filter(id=r_id).update(s_notice=False)
        if request.session['target'] == 1:
            RecordModel.objects.filter(id=r_id).update(t_notice=False)
        return super().get(self, request, r_id)#render(request, self.template_name)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        r_id = self.kwargs.get('r_id') # URLパラメータの取得
        r_data = RecordModel.objects.get(id=r_id) # Redodeデータの取得
        year, month, day, hours, minutes, _ = get_timedata(r_data) # 日付、時間データの取得
        end_time = None
        if r_data.updatedAt != None:
            end_time = [
                r_data.updatedAt.hour,
                r_data.updatedAt.minute
            ]

        data = {
            'year':year, 'month':month, 'day':day,
            'hours':hours, 'minutes':minutes, 'memo':r_data.memo,
            'comment': r_data.comment,
            'start_time':r_data.createdAt, 'end_time':r_data.updatedAt,
            'r_id':r_id, 'u_id': r_data.u_id
        }
        context['data'] = data
        return context

    def post(self, request, r_id):
        if not ('id' in request.session):
            return redirect('incampusApp:home')
        # 通知をオンにする
        try:
            if request.session['target'] == 0:
                RecordModel.objects.filter(id=r_id).update(memo=request.POST['memo'], t_notice=True)
            if request.session['target'] == 1:
                RecordModel.objects.filter(id=r_id).update(comment=request.POST['comment'], s_notice=True)
            messages.add_message(request, messages.SUCCESS, '更新しました')
        except:
            messages.add_message(request, messages.ERROR, 'エラーが発生しました')
        return super().get(self, request, r_id)

# 各学生の詳細(教員側の機能)
class EachStudetnDataView(TemplateView):
    template_name = 'teacher/each_student_data.html'
    def get(self, request, u_id):
        if not ('id' in self.request.session):
            return redirect('incampusApp:home')
        return super().get(self, request, u_id)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        u_id = self.kwargs.get('u_id') # URLパラメータを取得
        fiscal_year, focus_term = get_fiscal() # 注目年度・前期後期の判定
        # データの取得
        context = get_student_datalist(self.request, context, fiscal_year, focus_term, u_id)
        context['u_id'] = u_id
        context['u_name'] = (StudentModel.objects.get(u_id=u_id)).u_name
        context['focus_month'] = (timezone.now()).month
        if self.request.session['target'] == 0:
            t_id = (StudentModel.objects.get(u_id=self.request.session['id'])).t_id
        else:
            t_id = self.request.session['id']
        fiscal_year, focus_term = get_fiscal() # 前期・後期判定、年度の取得
        ttd, egt = get_graph_all_total(t_id=t_id, focus_term=focus_term, fiscal_year=fiscal_year) 
        context['ttd'] = json.dumps(ttd)
        context['egt'] = json.dumps(egt)
        context['fiscal_year'] = fiscal_year
        context['focus_term'] = focus_term
        return context

# 研究室情報のセッティング
class LaboratoryInfomationView(TemplateView):
    template_name = 'teacher/laboratory_infomation.html'
    def get(self, request):
        if not ('id' in request.session):
            return redirect('incampusApp:home')
        if not TeacherModel.objects.filter(t_id=request.session['id']).first():
            messages.add_message(request, messages.ERROR, '教員でしかこのページはひらけません')
            return redirect('incampusApp:home')
        return super().get(self, request)
    
    def get_context_data(self):
        context = super().get_context_data()
        # 研究室の情報を取得
        lab_data = LaboratoryModel.objects.get(t_id=self.request.session['id'])
        data = {}
        # コアタイムの取得
        for k, v in lab_data.__dict__.items():
            if k == 'createdAt' or k == 'updatedAt' or k == '_state' or k == 'id' or k == 't_id':
                continue
            if k == 'lab_name' or v == None:
                data[k] = v
                continue
            print(type(v))
            h = ''
            m = ''
            if v.hour < 10:
                h = '0{}'.format(v.hour)
            else:
                h = str(v.hour)
            if v.minute < 10:
                m = '0{}'.format(v.minute)
            else:
                m = str(v.minute)
            data[k] = {'hour':h, 'minute':m}
        context['data'] = data
        return context
    
    def post(self, request):
        if not ('id' in request.session):
            return redirect('incampusApp:home')
        if not TeacherModel.objects.filter(t_id=request.session['id']).first():
            messages.add_message(request, messages.ERROR, '教員でしかこのページはひらけません')
            return redirect('incampusApp:home')
        result = []
        # 研究室情報の更新処理
        try:
            for k, v in request.POST.items():
                if 'csrfmiddlewaretoken' == k:
                    continue
                if 'lab_name' == k:
                    result.append(v)
                    continue
                if v == '':
                    result.append(None)
                else:
                    result.append(datetime.time(hour=int(v[0:2]), minute=int(v[3:])))
            LaboratoryModel.objects.filter(t_id=request.session['id']).update(
                lab_name=result[0],
                s_core_time_start=result[1], s_core_time_end=result[2],
                m_core_time_start=result[3], m_core_time_end=result[4],
                d_core_time_start=result[5], d_core_time_end=result[6],
                updatedAt=timezone.now()
            )
            messages.add_message(request, messages.SUCCESS, '設定しました')
        except:
            messages.add_message(request, messages.ERROR, 'エラーが発生しました')
        return super().get(self, request)

class incampusAdminView(TemplateView):
    template_name = 'admin/incampus_admin.html'
    def get(self, request):
        if 'id' in request.session:
            if not AdminModel.objects.filter(admin_id=request.session['id']).first():
                messages.add_message(request, messages.ERROR, '管理者しかこのページはひらけません')
            return redirect('incampusApp:admin_home')
        return super().get(self, request)

    def post(self, request):
        login_result = auth_login(request, 2) # 認証処理
        if login_result != None:
            # フラッシュメッセージの追加
            messages.add_message(request, messages.ERROR, login_result)
            return super().get(self, request)
        return redirect('incampusApp:admin_home')


class adminHomeView(TemplateView):
    template_name = 'admin/admin_home.html'
    def get(self, request):
        if not ('id' in request.session):
            return redirect('incampusApp:incampus_admin')
        if not AdminModel.objects.filter(admin_id=request.session['id']).first():
            messages.add_message(request, messages.ERROR, '管理者しかこのページはひらけません')
            return redirect('incampusApp:home')

        return super().get(self, request)

class adminAutoRegisterView(TemplateView):
    template_name = 'admin/admin_auto_register.html'
    def get(self, request):
        if not ('id' in request.session):
            return redirect('incampusApp:incampus_admin')
        if not AdminModel.objects.filter(admin_id=request.session['id']).first():
            messages.add_message(request, messages.ERROR, '管理者しかこのページはひらけません')
            return redirect('incampusApp:home')
        return super().get(self, request)
    
    def post(self, request):
        if not ('id' in request.session):
            return redirect('incampusApp:incampus_admin')
        if not AdminModel.objects.filter(admin_id=request.session['id']).first():
            messages.add_message(request, messages.ERROR, '管理者しかこのページはひらけません')
            return redirect('incampusApp:home')

        file_contents = request.FILES['data_file'].read().decode()
        fc_buff = file_contents.split('\n')
        if '' in fc_buff:
            fc_buff.remove('')
        data = []
        for fc in fc_buff:
            f = fc.split(',')
            if '' in f:
                f.remove('')
            data.append(f)
        kind, result_message = auto_register_users(data=data, data_type=request.POST['data-type'])
        mt = messages.ERROR if kind == 1 else messages.SUCCESS
        messages.add_message(request, mt, result_message)
        return redirect('incampusApp:admin_home')

class adminManualRegisterView(TemplateView):
    template_name = 'admin/admin_manual_register.html'
    def get(self, request):
        if not ('id' in request.session):
            return redirect('incampusApp:incampus_admin')
        if not AdminModel.objects.filter(admin_id=request.session['id']).first():
            messages.add_message(request, messages.ERROR, '管理者しかこのページはひらけません')
            return redirect('incampusApp:home')
        return super().get(self, request)
    
    def post(self, request):
        if not AdminModel.objects.filter(admin_id=request.session['id']).first():
            messages.add_message(request, messages.ERROR, '管理者しかこのページはひらけません')
            return redirect('incampusApp:home')
        result_message = manual_register(request)
        if result_message != None:
            messages.add_message(request, messages.ERROR, result_message)
            return redirect('incampusApp:admin_manual_register')
        messages.add_message(request, messages.SUCCESS, "正常に登録されました")
        return redirect('incampusApp:admin_home')

class adminEditInfomationView(TemplateView):
    template_name = 'admin/admin_edit_infomation.html'
    def get(self, request):
        if not ('id' in request.session):
            return redirect('incampusApp:incampus_admin')
        if not AdminModel.objects.filter(admin_id=request.session['id']).first():
            messages.add_message(request, messages.ERROR, '管理者しかこのページはひらけません')
            return redirect('incampusApp:home')
        return super().get(self, request)
    
    def post(self, request):
        if not ('id' in request.session):
            return redirect('incampusApp:incampus_admin')
        if not AdminModel.objects.filter(admin_id=request.session['id']).first():
            messages.add_message(request, messages.ERROR, '管理者しかこのページはひらけません')
            return redirect('incampusApp:home')
        if request.POST['data-type'] == 'student' and (StudentModel.objects.filter(u_id=request.POST['user_id']).first() == None):
            messages.add_message(request, messages.ERROR, 'ユーザーが見つかりません')
            return super().get(self, request)
        if request.POST['data-type'] == 'teacher' and (TeacherModel.objects.filter(t_id=request.POST['user_id']).first() == None):
            messages.add_message(request, messages.ERROR, 'ユーザーが見つかりません')
            return super().get(self, request)
        return redirect('incampusApp:admin_edit_each_infomation', kind=request.POST['data-type'], user_id=request.POST['user_id'])

class adminEditEachInfomationView(TemplateView):
    template_name = 'admin/admin_edit_each_infomation.html'
    def get(self, request, kind, user_id):
        if not ('id' in request.session):
            return redirect('incampusApp:incampus_admin')
        if not AdminModel.objects.filter(admin_id=request.session['id']).first():
            messages.add_message(request, messages.ERROR, '管理者しかこのページはひらけません')
            return redirect('incampusApp:home')
        return super().get(self, request)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        kind = self.kwargs.get('kind') # URLパラメータを取得
        user_id = self.kwargs.get('user_id') # URLパラメータを取得
        data = None
        if kind == 'student':
            data = StudentModel.objects.get(u_id=user_id)
        if kind == 'teacher':
            data = TeacherModel.objects.get(t_id=user_id)
        context['data'] = data
        context['kind'] = kind
        return context
    
    def post(self, request, kind, user_id):
        if not ('id' in request.session):
            return redirect('incampusApp:incampus_admin')
        if not AdminModel.objects.filter(admin_id=request.session['id']).first():
            messages.add_message(request, messages.ERROR, '管理者しかこのページはひらけません')
            return redirect('incampusApp:home')
        kind = self.kwargs.get('kind') # URLパラメータを取得
        user_id = self.kwargs.get('user_id') # URLパラメータを取得
        result, message = edit_each_infomation(request, kind, user_id)
        if result == True:
            messages.add_message(request, messages.SUCCESS, message)
            return redirect('incampusApp:admin_home')
        messages.add_message(request, messages.ERROR, message)
        return super().get(self, request)

class setAdminView(TemplateView):
    template_name = 'admin/set_admin.html'
    def get(self, request):
        return super().get(self, request)
    def post(self, request):
        AdminModel.objects.create(
            admin_id='admin', password=make_password('password'),
            createdAt=timezone.now(), updatedAt=timezone.now()
        )

        return redirect('incampusApp:admin_home')
