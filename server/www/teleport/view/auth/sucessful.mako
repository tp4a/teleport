<!DOCTYPE html>
<html lang="en">
<head>
    <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
    <meta http-equiv="X-UA-Compatible" content="IE=edge" />
    <meta content="yes" name="apple-mobile-web-app-capable">
    <meta content="black-translucent" name="apple-mobile-web-app-status-bar-style">
    <title>TELEPORT::注册成功</title>
    <link rel="shortcut icon" href="${ static_url('favicon.png') }">

    <link href="${ static_url('plugins/bootstrap/css/bootstrap.min.css') }" rel="stylesheet" type="text/css" />
    <link href="${ static_url('plugins/font-awesome/css/font-awesome.min.css') }" rel="stylesheet">
    <link href="${ static_url('css/main.css') }" rel="stylesheet" type="text/css" />
    <link href="${ static_url('css/auth.css') }" rel="stylesheet" type="text/css" />

    <!--[if lt IE 9]>
    <script src="${ static_url('plugins/html5shiv/html5shiv.min.js') }"></script>
    <![endif]-->
    <script type="text/javascript" src="${ static_url('plugins/jquery/jquery.min.js') }"></script>
    <script type="text/javascript" src="${ static_url('plugins/bootstrap/js/bootstrap.min.js') }"></script>
    <script type="text/javascript" src="${ static_url('js/ywl_const.js') }"></script>
    <script type="text/javascript" src="${ static_url('js/ywl_common.js') }"></script>
    <script type="text/javascript" src="${ static_url('js/ywl_assist.js') }"></script>
    <script type="text/javascript" src="${ static_url('js/ywl.js') }"></script>
    <script type="text/javascript" src="${ static_url('js/ui/common.js') }"></script>
</head>
<style>
#main {position: absolute;width:800px;height:200px;left:50%;top:35%;
margin-left:-350px;margin-top:-100px;}
.span{font-size:26px}
</style>
<body>
<div id="head">
    <nav class="navbar navbar-default navbar-fixed-top">
        <div class="container">
            <ul class="nav navbar-nav navbar-left">
                <li>
                    <div class="logo">
                        <a href="/"><img src="${ static_url('img/site-logo.png') }" alt="TELEPORT，触维软件旗下产品。" /></a>
                        <span class="desc">连接 &middot; 尽在指掌中</span>
                    </div>
                </li>
            </ul>
        </div>
    </nav>
</div>
<div id="content">
<div  class="container">
    <div  id="main" class="row">
        <span class="span">您的账号密码已经发送到关联邮箱.请点击这里</span>
        <a class="span" ywl-login href="#">登陆</a><span class="span">进入登陆页面</span>
    </div>
</div>
</div>
<div id="foot">
<nav class="navbar navbar-default navbar-fixed-bottom">
    <div class="container">
        <p>触维软件旗下产品 | TELEPORT | &copy;2015 - 2016 <a href="http://www.eomsoft.net/" target="_blank">触维软件</a>，保留所有权利。<a href="/auth/logout">Logout</a></p>
    </div>
</nav>
</div>

<script type="text/javascript">


$(document).ready(function(){
    $("[ ywl-login]").click(function(){
        console.log('click');
        window.location.href= '/auth/login';
    });
});


</script>

</body>
</html>