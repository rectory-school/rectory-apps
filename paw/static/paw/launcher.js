function clickDialog(e) {
	toShow = $(e.currentTarget).attr("href")
	
	var count = $(toShow).find(".entry").length

  $(toShow).dialog({height: $(window).height() - 50})
  $(toShow).dialog({width: $(window).width() - 50})
  
	$(toShow).dialog("open");

	$(".dialogHide").hide();
	return false;
}

function dismissDialog(e, ui) {
	$(".dialogHide").show();
}

$(document).ready(function() {
	$( ".dialog" ).dialog({
		autoOpen: false,
		show: {
			effect: "blind",
			duration: 500},
		hide: {
			effect: "fade",
			duration: 250},
		height: 700,
		width: 700,
		modal: true,
		beforeClose: dismissDialog});

	$("a.dialogLauncher").click(clickDialog);
  $("div#content").show();
});