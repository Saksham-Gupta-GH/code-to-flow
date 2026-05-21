(function () {
  const codeInput = document.getElementById('code-input');
  const generateBtn = document.getElementById('generate-btn');
  const statusEl = document.getElementById('status');
  const asciiOutput = document.getElementById('ascii-output');
  const stepsOutput = document.getElementById('steps-output');
  const stepsSection = document.getElementById('steps-section');
  const toggleStepsBtn = document.getElementById('toggle-steps-btn');

  async function generateFlowchart() {
    const code = codeInput.value || '';

    statusEl.textContent = '';
    statusEl.classList.remove('error');
    asciiOutput.textContent = '';
    stepsOutput.textContent = '';

    if (!code.trim()) {
      statusEl.textContent = 'Please paste some code first.';
      statusEl.classList.add('error');
      return;
    }

    generateBtn.disabled = true;
    statusEl.textContent = 'Generating flowchart...';

    try {
      const response = await fetch('/api/flowchart', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ code }),
      });

      const data = await response.json();

      if (!response.ok) {
        const message = data && data.error ? data.error : 'Request failed.';
        statusEl.textContent = message;
        statusEl.classList.add('error');
        return;
      }

      asciiOutput.textContent = data.ascii || '';
      stepsOutput.textContent = JSON.stringify(data.steps || [], null, 2);
      statusEl.textContent = 'Done.';
    } catch (err) {
      console.error(err);
      statusEl.textContent = 'Unexpected error, please try again.';
      statusEl.classList.add('error');
    } finally {
      generateBtn.disabled = false;
    }
  }

  generateBtn.addEventListener('click', generateFlowchart);

  // Toggle visibility of normalized steps
  if (toggleStepsBtn && stepsSection) {
    toggleStepsBtn.addEventListener('click', () => {
      const isHidden = stepsSection.classList.toggle('hidden');
      toggleStepsBtn.textContent = isHidden
        ? 'Show normalized steps'
        : 'Hide normalized steps';
    });
  }

  // Allow Cmd/Ctrl+Enter to trigger generation
  codeInput.addEventListener('keydown', (event) => {
    if ((event.metaKey || event.ctrlKey) && event.key === 'Enter') {
      event.preventDefault();
      generateFlowchart();
    }
  });
})();
