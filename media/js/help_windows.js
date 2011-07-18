jQuery(document).ready(function() 
    { 
	jQuery.fx.speeds._default = 500;
	jQuery( "#dialog" ).dialog({
		autoOpen: false,
		modal: true,
		height: 200,
		width: 300
	});
	jQuery( "#opener" ).click(function() {
		$( "#dialog" ).dialog( "open" );
		return false;
	});
	
// --------------	

	jQuery( "#dialog_help_video_source" ).dialog({
		autoOpen: false,
		modal: true,
		height: 300,
		width: 500,
		show: "fade",
		hide: "fade"
	});
	jQuery( "#help_video_source" ).click(function() {
		$( "#dialog_help_video_source" ).dialog( "open" );
		return false;
	});
	
// --------------	

	jQuery( "#dialog_help_video_subject" ).dialog({
		autoOpen: false,
		modal: true,
		height: 300,
		width: 500,
		show: "fade",
		hide: "fade"
	});
	jQuery( "#help_video_subject" ).click(function() {
		$( "#dialog_help_video_subject" ).dialog( "open" );
		return false;
	});
	
// --------------	

	jQuery( "#dialog_help_video_tag" ).dialog({
		autoOpen: false,
		modal: true,
		height: 300,
		width: 500,
		show: "fade",
		hide: "fade"
	});
	jQuery( "#help_video_tag" ).click(function() {
		$( "#dialog_help_video_tag" ).dialog( "open" );
		return false;
	});
	
// --------------	

	jQuery( "#dialog_help_video_file" ).dialog({
		autoOpen: false,
		modal: true,
		height: 300,
		width: 500,
		show: "fade",
		hide: "fade"
	});
	jQuery( "#help_video_file" ).click(function() {
		$( "#dialog_help_video_file" ).dialog( "open" );
		return false;
	});
	
// --------------	

	jQuery( "#dialog_help_process_steps" ).dialog({
		autoOpen: false,
		modal: true,
		height: 300,
		width: 500,
		show: "fade",
		hide: "fade"
	});
	jQuery( "#help_process_steps" ).click(function() {
		$( "#dialog_help_process_steps" ).dialog( "open" );
		return false;
	});

	
   }
);

