<%!
    page_icon_class_ = 'fa fa-calendar fa-fw'
    page_title_ = ['系统', '系统日志']
    page_id_ = ['system', 'syslog']
%>
<%inherit file="../page_base.mako"/>

<%block name="extend_js_file">
    <script type="text/javascript" src="${ static_url('js/system/syslog.js') }"></script>
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
                <span class="table-name"><i class="fa fa-list fa-fw"></i> 系统日志</span>
                <button id="btn-refresh-log" class="btn btn-sm btn-default"><i class="fa fa-redo fa-fw"></i> 刷新列表</button>
            </div>
        </div>
        <!-- end filter -->

        <table class="table table-striped table-bordered table-hover table-data no-footer dtr-inline" id="table-log"></table>

        <!-- begin page-nav -->
        <div class="table-extend-area">
            <div class="table-extend-cell table-item-counter">
                <ol id="table-log-paging"></ol>
            </div>
        </div>

        <div class="table-extend-area">
            <div class="table-extend-cell">
                <div style="text-align:right;">
                    <nav>
                        <ul id="table-log-pagination" class="pagination"></ul>
                    </nav>
                </div>
            </div>
        </div>
        <!-- end page-nav -->

    </div>
    <!-- end of box -->

</div>
