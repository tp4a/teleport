<%!
    page_icon_class_ = 'fa fa-dashboard fa-fw'
    page_title_ = ['系统总览']
    page_id_ = ['dashboard']
%>
<%inherit file="../page_base.mako"/>

## <%block name="extend_js_file">
##     <script type="text/javascript" src="${ static_url('js/ui/config/info.js') }"></script>
## </%block>

<%block name="extend_css_file">
    <link href="${ static_url('css/dashboard.css') }" rel="stylesheet" type="text/css"/>
</%block>

## Begin Main Body.

<div class="page-content-inner">

    <div class="sys-msg">abc</div>

    <div class="row">
        <div class="col-sm-3">
            <div class="stats stats-box stats-id-user">
                <div class="stats-icon">
                    <i class="fa fa-id-card-o fa-fw"></i>
                </div>
                <div class="stats-content">
                    <div class="stats-name">用户</div>
                    <div class="stats-value">21</div>
                </div>
            </div>
        </div>
        <div class="col-sm-3">
            <div class="stats stats-box stats-id-host">
                <div class="stats-icon">
                    <i class="fa fa-cubes fa-fw"></i>
                </div>
                <div class="stats-content">
                    <div class="stats-name">主机</div>
                    <div class="stats-value">128</div>
                </div>
            </div>
        </div>
        <div class="col-sm-3">
            <div class="stats stats-box stats-id-account">
                <div class="stats-icon">
                    <i class="fa fa-user-secret fa-fw"></i>
                </div>
                <div class="stats-content">
                    <div class="stats-name">主机账号</div>
                    <div class="stats-value">63</div>
                </div>
            </div>
        </div>
        <div class="col-sm-3">
            <div class="stats stats-box stats-id-connect">
                <div class="stats-icon">
                    <i class="fa fa-link fa-fw"></i>
                </div>
                <div class="stats-content">
                    <div class="stats-name">当前连接</div>
                    <div class="stats-value">18</div>
                </div>
            </div>
        </div>
    </div>

    <div class="row">
        <div class="col-sm-6">
            <div class="stats stats-bar">
                <div class="stats-name">CPU负载</div>
                <div class="stats-value">
                </div>
            </div>
        </div>
        <div class="col-sm-6">
            <div class="stats stats-bar">
                <div class="stats-name">内存使用</div>
                <div class="stats-value">
                </div>
            </div>
        </div>
    </div>

    <div class="row">
        <div class="col-sm-6">
            <div class="stats stats-bar">
                <div class="stats-name">网络流量</div>
                <div class="stats-value">
                </div>
            </div>
        </div>
        <div class="col-sm-6">
            <div class="stats stats-bar">
                <div class="stats-name">网络连接</div>
                <div class="stats-value">
                </div>
            </div>
        </div>
    </div>

</div>


<%block name="extend_content"></%block>


<%block name="embed_js">
    <script type="text/javascript">
##         ywl.add_page_options(${ page_param });
    </script>
</%block>
