const mustInt = (val) => {
    if (val === "") {
        return null;
    }

    if (val === "null") {
        return null;
    }

    const out = Number.parseInt(val);
    if (Number.isNaN(out)) {
        throw new Error(`Could not parse '${val}' as int`);
    }

    return out;
}

const mustInts = (val) => {
    if (val === "") {
        return [];
    }
    const items = val.split(",")

    return items.map((item) => mustInt(item));
}
document.addEventListener('DOMContentLoaded', () => {
    const optionsById = JSON.parse(document.getElementById('all-options').textContent);
    const assignURL = JSON.parse(document.getElementById('assign-url').textContent);
    const csrfValue = JSON.parse(document.getElementById('csrf-token').textContent);

    document.querySelectorAll(".slot-grid-item.editable").forEach((elem) => {
        let editing = false;
        let saving = false;

        const data = elem.dataset;

        const slotId = mustInt(data.slotId);
        const studentId = mustInt(data.studentId);
        let currentOptionId = mustInt(data.currentItemId);
        const preferredOptionIds = mustInts(data.preferredOptions);
        const remainingOptionIds = mustInts(data.remainingOptions);
        const preferredOptions = preferredOptionIds.map((id) => optionsById[id]);
        const remainingOptions = remainingOptionIds.map((id) => optionsById[id]);

        const currentSelectionSpan = elem.getElementsByClassName("current-selection")[0];

        const reset = () => {
            editing = false;
            saving = false;

            if (currentOptionId && currentOptionId != 0) {
                const currentOption = optionsById[currentOptionId];
                currentSelectionSpan.innerText = currentOption.display;
            } else {
                currentSelectionSpan.innerText = "No assignment";
            }

            currentSelectionSpan.innerText += " ";

            const i = document.createElement("i")
            i.classList.add("fa-solid");
            i.classList.add("fa-edit");
            const space = document.createElement("span");
            space.innerText = " "
            elem.classList.remove("saving");
            elem.replaceChildren(i, space, currentSelectionSpan);
        }

        elem.addEventListener('click', (evt) => {
            if (editing || saving) {
                return;
            }

            editing = true;

            const selectOptions = [
                {
                    "id": 0,
                    "text": "Unassigned",
                },
                {
                    "text": "Preferred",
                    "children": preferredOptions.map((item) => ({ id: item.id, text: item.display, selected: item.id === currentOptionId }))
                },
                {
                    "text": "Other",
                    "children": remainingOptions.map((item) => ({ id: item.id, text: item.display, selected: item.id === currentOptionId }))
                }
            ]

            const placeholder = document.createElement('select');
            elem.replaceChildren(placeholder);
            $(placeholder).select2({
                data: selectOptions
            });
            $(placeholder).select2('open');
            $(placeholder).on('select2:close', () => reset());
            $(placeholder).on('select2:select', async (selectEvt) => {
                const id = selectEvt.params.data.id;

                saving = true;
                elem.classList.add("saving");

                const postData = {
                    slot_id: slotId,
                    student_id: studentId,
                    option_id: id,
                }

                const spinner = document.createElement("i");
                spinner.classList.add("fa-solid", "fa-spinner", "fa-spin");

                elem.replaceChildren(spinner);

                const resp = await fetch(assignURL, {
                    method: 'POST',
                    mode: 'cors',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': csrfValue,
                    },
                    body: JSON.stringify(postData),
                });

                const respData = await resp.json()
                if (!respData.success) {
                    alert(`Something went wrong during save: ${respData.code}`);
                    console.log(respData);
                    reset();
                    return;
                }

                currentOptionId = id;
                reset();
            });
        });
    });
});
