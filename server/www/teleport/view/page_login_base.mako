<!DOCTYPE html>
    <%!
        import app.app_ver as app_ver
        page_title_ = ''
    %>
<!--[if IE 8]><html lang="en" class="ie8"> <![endif]-->
<!--[if !IE]><!-->
<html lang="zh_CN">
<!--<![endif]-->
<head>
    <meta charset="utf-8"/>
    <meta http-equiv="Content-Type" content="text/html; charset=utf-8"/>
    <meta content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no" name="viewport"/>
    <meta http-equiv="X-UA-Compatible" content="IE=edge"/>
    <meta content="yes" name="apple-mobile-web-app-capable">
    <meta content="black-translucent" name="apple-mobile-web-app-status-bar-style">
    <title>${self.attr.page_title_}::TELEPORT</title>
    <link rel="shortcut icon" href="${ static_url('favicon.png') }">

    <link href="${ static_url('plugins/bootstrap/css/bootstrap.min.css') }" rel="stylesheet" type="text/css"/>
##     <link href="${ static_url('plugins/bootstrap/css/bootstrap-theme.min.css') }" rel="stylesheet" type="text/css"/>
    <link href="${ static_url('plugins/font-awesome/css/fontawesome-all.min.css') }" rel="stylesheet">
    ## 	<link href="${ static_url('css/main.css') }" rel="stylesheet" type="text/css"/>

    <link href="${ static_url('css/login.css') }" rel="stylesheet" type="text/css"/>

    <%block name="extend_css"/>

</head>

<body>

<div id="page-bg-container">
    <div id="page-bg">
        <div id="page-header">
            <nav class="navbar navbar-fixed-top">
                <div class="container">
                    <ul>
                        <li><a href="/" class="logo"><img src="${ static_url('img/site-logo.png') }" alt="TELEPORT"/></a></li>
                        <li>
                            <div class="desc">连接 &middot; 尽在指掌中</div>
                        </li>
                    </ul>
                </div>
            </nav>
        </div>

        <div id="page-content">
            <div class="container">

                ${self.body()}

            </div>
        </div>

        <%include file="_footer.mako"/>
    </div>
</div>

    <%block name="extend_content" />

<!-- JavaScript -->
<script type="text/javascript" src="${ static_url('plugins/underscore/underscore.js') }"></script>
<script type="text/javascript" src="${ static_url('plugins/jquery/jquery-2.2.3.min.js') }"></script>
<script type="text/javascript" src="${ static_url('plugins/bootstrap/js/bootstrap.min.js') }"></script>
<script type="text/javascript" src="${ static_url('plugins/blur/velocity.min.js') }"></script>
<script type="text/javascript" src="${ static_url('plugins/blur/background-blur.js') }"></script>

<!--[if lt IE 9]>
<script src="${ static_url('plugins/html5shiv/html5shiv.min.js') }"></script>
<script type="text/javascript" src="${ static_url('plugins/json2/json2.js') }"></script>
<![endif]-->

## <script type="text/javascript" src="${ static_url('js/tpapp_const.js') }"></script>
## <script type="text/javascript" src="${ static_url('js/tpapp_common.js') }"></script>
## <script type="text/javascript" src="${ static_url('js/tpapp.js') }"></script>
<script type="text/javascript" src="${ static_url('js/tp-utils.js') }"></script>
<script type="text/javascript" src="${ static_url('js/tp-const.js') }"></script>
## <script type="text/javascript" src="${ static_url('js/tp-assist.js') }"></script>
<script type="text/javascript" src="${ static_url('js/teleport.js') }"></script>
## <script type="text/javascript" src="${ static_url('js/teleport/common.js') }"></script>
## <script type="text/javascript" src="${ static_url('js/teleport/controls.js') }"></script>


    <%block name="extend_js_file"/>

## <script type="text/javascript">
##     $(document).ready(function () {
##         tpapp.init();
##     });
## </script>

    <%block name="embed_js" />

</body>
</html>