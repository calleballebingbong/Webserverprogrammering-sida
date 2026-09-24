document.querySelectorAll('.toggle-comments').forEach(button => {
    button.addEventListener('click', () => {
        const entryCard = button.closest('.entry-card');
        const panel = entryCard.querySelector('.comment-panel');

        if (!panel) return;

        const isHidden = panel.classList.toggle('hidden');
        button.textContent = isHidden ? 'Show Comments' : 'Hide Comments';
        button.setAttribute('aria-expanded', String(!isHidden));
    });
});
