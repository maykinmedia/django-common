document.querySelectorAll('.mkn-admin-login-options__local-user-login').forEach(details => {
  details.addEventListener('toggle', () => {
    if (details.open) {
      const inputToFocus = details.querySelector('input[autofocus]');
      if (inputToFocus) inputToFocus.focus();
    }
  });
});
