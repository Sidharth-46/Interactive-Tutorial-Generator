function completeStep(tutorialId, stepId, btn) {
    fetch(`/tutorial/${tutorialId}/step/${stepId}/complete`, {method: 'POST'})
    .then(res => res.json())
    .then(data => {
        if(data.success){
            btn.style.display = 'none';
            let completedSpan = document.createElement('span');
            completedSpan.style.color = 'green';
            completedSpan.style.fontWeight = 'bold';
            completedSpan.innerText = '✅ Completed';
            btn.parentNode.insertBefore(completedSpan, btn.nextSibling);
            let undoBtn = document.createElement('button');
            undoBtn.className = 'undo-btn';
            undoBtn.setAttribute('aria-label', 'Undo complete for this step');
            undoBtn.innerText = 'Undo';
            undoBtn.onclick = function() { undoStep(tutorialId, stepId, undoBtn); };
            btn.parentNode.insertBefore(undoBtn, completedSpan.nextSibling);
            updateProgressBar();
        } else {
            showError(btn);
        }
    })
    .catch(() => {
        showError(btn);
    });
}

function undoStep(tutorialId, stepId, btn) {
    fetch(`/tutorial/${tutorialId}/step/${stepId}/incomplete`, {method: 'POST'})
    .then(res => res.json())
    .then(data => {
        if(data.success){
            // Remove the completed span and undo button, show or create the complete button again
            let li = btn.closest('li');
            if(li) {
                let completedSpan = li.querySelector('span');
                if(completedSpan) completedSpan.remove();
                btn.remove();
                let completeBtn = li.querySelector('.complete-btn');
                if(completeBtn) {
                    completeBtn.style.display = '';
                } else {
                    // Create the button if it doesn't exist (e.g., after page reload)
                    completeBtn = document.createElement('button');
                    completeBtn.className = 'complete-btn';
                    completeBtn.setAttribute('aria-label', 'Mark step as complete');
                    completeBtn.innerText = 'Mark Complete';
                    completeBtn.onclick = function() { completeStep(tutorialId, stepId, completeBtn); };
                    // Insert before any error message span if present, else at end
                    let errorSpan = li.querySelector('.error-message');
                    if(errorSpan) {
                        li.insertBefore(completeBtn, errorSpan);
                    } else {
                        li.appendChild(completeBtn);
                    }
                }
            }
            updateProgressBar();
        }
    });
}

function showError(btn) {
    let errorSpan = btn.parentNode.querySelector('.error-message');
    if(errorSpan) errorSpan.style.display = 'inline';
}

function updateProgressBar() {
    // Count only spans that actually show '✅ Completed' in the steps list
    const stepsList = document.querySelector('ol');
    let completedCount = 0;
    if (stepsList) {
        completedCount = Array.from(stepsList.querySelectorAll('span')).filter(span => span.textContent.trim() === '✅ Completed').length;
    }
    const totalSteps = stepsList ? stepsList.querySelectorAll('li').length : 0;
    const percent = totalSteps > 0 ? (completedCount / totalSteps * 100) : 0;
    const bar = document.querySelector('.progress-bar');
    const countText = document.querySelector('.progress-count');
    if(bar) bar.style.width = percent + '%';
    if(countText) countText.textContent = `${completedCount} / ${totalSteps} steps completed`;
}

document.addEventListener('DOMContentLoaded', function() {
    updateProgressBar(); // Ensure progress bar is correct on page load
});
