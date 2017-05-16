<%!
    import eom_ver
%>
<%
    _sidebar = [
## 	{
## 		'require_type': 100,
## 		'id': 'dashboard',
## 		'link': '/dashboard',
## 		'name': '信息总览',
## 		'icon': 'fa-dashboard',
## 	},
	{
		'require_type': 1,
		'id': 'host',
		'link': '/host',
		'name': '主机管理',
		'icon': 'fa-server',
	},
	{
		'require_type': 100,
		'id': 'user',
		'link': '/user',
		'name': '用户管理',
		'icon': 'fa-user',
	},
	{
		'require_type': 100,
		'id': 'cert',
		'link': '/cert',
		'name': '密钥管理',
		'icon': 'fa-key',
	},
	{
		'require_type': 100,
		'id': 'group',
		'link': '/group',
		'name': '分组管理',
		'icon': 'fa-object-group',
	},
## 	{
## 		'require_type': 100,
## 		'id': 'set',
## 		'link': '',
## 		'name': '配置管理',
## 		'icon': 'fa-cogs',
## 		'sub': [
## 		    {
##                 'require_type': 100,
##                 'id': 'info',
##                 'link': '/set/info',
##                 'name': '配置信息'
## 		    },
## 		    {
##                 'require_type': 100,
##                 'id': 'database',
##                 'link': '/set/db',
##                 'name': '数据库管理'
## 		    }
## 		]
## 	},
	{
		'require_type': 100,
		'id': 'config',
		'link': '/config',
		'name': '配置管理',
		'icon': 'fa-cogs',
	},
	{
		'require_type': 100,
		'id': 'log',
		'link': '/log',
		'name': '日志查询',
		'icon': 'fa-database',
	},
	{
	    'separator': true,
		'require_type': 1,
		'id': 'assist-config',
		'link': 'http://127.0.0.1:50022/config',
		'target': '_blank',
		'name': '助手配置',
		'icon': 'fa-cog',
	},
]
%>


<!-- begin sidebar scrollbar -->
<div class="slimScrollDiv">

    <!-- begin sidebar user -->
    <div class="nav">
        <ul class="nav nav-profile">
            <li>
                <div class="image">
                    <img src="/static/img/avatar/001.png" width="36"/>
                    ##                     <i class="fa fa-male"></i>
                                    </div>

                <div class="dropdown">
                    <a class="title" href="#" id="user-profile" data-target="#" data-toggle="dropdown" role="button"
                       aria-haspopup="true" aria-expanded="false">
                        <span class="name">${ current_user['nick_name'] }</span>
                        <span class="role">
%if current_user['type'] == 100:
    平台管理员
%else:
    普通用户
%endif
                            <i class="fa fa-caret-right"></i></span>
                    </a>
                    <ul class="dropdown-menu dropdown-menu-right">
                        <li><a href="/pwd" id="btn-logout">修改密码</a></li>
                        <li><a href="/auth/logout" id="btn-logout">安全退出</a></li>
                    </ul>
                </div>


            </li>
        </ul>
    </div>
    <!-- end sidebar user -->

    <!-- begin sidebar nav -->
    <div class="nav">
        <ul class="nav nav-menu">

            %for menu in _sidebar:
                %if menu['require_type'] <= current_user['type']:
                    %if 'separator' in menu:
                        <hr style="border:none;border-bottom:1px solid #636363;margin-bottom:0;margin-top:5px;"/>
                    %endif

                    %if 'sub' in menu and len(menu['sub']) > 0:
                        <li id="sidebar_menu_${menu['id']}"><a href="javascript:;"
                                                               onclick="ywl._sidebar_toggle_submenu('${menu['id']}');"><i
                                class="fa ${menu['icon']} fa-fw icon"></i><span>${menu['name']}</span>
                            <i class="menu-caret"></i></a>
                            <ul class="sub-menu" id="sidebar_submenu_${menu['id']}" style="display:none;">
                                %for sub in menu['sub']:
                                    %if menu['require_type'] <= current_user['type']:
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
                        ><i class="fa ${menu['icon']} fa-fw icon"></i><span>${menu['name']}</span></a></li>
                    %endif
                %endif

            %endfor

        </ul>
    </div>
    <!-- end sidebar nav -->

    <hr style="border:none;border-bottom:1px dotted #4a4a4a;margin-bottom:0;"/>
    <div style="color:#717171;font-size:90%;margin-top:5px;"><span style="display:inline-block;width:100px;text-align: right">服务端：</span><span class="mono">v${eom_ver.TS_VER}</span></div>
    <div style="color:#717171;font-size:90%;margin-top:5px;"><span style="display:inline-block;width:100px;text-align: right">助手：</span><span class="mono" id="tp-assist-version" req-version=${eom_ver.TP_ASSIST_REQUIRE}>v${eom_ver.TP_ASSIST_LAST_VER}</span></div>
    <hr style="border:none;border-bottom:1px dotted #4a4a4a;margin-bottom:0;margin-top:5px;"/>

</div>
<!-- end sidebar scrollbar -->