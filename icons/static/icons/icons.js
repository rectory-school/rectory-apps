$(document).ready(function () {
    $(".enable-icon-sort").click(function (e) {
        e.preventDefault();

        $(".hide-during-sort").hide();
        $(".show-during-sort").show();

        $(".sortable").sortable();
        $(".sortable").disableSelection();
    });

    $(".save-icon-order").click(function (e) {
        e.preventDefault();

        $(".hide-during-sort").hide();
        $(".show-during-sort").hide();
        $(".hide-during-sort-saving").hide();
        $(".show-during-sort-saving").show();

        var postData = []

        $(".icons a").each(function (i, e) {
            elem = $(e);

            var sortId = elem.data("sortid");
            var href = elem.attr("href");

            if (href != "") {
                postData.push(sortId);
            }
        });

        const sortURL = JSON.parse(document.getElementById('sort_url').textContent);
        const csrfToken = JSON.parse(document.getElementById('csrf_token').textContent);

        $('.icons').hide();

        $.ajax({
            url: sortURL,
            type: 'post',
            data: { 'sort': postData },
            headers: { 'X-CSRFToken': csrfToken },
            success: function (data) {
                location.reload();
            },
            error: function () {
                $("#data-save-progerss").text("Error when saving positions, please check application logs and reload to try again");
            },
        });
    });

    $(".progressbar-spinner").progressbar({
        value: false,
    });

});