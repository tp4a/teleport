<%!
    import app.app_ver as app_ver
    page_title_ = '安装配置TELEPORT服务'
%>

<%inherit file="../page_single_base.mako"/>

<%block name="extend_js_file">
    <script type="text/javascript" src="${ static_url('js/maintenance/install.js') }"></script>
</%block>

<%block name="embed_js">
    <script type="text/javascript">
        $app.add_options(${ page_param });
    </script>
</%block>

<%block name="page_header">
    <div class="container-fluid top-navbar">
        <div class="brand"><a href="/" target="_blank"><span class="site-logo"></span></a></div>
        <div class="breadcrumb-container">
            <ol class="breadcrumb">
                <li><i class="fa fa-cog fa-fw"></i> ${self.attr.page_title_}</li>
            </ol>
        </div>
    </div>
</%block>


## Begin Main Body.

<div class="content-box">
    <p class="welcome-message"><i class="fa fa-heart"></i> <span>欢迎安装使用 TELEPORT v${app_ver.TP_SERVER_VER} 社区版！</span></p>

    <hr/>
    <h2><i class="fa fa-chevron-right"></i> 确定数据库类型</h2>
    <div>
        <p>TELEPORT支持 SQLite 和 MySQL 数据库，您目前使用的配置如下：</p>
        <table id="db-info" class="table"></table>
        <div class="alert alert-warning">
            <i class="fas fa-exclamation-triangle"></i> 注意：如果以上配置并不是您所期望的，请修改您的配置文件，然后刷新本页面。
            <a href="https://docs.tp4a.com/config/" target="_blank">如何设置配置文件？</a>
        </div>
    </div>

    <hr/>
    <h2><i class="fa fa-chevron-right"></i> 设置系统管理员</h2>
    <div>
        <p>请设置系统管理员的账号和密码。系统管理员具有本系统的最高权限，请使用高强度的密码。</p>
        <table class="form">
            <tr>
                <td class="key"><label for="sysadmin-account">系统管理员账号：</label></td>
                <td><input type="text" class="form-control" id="sysadmin-account" value="admin"></td>
            </tr>
            <tr>
                <td class="key"><label for="sysadmin-email">电子邮件地址：</label></td>
                <td><input type="text" class="form-control" id="sysadmin-email"></td>
            </tr>
            <tr>
                <td class="key"><label for="password">密码：</label></td>
                <td><input type="password" class="form-control" id="password"></td>
            </tr>
            <tr>
                <td class="key"><label for="password-again">再次确认密码：</label></td>
                <td><input type="password" class="form-control" id="password-again"></td>
            </tr>
        </table>

    </div>

    <hr/>
    <h2><i class="fa fa-chevron-right"></i> 开始配置</h2>
    <p>准备就绪了？配置操作将创建TELEPORT服务所需的数据库，并设置系统管理员账号！</p>
    <button id="btn-config" type="button" class="btn btn-primary"><i class="fa fa-wrench fa-fw"></i> 开始配置</button>
    <div id="steps-detail" class="steps-detail"></div>
    <div><p id="message" class="op_box" style="display:none;"></p></div>


    <div id="step2" style="display:none;">
        <hr/>
        <h2><i class="fa fa-chevron-right"></i> 已完成！</h2>
        <p>是的，就这么简单，安装配置已经完成了！刷新页面即可登录 TELEPORT 啦~~</p>
    </div>

</div>
