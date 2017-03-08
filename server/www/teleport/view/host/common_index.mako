<%!
    page_title_ = '主机列表'
    page_menu_ = ['host']
    page_id_ = 'host'
%>
<%inherit file="../page_base.mako"/>

<%block name="extend_js">
    <script type="text/javascript" src="${ static_url('js/ui/teleport.js') }"></script>
    <script type="text/javascript" src="${ static_url('js/ui/common_host.js') }"></script>
</%block>

<%block name="breadcrumb">
    <ol class="breadcrumb">
        <li><i class="fa fa-server fa-fw"></i> ${self.attr.page_title_}</li>
    </ol>
</%block>

## Begin Main Body.

<div class="page-content">

    <!-- begin box -->
    <div class="box" id="ywl_host_list">

        <!-- begin filter -->
        <div class="page-filter">
            <div class="" style="float:right;">
                <span id="tp-assist-current-version" style="margin-right: 50px"> 助手版本：未知</span>
                <a href="javascript:;" class="btn btn-sm btn-primary" ywl-filter="reload"><i class="fa fa-repeat fa-fw"></i> 刷新</a>
            </div>

            <div class="">

                <div class="input-group input-group-sm" style="display:inline-block;margin-right:10px;">
                    <span class="input-group-addon" style="display:inline-block;width:auto; line-height:28px;height:30px;padding:0 10px;font-size:13px;">主机分组</span>
                    <div class="input-group-btn" ywl-filter="host-group" style="display:inline-block;margin-left:-4px;">
                        <button type="button" class="btn btn-default dropdown-toggle" data-toggle="dropdown"><span>正在加载</span> <span class="caret"></span></button>
                        <ul class="dropdown-menu">
                            <li>正在加载</li>
                        </ul>
                    </div>
                </div>


                <div class="input-group input-group-sm" style="display:inline-block;margin-right:10px;">
                    <span class="input-group-addon" style="display:inline-block;width:auto; line-height:28px;height:30px;padding:0 10px;font-size:13px;">系统</span>
                    <div class="input-group-btn" ywl-filter="system-type" style="display:inline-block;margin-left:-4px;">
                        <button type="button" class="btn btn-default dropdown-toggle" data-toggle="dropdown"><span>正在加载</span> <span class="caret"></span></button>
                        <ul class="dropdown-menu">
                            <li>正在加载</li>
                        </ul>
                    </div>
                </div>


                <div class="input-group input-group-sm" ywl-filter="search" style="display:inline-block;">
                    <input type="text" class="form-control" placeholder="搜索 ID 或 IP" style="display:inline-block;">
                    <span class="input-group-btn" style="display:inline-block;margin-left:-4px;"><button type="button" class="btn btn-default"><i class="fa fa-search fa-fw"></i></button></span>
                </div>

            </div>
        </div>
        <!-- end filter -->


        <table class="table table-striped table-bordered table-hover table-data no-footer dtr-inline" ywl-table="host-list"></table>

        <!-- begin page-nav -->
        <div class="page-nav" ywl-paging="host-list">

            <div class="" style="float:right;">
                <nav>
                    <ul class="pagination pagination-sm"></ul>
                </nav>
            </div>

            <div style="float:right;margin-right:30px;">
                <div class="breadcrumb-container">
                    <ol class="breadcrumb">
                        <li><i class="fa fa-list fa-fw"></i> 记录总数 <strong ywl-field="recorder_total">0</strong></li>
                        <li>页数 <strong><span ywl-field="page_current">1</span>/<span ywl-field="page_total">1</span></strong></li>
                        <li>每页显示
                            <label>
                                <select></select>
                            </label>
                            条记录
                        </li>
                    </ol>
                </div>
            </div>

        </div>
        <!-- end page-nav -->

    </div>
    <!-- end of box -->

</div>






<%block name="extend_content">
</%block>



<%block name="embed_js">
    <script type="text/javascript">
        ywl.add_page_options(${page_param});
    </script>
</%block>
