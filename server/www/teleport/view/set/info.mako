<%!
    page_title_ = '配置管理'
    page_menu_ = ['set', 'info']
    page_id_ = 'set'
%>
<%inherit file="../page_base.mako"/>

<%block name="extend_js">
##     <script type="text/javascript" src="${ static_url('js/ui/teleport.js') }"></script>
    <script type="text/javascript" src="${ static_url('js/ui/config/info.js') }"></script>
</%block>

<%block name="breadcrumb">
    <ol class="breadcrumb">
        <li><i class="fa fa-cogs fa-fw"></i> ${self.attr.page_title_}</li>
        <li>配置信息</li>
    </ol>
</%block>

<%block name="extend_css">
    <style type="text/css">
        .table .key {
            text-align: right;
        }
        .table .value {
            text-align: left;
            font-weight:bold;
        }
    </style>
</%block>

## Begin Main Body.

<div class="page-content">

    <!-- begin box -->
    <div class="box">

        <div style="width:640px">

            <div class="form-horizontal">

                <h4><strong>服务器配置信息</strong></h4>

                <table id="info-kv" class="table">
##                     <tr><td class="key">RDP 端口：</td><td class="value">52089</td></tr>
##                     <tr><td class="key">SSH 端口：</td><td class="value">52189</td></tr>
##                     <tr><td class="key">TELNET 端口：</td><td class="value">52389</td></tr>
##                     <tr><td class="key">录像文件路径：</td><td class="value">C:\teleport-server\data\replay</td></tr>
                </table>

##
##                 <div class="form-group form-group-sm">
##                     <label for="current-rdp-port" class="col-sm-2 control-label"><strong>RDP 端口：</strong></label>
##                     <div class="col-sm-6">
##                         <input id="current-rdp-port" type="text" class="form-control" placeholder="默认值 52089" disabled/>
##                     </div>
## ##                     <div class="col-sm-4 control-label" style="text-align: left;">可以用默认值</div>
##                 </div>
##
##                 <div class="form-group form-group-sm">
##                     <label for="current-ssh-port" class="col-sm-2 control-label"><strong>SSH 端口：</strong></label>
##                     <div class="col-sm-6">
##                         <input id="current-ssh-port" type="text" class="form-control" placeholder="默认值 52189" disabled/>
##                     </div>
## ##                     <div class="col-sm-4 control-label" style="text-align: left;">可以用默认值</div>
##                 </div>
##
##
##                 <div class="form-group form-group-sm">
##                     <label for="current-telnet-port" class="col-sm-2 control-label"><strong>TELENT 端口：</strong></label>
##                     <div class="col-sm-6">
##                         <input id="current-telnet-port" type="text" class="form-control" placeholder="默认值 52389" disabled/>
##                     </div>
## ##                     <div class="col-sm-4 control-label" style="text-align: left;">可以用默认值</div>
##                 </div>
##
##
##                 <div class="form-group form-group-sm">
##                     <div class="col-sm-2"></div>
##                     <div class="col-sm-6">
##                         注意：要修改端口号，请直接修改配置文件。修改后需要重启服务方能生效！
##                     </div>
##                 </div>


                ## 				<hr/>
                ##
                ## 				<p><strong>Teleport核心服务设置</strong></p>
                ## 				<p>用于与teleport核心服务进行通讯，需要将WEB后台与核心服务部署在同一台主机上。</p>
                ## 				<p>如果您需要将核心服务部署在单独的主机上，建议您为RPC访问端口设置防火墙规则，仅允许WEB后台主机访问此RPC端口，以增强安全性。</p>
                ##
                ## 				<div class="form-group form-group-sm">
                ## 					<label for="current-rpc-ip" class="col-sm-2 control-label"><strong>IP地址：</strong></label>
                ## 					<div class="col-sm-6">
                ## 						<input id="current-rpc-ip" type="text" class="form-control" readonly="readonly" placeholder="默认值 127.0.0.1"/>
                ## 					</div>
                ## 				</div>
                ##
                ## 				<div class="form-group form-group-sm">
                ## 					<label for="current-rpc-port" class="col-sm-2 control-label"><strong>端口：</strong></label>
                ## 					<div class="col-sm-6">
                ## 						<input id="current-rpc-port" type="text" class="form-control" readonly="readonly" placeholder="默认值 52080"/>
                ## 					</div>
                ## 				</div>

##                 <hr/>
##                 <div class="form-group form-group-sm">
##                     <div class="col-sm-2"></div>
##                     <div class="col-sm-2">
##                         <a href="javascript:" id="btn-check" class="btn btn-success"><i class="fa fa-cog fa-fw"></i> 一键测试</a>
##                     </div>
##                     <div class="col-sm-4" style="text-align: right;">
##                         <a href="javascript:" id="btn-save-config" class="btn btn-primary"><i class="fa fa-check fa-fw"></i> 保存配置</a>
##                     </div>
##                 </div>

            </div>

        </div>
        <!-- end of box -->

    </div>
</div>


<%block name="extend_content">

##     <div class="modal fade" id="dlg_restart_service" tabindex="-1" role="dialog">
##         <div class="modal-dialog" role="document">
##             <div class="modal-content">
##                 <div class="modal-header">
##                     <h3 class="modal-title" style="text-align: center;">服务重启中...</h3>
##                 </div>
##                 <div class="modal-body">
##                     <p style="text-align: center; font-size:36px;"><i class="fa fa-cog fa-spin"></i></p>
##                     <p style="text-align: center;">配置已保存，正在重启teleport服务，请稍候...</p>
##                     <p style="text-align: center;"><span id="reboot_time"></span></p>
##                 </div>
##
##                 <div class="modal-footer">
##                 </div>
##             </div>
##         </div>
##     </div>


</%block>


<%block name="embed_js">
    <script type="text/javascript">
##         ywl.add_page_options({
##             config_list: ${config_list}
##         });
            ywl.add_page_options(${ page_param });
    </script>
</%block>
