<%!
    import app.app_ver as app_ver
    from app import const
    _sidebar = [
    {
		'privilege': const.TP_PRIVILEGE_LOGIN_WEB,
        'id': 'me'
    },
	{
		'privilege': const.TP_PRIVILEGE_ASSET_CREATE | const.TP_PRIVILEGE_USER_CREATE,
		'id': 'dashboard',
		'link': '/dashboard',
		'name': '总览',
		'icon': 'fas fa-tachometer-alt',
	},
	{
		'id': 'asset',
		'link': '',
		'name': '资产',
		'icon': 'fa fa-cubes',
		'sub': [
			{
                'privilege': const.TP_PRIVILEGE_ASSET_CREATE | const.TP_PRIVILEGE_ASSET_GROUP,
                'id': 'host',
                'link': '/asset/host',
                'name': '主机及账号',
            },
			{
                'privilege': const.TP_PRIVILEGE_ASSET_CREATE | const.TP_PRIVILEGE_ASSET_GROUP,
                'id': 'host-group',
                'link': '/asset/host-group',
                'name': '主机分组管理',
            },
            {
                'privilege': const.TP_PRIVILEGE_ACCOUNT | const.TP_PRIVILEGE_ACCOUNT_GROUP,
                'id': 'account-group',
                'link': '/asset/account-group',
                'name': '账号分组管理',
            },
		]
    },
	{
		'id': 'user',
		'link': '',
		'name': '用户',
		'icon': 'far fa-address-book',
		'sub': [
			{
                'privilege': const.TP_PRIVILEGE_USER_CREATE,
                'id': 'user',
                'link': '/user/user',
                'name': '用户管理',
            },
            {
                'privilege': const.TP_PRIVILEGE_USER_GROUP,
                'id': 'group',
                'link': '/user/group',
                'name': '用户分组管理',
            },
		]
	},
	{
		'id': 'ops',
		'link': '',
		'name': '运维',
		'icon': 'fa fa-wrench',
		'sub': [
            {
                'privilege': const.TP_PRIVILEGE_OPS_AUZ,
                'id': 'auz',
                'link': '/ops/auz',
                'name': '运维授权',
            },
			{
                'privilege': const.TP_PRIVILEGE_OPS,
                'id': 'remote',
                'link': '/ops/remote',
                'name': '主机运维',
            },
            {
                'privilege': const.TP_PRIVILEGE_SESSION_VIEW | const.TP_PRIVILEGE_SESSION_BLOCK,
                'id': 'session',
                'link': '/ops/session',
                'name': '在线会话',
            },
		]
	},
	{
		'id': 'audit',
		'link': '',
		'name': '审计',
		'icon': 'fa fa-eye',
		'sub': [
            {
                'privilege': const.TP_PRIVILEGE_AUDIT_AUZ,
                'id': 'auz',
                'link': '/audit/auz',
                'name': '审计授权',
            },
			{
                'privilege': const.TP_PRIVILEGE_AUDIT,
                'id': 'record',
                'link': '/audit/record',
                'name': '会话审计',
            },
		]
	},
	{
		'id': 'system',
		'link': '',
		'name': '系统',
		'icon': 'fa fa-cog',
		'sub': [
            {
                'privilege': const.TP_PRIVILEGE_SYS_LOG,
                'id': 'syslog',
                'link': '/system/syslog',
                'name': '系统日志',
            },
			{
                'privilege': const.TP_PRIVILEGE_SYS_ROLE,
                'id': 'role',
                'link': '/system/role',
                'name': '角色管理',
            },
            {
                'privilege': const.TP_PRIVILEGE_SYS_CONFIG,
                'id': 'config',
                'link': '/system/config',
                'name': '系统设置',
            },
		]
	},
	{
		'privilege': const.TP_PRIVILEGE_LOGIN_WEB,
		'id': 'assist',
		'link': 'http://127.0.0.1:50022/config',
		'target': '_blank',
		'name': '助手设置',
		'icon': 'fas fa-bolt'
	}
]
%>

## <div id="sidebar-menu-slim-scroll">
    <!-- begin sidebar nav -->
<div class="nav">
    <ul class="nav nav-menu">
        %for menu in _sidebar:
            %if menu['id'] == 'me':
                <li id="sidebar_menu_${menu['id']}" class="profile">
                    <div class="image">
                        <img src="/static/img/avatar/001.png" width="36"/>
                    </div>

                    <div class="dropdown">
                        <a class="title" href="#" id="user-profile" data-target="#" data-toggle="dropdown" role="button"
                           aria-haspopup="true" aria-expanded="false">
                            <span class="name">${ current_user['surname'] }</span>
                            <span class="role">${ current_user['role'] } <i class="fa fa-caret-right"></i></span>
                        </a>
                        <ul class="dropdown-menu dropdown-menu-right">
                            <li><a href="/user/me"><i class="far fa-id-card fa-fw"></i> 个人中心</a></li>
                            <li role="separator" class="divider"></li>
                            <li><a href="/auth/logout" id="btn-sidebar-menu-logout"><i class="fas fa-sign-out-alt fa-fw"></i> 退出</a></li>
                        </ul>
                    </div>
                </li>
            %else:
                %if 'sub' in menu and len(menu['sub']) > 0:
                    <%
                        menu['privilege'] = 0
                    %>
                    %for sub in menu['sub']:
                        <%
                            menu['privilege'] |= sub['privilege']
                        %>
                    %endfor
                %endif

                %if menu['privilege'] & current_user['privilege'] != 0:
                    %if 'sub' in menu and len(menu['sub']) > 0:
                        <li id="sidebar_menu_${menu['id']}">
                            <a href="javascript:;" onclick="$app.sidebar_menu.toggle_submenu('${menu['id']}');">
                                <i class="fa ${menu['icon']} fa-fw icon"></i>
                                <span>${menu['name']}</span>
                                <i class="menu-caret"></i>
                            </a>
                            <ul class="sub-menu" id="sidebar_submenu_${menu['id']}" style="display:none;">
                                %for sub in menu['sub']:
                                    %if (sub['privilege'] & current_user['privilege']) != 0:
                                        <li id="sidebar_menu_${menu['id']}_${sub['id']}"><a href="${sub['link']}"><span>${sub['name']}</span></a></li>
                                    %endif
                                %endfor
                            </ul>
                        </li>
                    %else:
                        <li id="sidebar_menu_${menu['id']}"><a href="${menu['link']}"
                            %if 'target' in menu:
                                                               target="${menu['target']}"
                            %endif
                        ><i class="${menu['icon']} fa-fw icon"></i><span>${menu['name']}</span></a></li>
                    %endif
                %endif
            %endif


        %endfor

    </ul>
</div>
<!-- end sidebar nav -->

<hr style="border:none;border-bottom:1px dotted #4a4a4a;margin-bottom:0;"/>
<div style="color:#717171;font-size:90%;margin-top:5px;text-align:center;">
    <div style="color:#717171;font-size:90%;margin-top:5px;"><span style="display:inline-block;width:50px;text-align: right">服务端：</span><span class="mono">v${app_ver.TP_SERVER_VER}</span></div>
    <div style="color:#717171;font-size:90%;margin-top:5px;"><span style="display:inline-block;width:50px;text-align: right">助手：</span><span class="mono"><span id="sidebar-tp-assist-ver"><i class="fa fa-cog fa-spin"></i></span></span></div>

##     <div style="font-size:80%;margin-top:5px;text-align:center;"><span class="error">beta版</span></div>
</div>
<hr style="border:none;border-bottom:1px dotted #4a4a4a;margin-bottom:20px;margin-top:5px;"/>

## </div>
