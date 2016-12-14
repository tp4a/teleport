<%!
    page_title_ = '服务器配置'
    page_menu_ = ['set']
    page_id_ = 'set'
%>
<%inherit file="../page_base.mako"/>

<%block name="extend_js">
    <script type="text/javascript" src="${ static_url('js/ui/teleport.js') }"></script>
    <script type="text/javascript" src="${ static_url('js/ui/set.js') }"></script>
</%block>

<%block name="breadcrumb">
    <ol class="breadcrumb">
        <li><i class="fa fa-server fa-fw"></i> ${self.attr.page_title_}</li>
    </ol>
</%block>

## Begin Main Body.

<div class="page-content">
    ##     <script language="javascript">
    ##         function changeF() {
    ##             document.getElementById('txt').value = document.getElementById('sel').options[document.getElementById('sel').selectedIndex].value;
    ##         }
    ##     </script>

    <!-- begin box -->
    <div class="box">

        <div style="width:640px">

            <div class="form-horizontal">

                <h4><strong>Teleport服务器设置</strong></h4>
##                 <p>设置teleport服务器的访问地址和服务的端口。</p>
##                 <p style="font-weight:bold;color:#ff3333;">请正确设置服务器地址（IP或域名），否则将无法进行跳板连接！！</p>
                <p>设置teleport服务器的服务端口。</p>

                <div class="form-group form-group-sm" style="display:none;">
                    <label for="current-ts-server-ip" class="col-sm-2 control-label"><strong>堡垒机地址：</strong></label>

                    <div class="col-sm-6">
                        <div class="input-group">
                            <input type="text" class="form-control" id="current-ts-server-ip">
                            <div class="input-group-btn">
                                <button type="button" class="btn btn-default dropdown-toggle" data-toggle="dropdown" aria-haspopup="true" aria-expanded="false"> 选择IP <span class="caret"></span></button>
                                <ul id='select-ip' class="dropdown-menu dropdown-menu-right">
                                </ul>
                            </div>
                        </div>
                    </div>
                    <label for="current-ts-server-ip" class="col-sm-4 control-label" style="text-align:left;color:red;"><strong>首次安装必须修改</strong></label>
                </div>

                <div class="form-group form-group-sm">
                    <label for="current-rdp-port" class="col-sm-2 control-label"><strong>RDP 端口：</strong></label>
                    <div class="col-sm-6">
                        <input id="current-rdp-port" type="text" class="form-control" placeholder="默认值 52089"/>
                    </div>
##                     <div class="col-sm-4 control-label" style="text-align: left;">可以用默认值</div>
                </div>

                <div class="form-group form-group-sm">
                    <label for="current-ssh-port" class="col-sm-2 control-label"><strong>SSH 端口：</strong></label>
                    <div class="col-sm-6">
                        <input id="current-ssh-port" type="text" class="form-control" placeholder="默认值 52189"/>
                    </div>
##                     <div class="col-sm-4 control-label" style="text-align: left;">可以用默认值</div>
                </div>


                <div class="form-group form-group-sm">
                    <label for="current-telnet-port" class="col-sm-2 control-label"><strong>TELENT 端口：</strong></label>
                    <div class="col-sm-6">
                        <input id="current-telnet-port" type="text" class="form-control" placeholder="默认值 52389"/>
                    </div>
##                     <div class="col-sm-4 control-label" style="text-align: left;">可以用默认值</div>
                </div>


                <div class="form-group form-group-sm">
                    <div class="col-sm-2"></div>
                    <div class="col-sm-6">
                        注意：修改端口号，需要重启服务方能生效！
                    </div>
                </div>

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

                <hr/>
                <div class="form-group form-group-sm">
                    <div class="col-sm-2"></div>
                    <div class="col-sm-2">
                        <a href="javascript:" id="btn-check" class="btn btn-success"><i class="fa fa-cog fa-fw"></i> 一键测试</a>
                    </div>
                    <div class="col-sm-4" style="text-align: right;">
                        <a href="javascript:" id="btn-save-config" class="btn btn-primary"><i class="fa fa-check fa-fw"></i> 保存配置</a>
                    </div>
                </div>

            </div>

        </div>
        <!-- end of box -->

    </div>
</div>


<%block name="extend_content">

    <div class="modal fade" id="dlg_restart_service" tabindex="-1" role="dialog">
        <div class="modal-dialog" role="document">
            <div class="modal-content">
                <div class="modal-header">
                    <h3 class="modal-title" style="text-align: center;">服务重启中...</h3>
                </div>
                <div class="modal-body">
                    <p style="text-align: center; font-size:36px;"><i class="fa fa-cog fa-spin"></i></p>
                    <p style="text-align: center;">配置已保存，正在重启teleport服务，请稍候...</p>
                    <p style="text-align: center;"><span id="reboot_time"></span></p>
                </div>

                <div class="modal-footer">
                </div>
            </div>
        </div>
    </div>


</%block>


<%block name="embed_js">
    <script type="text/javascript">
        ywl.add_page_options({
            config_list: ${config_list}
        });
    </script>
</%block>
