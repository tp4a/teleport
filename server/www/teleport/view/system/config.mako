<%!
    page_icon_class_ = 'fa fa-cog fa-fw'
    page_title_ = ['系统', '系统设置']
    page_id_ = ['system', 'config']
%>
<%inherit file="../page_base.mako"/>

<%block name="extend_js_file">
    <script type="text/javascript" src="${ static_url('js/system/config.js') }"></script>
</%block>
<%block name="embed_js">
    <script type="text/javascript">
        $app.add_options(${page_param});
    </script>
</%block>

<div class="page-content-inner">
    <div class="box box-nav-tabs">
        <ul class="nav nav-tabs">
            <li class="active"><a href="#tab-info" data-toggle="tab">基本信息</a></li>
            <li><a href="#tab-global" data-toggle="tab">全局配置</a></li>
            <li><a href="#tab-security" data-toggle="tab">安全</a></li>
            <li><a href="#tab-session" data-toggle="tab">连接控制</a></li>
            <li><a href="#tab-smtp" data-toggle="tab">邮件系统</a></li>
            <li><a href="#tab-storage" data-toggle="tab">存储</a></li>
            ##             <li><a href="#tab-backup" data-toggle="tab">备份</a></li>
        </ul>

        <div class="tab-content">
            <!-- panel for global information -->
            <div class="tab-pane active" id="tab-info">
                <h4>WEB服务配置</h4>
                <table id="web-info-kv" class="table table-info-list"></table>
                <hr/>
                <h4>核心服务配置</h4>
                <table id="core-info-kv" class="table table-info-list"></table>
            </div>
            
            <!-- panel for glabal config -->
            <div class="tab-pane" id="tab-global">
                <div class="alert alert-warning">
                    注意：该配置影响全局，请小心修改。
                </div>
                <table class="table table-config-list">
					<tr>
                        <td colspan="2" class="title">
                            <hr class="hr-sm"/>
                            远程启动方式
                        </td>
                    </tr>
					<tr>
                        <td class="key"></td>
                        <td class="value">
                            <div id="global-use-url-protocol" class="tp-checkbox tp-editable">使用UrlProtocl启动远程</div>
                        </td>
                    </tr>
                </table>
                <hr/>
                <button id="btn-save-global-config" class="btn btn-sm btn-primary"><i class="fa fa-check-circle fa-fw"></i> 保存设置</button>
            </div>

            <!-- panel for security config -->
            <div class="tab-pane" id="tab-security">
                <table class="table table-config-list">
                    <tr>
                        <td colspan="2" class="title">密码策略</td>
                    </tr>
                    <tr>
                        <td class="key">重置密码</td>
                        <td class="value">
                            <div id="sec-allow-reset-password" class="tp-checkbox tp-editable">允许用户通过邮件重置密码</div>
                            <span class="desc">关闭此功能，只能由管理员为用户手工重置密码。默认开启。</span>
                        </td>
                    </tr>
                    <tr>
                        <td class="key">密码强度</td>
                        <td class="value">
                            <div id="sec-force-strong-password" class="tp-checkbox tp-editable">强制使用强密码</div>
                            <span class="desc">至少8个英文字符，必须包含大写字母、小写字母和数字。默认开启。</span>
                        </td>
                    </tr>
                    <tr>
                        <td class="key">密码有效期</td>
                        <td class="value">
                            <input id="sec-password-timeout" type="text" value="0"/><span class="unit">天</span><span class="desc">0~180。密码过期后用户将无法登录，为0则密码永不过期。默认为0。</span>
                        </td>
                    </tr>

                    <tr>
                        <td colspan="2" class="title">
                            <hr class="hr-sm"/>
                            登录设置
                        </td>
                    </tr>
                    <tr>
                        <td class="key">WEB会话超时</td>
                        <td class="value">
                            <input id="sec-session-timeout" type="text" value="30"/><span class="unit">分钟</span><span class="desc">5~1440。超过设定时长无操作，用户将被强制登出。默认为60分钟。</span>
                        </td>
                    </tr>
                    <tr>
                        <td class="key">密码尝试次数</td>
                        <td class="value">
                            <input id="sec-login-retry" type="text" value="0"/><span class="unit">次</span><span class="desc">0~10。密码连续错误超过设定次数，用户将被临时锁定，为0则不限制。默认为0。</span>
                        </td>
                    </tr>
                    <tr>
                        <td class="key">临时锁定时长</td>
                        <td class="value">
                            <input id="sec-lock-timeout" type="text" value="30"/><span class="unit">分钟</span><span class="desc">0~9999。用户被临时锁定的持续时间，为0则持续到由管理员解锁。默认为30分钟。</span>
                        </td>
                    </tr>
                    <tr>
                        <td class="key">认证方式</td>
                        <td class="value">设置系统启用的登录认证方式
                            <span class="desc">还可以为每个用户指定特定的登录认证方式。</span>
                        </td>
                    </tr>
##                     <tr>
##                         <td class="key"></td>
##                         <td class="value">
##                             <div id="sec-auth-username-password" class="tp-checkbox tp-editable">用户名 + 密码</div>
##                         </td>
##                     </tr>
                    <tr>
                        <td class="key"></td>
                        <td class="value">
                            <div id="sec-auth-username-password-captcha" class="tp-checkbox tp-editable">用户名 + 密码 + 验证码</div>
                        </td>
                    </tr>
##                     <tr>
##                         <td class="key"></td>
##                         <td class="value">
##                             <div id="sec-auth-username-oath" class="tp-checkbox tp-editable">用户名 + 身份认证器动态密码</div>
##                         </td>
##                     </tr>
                    <tr>
                        <td class="key"></td>
                        <td class="value">
                            <div id="sec-auth-username-password-oath" class="tp-checkbox tp-editable">用户名 + 密码 + 身份认证器动态密码</div>
                        </td>
                    </tr>
                </table>
                <hr/>

                <table class="table table-config-list">
                    <tr>
                        <td colspan="2" class="title">授权策略映射</td>
                    </tr>
                    <tr>
                        <td colspan="2" class="value">
                            <div class="alert alert-warning">授权策略映射是根据运维授权策略和审计授权策略构建的用户权限列表。<br/>如果您的系统中用户授权出现异常，可以重建授权策略映射。构建授权策略映射可能会耗费一点时间，请谨慎操作！</div>
                        </td>
                    </tr>
                    <tr>
                        <td class="key"></td>
                        <td class="value">
                            <button id="btn-rebuild-ops-auz-map" class="btn btn-sm btn-danger"><i class="fa fa-leaf fa-fw"></i> 立即重建运维授权映射</button>
                            <button id="btn-rebuild-audit-auz-map" class="btn btn-sm btn-danger"><i class="fa fa-leaf fa-fw"></i> 立即重建审计授权映射</button>
                        </td>
                    </tr>
                </table>
                <hr/>

                <button id="btn-save-secure-config" class="btn btn-sm btn-primary"><i class="fa fa-check-circle fa-fw"></i> 保存安全设置</button>

            </div>

            <!-- panel for session connection config -->
            <div class="tab-pane" id="tab-session">
                <div class="alert alert-warning">
                    注意：运维授权策略的连接控制选项将继承系统连接控制选项的设定。例如，在本界面设定"不允许SFTP连接"，则所有运维授权策略中的SFTP连接均被禁止。又如，在本界面设定"允许SFTP连接"，但某个运维授权策略中禁止SFTP连接，则该运维授权策略中的所有SFTP连接均被禁止。
                </div>
                <table class="table table-config-list">
##                     <tr>
##                         <td colspan="2" class="title">全局会话选项</td>
##                     </tr>
##                     <tr>
##                         <td class="key"></td>
##                         <td class="value">
##                             <div id="sess-record-allow-replay" class="tp-checkbox tp-editable">记录会话历史</div>
##                         </td>
##                     </tr>
##                     <tr>
##                         <td class="key"></td>
##                         <td class="value">
##                             <div id="sess-record-allow-real-time" class="tp-checkbox tp-disabled">允许实时监控（开发中）</div>
##                         </td>
##                     </tr>

                    <tr>
                        <td colspan="2" class="title">
##                             <hr class="hr-sm"/>
                            全局RDP选项（注：尚未实现）
                        </td>
                    </tr>

                    ## <div id="rdp-allow-desktop" class="tp-checkbox tp-editable tp-selected">允许 远程桌面</div>
                    ## <div id="rdp-allow-app" class="tp-checkbox">允许 远程应用</div>

                    <tr>
                        <td class="key"></td>
                        <td class="value">
                            <div id="sess-rdp-allow-clipboard" class="tp-checkbox tp-editable">允许剪贴板</div>
                        </td>
                    </tr>
                    <tr>
                        <td class="key"></td>
                        <td class="value">
                            <div id="sess-rdp-allow-disk" class="tp-checkbox tp-editable">允许驱动器映射</div>
                        </td>
                    </tr>
                    <tr>
                        <td class="key"></td>
                        <td class="value">
                            <div id="sess-rdp-allow-console" class="tp-checkbox tp-editable">允许管理员连接（Console模式）</div>
                        </td>
                    </tr>

                    <tr>
                        <td colspan="2" class="title">
                            <hr class="hr-sm"/>
                            全局SSH选项（注：尚未实现）
                        </td>
                    </tr>

##                     <div id="ssh-allow-x11" class="tp-checkbox">允许X11转发</div>
##                     <div id="ssh-allow-tunnel" class="tp-checkbox">允许隧道转发</div>
##                     <div id="ssh-allow-exec" class="tp-checkbox">允许远程执行exec</div>

                    <tr>
                        <td class="key"></td>
                        <td class="value">
                            <div id="sess-ssh-allow-shell" class="tp-checkbox tp-editable">允许SSH</div>
                        </td>
                    </tr>
                    <tr>
                        <td class="key"></td>
                        <td class="value">
                            <div id="sess-ssh-allow-sftp" class="tp-checkbox tp-editable">允许SFTP</div>
                        </td>
                    </tr>
##                     <tr>
##                         <td class="key"></td>
##                         <td class="value">
##                             <div id="ssh-allow-x11" class="tp-checkbox tp-disabled">允许X11转发（开发中）</div>
##                         </td>
##                     </tr>

                    <tr>
                        <td colspan="2" class="title">
                            <hr class="hr-sm"/>
                            会话超时设置
                        </td>
                    </tr>
                    <tr>
                        <td class="key">会话超时</td>
                        <td class="value">
                            <input id="sess-noop-timeout" type="text" value="15"/><span class="unit">分钟</span><span class="desc">0~60。指定时间内远程会话没有任何数据包收发时，将此会话断开，为0则不检查。默认为15分钟。</span>
                        </td>
                    </tr>

                </table>
                <hr/>

                <button id="btn-save-session-config" class="btn btn-sm btn-primary"><i class="fa fa-check-circle fa-fw"></i> 保存设置</button>

            </div>

            <!-- panel for mail config -->
            <div class="tab-pane" id="tab-smtp">
                <table class="table table-info-list">
                    <tr>
                        <td class="key">SMTP服务器：</td>
                        <td class="value"><span id="smtp-server-info"></span></td>
                    </tr>
                    <tr>
                        <td class="key">SMTP 端口：</td>
                        <td class="value"><span id="smtp-port-info"></span></td>
                    </tr>
                    <tr>
                        <td class="key">SSL模式：</td>
                        <td class="value"><span id="smtp-ssl-info"></span></td>
                    </tr>
                    <tr>
                        <td class="key">发件人邮箱：</td>
                        <td class="value"><span id="smtp-sender-info"></span></td>
                    </tr>
                </table>
                <hr/>
                <button id="btn-edit-mail-config" class="btn btn-sm btn-primary"><i class="fa fa-cog fa-fw"></i> 设置发件服务器</button>
            </div>

            <!-- panel for storage config -->
            <div class="tab-pane" id="tab-storage">
                <div id="storage-size" class="alert alert-info">-</div>
                <table class="table table-config-list">
                    <tr>
                        <td colspan="2" class="title">系统日志</td>
                    </tr>
                    <tr>
                        <td class="key">保留时间</td>
                        <td class="value">
                            <input id="storage-keep-log" type="text" value="0"/><span class="unit">天</span><span class="desc">30~365。仅保留指定天数的系统日志，为0则永久保留。默认为0。</span>
                        </td>
                    </tr>

                    <tr>
                        <td colspan="2" class="title">
                            <hr class="hr-sm"/>
                            会话录像
                        </td>
                    </tr>
                    <tr>
                        <td class="key">保留时间</td>
                        <td class="value">
                            <input id="storage-keep-record" type="text" value="0"/><span class="unit">天</span><span class="desc">30~365。仅保留指定天数的会话录像（以会话开始时间为准），为0则永久保留。默认为0。</span>
                        </td>
                    </tr>

                    <tr>
                        <td colspan="2" class="title">
                            <hr class="hr-sm"/>
                            自动清理
                        </td>
                    </tr>
                    <tr>
                        <td class="key">时间点</td>
                        <td class="value">
                            <select id="select-cleanup-storage-hour" style="width:4rem;">
                                <option value="0">00</option>
                                <option value="1">01</option>
                                <option value="2">02</option>
                                <option value="3">03</option>
                                <option value="4">04</option>
                                <option value="5">05</option>
                                <option value="6">06</option>
                                <option value="7">07</option>
                                <option value="8">08</option>
                                <option value="9">09</option>
                                <option value="10">10</option>
                                <option value="11">11</option>
                                <option value="12">12</option>
                                <option value="13">13</option>
                                <option value="14">14</option>
                                <option value="15">15</option>
                                <option value="16">16</option>
                                <option value="17">17</option>
                                <option value="18">18</option>
                                <option value="19">19</option>
                                <option value="20">20</option>
                                <option value="21">21</option>
                                <option value="22">22</option>
                                <option value="23">23</option>
                            </select>
                            时
                            <select id="select-cleanup-storage-minute" style="width:4rem;">
                                <option value="0">00</option>
                                <option value="5">05</option>
                                <option value="10">10</option>
                                <option value="15">15</option>
                                <option value="20">20</option>
                                <option value="25">25</option>
                                <option value="30">30</option>
                                <option value="35">35</option>
                                <option value="40">40</option>
                                <option value="45">45</option>
                                <option value="50">50</option>
                                <option value="55">55</option>
                            </select>
                            分
                            <span class="desc">每天在指定时间点清理超出保留时间的数据。</span>
                        </td>
                    </tr>
                    <tr>
                        <td class="key"></td>
                        <td class="value">
                            <button id="btn-clear-storage" class="btn btn-sm btn-success"><i class="fa fa-leaf fa-fw"></i> 现在立即清理</button>
                        </td>
                    </tr>
                </table>
                <hr/>
                <button id="btn-save-storage-config" class="btn btn-sm btn-primary"><i class="fa fa-check-circle fa-fw"></i> 保存存储设置</button>
                ##                 <button id="btn-clear-storage" class="btn btn-sm btn-danger"><i class="fa fa-edit fa-fw"></i> 立即清理</button>
            </div>

            <!-- panel for backup config -->
            ##             <div class="tab-pane" id="tab-backup">
            ##                 <div class="alert alert-danger">备份功能尚未实现</div>
            ##
            ##                 <table class="table table-config-list">
            ##                     <tr>
            ##                         <td colspan="2" class="title">数据库备份</td>
            ##                     </tr>
            ##                     <tr>
            ##                         <td class="key">备份范围</td>
            ##                         <td class="value">
            ##                             <div id="btn-bak-syslog" class="tp-checkbox tp-editable">包括系统日志</div>
            ##                         </td>
            ##                     </tr>
            ##                     <tr>
            ##                         <td class="key"></td>
            ##                         <td class="value">
            ##                             <div id="btn-backup-alert" class="tp-checkbox tp-editable">包括报警日志</div>
            ##                         </td>
            ##                     </tr>
            ##                     <tr>
            ##                         <td class="key"></td>
            ##                         <td class="value">
            ##                             <div id="btn-backup-ops" class="tp-checkbox tp-editable">包括运维记录</div>
            ##                         </td>
            ##                     </tr>
            ##                     <tr>
            ##                         <td class="key">自动备份</td>
            ##                         <td class="value">
            ##                             <div id="btn-auto-backup" class="tp-checkbox tp-editable tp-selected">在指定时间点自动备份数据库</div>
            ##                         </td>
            ##                     </tr>
            ##                     <tr>
            ##                         <td class="key">备份时间点</td>
            ##                         <td class="value">
            ##                             <select id="select-backup-hour">
            ##                                 <option>00</option>
            ##                                 <option>01</option>
            ##                                 <option>02</option>
            ##                                 <option selected="selected">03</option>
            ##                                 <option>04</option>
            ##                                 <option>05</option>
            ##                                 <option>06</option>
            ##                                 <option>07</option>
            ##                                 <option>08</option>
            ##                                 <option>09</option>
            ##                                 <option>10</option>
            ##                                 <option>11</option>
            ##                                 <option>12</option>
            ##                                 <option>13</option>
            ##                                 <option>14</option>
            ##                                 <option>15</option>
            ##                                 <option>16</option>
            ##                                 <option>17</option>
            ##                                 <option>18</option>
            ##                                 <option>19</option>
            ##                                 <option>20</option>
            ##                                 <option>21</option>
            ##                                 <option>22</option>
            ##                                 <option>23</option>
            ##                             </select>
            ##                             时
            ##                             <select id="select-backup-min">
            ##                                 <option selected="selected">00</option>
            ##                                 <option>05</option>
            ##                                 <option>10</option>
            ##                                 <option>15</option>
            ##                                 <option>20</option>
            ##                                 <option>25</option>
            ##                                 <option>30</option>
            ##                                 <option>35</option>
            ##                                 <option>40</option>
            ##                                 <option>45</option>
            ##                                 <option>50</option>
            ##                                 <option>55</option>
            ##                             </select>
            ##                             分
            ##                             <span class="desc">每天在指定时间点备份数据库。</span>
            ##                         </td>
            ##                     </tr>
            ##                     <tr>
            ##                         <td class="key">备份保留时长</td>
            ##                         <td class="value">
            ##                             <input id="backup-keep-timeout" type="text" value="7"/><span class="unit">天</span><span class="desc">1~7。超过设定时间的备份将自动删除，默认为7天。</span>
            ##                         </td>
            ##                     </tr>
            ##                     <tr>
            ##                         <td class="key"></td>
            ##                         <td class="value">
            ##                             <a href="javascript:;"><i class="fa fa-download"></i> 下载自动备份文件</a>
            ##                         </td>
            ##                     </tr>
            ##
            ##                 </table>
            ##                 <hr/>
            ##                 <button id="btn-save-storage-config" class="btn btn-sm btn-primary"><i class="fa fa-edit fa-fw"></i> 保存存储设置</button>
            ##                 <button id="btn-do-backup" class="btn btn-sm btn-success"><i class="fa fa-edit fa-fw"></i> 立即备份</button>
            ##                 <button id="btn-import-backup" class="btn btn-sm btn-danger"><i class="fa fa-edit fa-fw"></i> 导入备份</button>
            ##             </div>
        </div>
    </div>
</div>


<%block name="extend_content">
    <!-- dialog for edit smtp config -->
    <div class="modal fade" id="dlg-edit-smtp-config">
        <div class="modal-dialog" role="document">
            <div class="modal-content">
                <div class="modal-header">
                    <button type="button" class="close" data-dismiss="modal" aria-label="Close"><i class="fa fa-times-circle fa-fw"></i></button>
                    <h3 class="modal-title">设置发件服务器</h3>
                </div>
                <div class="modal-body">

                    <div class="form-horizontal">

                        <div class="form-group form-group-sm">
                            <label for="edit-smtp-server" class="col-sm-3 control-label require">服务器地址：</label>
                            <div class="col-sm-5">
                                <input id="edit-smtp-server" type="text" class="form-control" placeholder="SMTP邮件服务器地址"/>
                            </div>
                        </div>

                        <div class="form-group form-group-sm">
                            <label for="edit-smtp-port" class="col-sm-3 control-label require">SMTP端口：</label>
                            <div class="col-sm-2">
                                <input id="edit-smtp-port" type="text" class="form-control" placeholder="25"/>
                            </div>
                            <div class="col-sm-6">
                                <div id="edit-smtp-ssl" class="form-control-static tp-checkbox tp-editable tp-selected">使用SSL</div>
                            </div>
                        </div>

                        <div class="form-group form-group-sm">
                            <label for="edit-smtp-sender" class="col-sm-3 control-label require">发件人邮箱：</label>
                            <div class="col-sm-5">
                                <input id="edit-smtp-sender" type="text" class="form-control" placeholder=""/>
                            </div>
                        </div>

                        <div class="form-group form-group-sm">
                            <label for="edit-smtp-password" class="col-sm-3 control-label require">发件人邮箱密码：</label>
                            <div class="col-sm-5">
                                <input id="edit-smtp-password" type="password" class="form-control" placeholder=""/>
                            </div>
                        </div>

                        <hr/>

                        <div class="form-group form-group-sm">
                            <label for="edit-smtp-test-recipient" class="col-sm-3 control-label">测试收件人邮箱：</label>
                            <div class="col-sm-5">
                                <input id="edit-smtp-test-recipient" type="text" class="form-control" placeholder=""/>
                            </div>
                            <div class="col-sm-4">
                                <div class="control-desc">仅用于测试。</div>
                            </div>
                        </div>


                        <div class="form-group form-group-sm">
                            <div class="col-sm-offset-3 col-sm-5">
                                <button type="button" class="btn btn-sm btn-success" id="btn-send-test-mail"><i class="fa fa-send fa-fw"></i> 发送测试邮件</button>
                            </div>
                        </div>

                        <div id="msg-send-test-mail" class="alert alert-success" style="display:none;">
                            <p><i class="fa fa-info-circle fa-fw"></i> 邮件发送成功！</p>
                            <p>请到您的收件箱中检查是否已正确接收到测试邮件（如未能接收到，请注意检查测试邮件是否被归类为垃圾邮件了）。</p>
                            <p>确定能正常接收邮件后，即可应用并保存以上设置了！</p>
                        </div>
                    </div>
                </div>

                <div class="modal-footer">
                    <button type="button" class="btn btn-sm btn-primary" id="btn-save-mail-config"><i class="fa fa-check fa-fw"></i> 应用并保存设置</button>
                    <button type="button" class="btn btn-sm btn-default" data-dismiss="modal"><i class="fa fa-times fa-fw"></i> 取消</button>
                </div>
            </div>
        </div>
    </div>

    <!-- dialog for show storage cleanup result -->
    <div class="modal fade" id="dlg-result">
        <div class="modal-dialog" role="document">
            <div class="modal-content">
                <div class="modal-header">
                    <button type="button" class="close" data-dismiss="modal" aria-label="Close"><i class="fa fa-times-circle fa-fw"></i></button>
                    <h3 id="dlg-result-title" class="modal-title">-</h3>
                </div>
                <div class="modal-body">
                    <div id="dlg-result-msg"></div>
                </div>

                <div class="modal-footer">
                    <button type="button" class="btn btn-sm btn-default" data-dismiss="modal"><i class="fa fa-times fa-fw"></i> 关闭</button>
                </div>
            </div>
        </div>
    </div>
</%block>
