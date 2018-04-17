<%!
    page_icon_class_ = 'fa fa-server fa-fw'
    page_title_ = ['审计', '审计授权']
    page_id_ = ['audit', 'auz']
%>
<%inherit file="../page_base.mako"/>

<%block name="extend_js_file">
    <script type="text/javascript" src="${ static_url('js/audit/auz-info.js') }"></script>
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
            padding: 0 0 10px 0;
            font-size: 1.2rem;
        }

        .nav-tabs-title .title {
            display: inline-block;
        }

        .nav-tabs-title .sub-title {
            display: inline-block;
            color: #878787;
            padding-left: 15px;
            font-size: 1rem;
        }

        #area-auditor, #area-auditee {
            border: 1px solid #d6d6d6;
        }

        .area-title {
            padding: 5px;
            background-color: #f4f4f4;
        }

        .area-title .name {
            font-size: 110%;
        }

        .area-title .desc {
            color: #858585;
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

    <div class="box" id="work-area">
        <div class="nav-tabs-title">
            <div class="title">授权策略：<span data-field="policy-name"></span></div>
            <div class="sub-title" data-field="policy-desc"></div>
        </div>

        <div class="row">
            <div class="col-md-6">
                <div id="area-auditor">
                    <div class="area-title"><span class="name">审计操作者</span><span class="desc">（执行审计操作的用户）</span></div>

                    <div style="padding:5px;">
                        <div class="table-extend-area">
                            <div class="table-extend-cell">
                                <div class="btn-group btn-group-sm">
                                    <btn class="btn btn-default" id="btn-refresh-auditor"><i class="fa fa-redo"></i> 刷新列表</btn>
                                </div>
                            </div>
                            <div class="table-extend-cell table-item-counter">
                                <div class="btn-group btn-group-sm">
                                    <btn class="btn btn-success" id="btn-add-auditor-user"><i class="fa fa-plus"></i> 添加用户</btn>
                                    <btn class="btn btn-primary" id="btn-add-auditor-user-group"><i class="fa fa-plus-circle"></i> 添加用户组</btn>
                                </div>
                            </div>
                        </div>

                        <table id="table-auditor" class="table table-striped table-bordered table-hover table-data no-footer dtr-inline"></table>

                        <div class="table-extend-area">
                            <div class="table-extend-cell checkbox-select-all"><input id="table-auditor-select-all" type="checkbox"/></div>
                            <div class="table-extend-cell group-actions">
                                <div class="btn-group" role="group">
                                    <button id="btn-remove-auditor" type="button" class="btn btn-default"><i class="fa fa-times-circle fa-fw"></i> 删除</button>
                                </div>
                            </div>
                            <div class="table-extend-cell table-item-counter">
                                <ol id="table-auditor-paging"></ol>
                            </div>
                        </div>

                        <div class="table-extend-area">
                            <div class="table-extend-cell">
                                <div style="text-align:right;">
                                    <nav>
                                        <ul id="table-auditor-pagination" class="pagination"></ul>
                                    </nav>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <div class="col-md-6">
                <div id="area-auditee">
                    <div class="area-title"><span class="name">被审计资源</span><span class="desc">（被审计的主机）</span></div>

                    <div style="padding:5px;">
                        <div class="table-extend-area">
                            <div class="table-extend-cell">
                                <div class="btn-group btn-group-sm">
                                    <btn class="btn btn-default" id="btn-refresh-auditee"><i class="fa fa-redo"></i> 刷新列表</btn>
                                </div>
                            </div>
                            <div class="table-extend-cell table-item-counter">
                                <div class="btn-group btn-group-sm">
##                                     <btn class="btn btn-success" id="btn-add-auditee-user"><i class="fa fa-plus"></i> 添加用户</btn>
##                                     <btn class="btn btn-primary" id="btn-add-auditee-user-group"><i class="fa fa-plus-circle"></i> 添加用户组</btn>
                                    <btn class="btn btn-success" id="btn-add-auditee-host"><i class="fa fa-plus"></i> 添加主机</btn>
                                    <btn class="btn btn-primary" id="btn-add-auditee-host-group"><i class="fa fa-plus-circle"></i> 添加主机组</btn>
                                </div>
                            </div>
                        </div>

                        <table id="table-auditee" class="table table-striped table-bordered table-hover table-data no-footer dtr-inline"></table>

                        <div class="table-extend-area">
                            <div class="table-extend-cell checkbox-select-all"><input id="table-auditee-select-all" type="checkbox"/></div>
                            <div class="table-extend-cell group-actions">
                                <div class="btn-group" role="group">
                                    <button id="btn-remove-auditee" type="button" class="btn btn-default"><i class="fa fa-times-circle fa-fw"></i> 删除</button>
                                </div>
                            </div>
                            <div class="table-extend-cell table-item-counter">
                                <ol id="table-auditee-paging"></ol>
                            </div>
                        </div>

                        <div class="table-extend-area">
                            <div class="table-extend-cell">
                                <div style="text-align:right;">
                                    <nav>
                                        <ul id="table-auditee-pagination" class="pagination"></ul>
                                    </nav>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <div class="box">
        <p>说明：</p>
        <ul class="help-list">
            <li>授权对象表格表示左侧“审计操作者”可以访问右侧“被审计者”相关的运维操作记录。</li>
            <li>按“组”进行授权，则后续加入对应组的用户或主机均自动获得本策略的授权。</li>
        </ul>
    </div>

</div>


<%block name="extend_content">
    <div class="modal fade" id="dlg-sel-auditor-user" tabindex="-1" role="dialog">
        <div class="modal-dialog modal-lg" role="document">
            <div class="modal-content">
                <div class="modal-header">
                    <button type="button" class="close" data-dismiss="modal" aria-label="Close"><i class="fa fa-times-circle fa-fw"></i></button>
                    <h3 data-field="dlg-title" class="modal-title">选择用户</h3>
                </div>
                <div class="modal-body">

                    <table id="table-sel-auditor-user" class="table table-striped table-bordered table-hover table-data no-footer dtr-inline"></table>
                    <div class="table-extend-area">
                        <div class="table-extend-cell checkbox-select-all"><input data-action="sel-all" type="checkbox"/></div>
                        <div class="table-extend-cell group-actions">
                            <div class="btn-group" role="group">
                                <button data-action="use-selected" type="button" class="btn btn-primary"><i class="fa fa-edit fa-fw"></i> 添加为授权操作者</button>
                            </div>
                        </div>
                        <div class="table-extend-cell table-item-counter">
                            <ol id="table-sel-auditor-user-paging"></ol>
                        </div>
                    </div>
                    <div class="table-extend-area">
                        <div class="table-extend-cell">
                            <div style="text-align:right;">
                                <nav>
                                    <ul id="table-sel-auditor-user-pagination" class="pagination"></ul>
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

##     <div class="modal fade" id="dlg-sel-auditee-user" tabindex="-1" role="dialog">
##         <div class="modal-dialog modal-lg" role="document">
##             <div class="modal-content">
##                 <div class="modal-header">
##                     <button type="button" class="close" data-dismiss="modal" aria-label="Close"><i class="fa fa-times-circle fa-fw"></i></button>
##                     <h3 data-field="dlg-title" class="modal-title">选择用户</h3>
##                 </div>
##                 <div class="modal-body">
##
##                     <table id="table-sel-auditee-user" class="table table-striped table-bordered table-hover table-data no-footer dtr-inline"></table>
##                     <div class="table-extend-area">
##                         <div class="table-extend-cell checkbox-select-all"><input data-action="sel-all" type="checkbox"/></div>
##                         <div class="table-extend-cell group-actions">
##                             <div class="btn-group" role="group">
##                                 <button data-action="use-selected" type="button" class="btn btn-primary"><i class="fa fa-edit fa-fw"></i> 添加为被授权资源</button>
##                             </div>
##                         </div>
##                         <div class="table-extend-cell table-item-counter">
##                             <ol id="table-sel-auditee-user-paging"></ol>
##                         </div>
##                     </div>
##                     <div class="table-extend-area">
##                         <div class="table-extend-cell">
##                             <div style="text-align:right;">
##                                 <nav>
##                                     <ul id="table-sel-auditee-user-pagination" class="pagination"></ul>
##                                 </nav>
##                             </div>
##                         </div>
##                     </div>
##
##                 </div>
##
##
##                 <div class="modal-footer">
##                     <button type="button" class="btn btn-sm btn-default" data-dismiss="modal"><i class="fa fa-times fa-fw"></i> 关闭</button>
##                 </div>
##             </div>
##         </div>
##     </div>

    <div class="modal fade" id="dlg-sel-auditor-user-group" tabindex="-1" role="dialog">
        <div class="modal-dialog" role="document">
            <div class="modal-content">
                <div class="modal-header">
                    <button type="button" class="close" data-dismiss="modal" aria-label="Close"><i class="fa fa-times-circle fa-fw"></i></button>
                    <h3 data-field="dlg-title" class="modal-title">选择用户组</h3>
                </div>
                <div class="modal-body">

                    <table id="table-sel-auditor-user-group" class="table table-striped table-bordered table-hover table-data no-footer dtr-inline"></table>
                    <div class="table-extend-area">
                        <div class="table-extend-cell checkbox-select-all"><input data-action="sel-all" type="checkbox"/></div>
                        <div class="table-extend-cell group-actions">
                            <div class="btn-group" role="group">
                                <button data-action="use-selected" type="button" class="btn btn-primary"><i class="fa fa-edit fa-fw"></i> 添加为授权操作者</button>
                            </div>
                        </div>
                        <div class="table-extend-cell table-item-counter">
                            <ol id="table-sel-auditor-user-group-paging"></ol>
                        </div>
                    </div>
                    <div class="table-extend-area">
                        <div class="table-extend-cell">
                            <div style="text-align:right;">
                                <nav>
                                    <ul id="table-sel-auditor-user-group-pagination" class="pagination"></ul>
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

##     <div class="modal fade" id="dlg-sel-auditee-user-group" tabindex="-1" role="dialog">
##         <div class="modal-dialog" role="document">
##             <div class="modal-content">
##                 <div class="modal-header">
##                     <button type="button" class="close" data-dismiss="modal" aria-label="Close"><i class="fa fa-times-circle fa-fw"></i></button>
##                     <h3 data-field="dlg-title" class="modal-title">选择用户组</h3>
##                 </div>
##                 <div class="modal-body">
##
##                     <table id="table-sel-auditee-user-group" class="table table-striped table-bordered table-hover table-data no-footer dtr-inline"></table>
##                     <div class="table-extend-area">
##                         <div class="table-extend-cell checkbox-select-all"><input data-action="sel-all" type="checkbox"/></div>
##                         <div class="table-extend-cell group-actions">
##                             <div class="btn-group" role="group">
##                                 <button data-action="use-selected" type="button" class="btn btn-primary"><i class="fa fa-edit fa-fw"></i> 添加为被授权资源</button>
##                             </div>
##                         </div>
##                         <div class="table-extend-cell table-item-counter">
##                             <ol id="table-sel-auditee-user-group-paging"></ol>
##                         </div>
##                     </div>
##                     <div class="table-extend-area">
##                         <div class="table-extend-cell">
##                             <div style="text-align:right;">
##                                 <nav>
##                                     <ul id="table-sel-auditee-user-group-pagination" class="pagination"></ul>
##                                 </nav>
##                             </div>
##                         </div>
##                     </div>
##
##                 </div>
##
##
##                 <div class="modal-footer">
##                     <button type="button" class="btn btn-sm btn-default" data-dismiss="modal"><i class="fa fa-times fa-fw"></i> 关闭</button>
##                 </div>
##             </div>
##         </div>
##     </div>

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
