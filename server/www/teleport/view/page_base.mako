<!DOCTYPE html>
	<%!
		page_title_ = ''
		page_menu_ = []
	%>
<!--[if IE 8]> <html lang="en" class="ie8"> <![endif]-->
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


	<link href="${ static_url('css/main.css') }" rel="stylesheet" type="text/css"/>
	<%block name="extend_css"/>

</head>
<body>

<!-- begin #page-container -->
<div id="page-container" class="page-header-fixed page-sidebar-fixed">
	<!-- begin #header -->
	<div id="header" class="header navbar navbar-default navbar-fixed-top">
		<div class="container-fluid">
			<div class="brand"><a href="http://teleport.eomsoft.net" target="_blank"><span class="navbar-logo"></span></a></div>
			<div class="breadcrumb-container">
					<%block name="breadcrumb" />
			</div>
## 			<div style="float:right;padding-top:14px;margin-right: 50px"><a href="/set" id="teleport-server-ip"></a></div>
		</div>
	</div>
	<!-- end #header -->


	<!-- begin #sidebar -->
	<div id="sidebar" class="sidebar">
			<%include file="common/_sidebar_nav_menu.mako" />
	</div>
	<!-- end #sidebar -->

	<!-- begin #content -->
	<div id="content" class="content">
		${self.body()}
	</div>
	<!-- end #content -->


</div>
<!-- end #page-container -->


<div class="modal fade" ywl_message_box="dialog-ywl-message-box" tabindex="-1" role="dialog">
	<div class="modal-dialog" role="document">
		<div class="modal-content">
			<div class="modal-header">
				<button type="button" class="close" data-dismiss="modal" aria-label="Close"><span aria-hidden="true">&times;</span></button>
				<h4 class="modal-title" ywl-title></h4>
			</div>
			<div class="modal-body" ywl-content style="font-size: 20px">

			</div>
			<div class="modal-footer">
				<input type="hidden" ywl-record-id="" ywl-row-id="">
				<button type="button" class="btn btn-success btn-sm" ywl-btn-ok="ok"><i class="glyphicon glyphicon-ok"></i></button>
				<button type="button" class="btn btn-danger btn-sm" data-dismiss="modal"><i class="glyphicon glyphicon-remove"></i></button>
			</div>
		</div>
	</div>
</div>

	<%block name="extend_content" />
<script type="text/javascript" src="${ static_url('js/var.js') }"></script>
<script type="text/javascript" src="${ static_url('plugins/underscore/underscore.js') }"></script>
<script type="text/javascript" src="${ static_url('plugins/jquery/jquery.min.js') }"></script>
<script type="text/javascript" src="${ static_url('plugins/jquery/ajaxfileupload.js') }"></script>
<script type="text/javascript" src="${ static_url('plugins/bootstrap/js/bootstrap.min.js') }"></script>
<!--[if lt IE 9]>
<script src="${ static_url('plugins/html5shiv/html5shiv.min.js') }"></script>
<![endif]-->
<script type="text/javascript" src="${ static_url('js/json2.js') }"></script>
<script type="text/javascript" src="${ static_url('plugins/gritter/js/jquery.gritter.js') }"></script>

<script type="text/javascript" src="${ static_url('js/ywl_const.js') }"></script>
<script type="text/javascript" src="${ static_url('js/ywl_common.js') }"></script>
<script type="text/javascript" src="${ static_url('js/ywl.js') }"></script>
<script type="text/javascript" src="${ static_url('js/ywl_assist.js') }"></script>
<script type="text/javascript" src="${ static_url('js/ui/common.js') }"></script>
<script type="text/javascript" src="${ static_url('js/ui/controls.js') }"></script>

	<%block name="extend_js"/>


<script type="text/javascript">
	ywl.add_page_options({
		## 	有些参数由后台python脚本生成到模板中，无法直接生成到js文件中，所以必须通过这种方式传递参数到js脚本中。
        active_menu: ${self.attr.page_menu_}
	});

	$(document).ready(function () {
		// once page ready, init ywl object.
## 		var teleport_ip_info = "请核对您的堡垒机IP地址，当前为 " + teleport_ip;
## 		$("#teleport-server-ip").text(teleport_ip_info);
		ywl.init();
	});

</script>

	<%block name="embed_js" />


</body>
</html>