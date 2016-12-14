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
                    <span class="input-group-btn" style="display:inline-block;margin-left:-4px;">
    <button type="button" class="btn btn-default"><i class="fa fa-search fa-fw"></i></button>
  </span>
                </div>

            </div>
        </div>
        <!-- end filter -->


        <table class="table table-striped table-bordered table-hover table-data no-footer dtr-inline" ywl-table="host-list"></table>

        <!-- begin page-nav -->
        <div class="page-nav" ywl-paging="host-list">
##             <div style="float:left;">
##                 <a href="https://127.0.0.1:50022/" target="_blank" class="btn btn-sm btn-danger"><i class="fa fa-info-circle fa-fw"></i> TELEPORT助手状态</a>
##             </div>

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


    <!-- begin box -->

    ## <div class="box">
    ##   <div class="box-license">
    ##     <div style="float:right;"><a href="#" class="btn btn-sm btn-primary"><i class="fa fa-plus-circle fa-fw"></i> 增加主机授权</a></div>
    ##     <div class="breadcrumb-container">
    ##     <ol class="breadcrumb">
    ##       <li><i class="fa fa-server fa-fw"></i> 授权主机数：<strong>120</strong></li>
    ##       <li>已激活主机数：<strong>118</strong></li>
    ##     </ol>
    ##     </div>
    ##
    ##   </div>
    ## </div>

    <!-- end of box -->

</div>






<%block name="extend_content">

    ## <div class="popover-inline-edit">
    ## 	<div class="popover fade bottom in" role="tooltip" ywl-dlg="modify-host-desc" style="display:none;">
    ## 		<div class="arrow" style="left:50px;"></div>
    ## 		<h3 class="popover-title">为主机 <span ywl-field="host-id"></span> 添加备注，以便识别</h3>
    ## 		<div class="popover-content">
    ## 			<div style="display:inline-block;float:right;">
    ## 				<a href="javascript:;" class="btn btn-success btn-sm" ywl-btn="ok"><i class="glyphicon glyphicon-ok"></i></a>
    ## 				<a href="javascript:;" class="btn btn-danger btn-sm" ywl-btn="cancel"><i class="glyphicon glyphicon-remove"></i></a>
    ## 			</div>
    ## 			<div style="padding-right:80px;">
    ## 				<input type="text" ywl-input="desc" class="form-control" value="">
    ## 				<input type="hidden" ywl-input="ywl-row-index" value="">
    ## 			</div>
    ## 		</div>
    ## 	</div>
    ## </div>

</%block>



<%block name="embed_js">
    <script type="text/javascript">

        // var host_dt = null;
        ywl.add_page_options({
            // 有些参数由后台python脚本生成到模板中，无法直接生成到js文件中，所以必须通过这种方式传递参数到js脚本中。
            group_list: ${group_list},
            ts_server: ${ts_server}
        });

        $(document).ready(function () {
            ## 			var ywl_options = {
            ## 				active_menu: ${self.attr.page_menu_}
            ## 			};
            ##
            ## 			ywl.add_page_options(ywl_options);

            // $('#username_account').keydown(function(event) { $('[data-toggle="popover"]').popover('hide'); if(event.which == 13) { $('#password_account').focus(); } });
            // $('#password_account').keydown(function(event) { $('[data-toggle="popover"]').popover('hide'); if(event.which == 13) { $('#captcha').focus(); } });
            // $('#username_usbkey').keydown(function(event) { $('[data-toggle="popover"]').popover('hide'); if(event.which == 13) { $('#password_usbkey').focus(); } });
            // $('#password_usbkey').keydown(function(event) { $('[data-toggle="popover"]').popover('hide'); if(event.which == 13) { $('#captcha').focus(); } });
            // $('#captcha').keydown(function(event) { $('[data-toggle="popover"]').popover('hide'); if(event.which == 13) { login(); } });
        });


    </script>
</%block>
