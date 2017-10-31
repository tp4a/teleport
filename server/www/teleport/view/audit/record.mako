<%!
    page_icon_class_ = 'fa fa-eye fa-fw'
    page_title_ = ['审计', '会话审计']
    page_id_ = ['audit', 'record']
%>
<%inherit file="../page_base.mako"/>

<%block name="extend_js_file">
    <script type="text/javascript" src="${ static_url('js/audit/record-list.js') }"></script>
</%block>

## <%block name="breadcrumb">
##     <ol class="breadcrumb">
##         <li><i class="fa fa-database fa-fw"></i> ${self.attr.page_title_}</li>
##     </ol>
## </%block>

## Begin Main Body.

<div class="page-content-inner">

    <!-- begin box -->
    <div class="box">
        <!-- begin filter -->
##         <div class="page-filter">
##             <div class="" style="float:right;">
##                 ## <span id="disk-status" class="badge badge-info" style="margin-right:10px;">磁盘状态</span>
##                 <a href="javascript:;" class="btn btn-sm btn-primary" ywl-filter="reload"><i class="fa fa-repeat fa-fw"></i> 刷新</a>
##             </div>
##
##             <div class="">
##
##                 <div class="input-group input-group-sm" style="display:inline-block;margin-right:10px;">
##                     <span class="input-group-addon" style="display:inline-block;width:auto; line-height:28px;height:30px;padding:0 10px;font-size:13px;">用户名</span>
##                     <div class="input-group-btn" ywl-filter="user-name" style="display:inline-block;margin-left:-4px;">
##                         <button type="button" class="btn btn-default dropdown-toggle" data-toggle="dropdown"><span>所有</span> <span class="caret"></span></button>
##                         <ul class="dropdown-menu">
##                             <li>所有</li>
##                         </ul>
##                     </div>
##                 </div>
##
##
##                 <div class="input-group input-group-sm" ywl-filter="search" style="display:inline-block;">
##                     <input type="text" class="form-control" placeholder="搜索 ID 或 IP" style="display:inline-block;">
##                     <span class="input-group-btn" style="display:inline-block;margin-left:-4px;">
##                         <button type="button" class="btn btn-default"><i class="fa fa-search fa-fw"></i></button>
##                     </span>
##                 </div>
##
##             </div>
##         </div>
        <div class="table-prefix-area">
            <div class="table-extend-cell">
                <span class="table-name"><i class="fa fa-list fa-fw"></i> 会话列表</span>
                <button id="btn-refresh-record" class="btn btn-sm btn-default"><i class="fa fa-rotate-right fa-fw"></i> 刷新列表</button>
            </div>
##            <div class="table-extend-cell table-extend-cell-right group-actions">
                ##<button id="btn-add-host" class="btn btn-sm btn-primary"><i class="fa fa-plus-circle fa-fw"></i> 添加主机</button>
##                 <button id="btn-add-temp-account" class="btn btn-sm btn-success"><i class="fa fa-plus-circle fa-fw"></i> 添加主机</button>
                ##<button id="btn-import-host" class="btn btn-sm btn-default"><i class="fa fa-plus-square fa-fw"></i> 导入主机和账号</button>
##            </div>
        </div>
        <!-- end filter -->

        <table class="table table-striped table-bordered table-hover table-data no-footer dtr-inline" id="table-record"></table>

        <!-- begin page-nav -->
        <div class="table-extend-area">
##             <div class="table-extend-cell checkbox-select-all"><input id="table-record-select-all" type="checkbox"/></div>
##             <div class="table-extend-cell group-actions">
##                 <div class="btn-group" role="group">
##                     ## <button id="btn-edit-host" type="button" class="btn btn-default"><i class="fa fa-edit fa-fw"></i> 编辑</button>
##                     ## <button id="btn-lock-host" type="button" class="btn btn-default"><i class="fa fa-lock fa-fw"></i> 禁用</button>
##                     ## <button id="btn-unlock-host" type="button" class="btn btn-default"><i class="fa fa-unlock fa-fw"></i> 解禁</button>
##                     <button id="btn-remove-record" type="button" class="btn btn-default"><i class="fa fa-times-circle fa-fw"></i> 删除</button>
##                 </div>
##             </div>
            <div class="table-extend-cell table-item-counter">
                <ol id="table-record-paging"></ol>
            </div>
        </div>

        <div class="table-extend-area">
            <div class="table-extend-cell">
                <div style="text-align:right;">
                    <nav>
                        <ul id="table-record-pagination" class="pagination"></ul>
                    </nav>
                </div>
            </div>
        </div>
        <!-- end page-nav -->

    </div>
    <!-- end of box -->

</div>


<%block name="embed_js">
    <script type="text/javascript">
        $app.add_options(${page_param});
    </script>
</%block>
