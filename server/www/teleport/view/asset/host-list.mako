<%!
    page_icon_class_ = 'fa fa-server fa-fw'
    page_title_ = ['资产', '主机管理']
    page_id_ = ['asset', 'host']
%>
<%inherit file="../page_base.mako"/>

<%block name="extend_js_file">
    <script type="text/javascript" src="${ static_url('js/asset/host-list.js') }"></script>
    <script type="text/javascript" src="${ static_url('plugins/jquery/ajaxfileupload.js') }"></script>
</%block>

<%block name="embed_js">
    <script type="text/javascript">
        $app.add_options(${page_param});
    </script>
</%block>

<%block name="embed_css">
    <style>
    </style>
</%block>

<%block name="breadcrumb_extra">
    <ol class="breadcrumb breadcrumb-list">
        ##         <li><i class="fa fa-clock-o"></i> 服务器时间：<span id="tp-timer">-</span></li>
##         <li><i class="fa fa-bolt"></i> 助手版本：<span id="tp-assist-ver"></span></li>
    </ol>
</%block>

## Begin Main Body.

<div class="page-content-inner">

    <!-- begin box -->
    <div class="box">
        <div class="table-prefix-area">
            <div class="table-extend-cell">
                <span class="table-name"><i class="fa fa-list fa-fw"></i> 主机列表</span>
                <div class="btn-group btn-group-sm dropdown" id="filter-host-group">
                    <button type="button" class="btn btn-default dropdown-toggle" data-toggle="dropdown"><i class="fa fa-filter fa-fw"></i>主机分组：<span data-tp-select-result>所有</span> <i class="fa fa-caret-right"></i></button>
                    <ul class="dropdown-menu  dropdown-menu-sm"></ul>
                </div>
                <button id="btn-refresh-host" class="btn btn-sm btn-default"><i class="fa fa-redo fa-fw"></i> 刷新列表</button>
            </div>
            <div class="table-extend-cell table-extend-cell-right group-actions">
                <button id="btn-add-host" class="btn btn-sm btn-primary"><i class="fa fa-plus-circle fa-fw"></i> 添加主机</button>
                <button id="btn-import-asset" class="btn btn-sm btn-default"><i class="fa fa-plus-square fa-fw"></i> 导入主机和账号</button>
            </div>
        </div>

        <table id="table-host" class="table table-striped table-bordered table-hover table-data no-footer dtr-inline"></table>

        <div class="table-extend-area">
            <div class="table-extend-cell checkbox-select-all"><input id="table-host-select-all" type="checkbox"/></div>
            <div class="table-extend-cell group-actions">
                <div class="btn-group" role="group">
                    <button id="btn-lock-host" type="button" class="btn btn-default"><i class="fa fa-lock fa-fw"></i> 禁用</button>
                    <button id="btn-unlock-host" type="button" class="btn btn-default"><i class="fa fa-unlock fa-fw"></i> 解禁</button>
                    <button id="btn-remove-host" type="button" class="btn btn-default"><i class="fa fa-times-circle fa-fw"></i> 删除</button>
                </div>
            </div>
            <div class="table-extend-cell table-item-counter">
                <ol id="table-host-paging"></ol>
            </div>
        </div>

        <div class="table-extend-area">
            <div class="table-extend-cell">
                <div style="text-align:right;">
                    <nav>
                        <ul id="table-host-pagination" class="pagination"></ul>
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
            <li>批量导入主机和账号需要上传.csv格式的文件，您可以 <a href="/static/download/teleport-example-asset.csv"><i class="fa fa-download fa-fw"></i>下载资产信息文件模板</a> 进行编辑。</li>
        </ul>
    </div>
</div>


<%block name="extend_content">
    <div class="modal fade" id="dlg-host-info" tabindex="-1">
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
                    <button type="button" class="btn btn-sm btn-primary" data-field="btn-edit"><i class="fa fa-edit fa-fw"></i> 编辑主机信息</button>
                    <button type="button" class="btn btn-sm btn-default" data-dismiss="modal"><i class="fa fa-times fa-fw"></i> 关闭</button>
                </div>
            </div>
        </div>
    </div>

    <div class="modal fade" id="dlg-edit-host" tabindex="-1">
        <div class="modal-dialog" role="document">
            <div class="modal-content">
                <div class="modal-header">
                    <button type="button" class="close" data-dismiss="modal" aria-label="Close"><i class="fa fa-times-circle fa-fw"></i></button>
                    <h3 data-field="dlg-title" class="modal-title"></h3>
                </div>
                <div class="modal-body">

                    <div class="form-horizontal">

                        ##                         <div class="form-group form-group-sm">
                        ##                             <label for="edit-host-type" class="col-sm-2 control-label require">主机类型：</label>
                        ##                             <div class="col-sm-6">
                        ##                                 <div id="edit-host-type" class="btn-group btn-group-sm"></div>
                        ##                             </div>
                        ##                         </div>

                        <div class="form-group form-group-sm">
                            <label for="edit-host-os-type" class="col-sm-3 control-label require">远程主机系统：</label>
                            <div class="col-sm-4">
                                <select id="edit-host-os-type" class="form-control"></select>
                            </div>
                        </div>

                        <div class="form-group form-group-sm">
                            <label for="edit-host-ip" class="col-sm-3 control-label require">远程主机地址：</label>
                            <div class="col-sm-4">
                                <input id="edit-host-ip" type="text" class="form-control" placeholder="远程主机IP地址"/>
                            </div>
                        </div>

                        <div class="form-group form-group-sm">
                            <label for="edit-host-conn-mode" class="col-sm-3 control-label require">连接模式：</label>
                            <div class="col-sm-4">
                                <select id="edit-host-conn-mode" class="form-control">
                                    <option value="0">直接连接</option>
                                    <option value="1">端口映射</option>
                                </select>
                            </div>
                            <div class="col-sm-2">
                                <div class="control-desc">
                                    <a id="help-host-conn-mode" tabindex="0" role="button" data-toggle="popover" data-placement="bottom"
                                       data-html="true" data-title="连接模式说明"
                                       data-content='<div style="width:400px;"><strong>直接连接</strong><br/>远程主机可以由teleport直接连通。<br/>操作端 <i class="fa fa-arrow-right fa-fw"></i> teleport <i class="fa fa-arrow-right fa-fw"></i> 远程主机<br/><br/><strong>端口映射</strong><br/>Teleport需要通过一台路由主机以端口映射方式访问远程主机。<br/>操作端 <i class="fa fa-arrow-right fa-fw"></i> teleport <i class="fa fa-arrow-right fa-fw"></i> 路由主机 <i class="fa fa-arrow-right fa-fw"></i> 远程主机</div>'
                                    ><i class="fa fa-question-circle fw"></i></a>
                                </div>
                            </div>
                        </div>

                        <div id="block-router-mode" style="display:none;">
                            <div class="form-group form-group-sm">
                                <label for="edit-host-router-ip" class="col-sm-3 control-label require">路由主机地址：</label>
                                <div class="col-sm-4">
                                    <input id="edit-host-router-ip" type="text" class="form-control" placeholder="路由主机IP地址"/>
                                </div>
                                <label for="edit-host-router-port" class="col-sm-2 control-label require">映射端口：</label>
                                <div class="col-sm-2">
                                    <input id="edit-host-router-port" type="text" class="form-control"/>
                                </div>
                            </div>
                        </div>

                        <div class="form-group form-group-sm">
                            <label for="edit-host-name" class="col-sm-3 control-label">名称：</label>
                            <div class="col-sm-8">
                                <input id="edit-host-name" type="text" class="form-control"/>
                            </div>
                        </div>

                        <div class="form-group form-group-sm">
                            <label for="edit-host-cid" class="col-sm-3 control-label">资产编号：</label>
                            <div class="col-sm-8">
                                <input id="edit-host-cid" type="text" class="form-control"/>
                            </div>
                            <div class="col-sm-1">
                                <div class="control-desc">
                                    <a id="help-host-cid" tabindex="0" role="button" data-toggle="popover" data-placement="bottom"
                                       data-html="true" data-title="资产编号说明"
                                       data-content='<div style="width:300px;">为统一管理资产所设定的内部编号。</div>'
                                    ><i class="fa fa-question-circle fw"></i></a>
                                </div>
                            </div>
                        </div>

                        <div class="form-group form-group-sm">
                            <label for="edit-host-desc" class="col-sm-3 control-label">备注：</label>
                            <div class="col-sm-9">
                                <textarea id="edit-host-desc" class="form-control" style="resize:vertical;height:8em;"></textarea>
                            </div>
                        </div>
                    </div>
                </div>


                <div class="modal-footer">
                    <div class="row">
                        <div class="col-sm-8">
                            <div id="edit-host-message" class="alert alert-danger" style="text-align:left;display:none;"></div>
                        </div>
                        <div class="col-sm-4">
                            <button type="button" class="btn btn-sm btn-primary" id="btn-edit-host-save"><i class="fa fa-check fa-fw"></i> 确定</button>
                            <button type="button" class="btn btn-sm btn-default" data-dismiss="modal"><i class="fa fa-times fa-fw"></i> 取消</button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <div class="modal fade" id="dlg-accounts" tabindex="-1">
        <div class="modal-dialog" style="width:800px;">
            <div class="modal-content">
                <div class="modal-header">
                    <button type="button" class="close" data-dismiss="modal" aria-label="Close"><i class="fa fa-times-circle fa-fw"></i></button>
                    <h3 data-field="dlg-title" class="modal-title">远程主机账号管理</h3>
                </div>

                <div class="modal-body">

                    <div class="table-prefix-area">
                        <div class="table-extend-cell">
                            <span class="table-name"><i class="fa fa-list fa-fw"></i> 账号列表</span>
                            <button id="btn-refresh-acc" class="btn btn-sm btn-default"><i class="fa fa-redo fa-fw"></i> 刷新列表</button>
                        </div>
                        <div class="table-extend-cell table-extend-cell-right group-actions">
                            <button id="btn-add-acc" class="btn btn-sm btn-primary"><i class="fa fa-plus-circle fa-fw"></i> 添加账号</button>
                        </div>
                    </div>

                    <table id="table-acc" class="table table-striped table-bordered table-hover table-data no-footer dtr-inline"></table>

                    <div class="table-extend-area">
                        <div class="table-extend-cell checkbox-select-all"><input id="table-acc-select-all" type="checkbox"/></div>
                        <div class="table-extend-cell group-actions">
                            <div class="btn-group" role="group">
                                <button id="btn-lock-acc" type="button" class="btn btn-default"><i class="fa fa-lock fa-fw"></i> 禁用</button>
                                <button id="btn-unlock-acc" type="button" class="btn btn-default"><i class="fa fa-unlock fa-fw"></i> 解禁</button>
                                <button id="btn-remove-acc" type="button" class="btn btn-default"><i class="fa fa-times-circle fa-fw"></i> 删除</button>
                            </div>
                        </div>
                    </div>

                </div>

                <div class="modal-footer">
                    <button type="button" class="btn btn-sm btn-default" data-dismiss="modal"><i class="fa fa-times fa-fw"></i> 完成</button>
                </div>
            </div>
        </div>
    </div>

    <div class="modal fade" id="dlg-edit-account" tabindex="-1">
        <div class="modal-dialog" role="document" style="width:480px;top:60px;">
            <div class="modal-content">
                <div class="modal-header">
                    <button type="button" class="close" data-dismiss="modal" aria-label="Close"><i class="fa fa-times-circle fa-fw"></i></button>
                    <h3 data-field="dlg-title" class="modal-title"></h3>
                </div>
                <div class="modal-body">

                    <div class="form-horizontal">

                        <div class="form-group form-group-sm">
                            <label class="col-sm-3 control-label" for="account-protocol-type"><strong>连接协议：</strong></label>
                            <div class="col-sm-9">
                                <select id="account-protocol-type" class="form-control">
                                    <option value="1">RDP</option>
                                    <option value="2">SSH</option>
                                    <option value="3">TELNET</option>
                                </select>
                            </div>
                        </div>

                        <div class="form-group form-group-sm">
                            <label class="col-sm-3 control-label" for="account-protocol-port"><strong>端口：</strong></label>
                            <div class="col-sm-9">
                                <input id="account-protocol-port" type="text" class="form-control" placeholder=""/>
                                ##                                 <p id="account-protocol-port-static" class="form-control-static mono" style="color:#0a6aa1;font-weight:bold;display:none;"></p>
                            </div>
                        </div>

                        <div class="form-group form-group-sm">
                            <label class="col-sm-3 control-label" for="account-auth-type"><strong>认证方式：</strong></label>
                            <div class="col-sm-9">
                                <select id="account-auth-type" class="form-control">
                                    <option value="1">用户名/密码 认证</option>
                                    <option value="2">SSH私钥 认证</option>
                                    <option value="0">无需认证</option>
                                </select>
                            </div>
                        </div>

                        <div id="block-prompt" style="display:none;">
                            <div class="form-group form-group-sm">
                                <label for="account-username-prompt" class="col-sm-3 control-label"><strong>用户名预期提示：</strong></label>
                                <div class="col-sm-6">
                                    <input id="account-username-prompt" type="text" class="form-control" placeholder="遇到此提示则自动发送用户名" value="ogin:"/>
                                </div>
                                <div class="col-sm-3">
                                    <div class="control-desc">
                                        <a id="help-username-prompt" tabindex="0" role="button" data-toggle="popover" data-placement="bottom"><i class="fa fa-question-circle fw"></i> 这是什么？</a>
                                    </div>
                                </div>
                            </div>
                            <div class="form-group form-group-sm">
                                <label for="account-password-prompt" class="col-sm-3 control-label"><strong>密码预期提示：</strong></label>
                                <div class="col-sm-6">
                                    <input id="account-password-prompt" type="text" class="form-control" placeholder="遇到此提示则自动发送密码" value="assword:"/>
                                </div>
                                <div class="col-sm-3">
                                    <div class="control-desc">
                                        <a id="help-password-prompt" tabindex="0" role="button" data-toggle="popover" data-placement="bottom"><i class="fa fa-question-circle fw"></i> 这是什么？</a>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div id="block-username" class="form-group form-group-sm">
                            <label for="account-username" class="col-sm-3 control-label"><strong>远程账号：</strong></label>
                            <div class="col-sm-9">
                                <input id="account-username" type="text" class="form-control" placeholder="登录远程主机的账号名"/>
                            </div>
                        </div>

                        <div id="block-password">
                            <div class="form-group form-group-sm">
                                <label for="account-password" class="col-sm-3 control-label"><strong>密码：</strong></label>
                                <div class="col-sm-9">
                                    <div class="input-group">
                                        <input id="account-password" type="password" class="form-control" placeholder="登录远程主机的密码">
                                        <span class="input-group-btn"><button class="btn btn-sm btn-default" type="button" id="btn-show-account-password"><i class="fa fa-eye fa-fw"></i></button></span>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div id="block-sshkey" style="display:none;">
                            <div class="form-group form-group-sm">
                                <label for="account-ssh-pri" class="col-sm-3 control-label"><strong>SSH私钥：</strong></label>
                                <div class="col-sm-9">
                                    <textarea title="" class="form-control textarea-resize-y textarea-code" id="account-ssh-pri" rows=5 placeholder="登录远程主机的私钥"></textarea>
                                </div>
                            </div>
                        </div>

                    </div>
                </div>


                <div class="modal-footer">
                    <button type="button" class="btn btn-sm btn-success" id="btn-edit-account-test"><i class="fa fa-bolt fa-fw"></i> 测试连接</button>
                    <button type="button" class="btn btn-sm btn-primary" id="btn-edit-account-save"><i class="fa fa-check fa-fw"></i> 确定</button>
                    <button type="button" class="btn btn-sm btn-default" data-dismiss="modal"><i class="fa fa-times fa-fw"></i> 取消</button>
                </div>
            </div>
        </div>
    </div>

    <div class="modal fade" id="dlg-import-asset" tabindex="-1">
        <div class="modal-dialog" role="document">
            <div class="modal-content">
                <div class="modal-header">
                    <button type="button" class="close" data-dismiss="modal" aria-label="Close"><i class="fa fa-times-circle fa-fw"></i></button>
                    <h3 class="modal-title">导入资产（主机及账号）</h3>
                </div>
                <div class="modal-body">

                    <div style="text-align:center;margin:10px 0 20px 0;">
                        <p>请点击图标，选择要上传的文件！</p>
                        <p><a href="/static/download/teleport-example-asset.csv"><i class="fa fa-download fa-fw"></i>下载资产信息文件模板</a></p>
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

## <%block name="embed_js">
##     <script type="text/javascript">
##     </script>
## </%block>
