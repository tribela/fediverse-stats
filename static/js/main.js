const form = document.querySelector('form');
const buttonOk = document.querySelector('button#ok');
const inputAcct = document.querySelector('input[name=acct]')

function submit(event) {
    event.preventDefault();
    buttonOk.disabled = true;
    const acct = inputAcct.value;

    window.location.href = `/${acct}`;
}

buttonOk.addEventListener('click', submit);
form.addEventListener('submit', submit);
