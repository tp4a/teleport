<%!
    page_icon_class_ = 'fa fa-cogs fa-fw'
    page_title_ = ['运维', '在线会话']
    page_id_ = ['ops', 'session']
%>
<%inherit file="../page_base.mako"/>

<%block name="extend_js_file">
    <script type="text/javascript" src="${ static_url('js/ops/session-list.js') }"></script>
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
        <div class="table-prefix-area">
            <div class="table-extend-cell">
                <span class="table-name"><i class="fa fa-list fa-fw"></i> 在线会话列表</span>
                <button id="btn-refresh-session" class="btn btn-sm btn-default"><i class="fa fa-redo fa-fw"></i> 刷新列表</button>
            </div>
        </div>
        <!-- end filter -->

        <table class="table table-striped table-bordered table-hover table-data no-footer dtr-inline" id="table-session"></table>

        <!-- begin page-nav -->
        <div class="table-extend-area">
            <div class="table-extend-cell checkbox-select-all"><input id="table-session-select-all" type="checkbox"/></div>
            <div class="table-extend-cell group-actions">
                <div class="btn-group" role="group">
                    <button id="btn-kill-sessions" type="button" class="btn btn-danger"><i class="fa fa-times-circle fa-fw"></i> 强行中断</button>
                </div>
            </div>
            <div class="table-extend-cell table-item-counter">
                <ol id="table-session-paging"></ol>
            </div>
        </div>

        <div class="table-extend-area">
            <div class="table-extend-cell">
                <div style="text-align:right;">
                    <nav>
                        <ul id="table-session-pagination" class="pagination"></ul>
                    </nav>
                </div>
            </div>
        </div>
        <!-- end page-nav -->

    </div>
    <!-- end of box -->

    <div class="box">
        <p>说明：</p>
        <ul class="help-list">
            <li>注意：强制中断会话时，相同会话ID的会话（例如使用SecureCRT或者xShell客户端的“克隆会话”功能打开的会话）均会被中断。</li>
        </ul>
    </div>
</div>
