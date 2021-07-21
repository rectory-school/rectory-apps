$(document).ready(function () {
    const folderHrefPrefix = JSON.parse(document.getElementById('folder_id_prefix').textContent);

    folderLinkSelector = 'a[href^="#' + folderHrefPrefix + '"]';
    let folderLinks = $(folderLinkSelector);

    folderLinks.each(function (i, elem) {
        $(elem).on('click', function (event) {
            event.preventDefault();

            let href = $(elem).attr('href');
            $(href).modal('show');
        });
    })
});