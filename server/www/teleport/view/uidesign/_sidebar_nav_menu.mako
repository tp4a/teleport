<%!
    import eom_ver
%>
<%
    _sidebar = [
	{
		'require_type': 0,
		'id': 'with-sidebar',
		'link': '',
		'name': '左侧菜单',
		'icon': 'fa-database',
		'sub': [
			{
                'require_type': 0,
                'id': 'normal',
                'link': '/uidesign',
                'name': '普通页面',
                'icon': 'fa-server',
            },
            {
                'require_type': 0,
                'id': 'table',
                'link': '/uidesign/table',
                'name': '表格页面',
                'icon': 'fa-user',
            },
		]
	},
	{
		'require_type': 0,
		'id': 'without-sidebar',
		'link': '/uidesign/without-sidebar',
		'name': '无侧边菜单',
		'icon': 'fa-database'
	}
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
                </div>

                <div class="dropdown">
                    <a class="title" href="#" id="user-profile" data-target="#" data-toggle="dropdown" role="button"
                       aria-haspopup="true" aria-expanded="false">
                        <span class="name">${ current_user['nick_name'] }</span>
                        <span class="role">测试用户 <i class="fa fa-caret-right"></i></span>
                    </a>
                    <ul class="dropdown-menu dropdown-menu-right">
                        <li><a href="/auth/logout" id="btn-logout">退出</a></li>
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
                    %if 'sub' in menu and len(menu['sub']) > 0:
                        <li id="sidebar_menu_${menu['id']}">
                            <a href="javascript:;" onclick="ywl._sidebar_toggle_submenu('${menu['id']}');">
                                <i class="fa ${menu['icon']} fa-fw icon"></i>
                                <span>${menu['name']}</span>
                                <i class="menu-caret"></i>
                            </a>
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
    <div style="color:#717171;font-size:90%;margin-top:5px;"><span style="display:inline-block;width:100px;text-align: right">当前助手：</span><span class="mono">v${eom_ver.TP_ASSIST_REQUIRE}</span></div>

</div>
<!-- end sidebar scrollbar -->