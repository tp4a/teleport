<%!
	page_title_ = '分组管理'
	page_menu_ = ['group']
	page_id_ = 'group'
%>
<%inherit file="../page_base.mako"/>

<%block name="extend_js">
	<script type="text/javascript" src="${ static_url('js/ui/teleport.js') }"></script>
	<script type="text/javascript" src="${ static_url('js/ui/group.js') }"></script>
</%block>

<%block name="breadcrumb">
	<ol class="breadcrumb">
		<li><i class="fa fa-server fa-fw"></i> ${self.attr.page_title_}</li>
	</ol>
</%block>

## Begin Main Body.

<div class="page-content">

	<!-- begin box -->
	<div class="box" id="ywl_group_list">
		<div class="page-filter">
			<div class="" style="float:right;">
				<a href="javascript:;" class="btn btn-sm btn-primary" ywl-filter="reload"><i class="fa fa-repeat fa-fw"></i> 刷新</a>
			</div>
		</div>
		<table class="table table-striped table-bordered table-hover table-data no-footer dtr-inline" ywl-table="group-list"></table>

		<!-- begin page-nav -->
		<div class="page-nav" ywl-paging="group-list">
			<div class="input-group input-group-sm" style="display:inline-block;">
				<a href="#" id="btn-add-group" class="btn btn-sm btn-primary"><i class="fa fa-plus-circle fa-fw"></i> 创建分组</a>
			</div>


			<div class="" style="float:right;">
				<nav>
					<ul class="pagination pagination-sm"></ul>
				</nav>
			</div>

			<div style="float:right;margin-right:30px;">
				<div class="breadcrumb-container">
					<ol class="breadcrumb">
						<li><i class="fa fa-list fa-fw"></i> 记录总数 <strong ywl-field="recorder_total">0</strong></li>
						<li>页数 <strong><span ywl-field="page_current">1</span>/<span ywl-field="page_total">1</span></strong></li>
						<li>每页显示
							<label>
								<select></select>
							</label>
							条记录
						</li>
					</ol>
				</div>
			</div>

		</div>
		<!-- end page-nav -->

	</div>
	<!-- end of box -->

</div>






<%block name="extend_content">
<div class="modal fade" id="dialog_group_info" tabindex="-1" role="dialog">
	<div class="modal-dialog" role="document">
		<div class="modal-content">
			<div class="modal-header">
				<h3 class="modal-title">分组信息</h3>
			</div>
			<div class="modal-body">

				<div class="form-horizontal">
					<div class="form-group form-group-sm">
						<label for="group_name" class="col-sm-3 control-label"><strong>分组名称：</strong></label>
						<div class="col-sm-6">
							<input id="group_name" type="text" class="form-control" placeholder=""/>
						</div>
					</div>
				</div>

			</div>
			<div class="modal-footer">
				<button type="button" class="btn btn-sm btn-primary" id="btn-save"><i class="fa fa-check fa-fw"></i> 确定</button>
				<button type="button" class="btn btn-sm btn-default" data-dismiss="modal"><i class="fa fa-close fa-fw"></i> 取消</button>
			</div>
		</div>
	</div>
</%block>



<%block name="embed_js">
	<script type="text/javascript">

		$(document).ready(function () {
		});


	</script>
</%block>
