<%!
    page_icon_class_ = 'fa fa-cog fa-fw'
    page_title_ = ['系统', '角色管理']
    page_id_ = ['system', 'role']
%>
<%inherit file="../page_base.mako"/>

<%block name="extend_js_file">
    <script type="text/javascript" src="${ static_url('js/system/role.js') }"></script>
</%block>

<div class="page-content-inner">
    <div class="box">
        <div class="alert alert-info">
            <i class="fa fa-info-circle fa-fw icon-bg"></i> 角色就是一组权限的集合。
        </div>

        <div>
            <table class="table table-role">
                <tr>
                    <td class="role-name">
                        <div class="header">角色列表</div>
                        <ul id="role-list"></ul>
                    </td>
                    <td id="role-info" class="role-privilege editable">

                        <div>
                            <div style="float:left;">
                                <div class="header">
                                    <div id="label-role-name-area" style="display:none;"><span data-role-name>系统管理员</span> 权限一览</div>
                                    <div id="input-role-name-area" style="display:none;">
                                        <input id="input-role-name" type="text" class="form-control" value="系统管理员" placeholder="设置角色名称"/>
                                    </div>
                                </div>
                            </div>
                            <div style="float:right;" id="area-action">
                                <button id="btn-edit-role" class="btn btn-sm btn-primary"><i class="fa fa-edit fa-fw"></i> 编辑角色</button>
                                <button id="btn-remove-role" class="btn btn-sm btn-danger"><i class="far fa-times-circle fa-fw"></i> 删除角色</button>
                            </div>
                            <div class="clear-float"></div>
                        </div>

                        <div id="privilege-list"></div>

                        <div id="save-area" style="display:none;">
                            <hr/>
                            <button id="btn-save-role" class="btn btn-sm btn-primary"><i class="fa fa-check fa-fw"></i> 保存</button>
                            <button id="btn-cancel-edit-role" class="btn btn-sm btn-default"><i class="fa fa-times fa-fw"></i> 取消</button>
                        </div>
                    </td>
                </tr>
            </table>

        </div>
    </div>


    <div class="box">
        <p>权限说明：</p>
        <ul class="help-list">
            <li><em>主机创建/编辑</em> 允许创建和编辑主机资产信息，如IP地址、端口与协议、名称、备注等。</li>
            <li><em>删除主机</em> 允许删除主机资产。</li>
            <li><em>主机禁用/解禁</em> 允许设置禁止访问某主机，或者解禁。</li>
            <li><em>主机分组管理</em> 将主机进行分组，便于快速查找或者授权管理。</li>
            <li><em>账号管理</em> 管理能够远程登录主机的账号，包括账号名称和密码、SSH密钥等。</li>
            <li><em>账号分组管理</em> 将远程账号进行分组管理，便于批量授权。</li>
            <li><em>登录WEB系统</em> 允许用户登录本WEB系统，除特殊情况外，用户应该具有本权限。</li>
            <li><em>用户创建/编辑</em> 允许创建或编辑登录teleport系统的用户账号。</li>
            <li><em>删除用户</em> 允许删除登录teleport系统的用户。</li>
            <li><em>用户禁用/解禁</em> 允许设置禁止用户访问teleport系统，或者解禁。当用户因连续认证失败而被临时锁定时，也可由此权限进行解锁。</li>
            <li><em>用户分组管理</em> 将用户进行分组，便于快速查找或者授权管理。</li>
            <li><em>远程主机运维</em> 允许用户访问指定的远程主机，允许用户查看、回放自己的操作录像。</li>
            <li><em>运维授权管理</em> 授权用户/用户组使用特定的远程主机账号访问指定远程主机。具有本权限的用户自动具有远程主机运维的权限。</li>
            <li><em>查看在线会话</em> 允许查看在线运维会话，并进行实时同步显示。【此功能尚未实现】</li>
            <li><em>阻断在线会话</em> 强行终止在线运维会话。【此功能尚未实现】</li>
            <li><em>审计（回放操作录像）</em> 允许重放会话的操作录像。注意：运维人员总是可以回放自己的操作录像。</li>
            <li><em>审计授权管理</em> 授权用户/用户组重放指定远程主机的历史会话。具有本权限的用户自动具有审计权限。</li>
            <li><em>角色管理</em> 允许创建、编辑、删除角色。</li>
            <li><em>系统配置与维护</em> 允许对teleport系统进行配置和维护操作。</li>
##             <li><em>历史会话管理</em> 允许查看用户在teleport系统上的操作记录。</li>
            <li><em>查看系统日志</em> 允许查看用户在teleport系统上的操作记录。</li>
        </ul>
        <p>特别注意：teleport系统使用<strong>最小权限判定规则</strong>，也即，在检查权限时，会按用户所具有的最小权限进行判断。例如：如用户无远程主机运维权限，那么即使其所在用户组被授权访问某远程主机，此用户也无法连接到该远程主机。</p>
    </div>
</div>
