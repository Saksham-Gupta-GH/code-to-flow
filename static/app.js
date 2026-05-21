(function () {
  const codeInput = document.getElementById('code-input');
  const generateBtn = document.getElementById('generate-btn');
  const statusEl = document.getElementById('status');
  
  const asciiOutput = document.getElementById('ascii-output');
  const stepsOutput = document.getElementById('steps-output');
  const mermaidContainer = document.getElementById('mermaid-container');
  
  const copyMermaidBtn = document.getElementById('copy-mermaid-btn');
  const downloadSvgBtn = document.getElementById('download-svg-btn');
  
  const tabButtons = document.querySelectorAll('.tab-btn');
  const tabContents = document.querySelectorAll('.tab-content');

  // Handle Tab Switching
  tabButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      const tabId = btn.dataset.tab;
      
      // Update buttons
      tabButtons.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      
      // Update contents
      tabContents.forEach(content => {
        content.classList.remove('active');
        if (content.id === `tab-${tabId}`) {
          content.classList.add('active');
        }
      });
    });
  });

  async function generateFlowchart() {
    const code = codeInput.value || '';

    // Reset UI states
    statusEl.textContent = '';
    statusEl.classList.remove('error');
    
    // Disable actions
    copyMermaidBtn.setAttribute('disabled', 'true');
    copyMermaidBtn.removeAttribute('data-code');
    downloadSvgBtn.setAttribute('disabled', 'true');
    downloadSvgBtn.removeAttribute('data-svg');

    if (!code.trim()) {
      statusEl.textContent = 'Please paste some code first.';
      statusEl.classList.add('error');
      return;
    }

    generateBtn.disabled = true;
    statusEl.textContent = 'Extracting control flow...';
    
    mermaidContainer.innerHTML = `
      <div class="loading-state">
        <div class="spinner"></div>
        <p>Drawing your interactive flowchart...</p>
      </div>
    `;

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
        mermaidContainer.innerHTML = `
          <div class="empty-state">
            <div class="empty-state-icon">⚠️</div>
            <p>Generation failed: ${message}</p>
          </div>
        `;
        return;
      }

      // 1. Render ASCII Fallback
      if (data.ascii) {
        asciiOutput.textContent = data.ascii;
      } else {
        asciiOutput.innerHTML = `<div class="empty-state"><p>No ASCII flowchart generated.</p></div>`;
      }

      // 2. Render JSON Steps
      stepsOutput.textContent = JSON.stringify(data.steps || [], null, 2);

      // 3. Render Visual Mermaid Flowchart
      const mermaidCode = data.mermaid;
      if (mermaidCode) {
        copyMermaidBtn.removeAttribute('disabled');
        copyMermaidBtn.dataset.code = mermaidCode;
        
        try {
          const uniqueId = `mermaid-${Date.now()}`;
          // Use the global Mermaid object initialized in index.html
          const { svg } = await window.mermaid.render(uniqueId, mermaidCode);
          mermaidContainer.innerHTML = svg;
          
          // Enable download
          downloadSvgBtn.removeAttribute('disabled');
          downloadSvgBtn.dataset.svg = svg;
        } catch (renderError) {
          console.error("Mermaid Render Error:", renderError);
          mermaidContainer.innerHTML = `
            <div class="error-state">
              <div class="empty-state-icon">⚠️</div>
              <p>Could not render graphical diagram. Raw Mermaid code is copyable.</p>
              <pre class="raw-mermaid-fallback">${escapeHtml(mermaidCode)}</pre>
            </div>
          `;
        }
      } else {
        mermaidContainer.innerHTML = `
          <div class="empty-state">
            <div class="empty-state-icon">📊</div>
            <p>No visual diagram returned.</p>
          </div>
        `;
      }

      statusEl.textContent = 'Done.';
    } catch (err) {
      console.error(err);
      statusEl.textContent = 'Unexpected error, please try again.';
      statusEl.classList.add('error');
      mermaidContainer.innerHTML = `
        <div class="empty-state">
          <div class="empty-state-icon">⚠️</div>
          <p>Unexpected communication error occurred.</p>
        </div>
      `;
    } finally {
      generateBtn.disabled = false;
    }
  }

  function escapeHtml(string) {
    return String(string)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }

  // Bind Actions
  generateBtn.addEventListener('click', generateFlowchart);

  copyMermaidBtn.addEventListener('click', () => {
    const code = copyMermaidBtn.dataset.code;
    if (code) {
      navigator.clipboard.writeText(code).then(() => {
        const originalText = copyMermaidBtn.textContent;
        copyMermaidBtn.textContent = 'Copied!';
        copyMermaidBtn.classList.add('success');
        setTimeout(() => {
          copyMermaidBtn.textContent = originalText;
          copyMermaidBtn.classList.remove('success');
        }, 1500);
      });
    }
  });

  downloadSvgBtn.addEventListener('click', () => {
    const svgContent = downloadSvgBtn.dataset.svg;
    if (svgContent) {
      const blob = new Blob([svgContent], { type: 'image/svg+xml' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'flowchart.svg';
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    }
  });

  // Allow Cmd/Ctrl+Enter to trigger generation
  codeInput.addEventListener('keydown', (event) => {
    if ((event.metaKey || event.ctrlKey) && event.key === 'Enter') {
      event.preventDefault();
      generateFlowchart();
    }
  });
})();
