document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll(".link-form-post").forEach((elem) => {
        elem.addEventListener('click', (evt) => {
            evt.preventDefault();

            const csrfValue = JSON.parse(document.getElementById('csrf-token').textContent);

            const form = document.createElement('form');
            form.setAttribute("method", "POST");
            form.setAttribute("action", evt.target.href);

            csrf = document.createElement("input");
            csrf.setAttribute("type", "hidden");
            csrf.value = csrfValue
            csrf.name = "csrfmiddlewaretoken"
            form.appendChild(csrf);

            document.body.appendChild(form);
            form.submit();
        });
    })
});