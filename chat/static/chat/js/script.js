function copyPassword() {
    var copyText = document.getElementById("passwordInput");
    copyText.select();
    copyText.setSelectionRange(0, 99999); // Для мобільних пристроїв

    navigator.clipboard.writeText(copyText.value)

    alert("Пароль скопійовано: " + copyText.value);
}