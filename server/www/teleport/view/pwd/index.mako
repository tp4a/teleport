<%!
	page_title_ = '修改密码'
	page_menu_ = ['pwd']
	page_id_ = 'pwd'
%>
<%inherit file="../page_base.mako"/>

<%block name="extend_js">
	<script type="text/javascript" src="${ static_url('js/ui/teleport.js') }"></script>
	<script type="text/javascript" src="${ static_url('js/ui/pwd.js') }"></script>
</%block>

<%block name="breadcrumb">
	<ol class="breadcrumb">
		<li><i class="fa fa-pencil-square-o fa-fw"></i> ${self.attr.page_title_}</li>
	</ol>
</%block>

## Begin Main Body.

<div class="page-content">

	<!-- begin box -->
	<div class="box" id="ywl_host_list">


		<div class="input-group input-group-sm" style="margin-top: 10px">
			<span class="input-group-addon" style="width:90px;">当前密码:</span>
			<input type="password" class="form-control" id="current-pwd" aria-describedby="basic-addon1">
		</div>
		<div class="input-group input-group-sm" style="margin-top: 10px">
			<span class="input-group-addon" style="width:90px;">新密码:</span>
			<input type="password" class="form-control" id="new-pwd-1" aria-describedby="basic-addon1">
		</div>
		<div class="input-group input-group-sm" style="margin-top: 10px">
			<span class="input-group-addon" style="width:90px;">重复新密码:</span>
			<input type="password" class="form-control" id="new-pwd-2" aria-describedby="basic-addon1">
		</div>

		<div style="margin-top:20px;">
			<a href="#" id="btn-modify-pwd" class="btn btn-sm btn-primary"><i class="fa fa-check fa-fw"></i> 确认修改</a>
		</div>

	</div>
	<!-- end of box -->

</div>






<%block name="extend_content">
</%block>



<%block name="embed_js">
	<script type="text/javascript">

		$(document).ready(function () {
		});


	</script>
</%block>
