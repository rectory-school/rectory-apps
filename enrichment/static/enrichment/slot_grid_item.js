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

            if (currentOptionId) {
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

            elem.replaceChildren(i, space, currentSelectionSpan);
        }

        elem.addEventListener('click', (evt) => {
            if (editing || saving) {
                return;
            }

            editing = true;

            const getLabel = (label) => {
                const out = document.createElement("option");
                out.innerText = label
                out.setAttribute("disabled", "disabled");
                return out;
            }

            const getSpacer = () => {
                return getLabel("---");
            }

            const select = document.createElement('select');
            select.setAttribute("name", "optionId");
            const noSelection = document.createElement('option');
            noSelection.value = null
            noSelection.innerText = "Unassigned";
            select.appendChild(noSelection);
            select.appendChild(getSpacer())

            preferredOptions.forEach((opt) => {
                const optionElem = document.createElement('option');
                optionElem.value = opt.id;
                optionElem.innerText = opt.display;

                if (currentOptionId === opt.id) {
                    optionElem.setAttribute("selected", "selected");
                }
                select.appendChild(optionElem);
            });

            select.appendChild(getSpacer());

            remainingOptions.forEach((opt) => {
                const optionElem = document.createElement('option');
                optionElem.value = opt.id;
                optionElem.innerText = opt.display;

                if (currentOptionId === opt.id) {
                    optionElem.setAttribute("selected", "selected");
                }
                select.appendChild(optionElem);
            });

            elem.replaceChildren(select);
            select.addEventListener('change', async (evt) => {
                saving = true;

                const newOptionId = mustInt(select.value);

                const postData = {
                    slot_id: slotId,
                    student_id: studentId,
                    option_id: newOptionId,
                }

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

                currentOptionId = newOptionId;
                reset();
            });
        });
    });
});
