<%!
    page_icon_class_ = 'fa fa-server fa-fw'
    page_title_ = ['运维', '运维授权']
    page_id_ = ['ops', 'auz']
%>
<%inherit file="../page_base.mako"/>

<%block name="extend_js_file">
    <script type="text/javascript" src="${ static_url('js/ops/auz-list.js') }"></script>
</%block>

<%block name="embed_css">
    <style>
        .policy-desc {
            margin-left: 8px;
            color: #7f7f7f;
        }
    </style>
</%block>

## Begin Main Body.

<div class="page-content-inner">

    <!-- begin box -->
    <div class="box box-nav-tabs">

        <!-- Nav tabs -->
        <ul class="nav nav-tabs">
            <li class="active"><a href="#tab-policy" data-toggle="tab">授权策略</a></li>
            <li><a href="#tab-search" data-toggle="tab">快速查找</a></li>
        </ul>

        <div class="tab-content">
            <div class="tab-pane active" style="padding:15px;" id="tab-policy">

                <div class="table-prefix-area">
                    <div class="table-extend-cell">
                        <span class="table-name"><i class="fa fa-list fa-fw"></i> 授权策略列表</span>
                        <button id="btn-refresh-policy" class="btn btn-sm btn-default"><i class="fa fa-redo fa-fw"></i> 刷新列表</button>
##                         <button id="btn-rebuild" class="btn btn-sm btn-danger"><i class="fa fa-bolt fa-fw"></i> 重建授权映射</button>
                    </div>
                    <div class="table-extend-cell table-extend-cell-right group-actions">
                        <button id="btn-create-policy" class="btn btn-sm btn-primary"><i class="fa fa-plus-circle fa-fw"></i> 新建授权策略</button>
                    </div>
                </div>

                <table id="table-policy" class="table table-striped table-bordered table-hover table-data no-footer dtr-inline"></table>

                <div class="table-extend-area">
                    <div class="table-extend-cell checkbox-select-all"><input id="table-auz-select-all" type="checkbox"/></div>
                    <div class="table-extend-cell group-actions">
                        <div class="btn-group" role="group">
                            ##                     <button id="btn-edit-host" type="button" class="btn btn-default"><i class="fa fa-edit fa-fw"></i> 编辑</button>

                            <button id="btn-lock" type="button" class="btn btn-default"><i class="fa fa-lock fa-fw"></i> 禁用</button>
                            <button id="btn-unlock" type="button" class="btn btn-default"><i class="fa fa-unlock fa-fw"></i> 解禁</button>
                            <button id="btn-remove" type="button" class="btn btn-default"><i class="fa fa-times-circle fa-fw"></i> 删除</button>
                        </div>
                    </div>
                    <div class="table-extend-cell table-item-counter">
                        <ol id="table-auz-paging"></ol>
                    </div>
                </div>

                <div class="table-extend-area">
                    <div class="table-extend-cell">
                        <div style="text-align:right;">
                            <nav>
                                <ul id="table-auz-pagination" class="pagination"></ul>
                            </nav>
                        </div>
                    </div>
                </div>
            </div>

            <div class="tab-pane" style="padding:15px;" id="tab-search">
                <div class="alert alert-danger">快速查找功能尚未实现</div>

            </div>
        </div>

    </div>
    <!-- end of box -->

    <div class="box">
        <p>说明：</p>
        <ul class="help-list">
##             <li><span class="error">编辑了授权策略或调整策略顺序之后，请点击“重建授权映射”来使之生效！</span>正式版本将会改进为自动进行重建。</li>
            <li>上下拖动“顺序”栏中的 <i class="fas fa-bars fa-fw"></i> 可以调节策略的检查顺序。</li>
            <li>可以在“快速查找”中快速定位用户或主机的授权关系。</li>
        </ul>
    </div>
</div>


<%block name="extend_content">

    <div class="modal fade" id="dlg-edit-policy" tabindex="-1">
        <div class="modal-dialog" role="document">
            <div class="modal-content">
                <div class="modal-header">
                    <button type="button" class="close" data-dismiss="modal" aria-label="Close"><i class="fa fa-times-circle fa-fw"></i></button>
                    <h3 data-field="dlg-title" class="modal-title"></h3>
                </div>
                <div class="modal-body">

                    <div class="form-horizontal">

                        <div class="form-group form-group-sm">
                            <label for="edit-name" class="col-sm-2 control-label require">策略名称：</label>
                            <div class="col-sm-10">
                                <input id="edit-name" type="text" class="form-control" placeholder=""/>
                            </div>
                        </div>

                        <div class="form-group form-group-sm">
                            <label for="edit-desc" class="col-sm-2 control-label">策略描述：</label>
                            <div class="col-sm-10">
                                <input id="edit-desc" type="text" class="form-control"/>
                            </div>
                        </div>
                    </div>
                </div>


                <div class="modal-footer">
                    <button type="button" class="btn btn-sm btn-primary" id="btn-edit-policy-save"><i class="fa fa-check fa-fw"></i> 确定</button>
                    <button type="button" class="btn btn-sm btn-default" data-dismiss="modal"><i class="fa fa-times fa-fw"></i> 取消</button>
                </div>
            </div>
        </div>
    </div>
</%block>
