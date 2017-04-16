<%!
    page_title_ = '远程主机管理'
    page_menu_ = ['host']
    page_id_ = 'host'
%>
<%inherit file="../page_base.mako"/>

<%block name="extend_js">
    <script type="text/javascript" src="${ static_url('js/ui/teleport.js') }"></script>
    <script type="text/javascript" src="${ static_url('js/ui/admin_host.js') }"></script>
</%block>

<%block name="breadcrumb">
    <ol class="breadcrumb">
        <li><i class="fa fa-server fa-fw"></i> ${self.attr.page_title_}</li>
    </ol>
</%block>

## Begin Main Body.

<div class="page-content">

    <!-- begin box -->
    <div class="box" id="ywl_host_list">

        <!-- begin filter -->
        <div class="page-filter">
            <div class="" style="float:right;">
                <span id="tp-assist-current-version" style="margin-right: 50px"> 助手版本：未知</span>

                <a href="javascript:;" class="btn btn-sm btn-primary" ywl-filter="reload"><i class="fa fa-repeat fa-fw"></i> 刷新</a>
            </div>

            <div class="">

                <div class="input-group input-group-sm" style="display:inline-block;margin-right:10px;">
                    <span class="input-group-addon" style="display:inline-block;width:auto; line-height:28px;height:30px;padding:0 10px;font-size:13px;">主机分组</span>
                    <div class="input-group-btn" ywl-filter="host-group" style="display:inline-block;margin-left:-4px;">
                        <button type="button" class="btn btn-default dropdown-toggle" data-toggle="dropdown"><span>正在加载</span> <span class="caret"></span></button>
                        <ul class="dropdown-menu">
                            <li>正在加载</li>
                        </ul>
                    </div>
                </div>


                <div class="input-group input-group-sm" style="display:inline-block;margin-right:10px;">
                    <span class="input-group-addon" style="display:inline-block;width:auto; line-height:28px;height:30px;padding:0 10px;font-size:13px;">系统</span>
                    <div class="input-group-btn" ywl-filter="system-type" style="display:inline-block;margin-left:-4px;">
                        <button type="button" class="btn btn-default dropdown-toggle" data-toggle="dropdown"><span>正在加载</span> <span class="caret"></span></button>
                        <ul class="dropdown-menu">
                            <li>正在加载</li>
                        </ul>
                    </div>
                </div>


                <div class="input-group input-group-sm" ywl-filter="search" style="display:inline-block;">
                    <input type="text" class="form-control" placeholder="搜索 ID 或 IP" style="display:inline-block;">
                    <span class="input-group-btn" style="display:inline-block;margin-left:-4px;"><button type="button" class="btn btn-default"><i class="fa fa-search fa-fw"></i></button></span>
                </div>

            </div>
        </div>
        <!-- end filter -->


        <table class="table table-striped table-bordered table-hover table-data no-footer dtr-inline" ywl-table="host-list"></table>

        <!-- begin page-nav -->
        <div class="page-nav" ywl-paging="host-list">

            <div class="input-group input-group-sm" style="display:inline-block;">
                <a href="#" id="btn-add-host" class="btn btn-sm btn-primary"><i class="fa fa-plus-circle fa-fw"></i> 添加主机</a>
            </div>


            <div class="" style="float:right;">
                <nav>
                    <ul class="pagination pagination-sm"></ul>
                </nav>
            </div>

            <div style="float:right;margin-right:30px;">
                <div class="breadcrumb-container">
                    <ol class="breadcrumb">
                        <li><i class="fa fa-list fa-fw"></i> 记录总数 <strong ywl-field="recorder_total">0</strong></li>
                        <li>页数 <strong><span ywl-field="page_current">1</span>/<span ywl-field="page_total">1</span></strong></li>
                        <li>每页显示
                            <label>
                                <select></select>
                            </label>
                            条记录
                        </li>
                    </ol>
                </div>
            </div>

        </div>
        <!-- end page-nav -->

    </div>
    <!-- end of box -->


    <!-- begin box -->

    <div class="box">
        <div class="box-btn-bar">
            <div>批量操作：</div>
            <div>
                <div>
                    <button type="button" id="btn-batch-add-host" class="btn btn-sm btn-primary"><i class="fa fa-plus-square fa-fw"></i> 批量添加主机</button>
                    <button type="button" id="btn-delete-host" class="btn btn-sm btn-danger"><i class="fa fa-trash fa-fw"></i> 批量移除主机</button>
                    <button type="button" id="btn-apply-group" class="btn btn-sm btn-primary"><i class="fa fa-cubes fa-fw"></i> 批量设置分组</button>
                    <button type="button" id="btn-batch-export-host" class="btn btn-sm btn-primary"><i class="fa fa-exchange fa-fw"></i> 备份所有主机及登录信息</button>
                </div>
                <div>
                    <hr/>
                    <p>要进行批量导入主机，需要上传主机信息文件，您可以
                        <a href="/static/download/example.csv"><i class="fa fa-download fa-fw"></i> <strong>下载主机信息文件模板</strong></a> 进行编辑。
                    </p>
                </div>

            </div>
            <div class="breadcrumb-container">
            </div>

            <div class="clear-float"></div>
        </div>
    </div>

    <!-- end of box -->

</div>
<div style="height: 60px;"></div>





<%block name="extend_content">

    <div class="modal fade" id="dialog-host-edit" tabindex="-1" role="dialog">
        <div class="modal-dialog" role="document">
            <div class="modal-content">
                <div class="modal-header">
                    <h3 class="modal-title">远程主机认证信息</h3>
                </div>
                <div class="modal-body">

                    <div class="form-horizontal">

                        <div class="form-group form-group-sm">
                            <label class="col-sm-3 control-label" for="auth-sys-type"><strong>操作系统：</strong></label>
                            <div class="col-sm-6">
                                <select id="auth-sys-type" class="form-control">
                                    <option value=2>Linux</option>
                                    <option value=1>Windows</option>
                                </select>
                            </div>
                        </div>
                        <div class="form-group form-group-sm">
                            <label for="auth-host-ip" class="col-sm-3 control-label"><strong>IP 地址：</strong></label>
                            <div class="col-sm-6">
                                <input id="auth-host-ip" type="text" class="form-control" placeholder="远程主机的IP地址或域名"/>
                            </div>
                        </div>
                        <div class="form-group form-group-sm">
                            <label for="auth-host-desc" class="col-sm-3 control-label"><strong>简要描述：</strong></label>
                            <div class="col-sm-6">
                                <input id="auth-host-desc" type="text" class="form-control" placeholder="对此远程主机的简要描述，可以忽略不填。"/>
                            </div>
                        </div>

                        <div class="form-group form-group-sm">
                            <label class="col-sm-3 control-label" for="dlg-edit-host-group"><strong>主机分组：</strong></label>
                            <div class="col-sm-6">
                                <select id="dlg-edit-host-group" class="form-control"></select>
                            </div>
                        </div>

                        <hr class="small"/>

                        <div class="form-group form-group-sm">
                            <label class="col-sm-3 control-label" for="auth-sys-type"><strong>访问协议：</strong></label>
                            <div class="col-sm-6">
                                <select id="host-protocol-type" class="form-control">
                                    <option value=1>RDP</option>
                                    <option value=2>SSH</option>
                                    <option value=3>TELNET</option>
                                </select>
                            </div>
                        </div>
                        <div class="form-group form-group-sm">
                            <label class="col-sm-3 control-label" for="auth-sys-type"><strong>协议端口：</strong></label>
                            <div class="col-sm-6">
                                <input id="dlg-edit-host-protocol-port" type="text" class="form-control" value="3389">
                            </div>
                        </div>

                        <hr class="small"/>
                    </div>

                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-sm btn-primary" id="host-btn-save"><i class="fa fa-check fa-fw"></i> 保存主机信息</button>
                    <button type="button" class="btn btn-sm btn-default" data-dismiss="modal"><i class="fa fa-close fa-fw"></i> 取消</button>
                </div>
            </div>
        </div>
    </div>

    <div class="modal fade" id="dialog-host-user-edit" tabindex="-1" role="dialog">
        <div class="modal-dialog" role="document">
            <div class="modal-content">
                <div class="modal-header">
                    <h3 class="modal-title">添加系统用户</h3>
                </div>
                <div class="modal-body">
                    <div class="form-horizontal">
                        <div class="form-group form-group">
                            <label class="col-sm-2 control-label" for="auth-protocol-type"><strong>登录账号：</strong></label>
                            <div class="col-sm-10" id="sys-user-list"></div>
                        </div>
                    </div>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-sm btn-primary" id="host-user-btn-save"><i class="fa fa-check fa-fw"></i> 确定</button>
                    <button type="button" class="btn btn-sm btn-default" data-dismiss="modal"><i class="fa fa-close fa-fw"></i> 取消</button>
                </div>
            </div>
        </div>
    </div>

    <div class="modal fade" id="dialog_user" tabindex="-1" role="dialog">
        <div class="modal-dialog" style="width:460px;top:80px;">
            <div class="modal-content">
                <div class="modal-header">
                    <h3 class="modal-title">登录账号</h3>
                </div>
                <div class="modal-body">

                    <div class="form-horizontal">

                        <div class="form-group form-group-sm">
                            <label class="col-sm-4 control-label"><strong>协议：</strong></label>
                            <div class="col-sm-6">
                                <p id="auth-user-protocol-type" class="form-control-static mono" style="color:#0a6aa1;font-weight:bold;">123.45.67.89:123456</p>
                            </div>
                        </div>
                        <div class="form-group form-group-sm">
                            <label class="col-sm-4 control-label"><strong>远程主机地址：</strong></label>
                            <div class="col-sm-6">
                                <p id="add-user-host-ip" class="form-control-static mono" style="color:#0a6aa1;font-weight:bold;">123.45.67.89:123456</p>
                            </div>
                        </div>

                        <div class="form-group form-group-sm">
                            <label class="col-sm-4 control-label" for="auth-user-type"><strong>认证方式：</strong></label>
                            <div class="col-sm-6" id="auth-sys-user-type-combox">
                                <select id="auth-user-type" class="form-control">
                                    <option value="1">用户名/密码 认证</option>
                                    <option value="2">SSH私钥 认证</option>
                                    <option value="0">无需认证</option>
                                </select>
                            </div>
                        </div>

                        <div id="auth-user-block-telnet" style="display: none;">
                            <div class="form-group form-group-sm">
                                <label for="auth-user-telnet-username-prompt" class="col-sm-4 control-label"><strong>用户名预期提示：</strong></label>
                                <div class="col-sm-6">
                                    <input id="auth-user-telnet-username-prompt" type="text" class="form-control" placeholder="遇到此提示则自动发送用户名" value="ogin:"/>
                                </div>
                            </div>
                            <div class="form-group form-group-sm">
                                <label for="auth-user-telnet-pswd-prompt" class="col-sm-4 control-label"><strong>密码预期提示：</strong></label>
                                <div class="col-sm-6">
                                    <input id="auth-user-telnet-pswd-prompt" type="text" class="form-control" placeholder="遇到此提示则自动发送密码" value="assword:"/>
                                </div>
                            </div>
                        </div>


                        <div class="form-group form-group-sm" id="auth-user-block-name">
                            <label for="auth-user-host-username" class="col-sm-4 control-label"><strong>远程主机用户名：</strong></label>
                            <div class="col-sm-6">
                                <input id="auth-user-host-username" type="text" class="form-control" placeholder="请输入登录远程主机的用户名"/>
                            </div>
                        </div>

                        <div id="auth-user-block-pswd">
                            <div class="form-group form-group-sm">
                                <label for="auth-user-host-pswd" class="col-sm-4 control-label"><strong>密码：</strong></label>
                                <div class="col-sm-6">
                                    <input id="auth-user-host-pswd" type="password" class="form-control" placeholder="请输入登录远程主机的密码"/>
                                </div>
                            </div>
                            <div class="form-group form-group-sm">
                                <label for="auth-user-host-pswd-confirm" class="col-sm-4 control-label"><strong>确认密码：</strong></label>
                                <div class="col-sm-6">
                                    <input id="auth-user-host-pswd-confirm" type="password" class="form-control" placeholder="请再次输入密码"/>
                                </div>
                            </div>
                        </div>


                        <div id="auth-user-block-sshkey" style="display: none;">
                            <div class="form-group form-group-sm">
                                <label class="col-sm-4 control-label" for="auth-user-sshkey-list"><strong>SSH密钥：</strong></label>
                                <div class="col-sm-6">
                                    <select id="auth-user-sshkey-list" class="form-control"></select>
                                </div>
                            </div>
                        </div>

                    </div>
                </div>

                <div class="modal-footer">
                    <button type="button" class="btn btn-sm btn-success" id="test-btn-connect"><i class="fa fa-check fa-fw"></i> 测试连接</button>
                    <button type="button" class="btn btn-sm btn-primary" id="sys-user-btn-save"><i class="fa fa-check fa-fw"></i> 确定</button>
                    <button type="button" class="btn btn-sm btn-default" data-dismiss="modal"><i class="fa fa-close fa-fw"></i> 取消</button>
                </div>
            </div>
        </div>
    </div>

    <div class="modal fade" id="dialog_batch_join_group" tabindex="-1" role="dialog">
        <div class="modal-dialog" role="document">
            <div class="modal-content">
                <div class="modal-header">
                    <h3 class="modal-title">设置分组</h3>
                </div>
                <div class="modal-body">
                    <p>将所选主机设定为以下分组：</p>

                    <div class="form-horizontal">
                        <div class="form-group form-group-sm">
                            <label class="col-sm-3 control-label" for="group-host-group"><strong>主机分组：</strong></label>
                            <div class="col-sm-6">
                                <select id="group-host-group" class="form-control"></select>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="modal-footer">
                    <button type="button" class="btn btn-sm btn-primary" id="group-btn-save"><i class="fa fa-check fa-fw"></i> 确定</button>
                    <button type="button" class="btn btn-sm btn-default" data-dismiss="modal"><i class="fa fa-close fa-fw"></i> 取消</button>
                </div>
            </div>
        </div>
    </div>


    <div class="modal fade" id="dialog_batch_add_host" tabindex="-1" role="dialog">
        <div class="modal-dialog" role="document">
            <div class="modal-content">
                <div class="modal-header">
                    <h3 class="modal-title">批量导入结果</h3>
                </div>
                <div class="modal-body">
                    <p>以下条目未能导入：</p>
					<div id="batch_add_host_result"></div>
                </div>

                <div class="modal-footer">
                    <button type="button" class="btn btn-sm btn-default" data-dismiss="modal"><i class="fa fa-check fa-fw"></i> 知道了</button>
                </div>
            </div>
        </div>
    </div>


</%block>


<%block name="embed_js">
    <script type="text/javascript">
        ywl.add_page_options(${page_param});
    </script>
</%block>
