<%!
    page_icon_class_ = 'fa fa-server fa-fw'
    page_title_ = ['资产', '主机分组管理']
    page_id_ = ['asset', 'host-group']
%>
<%inherit file="../page_base.mako"/>

<%block name="extend_js_file">
    <script type="text/javascript" src="${ static_url('js/asset/host-group-list.js') }"></script>
</%block>

<%block name="embed_css">
    <style>
        .acc-info-wrap {
            display: inline-block;
        }
        .acc-info, .acc-info-router {
            display:inline-block;
            background-color: #daebff;
            height: 24px;
            line-height: 24px;
            border-radius: 12px;
            border: 1px solid #cad9ec;
            padding: 0 8px;
            margin-right: 8px;
            margin-bottom: 3px;
            white-space: nowrap;
        }

        .acc-info-router {
            background-color: #afffc3;
            border: 1px solid #b4ebbd;
        }
##         .user-account, .user-email {
##             font-family: Monaco, Lucida Console, Consolas, Courier, 'Courier New', monospace;
##         }

##         .user-account, .group-desc {
##             color: #7a7a7a;
##             white-space: nowrap;
##         }

    </style>
</%block>

## Begin Main Body.

<div class="page-content-inner">

    <!-- begin box -->
    <div class="box">
        <div class="table-prefix-area">
            <div class="table-extend-cell">
                <span class="table-name"><i class="fa fa-list fa-fw"></i> 主机分组列表</span>
                <button id="btn-refresh-groups" class="btn btn-sm btn-default"><i class="fa fa-redo fa-fw"></i> 刷新列表</button>
            </div>
            <div class="table-extend-cell table-extend-cell-right group-actions">
                <button id="btn-create-group" class="btn btn-sm btn-primary"><i class="fa fa-plus-circle fa-fw"></i> 创建主机分组</button>
            </div>
        </div>

        <table id="table-groups" class="table table-striped table-bordered table-hover table-data no-footer dtr-inline"></table>

        <div class="table-extend-area">
            <div class="table-extend-cell checkbox-select-all"><input id="table-groups-select-all" type="checkbox"/></div>
            <div class="table-extend-cell group-actions">
                <div class="btn-group" role="group">
##                     <button id="btn-remove-group" type="button" class="btn btn-danger"><i class="fa fa-times-circle fa-fw"></i> 批量删除</button>
                    <button id="btn-lock-group" type="button" class="btn btn-default"><i class="fa fa-lock fa-fw"></i> 禁用</button>
                    <button id="btn-unlock-group" type="button" class="btn btn-default"><i class="fa fa-unlock fa-fw"></i> 解禁</button>
                    <button id="btn-remove-group" type="button" class="btn btn-default"><i class="fa fa-times-circle fa-fw"></i> 删除</button>
                </div>
            </div>
            <div class="table-extend-cell table-item-counter">
                <ol id="table-groups-paging"></ol>
            </div>
        </div>

        <div class="table-extend-area">
            <div class="table-extend-cell">
                <div style="text-align:right;">
                    <nav>
                        <ul id="table-groups-pagination" class="pagination"></ul>
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
        </ul>
    </div>
</div>


<%block name="extend_content">
    <div class="modal fade" id="dlg-edit-group" tabindex="-1" role="dialog">
        <div class="modal-dialog" role="document">
            <div class="modal-content">
                <div class="modal-header">
                    <button type="button" class="close" data-dismiss="modal" aria-label="Close"><i class="fa fa-times-circle fa-fw"></i></button>
                    <h3 data-field="dlg-title" class="modal-title"></h3>
                </div>
                <div class="modal-body">

                    <div class="form-horizontal">

                        <div class="form-group form-group-sm">
                            <label for="edit-group-name" class="col-sm-2 control-label require">名称：</label>
                            <div class="col-sm-4">
                                <input id="edit-group-name" type="text" class="form-control" placeholder="主机分组名称"/>
                            </div>
                            <div class="col-sm-6">
                                <div class="control-desc">最大64英文字符，或20汉字</div>
                            </div>
                        </div>

                        <div class="form-group form-group-sm">
                            <label for="edit-group-desc" class="col-sm-2 control-label">简要描述：</label>
                            <div class="col-sm-10">
                                <input id="edit-group-desc" type="text" class="form-control"/>
                            </div>
                        </div>

                    </div>

                </div>


                <div class="modal-footer">
                    <div class="row">
                        <div class="col-sm-8">
                            <div id="edit-group-message" class="alert alert-danger" style="text-align:left;display:none;"></div>
                        </div>
                        <div class="col-sm-4">
                            <button type="button" class="btn btn-sm btn-primary" id="btn-edit-group-save"><i class="fa fa-check fa-fw"></i> 确定</button>
                            <button type="button" class="btn btn-sm btn-default" data-dismiss="modal"><i class="fa fa-times fa-fw"></i> 取消</button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</%block>
