<!DOCTYPE html>
	<%!
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

	<link href="${ static_url('plugins/google-cache/open-sans.css') }" rel="stylesheet">
	<link href="${ static_url('plugins/bootstrap/css/bootstrap.min.css') }" rel="stylesheet" type="text/css"/>
	<link href="${ static_url('plugins/font-awesome/css/font-awesome.min.css') }" rel="stylesheet">
	<link href="${ static_url('plugins/gritter/css/jquery.gritter.css') }" rel="stylesheet">

	<link href="${ static_url('css/sub.css') }" rel="stylesheet" type="text/css"/>

	<%block name="extend_css"/>
	<%block name="embed_css"/>

</head>
<body>

<!-- begin #page-container -->
<div class="page-header-fixed">
	<div id="header" class="header header-fixed-top">

		<div class="container-fluid top-navbar">
			<div class="brand"><div class="site-logo"></div></div>
			<div class="breadcrumb-container">
				<%block name="breadcrumb" />
			</div>

## 			<div class="status-container">
## 				more status or global tool buttons goes here.
## 			</div>
		</div>

	</div>

	<div id="footer" class="footer footer-fixed-bottom">
		<div class="container-fluid">
			<p>触维软件旗下产品 | TELEPORT | &copy;2015 - 2017 <a href="http://teleport.eomsoft.net/" target="_blank">触维软件</a>，保留所有权利。</p>
		</div>
	</div>


	<div class="container-fluid">
        ${self.body()}
	</div>


</div>


	<%block name="extend_content" />

<script type="text/javascript" src="${ static_url('plugins/underscore/underscore.js') }"></script>
<script type="text/javascript" src="${ static_url('plugins/jquery/jquery.min.js') }"></script>
<script type="text/javascript" src="${ static_url('plugins/bootstrap/js/bootstrap.min.js') }"></script>
<!--[if lt IE 9]>
<script src="${ static_url('plugins/html5shiv/html5shiv.min.js') }"></script>
<![endif]-->
	## <script type="text/javascript" src="${ static_url('js/json2.js') }"></script>

<script type="text/javascript" src="${ static_url('plugins/gritter/js/jquery.gritter.js') }"></script>
## <script type="text/javascript" src="${ static_url('plugins/jstree/jstree.js') }"></script>

<script type="text/javascript" src="${ static_url('plugins/keypress/keypress.js') }"></script>

<script type="text/javascript" src="${ static_url('js/ywl_const.js') }"></script>
<script type="text/javascript" src="${ static_url('js/ywl_common.js') }"></script>
<script type="text/javascript" src="${ static_url('js/ywl.js') }"></script>
## <script type="text/javascript" src="${ static_url('js/ywl_assist.js') }"></script>
## <script type="text/javascript" src="${ static_url('js/ui/common.js') }"></script>
## <script type="text/javascript" src="${ static_url('js/ui/controls.js') }"></script>


	<%block name="extend_js"/>



<script type="text/javascript">

	$(document).ready(function () {
		// once page ready, init ywl object.
		ywl.init();
	});

</script>

	<%block name="embed_js" />


</body>
</html>