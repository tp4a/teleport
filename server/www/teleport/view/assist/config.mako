<%!
    page_icon_class_ = 'fas fa-bolt fa-fw'
    page_title_ = ['助手设置']
    page_id_ = ['assist']
%>
<%inherit file="../page_base.mako"/>

<%block name="extend_js_file">
    <script type="text/javascript" src="${ static_url('js/assist/config.js') }"></script>
</%block>
<%block name="embed_js">
    <script type="text/javascript">
        $app.add_options(${page_param});
    </script>
</%block>

## Begin Main Body.

<div class="page-content-inner">

    <!-- begin box -->
    <div class="box assist-config">
        <div class="alert alert-warning">
            <p><strong><i class="fa fa-exclamation-circle fa-fw"></i> 注意：</strong>助手设置读取和保存的是您当前工作机上的助手设置。如果您更换了工作机，则需要重新对助手进行设置。</p>
        </div>
        ##         <div class="arg-detail arg-detail-common">

        <div class="alert alert-info">
            <p>在命令行参数设置中，可以用以下变量替换需要在命令行中填写的内容（注意大小写！）：</p>
            <ul>
                <li><span class="arg-varb">{host_ip}</span> 替换远程主机IP地址</li>
                <li><span class="arg-varb">{host_port}</span> 替换远程主机端口号</li>
                <li><span class="arg-varb">{host_name}</span> 替换远程主机名称</li>
                <li><span class="arg-varb">{user_name}</span> 替换远程登录账号名</li>
                <li><span class="arg-varb">{real_ip}</span> 替换为远程主机真实IP（仅用于显示，例如客户端的窗口标题或标签页标题等）</li>
                <li><span class="arg-varb">{assist_tools_path}</span> 替换为助手工具所在的tools目录的绝对路径</li>
            </ul>
            <p>例如，命令行中需要指定用户名，则直接填写 {user_name} 即可。</p>
        </div>

        <hr/>

        <p class="cfg-title">本地 SSH 客户端配置</p>

        <div class="form-horizontal">
            <div class="form-group form-group-sm">
                <label for="ssh-type" class="col-sm-2 control-label"><strong>客户端：</strong></label>
                <div class="col-sm-4">
                    <select id="ssh-type" class="form-control"></select>
                </div>
            </div>

            <div class="form-group form-group-sm">
                <label for="ssh-app" class="col-sm-2 control-label"><strong>程序路径：</strong></label>
                <div class="col-sm-9">
                    <div class="input-group">
                        <input id="ssh-app" type="text" class="form-control input-args" placeholder="客户端可执行程序文件路径"/>
                        <span class="input-group-btn"><button class="btn btn-sm btn-primary" type="button" id="ssh-select-app">选择...</button></span>
                    </div>
                </div>
            </div>

            <div class="form-group form-group-sm">
                <label for="ssh-cmdline" class="col-sm-2 control-label"><strong>命令参数：</strong></label>
                <div class="col-sm-9">
                    <input id="ssh-cmdline" type="text" class="form-control input-args" placeholder="客户端启动所需命令行参数"/>
                    <div id="ssh-desc"></div>
                </div>
            </div>
        </div>


        <hr/>
        <p class="cfg-title">本地 SFTP 客户端配置</p>


        <div class="form-horizontal">
            <div class="form-group form-group-sm">
                <label for="sftp-type" class="col-sm-2 control-label"><strong>客户端：</strong></label>
                <div class="col-sm-4">
                    <select id="sftp-type" class="form-control"></select>
                </div>
            </div>

            <div class="form-group form-group-sm">
                <label for="sftp-app" class="col-sm-2 control-label"><strong>程序路径：</strong></label>
                <div class="col-sm-9">
                    <div class="input-group">
                        <input id="sftp-app" type="text" class="form-control input-args" placeholder="客户端可执行程序文件路径"/>
                        <span class="input-group-btn"><button class="btn btn-sm btn-primary" type="button" id="sftp-select-app">选择...</button></span>
                    </div>
                </div>
            </div>

            <div class="form-group form-group-sm">
                <label for="sftp-cmdline" class="col-sm-2 control-label"><strong>命令参数：</strong></label>
                <div class="col-sm-9">
                    <input id="sftp-cmdline" type="text" class="form-control input-args" placeholder="客户端启动所需命令行参数"/>
                    <div id="sftp-desc"></div>
                </div>
            </div>

        </div>


        <hr/>
        <p class="cfg-title">本地 TELNET 客户端配置</p>

        <div class="form-horizontal">
            <div class="form-group form-group-sm">
                <label for="telnet-type" class="col-sm-2 control-label"><strong>客户端：</strong></label>
                <div class="col-sm-4">
                    <select id="telnet-type" class="form-control"></select>
                </div>
            </div>

            <div class="form-group form-group-sm">
                <label for="telnet-app" class="col-sm-2 control-label"><strong>程序路径：</strong></label>
                <div class="col-sm-9">
                    <div class="input-group">
                        <input id="telnet-app" type="text" class="form-control input-args" placeholder="客户端可执行程序文件路径"/>
                        <span class="input-group-btn"><button class="btn btn-sm btn-primary" type="button" id="telnet-select-app">选择...</button></span>
                    </div>
                </div>
            </div>

            <div class="form-group form-group-sm">
                <label for="telnet-cmdline" class="col-sm-2 control-label"><strong>命令参数：</strong></label>
                <div class="col-sm-9">
                    <input id="telnet-cmdline" type="text" class="form-control input-args" placeholder="客户端启动所需命令行参数"/>
                </div>
            </div>

        </div>


        <hr/>
        <p class="cfg-title">本地 RDP 客户端配置</p>

        <div class="form-horizontal">
            <div class="form-group form-group-sm">
                <label for="rdp-type" class="col-sm-2 control-label">客户端：</label>
                <div class="col-sm-4">
                    <select id="rdp-type" class="form-control"></select>
                </div>
            </div>

            <div class="form-group form-group-sm">
                <label for="rdp-app" class="col-sm-2 control-label">程序路径：</label>
                <div class="col-sm-9">
                    <div class="input-group">
                        <input id="rdp-app" type="text" class="form-control input-args" placeholder="客户端可执行程序文件路径"/>
                        <span class="input-group-btn"><button class="btn btn-sm btn-primary" type="button" id="rdp-select-app">选择...</button></span>
                    </div>
                </div>
            </div>

            <div class="form-group form-group-sm">
                <label for="rdp-cmdline" class="col-sm-2 control-label">命令参数：</label>
                <div class="col-sm-9">
                    <input id="rdp-cmdline" type="text" class="form-control input-args" placeholder="客户端启动所需命令行参数"/>
                    <div id="rdp-desc"></div>
                </div>
            </div>
        </div>


        <hr/>
        <div class="form-horizontal">
            <div class="form-group form-group-sm">
                <div class="col-sm-2"></div>
                <div class="col-sm-6">
                    <a id="btn-save" class="btn btn-primary" href="javascript:"><i class="fa fa-check fa-fw"></i> 保存设置！</a>
                </div>
            </div>
        </div>
    </div>

</div>
