const onAuthFinished = async (googleUser) => {
    const csrfToken = JSON.parse(document.getElementById('csrf_token').textContent);

    const loc = window.location.href;
    const id_token = googleUser.getAuthResponse().id_token;

    const response = await fetch(loc, {
        method: 'POST',
        headers: {
            'X-CSRFToken': csrfToken,
            'Accept': 'application/json',
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 'token': id_token }),
    });

    if (!response.ok) {
        onAuthError(response);
        return
    }

    const json_data = await response.json();
    if (json_data.success) {
        const next = JSON.parse(document.getElementById('next').textContent);

        window.location = next;
        return
    }

    // If we didn't have a success, we'll have an error here
    onAuthError(json_data.error);
}

const onAuthError = (error) => {
    showAuthElements();

    if (error.error == "popup_closed_by_user") {
        console.log("popup was closed");
        return
    }

    console.log("error when executing Google sign-in: ", error);
    alert("There was an issue when signing into Google. Please contact Technology.");
};

const hideAuthElements = () => {
    document.querySelectorAll(".hide-during-sign-in").forEach(elem => {
        elem.style.display = "none";
    });

    document.querySelectorAll(".show-during-sign-in").forEach(elem => {
        elem.style.display = "block";
    });
}

const showAuthElements = () => {
    document.querySelectorAll(".hide-during-sign-in").forEach(elem => {
        elem.style.display = "block";
    });

    document.querySelectorAll(".show-during-sign-in").forEach(elem => {
        elem.style.display = "none";
    });
}

setup = () => {
    gapi.load('auth2', function () {
        const auth_data = JSON.parse(document.getElementById('auth_data').textContent);

        auth2 = gapi.auth2.init({
            client_id: auth_data["client_id"],
            hosted_domain: auth_data["hosted_domain"]
        });

        // Attach handlers for both launching auth through Google
        // and running our auth start for page modification
        document.querySelectorAll(".google-sign-in").forEach(elem => {
            auth2.attachClickHandler(elem, {}, onAuthFinished, onAuthError);

            elem.addEventListener("click", (evt) => {
                hideAuthElements();
            });
        });
    });
}

const ready = (callback) => {
    if (document.readyState != "loading")
        callback();
    else
        document.addEventListener("DOMContentLoaded", callback);
}

ready(() => {
    setup();
});

