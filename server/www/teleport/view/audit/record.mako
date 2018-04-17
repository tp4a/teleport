<%!
    page_icon_class_ = 'fa fa-eye fa-fw'
    page_title_ = ['审计', '会话审计']
    page_id_ = ['audit', 'record']
%>
<%inherit file="../page_base.mako"/>

<%block name="extend_js_file">
##     <script type="text/javascript" src="${ static_url('js/tp-assist.js') }"></script>
    <script type="text/javascript" src="${ static_url('js/audit/record-list.js') }"></script>
</%block>

## Begin Main Body.

<div class="page-content-inner">

    <!-- begin box -->
    <div class="box">
        <div class="table-prefix-area">
            <div class="table-extend-cell">
                <span class="table-name"><i class="fa fa-list fa-fw"></i> 会话列表</span>
                <button id="btn-refresh-record" class="btn btn-sm btn-default"><i class="fa fa-redo fa-fw"></i> 刷新列表</button>
            </div>
           <div class="table-extend-cell table-extend-cell-right group-actions">
               <div class="label label-ignore">存储空间：<span id="storage-info"></span></div>
           </div>
        </div>

        <table class="table table-striped table-bordered table-hover table-data no-footer dtr-inline" id="table-record"></table>

        <div class="table-extend-area">
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

    </div>
    <!-- end of box -->

</div>


<%block name="embed_js">
    <script type="text/javascript">
        $app.add_options(${page_param});
    </script>
</%block>
