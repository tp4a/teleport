<%!
    page_icon_class_ = 'fa fa-server fa-fw'
    page_title_ = ['运维', '主机运维']
    page_id_ = ['ops', 'remote']
%>
<%inherit file="../page_base.mako"/>

<%block name="extend_js_file">
    ##     <script type="text/javascript" src="${ static_url('js/tp-assist.js') }"></script>

    <script type="text/javascript" src="${ static_url('js/ops/remote-list.js') }"></script>
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
            </div>
        </div>

        <table id="table-host" class="table table-striped table-bordered table-hover table-data no-footer dtr-inline"></table>

        <div class="table-extend-area">
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
            <li>可以通过表格标题栏进行搜索或过滤，以便快速定位。标题栏左侧的 <i class="fa fa-undo fa-fw"></i> 可以重置过滤器。</li>
        </ul>
    </div>
</div>


<%block name="extend_content">
    <div id="dlg-rdp-options" class="rdp-options">
        <div class="title">RDP连接选项</div>
        <div class="item" data-field="screen-size">
            ##             屏幕尺寸：
            ##             <select data-field="screen-size">
            ##                 <option value="0">全屏</option>
            ##                 <option value="800x600">800x600</option>
            ##                 <option value="1024x768">1024x768</option>
            ##                 <option value="1280x1024">1280x1024</option>
            ##                 <option value="1366x768">1366x768</option>
            ##                 <option value="1440x900">1440x900</option>
            ##                 <option value="1600x1024">1600x1024</option>
            ##             </select>

            <div class="radio">
                <div><label><input type="radio" name="screen-size" id="ss-800x600" checked> 800 x 600</label></div>
                <div><label><input type="radio" name="screen-size" id="ss-1024x768"> 1024 x 768</label></div>
            </div>
        </div>


        ##         <div class="item"><a href="javascript:;" data-field="allow-clipboard" class="tp-checkbox tp-editable">允许映射剪贴板</a></div>
        ##         <div class="item"><a href="javascript:;" class="tp-checkbox tp-editable">允许映射本地磁盘</a></div>

        <hr/>
        <div class="item">
            ##             <a href="javascript:;" data-field="console-mode" class="tp-checkbox tp-editable">Console模式</a>

            <div class="checkbox">
                <label><input type="checkbox" data-field="console-mode"> Console模式</label>
            </div>
        </div>
        <hr/>
        <div class="item">
            <div class="center">
                <button type="button" data-field="do-rdp-connect" class="btn btn-sm btn-primary"><i class="fa fa-desktop fa-fw"></i> 开始连接</button>
            </div>
        </div>
    </div>
</%block>

## <%block name="embed_js">
##     <script type="text/javascript">
##     </script>
## </%block>
