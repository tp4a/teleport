<%!
    page_icon_class_ = 'far fa-address-book fa-fw'
    page_title_ = ['用户', '用户管理']
    page_id_ = ['user', 'user']
%>
<%inherit file="../page_base.mako"/>

<%block name="extend_js_file">
    <script type="text/javascript" src="${ static_url('js/user/user-list.js') }"></script>
    <script type="text/javascript" src="${ static_url('plugins/jquery/ajaxfileupload.js') }"></script>
</%block>

<%block name="embed_js">
    <script type="text/javascript">
        $app.add_options(${page_param});
    </script>
</%block>

<%block name="embed_css">
    <style>
        .user-username {
            display: inline-block;
            min-width: 120px;
            padding-right: 15px;
            font-family: Monaco, Lucida Console, Consolas, Courier, 'Courier New', monospace;
        }

        .user-surname {
            color: #7a7a7a;
        }

        .user-email {
            font-family: Monaco, Lucida Console, Consolas, Courier, 'Courier New', monospace;
        }
    </style>
</%block>

## Begin Main Body.

<div class="page-content-inner">

    <!-- begin box -->
    <div class="box">
        <div class="table-prefix-area">
            <div class="table-extend-cell">
                <span class="table-name"><i class="fa fa-list fa-fw"></i> 用户列表</span>
                <button id="btn-refresh-user-list" class="btn btn-sm btn-default"><i class="fa fa-redo fa-fw"></i> 刷新列表</button>
            </div>
            <div class="table-extend-cell table-extend-cell-right group-actions">
                <button id="btn-create-user" class="btn btn-sm btn-primary"><i class="fa fa-plus-circle fa-fw"></i> 创建用户</button>
                <button id="btn-import-user" class="btn btn-sm btn-default"><i class="fa fa-plus-square fa-fw"></i> 导入用户</button>
            </div>
        </div>

        <table id="table-user-list" class="table table-striped table-bordered table-hover table-data no-footer dtr-inline"></table>

        <div class="table-extend-area">
            <div class="table-extend-cell checkbox-select-all"><input id="table-user-list-select-all" type="checkbox"/></div>

            ##         _ret.push('<div id="' + _tblf.dom_id + '" class="btn-group search-select">');
            ##         _ret.push('<button type="button" class="btn dropdown-toggle" data-toggle="dropdown">');
            ##         _ret.push('<span data-tp-select-result></span> <i class="fa fa-caret-right"></i></button>');
            ##         _ret.push('<ul class="dropdown-menu dropdown-menu-right dropdown-menu-sm">');
            ##         _ret.push('<li><a href="javascript:;" data-tp-selector="0"><i class="fa fa-list-ul fa-fw"></i> 所有</a></li>');
            ##         _ret.push('<li role="separator" class="divider"></li>');
            ##         $.each(_tblf.roles, function (i, role) {
            ##             _ret.push('<li><a href="javascript:;" data-tp-selector="' + role.id + '"><i class="fa fa-caret-right fa-fw"></i> ' + role.name + '</a></li>');
            ##         });
            ##         _ret.push('</ul></div>');



            <div class="table-extend-cell group-actions">
                <div class="btn-group">
                    <div class="btn-group dropup" id="btn-set-role" role="group">
                        <button type="button" class="btn btn-default dropdown-toggle" data-toggle="dropdown"><i class="fa fa-edit fa-fw"></i> 设置角色 <i class="fa fa-caret-right"></i></button>
                        <ul class="dropdown-menu  dropdown-menu-sm"></ul>
                    </div>
                    ##                     <button id="btn-set-role" type="button" class="btn btn-default"><i class="fa fa-edit fa-fw"></i> 设置角色</button>

                    <button id="btn-lock-user" type="button" class="btn btn-default"><i class="fa fa-lock fa-fw"></i> 禁用</button>
                    <button id="btn-unlock-user" type="button" class="btn btn-default"><i class="fa fa-unlock fa-fw"></i> 解禁</button>
                    <button id="btn-remove-user" type="button" class="btn btn-default"><i class="fa fa-times-circle fa-fw"></i> 删除</button>
                </div>
            </div>
            <div class="table-extend-cell table-item-counter">
                <ol id="table-user-list-paging"></ol>
            </div>
        </div>

        <div class="table-extend-area">
            <div class="table-extend-cell">
                <div style="text-align:right;">
                    <nav>
                        <ul id="table-user-list-pagination" class="pagination"></ul>
                    </nav>
                </div>
            </div>
        </div>
    </div>
    <!-- end of box -->

    <div class="box">
        <p>说明：</p>
        <ul class="help-list">
            <li>可以通过表格标题栏进行搜索或过滤，以便快速定位你需要的信息。标题栏左侧的 <i class="fa fa-undo fa-fw"></i> 可以重置过滤器。</li>
            <li>批量导入用户需要上传.csv格式的文件，您可以 <a href="/static/download/teleport-example-user.csv"><i class="fa fa-download fa-fw"></i>下载用户信息文件模板</a> 进行编辑。</li>
        </ul>
    </div>
</div>


<%block name="extend_content">
    <div class="modal fade" id="dlg-user-info" tabindex="-1">
        <div class="modal-dialog">
            <div class="modal-content">
                <div class="modal-header">
                    <button type="button" class="close" data-dismiss="modal" aria-label="Close"><i class="fa fa-times-circle fa-fw"></i></button>
                    <h3 data-field="dlg-title" class="modal-title"></h3>
                </div>
                <div class="modal-body">

                    <table data-field="user-info" class="table table-info-list table-info-list-lite"></table>

                </div>


                <div class="modal-footer">
                    <button type="button" class="btn btn-sm btn-primary" data-field="btn-edit"><i class="fa fa-edit fa-fw"></i> 编辑用户信息</button>
                    <button type="button" class="btn btn-sm btn-default" data-dismiss="modal"><i class="fa fa-times fa-fw"></i> 关闭</button>
                </div>
            </div>
        </div>
    </div>

    <div class="modal fade" id="dlg-edit-user" tabindex="-1" role="dialog">
        <div class="modal-dialog" role="document">
            <div class="modal-content">
                <div class="modal-header">
                    <button type="button" class="close" data-dismiss="modal" aria-label="Close"><i class="fa fa-times-circle fa-fw"></i></button>
                    <h3 data-field="dlg-title" class="modal-title"></h3>
                </div>
                <div class="modal-body">

                    <div class="form-horizontal">

                        <div class="form-group form-group-sm">
                            <label for="edit-user-role" class="col-sm-2 control-label require">角色：</label>
                            <div class="col-sm-6">
                                <div id="edit-user-role" class="btn-group btn-group-sm"></div>
                            </div>
                        </div>

                        <div class="form-group form-group-sm">
                            <label for="edit-user-username" class="col-sm-2 control-label require">账号：</label>
                            <div class="col-sm-6">
                                <input id="edit-user-username" type="text" class="form-control" placeholder="用户账号，也就是用户登录名"/>
                            </div>
                            <div class="col-sm-4">
                                <div class="control-desc">英文字符和数字，最大32字符</div>
                            </div>
                        </div>

                        <div class="form-group form-group-sm">
                            <label for="edit-user-surname" class="col-sm-2 control-label">姓名：</label>
                            <div class="col-sm-6">
                                <input id="edit-user-surname" type="text" class="form-control" placeholder="用户的真实姓名"/>
                            </div>
                        </div>

                        <div class="form-group form-group-sm">
                            <label for="edit-user-email" class="col-sm-2 control-label">email：</label>
                            <div class="col-sm-6">
                                <input id="edit-user-email" type="text" class="form-control" placeholder="电子邮箱地址"/>
                            </div>
                            <div class="col-sm-4">
                                <div class="control-desc">用于激活账号、重置密码。</div>
                            </div>
                        </div>

                        <div class="form-group form-group-sm">
                            <label for="edit-user-mobile" class="col-sm-2 control-label">电话：</label>
                            <div class="col-sm-6">
                                <input id="edit-user-mobile" type="text" class="form-control" placeholder=""/>
                            </div>
                        </div>

                        <div class="form-group form-group-sm">
                            <label for="edit-user-qq" class="col-sm-2 control-label">QQ：</label>
                            <div class="col-sm-6">
                                <input id="edit-user-qq" type="text" class="form-control"/>
                            </div>
                        </div>

                        <div class="form-group form-group-sm">
                            <label for="edit-user-wechat" class="col-sm-2 control-label">微信：</label>
                            <div class="col-sm-6">
                                <input id="edit-user-wechat" type="text" class="form-control"/>
                            </div>
                        </div>

                        <div class="form-group form-group-sm">
                            <label for="edit-user-desc" class="col-sm-2 control-label">备注：</label>
                            <div class="col-sm-10">
                                <textarea id="edit-user-desc" class="form-control" style="resize: vertical;"></textarea>
                            </div>
                        </div>


                        <div class="form-group form-group-sm">
                            <label for="edit-user-desc" class="col-sm-2 control-label">认证方式：</label>
                            <div class="col-sm-10">
                                <div class="control-desc">当前使用系统默认设置</div>
                                <ul class="list">
                                    <li><div id="sec-auth-use-sys-config" class="tp-checkbox tp-editable">使用系统默认设置</div></li>
                                    <li><hr class="hr-sm"/></li>
##                                     <li><div id="sec-auth-username-password" class="tp-checkbox">用户名 + 密码</div></li>
                                    <li><div id="sec-auth-username-password-captcha" class="tp-checkbox">用户名 + 密码 + 验证码</div></li>
##                                     <li><div id="sec-auth-username-oath" class="tp-checkbox">用户名 + 身份认证器动态密码</div></li>
                                    <li><div id="sec-auth-username-password-oath" class="tp-checkbox">用户名 + 密码 + 身份认证器动态密码</div></li>
                                </ul>
                            </div>
                        </div>


                    </div>
                </div>


                <div class="modal-footer">
                    <div class="row">
                        <div class="col-sm-8">
                            <div id="edit-user-message" class="alert alert-danger" style="text-align:left;display:none;"></div>
                        </div>
                        <div class="col-sm-4">
                            <button type="button" class="btn btn-sm btn-primary" id="btn-edit-user-save"><i class="fa fa-check fa-fw"></i> 确定</button>
                            <button type="button" class="btn btn-sm btn-default" data-dismiss="modal"><i class="fa fa-times fa-fw"></i> 取消</button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <div class="modal fade" id="dlg-reset-password" tabindex="-1" role="dialog">
        <div class="modal-dialog" role="document">
            <div class="modal-content">
                <div class="modal-header">
                    <button type="button" class="close" data-dismiss="modal" aria-label="Close"><i class="fa fa-times-circle fa-fw"></i></button>
                    <h3 data-field="dlg-title" class="modal-title"></h3>
                </div>
                <div class="modal-body">

                    <div class="form-horizontal">

                        <div class="form-group form-group-sm">
                            <div class="col-sm-12" style="font-size:120%;">
                                发送密码重置邮件
                            </div>
                        </div>

                        <div class="form-group form-group-sm">
                            <div class="col-sm-10 col-sm-offset-1">
                                <div id="can-send-email" style="display:none">
                                    <div> 向用户绑定的邮箱地址 <span data-field="email" class="mono"></span> 发送密码重置邮件，然后用户可通过邮件中的密码重置链接自行设置新密码。</div>
                                    <button type="button" class="btn btn-sm btn-primary" id="btn-send-reset-email" style="margin-top:10px;"><i class="fa fa-send fa-fw"></i> 发送邮件</button>
                                </div>
                                <div id="cannot-send-email" class="alert alert-warning" style="margin-top:10px;">
                                    <i class="fas fa-exclamation-triangle fa-fw"></i> <span id="msg-cannot-send-email">用户未设置邮箱</span>，密码重置邮件功能无法使用，请使用手动重置方式。
                                </div>
                            </div>
                        </div>

                    </div>

                    <hr class="sm"/>

                    <div class="form-horizontal">

                        <div class="form-group form-group-sm">
                            <div class="col-sm-12" style="font-size:120%;">
                                手动重置
                            </div>
                        </div>
                        <div class="form-group form-group-sm">
                            <div class="col-sm-10 col-sm-offset-1">
                                为用户设置新密码，并立即生效，需要通过其它方式告知用户新密码。
                            </div>
                        </div>

                        <div class="form-group form-group-sm">
                            <div class="col-sm-5 col-sm-offset-1">
                                <div class="input-group">
                                    <input data-field="password" type="password" class="form-control mono" placeholder="设置用户的新密码">
                                    <span class="input-group-btn"><button class="btn btn-sm btn-default" type="button" id="btn-switch-password"><i class="fa fa-eye fa-fw"></i></button></span>
                                </div>
                            </div>
                            <div class="col-sm-4">
                                <button type="button" class="btn btn-sm btn-info" id="btn-gen-random-password"><i class="far fa-snowflake fa-fw"></i> 生成随机密码</button>
                            </div>
                        </div>

                        <div class="form-group form-group-sm">
                            <div class="col-sm-6 col-sm-offset-1">
                                <button type="button" class="btn btn-sm btn-primary" id="btn-reset-password"><i class="fa fa-check fa-fw"></i> 重置密码</button>
                            </div>
                        </div>

                    </div>
                </div>


                <div class="modal-footer">
                    <div class="row">
                        <div class="col-sm-8">
                            <div id="edit-user-message" class="alert alert-danger" style="text-align:left;display:none;"></div>
                        </div>
                        <div class="col-sm-4">
                            <button type="button" class="btn btn-sm btn-default" data-dismiss="modal"><i class="fa fa-times fa-fw"></i> 取消</button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <div class="modal fade" id="dlg-import-user" tabindex="-1" role="dialog">
        <div class="modal-dialog" role="document">
            <div class="modal-content">
                <div class="modal-header">
                    <button type="button" class="close" data-dismiss="modal" aria-label="Close"><i class="fa fa-times-circle fa-fw"></i></button>
                    <h3 class="modal-title">导入用户</h3>
                </div>
                <div class="modal-body">

                    <div style="text-align:center;margin:10px 0 20px 0;">
                        <p>请点击图标，选择要上传的文件！</p>
                        <p><a href="/static/download/teleport-example-user.csv"><i class="fa fa-download fa-fw"></i>下载用户信息文件模板</a></p>
                    </div>
                    <div style="text-align:center;">
                        <i id="btn-select-file" class="upload-button far fa-file-alt fa-fw"></i>
                    </div>
                    <div style="text-align:center;margin:10px;" id="upload-file-info">- 尚未选择文件 -</div>
                    <div style="text-align:center;">
                        <div id="upload-file-message" style="display:none;margin:10px;text-align: left;" class="alert alert-info">
                            <i class="fa fa-cog fa-spin fa-fw"></i> 正在导入，请稍候...
                        </div>
                        <button type="button" class="btn btn-sm btn-primary" id="btn-do-upload-file" style="display:none;margin:10px;"><i class="fa fa-upload fa-fw"></i> 开始导入</button>
                    </div>
                </div>
            </div>
        </div>
    </div>
</%block>
