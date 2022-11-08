from ldap3 import Server, Connection, ObjectDef, AttrDef, Reader, Writer, ALL

def ldap_auth_login(user_id, password, debug_mode, debug_users):
    rt_code = None
    message = None
    if debug_mode:
        rt_code = 1
    else:
        if user_id in debug_users:
            rt_code = 1
        else:
            try: # サーバーとの接続
                server = Server("ldap://ldap01.bene.fit.ac.jp/", get_info=ALL)
                auth_data = ("uid={},ou=FIT_Users,dc=bene,dc=fit,dc=ac,dc=jp").format(user_id)
                ds = Connection(server=server, user=auth_data, password=password, read_only=True)
            except:
                message = 'サーバーに接続できませんでした'
                rt_code = 0
            if ds.bind():# 認証部分
                rt_code = 1
            else:
                rt_code = 0
                message = 'ログインできませんでした'
    return rt_code, message                
