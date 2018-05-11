<%!
    page_icon_class_ = 'fa fa-server fa-fw'
    page_title_ = ['运维', '运维授权']
    page_id_ = ['ops', 'auz']
%>
<%inherit file="../page_base.mako"/>

<%block name="extend_js_file">
    <script type="text/javascript" src="${ static_url('js/ops/auz-info.js') }"></script>
</%block>

<%block name="breadcrumb">
    <ol class="breadcrumb">
        %for i in range(len(self.attr.page_title_)):
            %if i == 0:
                <li><i class="${self.attr.page_icon_class_}"></i> ${self.attr.page_title_[i]}</li>
            %else:
                <li>${self.attr.page_title_[i]}</li>
            %endif
        %endfor
        <li><strong id="group-name-breadcrumb"></strong><span data-field="policy-name"></span></li>
    </ol>
</%block>

<%block name="embed_js">
    <script type="text/javascript">
        $app.add_options(${page_param});
        if ($app.options.policy_id !== 0) {
            $('[data-field="policy-name"]').text($app.options.policy_name);
            $('[data-field="policy-desc"]').text($app.options.policy_desc);
        } else {
            ##             $tp.notify_error('授权策略不存在！');
            $tp.disable_dom('#work-area', '授权策略不存在！');
        }
    </script>
</%block>


<%block name="embed_css">
    <style type="text/css">
        .nav-tabs-title {
            padding: 10px;
            font-size: 1.2rem;
        }

        .nav-tabs-title .title {
            display: inline-block;
        }

        .nav-tabs-title .sub-title {
            display: inline-block;
            color: #878787;
            padding-left: 15px;
            font-size:1rem;
        }

        #area-operator, #area-asset {
            border: 1px solid #d6d6d6;
        }

        .area-title {
            padding: 5px;
            background-color: #f4f4f4;
        }
        .area-title .name {
            font-size:110%;
        }
        .area-title .desc {
            color:#858585;
        }

        .field-name {
            padding-right: 20px;
        }

        .field-desc {
            display: inline-block;
            color: #878787;
        }

    </style>
</%block>

## Begin Main Body.

<div class="page-content-inner">

    <div class="box box-nav-tabs" id="work-area">

        <div class="nav-tabs-title">
            <div class="title">授权策略：<span data-field="policy-name"></span></div>
            <div class="sub-title" data-field="policy-desc"></div>
        </div>

        <!-- Nav tabs -->
        <ul class="nav nav-tabs">
            <li class="active"><a href="#tab-object" data-toggle="tab">授权对象</a></li>
            <li><a href="#tab-config" data-toggle="tab">连接控制</a></li>
        </ul>

        <!-- Tab panes -->
        <div class="tab-content">
            <div class="tab-pane active" style="padding:15px;" id="tab-object">
                <div class="row">
                    <div class="col-md-6">
                        <div id="area-operator">
                            <div class="area-title"><span class="name">授权操作者</span><span class="desc">（允许远程操作的用户）</span></div>

                            <div style="padding:5px;">
                                <div class="table-extend-area">
                                    <div class="table-extend-cell">
                                        <div class="btn-group btn-group-sm">
                                            <btn class="btn btn-default" id="btn-refresh-operator"><i class="fa fa-redo"></i> 刷新列表</btn>
                                        </div>
                                    </div>
                                    <div class="table-extend-cell table-item-counter">
                                        <div class="btn-group btn-group-sm">
                                            <btn class="btn btn-success" id="btn-add-user"><i class="fa fa-plus"></i> 添加用户</btn>
                                            <btn class="btn btn-primary" id="btn-add-user-group"><i class="fa fa-plus-circle"></i> 添加用户组</btn>
                                        </div>
                                    </div>
                                </div>

                                <table id="table-operator" class="table table-striped table-bordered table-hover table-data no-footer dtr-inline"></table>

                                <div class="table-extend-area">
                                    <div class="table-extend-cell checkbox-select-all"><input id="table-operator-select-all" type="checkbox"/></div>
                                    <div class="table-extend-cell group-actions">
                                        <div class="btn-group" role="group">
                                            <button id="btn-remove-operator" type="button" class="btn btn-default"><i class="fa fa-times-circle fa-fw"></i> 删除</button>
                                        </div>
                                    </div>
                                    <div class="table-extend-cell table-item-counter">
                                        <ol id="table-operator-paging"></ol>
                                    </div>
                                </div>

                                <div class="table-extend-area">
                                    <div class="table-extend-cell">
                                        <div style="text-align:right;">
                                            <nav>
                                                <ul id="table-operator-pagination" class="pagination"></ul>
                                            </nav>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div class="col-md-6">
                        <div id="area-asset">
                            <div class="area-title"><span class="name">被授权资产</span><span class="desc">（允许被远程操作的主机或账号）</span></div>

                            <div style="padding:5px;">
                                <div class="table-extend-area">
                                    <div class="table-extend-cell">
                                        <div class="btn-group btn-group-sm">
                                            <btn class="btn btn-default" id="btn-refresh-asset"><i class="fa fa-redo"></i> 刷新列表</btn>
                                        </div>
                                    </div>
                                    <div class="table-extend-cell table-item-counter">
                                        <div class="btn-group btn-group-sm">
                                            <btn class="btn btn-success" id="btn-add-acc"><i class="fa fa-plus"></i> 添加账号</btn>
                                            <btn class="btn btn-primary" id="btn-add-acc-group"><i class="fa fa-plus-circle"></i> 添加账号组</btn>
                                            <btn class="btn btn-success" id="btn-add-host"><i class="fa fa-plus"></i> 添加主机</btn>
                                            <btn class="btn btn-primary" id="btn-add-host-group"><i class="fa fa-plus-circle"></i> 添加主机组</btn>
                                        </div>
                                    </div>
                                </div>

                                <table id="table-asset" class="table table-striped table-bordered table-hover table-data no-footer dtr-inline"></table>

                                <div class="table-extend-area">
                                    <div class="table-extend-cell checkbox-select-all"><input id="table-asset-select-all" type="checkbox"/></div>
                                    <div class="table-extend-cell group-actions">
                                        <div class="btn-group" role="group">
                                            <button id="btn-remove-asset" type="button" class="btn btn-default"><i class="fa fa-times-circle fa-fw"></i> 删除</button>
                                        </div>
                                    </div>
                                    <div class="table-extend-cell table-item-counter">
                                        <ol id="table-asset-paging"></ol>
                                    </div>
                                </div>

                                <div class="table-extend-area">
                                    <div class="table-extend-cell">
                                        <div style="text-align:right;">
                                            <nav>
                                                <ul id="table-asset-pagination" class="pagination"></ul>
                                            </nav>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <div class="tab-pane" id="tab-config">
                <table class="table table-config-list">
##                     <tr>
##                         <td class="key">会话选项</td>
##                         <td class="value">
##                             <div id="record-allow-replay" class="tp-checkbox tp-editable">记录会话历史</div>
##                         </td>
##                     </tr>
##                     <tr>
##                         <td class="key"></td>
##                         <td class="value">
##                             <div id="record-allow-real-time" class="tp-checkbox tp-disabled">允许实时监控（开发中）</div>
##                         </td>
##                     </tr>

##                     <tr>
##                         <td colspan="2" class="title">
##                             <hr class="hr-sm"/>
##                         </td>
##                     </tr>

                    ## <div id="rdp-allow-desktop" class="tp-checkbox tp-editable tp-selected">允许 远程桌面</div>
                    ## <div id="rdp-allow-app" class="tp-checkbox">允许 远程应用</div>

                    <tr>
                        <td class="key">RDP选项</td>
                        <td class="value">
                            <div id="rdp-allow-clipboard" class="tp-checkbox tp-editable">允许剪贴板</div>
                        </td>
                    </tr>
                    <tr>
                        <td class="key"></td>
                        <td class="value">
                            <div id="rdp-allow-disk" class="tp-checkbox tp-editable">允许驱动器映射</div>
                        </td>
                    </tr>
                    <tr>
                        <td class="key"></td>
                        <td class="value">
                            <div id="rdp-allow-console" class="tp-checkbox tp-editable">允许管理员连接（Console模式）</div>
                        </td>
                    </tr>

                    <tr>
                        <td colspan="2" class="title">
                            <hr class="hr-sm"/>
                        </td>
                    </tr>

                    ## <div id="ssh-allow-x11" class="tp-checkbox">允许X11转发</div>
                    ## <div id="ssh-allow-tunnel" class="tp-checkbox">允许隧道转发</div>
                    ## <div id="ssh-allow-exec" class="tp-checkbox">允许远程执行exec</div>

                    <tr>
                        <td class="key">SSH选项</td>
                        <td class="value">
                            <div id="ssh-allow-shell" class="tp-checkbox tp-editable">允许SSH</div>
                        </td>
                    </tr>
                    <tr>
                        <td class="key"></td>
                        <td class="value">
                            <div id="ssh-allow-sftp" class="tp-checkbox tp-editable">允许SFTP</div>
                        </td>
                    </tr>
##                     <tr>
##                         <td class="key"></td>
##                         <td class="value">
##                             <div id="ssh-allow-x11" class="tp-checkbox tp-disabled">允许X11转发（开发中）</div>
##                         </td>
##                     </tr>

                    <tr>
                        <td colspan="2" class="title">
                            <hr class="hr-sm"/>
                        </td>
                    </tr>

                    <tr>
                        <td class="key"></td>
                        <td class="value">
                            <button type="button" class="btn btn-sm btn-success" id="btn-save-flags"><i class="fa fa-check fa-fw"></i> 保存设置</button>
                        </td>
                    </tr>
                </table>


            </div>
        </div>
    </div>

    <div class="box">
        <p>说明：</p>
        <ul class="help-list">
            <li>授权对象表格表示左侧“授权操作者”可以访问右侧“被授权资产”。</li>
            <li>修改授权对象和连接控制选项不会影响当前已经建立的连接。</li>
            <li>如被授权资产为主机/主机组，则允许用户以对应主机相关的任意账号进行连接。</li>
            <li>按“组”进行授权，则后续加入对应组的用户、账号或主机均自动获得本策略的授权。</li>
        </ul>
    </div>

</div>


<%block name="extend_content">
    <div class="modal fade" id="dlg-sel-user" tabindex="-1" role="dialog">
        <div class="modal-dialog modal-lg" role="document">
            <div class="modal-content">
                <div class="modal-header">
                    <button type="button" class="close" data-dismiss="modal" aria-label="Close"><i class="fa fa-times-circle fa-fw"></i></button>
                    <h3 data-field="dlg-title" class="modal-title">选择用户</h3>
                </div>
                <div class="modal-body">

                    <table id="table-sel-user" class="table table-striped table-bordered table-hover table-data no-footer dtr-inline"></table>
                    <div class="table-extend-area">
                        <div class="table-extend-cell checkbox-select-all"><input data-action="sel-all" type="checkbox"/></div>
                        <div class="table-extend-cell group-actions">
                            <div class="btn-group" role="group">
                                <button data-action="use-selected" type="button" class="btn btn-primary"><i class="fa fa-edit fa-fw"></i> 添加为授权操作者</button>
                            </div>
                        </div>
                        <div class="table-extend-cell table-item-counter">
                            <ol id="table-sel-user-paging"></ol>
                        </div>
                    </div>
                    <div class="table-extend-area">
                        <div class="table-extend-cell">
                            <div style="text-align:right;">
                                <nav>
                                    <ul id="table-sel-user-pagination" class="pagination"></ul>
                                </nav>
                            </div>
                        </div>
                    </div>

                </div>


                <div class="modal-footer">
                    <button type="button" class="btn btn-sm btn-default" data-dismiss="modal"><i class="fa fa-times fa-fw"></i> 关闭</button>
                </div>
            </div>
        </div>
    </div>

    <div class="modal fade" id="dlg-sel-user-group" tabindex="-1" role="dialog">
        <div class="modal-dialog" role="document">
            <div class="modal-content">
                <div class="modal-header">
                    <button type="button" class="close" data-dismiss="modal" aria-label="Close"><i class="fa fa-times-circle fa-fw"></i></button>
                    <h3 data-field="dlg-title" class="modal-title">选择用户组</h3>
                </div>
                <div class="modal-body">

                    <table id="table-sel-user-group" class="table table-striped table-bordered table-hover table-data no-footer dtr-inline"></table>
                    <div class="table-extend-area">
                        <div class="table-extend-cell checkbox-select-all"><input data-action="sel-all" type="checkbox"/></div>
                        <div class="table-extend-cell group-actions">
                            <div class="btn-group" role="group">
                                <button data-action="use-selected" type="button" class="btn btn-primary"><i class="fa fa-edit fa-fw"></i> 添加为授权操作者</button>
                            </div>
                        </div>
                        <div class="table-extend-cell table-item-counter">
                            <ol id="table-sel-user-group-paging"></ol>
                        </div>
                    </div>
                    <div class="table-extend-area">
                        <div class="table-extend-cell">
                            <div style="text-align:right;">
                                <nav>
                                    <ul id="table-sel-user-group-pagination" class="pagination"></ul>
                                </nav>
                            </div>
                        </div>
                    </div>

                </div>


                <div class="modal-footer">
                    <button type="button" class="btn btn-sm btn-default" data-dismiss="modal"><i class="fa fa-times fa-fw"></i> 关闭</button>
                </div>
            </div>
        </div>
    </div>

    <div class="modal fade" id="dlg-sel-acc" tabindex="-1" role="dialog">
        <div class="modal-dialog modal-lg" role="document">
            <div class="modal-content">
                <div class="modal-header">
                    <button type="button" class="close" data-dismiss="modal" aria-label="Close"><i class="fa fa-times-circle fa-fw"></i></button>
                    <h3 data-field="dlg-title" class="modal-title">选择账号</h3>
                </div>
                <div class="modal-body">

                    <table id="table-sel-acc" class="table table-striped table-bordered table-hover table-data no-footer dtr-inline"></table>
                    <div class="table-extend-area">
                        <div class="table-extend-cell checkbox-select-all"><input data-action="sel-all" type="checkbox"/></div>
                        <div class="table-extend-cell group-actions">
                            <div class="btn-group" role="group">
                                <button data-action="use-selected" type="button" class="btn btn-primary"><i class="fa fa-edit fa-fw"></i> 添加为被授权资产</button>
                            </div>
                        </div>
                        <div class="table-extend-cell table-item-counter">
                            <ol id="table-sel-acc-paging"></ol>
                        </div>
                    </div>
                    <div class="table-extend-area">
                        <div class="table-extend-cell">
                            <div style="text-align:right;">
                                <nav>
                                    <ul id="table-sel-acc-pagination" class="pagination"></ul>
                                </nav>
                            </div>
                        </div>
                    </div>

                </div>


                <div class="modal-footer">
                    <button type="button" class="btn btn-sm btn-default" data-dismiss="modal"><i class="fa fa-times fa-fw"></i> 关闭</button>
                </div>
            </div>
        </div>
    </div>

    <div class="modal fade" id="dlg-sel-acc-group" tabindex="-1" role="dialog">
        <div class="modal-dialog" role="document">
            <div class="modal-content">
                <div class="modal-header">
                    <button type="button" class="close" data-dismiss="modal" aria-label="Close"><i class="fa fa-times-circle fa-fw"></i></button>
                    <h3 data-field="dlg-title" class="modal-title">选择账号组</h3>
                </div>
                <div class="modal-body">

                    <table id="table-sel-acc-group" class="table table-striped table-bordered table-hover table-data no-footer dtr-inline"></table>
                    <div class="table-extend-area">
                        <div class="table-extend-cell checkbox-select-all"><input data-action="sel-all" type="checkbox"/></div>
                        <div class="table-extend-cell group-actions">
                            <div class="btn-group" role="group">
                                <button data-action="use-selected" type="button" class="btn btn-primary"><i class="fa fa-edit fa-fw"></i> 添加为被授权资产</button>
                            </div>
                        </div>
                        <div class="table-extend-cell table-item-counter">
                            <ol id="table-sel-acc-group-paging"></ol>
                        </div>
                    </div>
                    <div class="table-extend-area">
                        <div class="table-extend-cell">
                            <div style="text-align:right;">
                                <nav>
                                    <ul id="table-sel-acc-group-pagination" class="pagination"></ul>
                                </nav>
                            </div>
                        </div>
                    </div>

                </div>


                <div class="modal-footer">
                    <button type="button" class="btn btn-sm btn-default" data-dismiss="modal"><i class="fa fa-times fa-fw"></i> 关闭</button>
                </div>
            </div>
        </div>
    </div>

    <div class="modal fade" id="dlg-sel-host" tabindex="-1" role="dialog">
        <div class="modal-dialog modal-lg" role="document">
            <div class="modal-content">
                <div class="modal-header">
                    <button type="button" class="close" data-dismiss="modal" aria-label="Close"><i class="fa fa-times-circle fa-fw"></i></button>
                    <h3 data-field="dlg-title" class="modal-title">选择主机</h3>
                </div>
                <div class="modal-body">

                    <table id="table-sel-host" class="table table-striped table-bordered table-hover table-data no-footer dtr-inline"></table>
                    <div class="table-extend-area">
                        <div class="table-extend-cell checkbox-select-all"><input data-action="sel-all" type="checkbox"/></div>
                        <div class="table-extend-cell group-actions">
                            <div class="btn-group" role="group">
                                <button data-action="use-selected" type="button" class="btn btn-primary"><i class="fa fa-edit fa-fw"></i> 添加为被授权资产</button>
                            </div>
                        </div>
                        <div class="table-extend-cell table-item-counter">
                            <ol id="table-sel-host-paging"></ol>
                        </div>
                    </div>
                    <div class="table-extend-area">
                        <div class="table-extend-cell">
                            <div style="text-align:right;">
                                <nav>
                                    <ul id="table-sel-host-pagination" class="pagination"></ul>
                                </nav>
                            </div>
                        </div>
                    </div>

                </div>


                <div class="modal-footer">
                    <button type="button" class="btn btn-sm btn-default" data-dismiss="modal"><i class="fa fa-times fa-fw"></i> 关闭</button>
                </div>
            </div>
        </div>
    </div>

    <div class="modal fade" id="dlg-sel-host-group" tabindex="-1" role="dialog">
        <div class="modal-dialog" role="document">
            <div class="modal-content">
                <div class="modal-header">
                    <button type="button" class="close" data-dismiss="modal" aria-label="Close"><i class="fa fa-times-circle fa-fw"></i></button>
                    <h3 data-field="dlg-title" class="modal-title">选择主机组</h3>
                </div>
                <div class="modal-body">

                    <table id="table-sel-host-group" class="table table-striped table-bordered table-hover table-data no-footer dtr-inline"></table>
                    <div class="table-extend-area">
                        <div class="table-extend-cell checkbox-select-all"><input data-action="sel-all" type="checkbox"/></div>
                        <div class="table-extend-cell group-actions">
                            <div class="btn-group" role="group">
                                <button data-action="use-selected" type="button" class="btn btn-primary"><i class="fa fa-edit fa-fw"></i> 添加为被授权资产</button>
                            </div>
                        </div>
                        <div class="table-extend-cell table-item-counter">
                            <ol id="table-sel-host-group-paging"></ol>
                        </div>
                    </div>
                    <div class="table-extend-area">
                        <div class="table-extend-cell">
                            <div style="text-align:right;">
                                <nav>
                                    <ul id="table-sel-host-group-pagination" class="pagination"></ul>
                                </nav>
                            </div>
                        </div>
                    </div>

                </div>


                <div class="modal-footer">
                    <button type="button" class="btn btn-sm btn-default" data-dismiss="modal"><i class="fa fa-times fa-fw"></i> 关闭</button>
                </div>
            </div>
        </div>
    </div>

</%block>
