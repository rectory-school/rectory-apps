$(document).ready(function () {
    $(".enable-icon-sort").click(function (e) {
        e.preventDefault();

        $(".hide-during-sort").hide();
        $(".show-during-sort").show();

        $(".icons").sortable();
        $(".icons").disableSelection();
    });

    $(".save-icon-order").click(function (e) {
        e.preventDefault();

        $(".icons").sortable("disable");
        $(".icons").disableSelection("disable");

        $(".hide-during-sort").show();
        $(".show-during-sort").hide();

        $(".icons a").each(function (i, e) {
            console.log(i, e);
        })
    });

})