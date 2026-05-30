"""
HTML/JS Snippets Skill for llama.cpp Coder
──────────────────────────────────────────
Provides ready-to-use HTML and JavaScript snippets for common web dev scenarios.
No dependencies, no API keys. Fast and lightweight.

Usage:
  execute(situation="form validation", framework="vanilla", output="combined")
  execute(category="ui_components", type="modal")
  execute(search="responsive table")
"""

SNIPPETS_DB = {
    # ──────────────────────────────────────────────────────────────────
    # UI COMPONENTS
    # ──────────────────────────────────────────────────────────────────
    "ui_components": {
        "modal": {
            "description": "Accessible modal dialog with backdrop",
            "html": """
<div id="modal" class="modal" role="dialog" aria-modal="true" aria-labelledby="modal-title">
  <div class="modal-content">
    <div class="modal-header">
      <h2 id="modal-title">Modal Title</h2>
      <button class="modal-close" aria-label="Close modal">&times;</button>
    </div>
    <div class="modal-body">
      <p>Modal content goes here</p>
    </div>
    <div class="modal-footer">
      <button class="btn-secondary">Cancel</button>
      <button class="btn-primary">Confirm</button>
    </div>
  </div>
</div>
""",
            "css": """
.modal {
  display: none;
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.5);
  z-index: 1000;
  align-items: center;
  justify-content: center;
}
.modal.active {
  display: flex;
}
.modal-content {
  background: white;
  border-radius: 8px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
  max-width: 500px;
  width: 90%;
  max-height: 90vh;
  overflow-y: auto;
}
.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  border-bottom: 1px solid #e0e0e0;
}
.modal-body {
  padding: 20px;
}
.modal-footer {
  padding: 20px;
  border-top: 1px solid #e0e0e0;
  display: flex;
  gap: 10px;
  justify-content: flex-end;
}
.modal-close {
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: #666;
}
""",
            "javascript": """
const modal = document.getElementById('modal');
const closeBtn = document.querySelector('.modal-close');

function openModal() {
  modal.classList.add('active');
  document.body.style.overflow = 'hidden';
}

function closeModal() {
  modal.classList.remove('active');
  document.body.style.overflow = '';
}

closeBtn.addEventListener('click', closeModal);
modal.addEventListener('click', (e) => {
  if (e.target === modal) closeModal();
});

// Keyboard: Escape to close
document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape' && modal.classList.contains('active')) {
    closeModal();
  }
});
"""
        },
        "dropdown_menu": {
            "description": "Accessible dropdown/select menu",
            "html": """
<div class="dropdown">
  <button class="dropdown-toggle" aria-haspopup="true" aria-expanded="false">
    Menu <span class="arrow">▼</span>
  </button>
  <ul class="dropdown-menu" role="menu">
    <li><a href="#" role="menuitem">Option 1</a></li>
    <li><a href="#" role="menuitem">Option 2</a></li>
    <li><hr></li>
    <li><a href="#" role="menuitem">Option 3</a></li>
  </ul>
</div>
""",
            "css": """
.dropdown {
  position: relative;
  display: inline-block;
}
.dropdown-toggle {
  padding: 10px 15px;
  background: #007bff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
}
.dropdown-toggle:hover {
  background: #0056b3;
}
.dropdown-menu {
  display: none;
  position: absolute;
  top: 100%;
  left: 0;
  background: white;
  border: 1px solid #ddd;
  border-radius: 4px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  list-style: none;
  margin: 8px 0 0 0;
  padding: 0;
  min-width: 200px;
  z-index: 100;
}
.dropdown-menu.active {
  display: block;
}
.dropdown-menu li {
  margin: 0;
}
.dropdown-menu a {
  display: block;
  padding: 10px 15px;
  color: #333;
  text-decoration: none;
}
.dropdown-menu a:hover {
  background: #f5f5f5;
}
.dropdown-menu hr {
  margin: 5px 0;
  border: none;
  border-top: 1px solid #ddd;
}
""",
            "javascript": """
const toggle = document.querySelector('.dropdown-toggle');
const menu = document.querySelector('.dropdown-menu');

toggle.addEventListener('click', () => {
  menu.classList.toggle('active');
  toggle.setAttribute('aria-expanded', menu.classList.contains('active'));
});

document.addEventListener('click', (e) => {
  if (!e.target.closest('.dropdown')) {
    menu.classList.remove('active');
    toggle.setAttribute('aria-expanded', 'false');
  }
});
"""
        },
        "toast_notification": {
            "description": "Toast/snackbar notification system",
            "html": """
<div id="toast-container"></div>
""",
            "css": """
#toast-container {
  position: fixed;
  top: 20px;
  right: 20px;
  z-index: 2000;
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.toast {
  background: white;
  padding: 16px;
  border-radius: 4px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  display: flex;
  align-items: center;
  gap: 12px;
  animation: slideIn 0.3s ease-out;
  min-width: 300px;
}
.toast.success {
  border-left: 4px solid #28a745;
}
.toast.error {
  border-left: 4px solid #dc3545;
}
.toast.warning {
  border-left: 4px solid #ffc107;
}
.toast.info {
  border-left: 4px solid #17a2b8;
}
.toast-close {
  margin-left: auto;
  background: none;
  border: none;
  cursor: pointer;
  font-size: 18px;
  color: #999;
}
@keyframes slideIn {
  from {
    transform: translateX(400px);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}
""",
            "javascript": """
function showToast(message, type = 'info', duration = 3000) {
  const container = document.getElementById('toast-container');
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.innerHTML = `
    <span>${message}</span>
    <button class="toast-close" aria-label="Close">&times;</button>
  `;
  
  container.appendChild(toast);
  
  toast.querySelector('.toast-close').addEventListener('click', () => {
    toast.remove();
  });
  
  if (duration > 0) {
    setTimeout(() => toast.remove(), duration);
  }
}

// Usage: showToast('Success!', 'success');
"""
        },
        "tabs": {
            "description": "Tabbed interface component",
            "html": """
<div class="tabs">
  <div class="tab-buttons" role="tablist">
    <button class="tab-btn active" role="tab" aria-selected="true" aria-controls="panel-1">Tab 1</button>
    <button class="tab-btn" role="tab" aria-selected="false" aria-controls="panel-2">Tab 2</button>
    <button class="tab-btn" role="tab" aria-selected="false" aria-controls="panel-3">Tab 3</button>
  </div>
  <div class="tab-panels">
    <div id="panel-1" class="tab-panel active" role="tabpanel">Content 1</div>
    <div id="panel-2" class="tab-panel" role="tabpanel">Content 2</div>
    <div id="panel-3" class="tab-panel" role="tabpanel">Content 3</div>
  </div>
</div>
""",
            "css": """
.tabs {
  border: 1px solid #ddd;
  border-radius: 4px;
  overflow: hidden;
}
.tab-buttons {
  display: flex;
  border-bottom: 2px solid #ddd;
  background: #f9f9f9;
}
.tab-btn {
  flex: 1;
  padding: 12px;
  background: none;
  border: none;
  cursor: pointer;
  font-size: 14px;
  border-bottom: 3px solid transparent;
  transition: all 0.3s;
}
.tab-btn.active {
  border-bottom-color: #007bff;
  color: #007bff;
  font-weight: 500;
}
.tab-btn:hover {
  background: #f0f0f0;
}
.tab-panels {
  position: relative;
}
.tab-panel {
  display: none;
  padding: 20px;
  animation: fadeIn 0.3s;
}
.tab-panel.active {
  display: block;
}
@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}
""",
            "javascript": """
const tabButtons = document.querySelectorAll('.tab-btn');
const tabPanels = document.querySelectorAll('.tab-panel');

tabButtons.forEach((btn, idx) => {
  btn.addEventListener('click', () => {
    tabButtons.forEach(b => {
      b.classList.remove('active');
      b.setAttribute('aria-selected', 'false');
    });
    tabPanels.forEach(p => p.classList.remove('active'));
    
    btn.classList.add('active');
    btn.setAttribute('aria-selected', 'true');
    tabPanels[idx].classList.add('active');
  });
});
"""
        }
    },

    # ──────────────────────────────────────────────────────────────────
    # FORMS & VALIDATION
    # ──────────────────────────────────────────────────────────────────
    "forms": {
        "form_validation": {
            "description": "Client-side form validation with error messages",
            "html": """
<form id="myForm" novalidate>
  <div class="form-group">
    <label for="email">Email:</label>
    <input type="email" id="email" name="email" required>
    <span class="error-msg"></span>
  </div>
  
  <div class="form-group">
    <label for="password">Password:</label>
    <input type="password" id="password" name="password" required minlength="8">
    <span class="error-msg"></span>
  </div>
  
  <div class="form-group">
    <label for="confirm">Confirm Password:</label>
    <input type="password" id="confirm" name="confirm" required>
    <span class="error-msg"></span>
  </div>
  
  <button type="submit" class="btn-primary">Submit</button>
</form>
""",
            "javascript": """
const form = document.getElementById('myForm');

function validateField(field) {
  const errorMsg = field.nextElementSibling;
  let isValid = true;
  let message = '';
  
  if (!field.value.trim()) {
    isValid = false;
    message = 'This field is required';
  } else if (field.type === 'email' && !isValidEmail(field.value)) {
    isValid = false;
    message = 'Enter a valid email';
  } else if (field.name === 'password' && field.value.length < 8) {
    isValid = false;
    message = 'Password must be at least 8 characters';
  } else if (field.name === 'confirm' && field.value !== form.password.value) {
    isValid = false;
    message = 'Passwords do not match';
  }
  
  field.classList.toggle('is-invalid', !isValid);
  errorMsg.textContent = message;
  return isValid;
}

function isValidEmail(email) {
  return /^[^\\s@]+@[^\\s@]+\\.[^\\s@]+$/.test(email);
}

form.querySelectorAll('input').forEach(field => {
  field.addEventListener('blur', () => validateField(field));
});

form.addEventListener('submit', (e) => {
  e.preventDefault();
  const fields = form.querySelectorAll('input[required]');
  let allValid = true;
  
  fields.forEach(field => {
    if (!validateField(field)) allValid = false;
  });
  
  if (allValid) {
    console.log('Form valid!', new FormData(form));
    // Submit here
  }
});
""",
            "css": """
.form-group {
  margin-bottom: 16px;
  display: flex;
  flex-direction: column;
}
label {
  font-weight: 500;
  margin-bottom: 6px;
  color: #333;
}
input {
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
  transition: border-color 0.3s;
}
input:focus {
  outline: none;
  border-color: #007bff;
  box-shadow: 0 0 0 3px rgba(0, 123, 255, 0.1);
}
input.is-invalid {
  border-color: #dc3545;
}
.error-msg {
  color: #dc3545;
  font-size: 12px;
  margin-top: 4px;
  min-height: 16px;
}
"""
        },
        "file_upload": {
            "description": "Drag-and-drop file upload with preview",
            "html": """
<div class="file-upload" id="fileUpload">
  <div class="upload-area">
    <input type="file" id="fileInput" multiple accept="image/*" hidden>
    <p>📁 Drag files here or <a href="#" id="selectBtn">click to upload</a></p>
  </div>
  <div id="previewContainer" class="preview-container"></div>
</div>
""",
            "css": """
.file-upload {
  padding: 20px;
}
.upload-area {
  border: 2px dashed #007bff;
  border-radius: 4px;
  padding: 40px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s;
}
.upload-area:hover {
  background: #f0f7ff;
  border-color: #0056b3;
}
.upload-area.dragover {
  background: #e7f3ff;
  border-color: #0056b3;
}
.preview-container {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(100px, 1fr));
  gap: 10px;
  margin-top: 20px;
}
.preview-item {
  position: relative;
  border-radius: 4px;
  overflow: hidden;
  aspect-ratio: 1;
}
.preview-item img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.preview-item .remove {
  position: absolute;
  top: 5px;
  right: 5px;
  background: #dc3545;
  color: white;
  border: none;
  border-radius: 50%;
  width: 28px;
  height: 28px;
  cursor: pointer;
}
""",
            "javascript": """
const fileUpload = document.getElementById('fileUpload');
const fileInput = document.getElementById('fileInput');
const uploadArea = fileUpload.querySelector('.upload-area');
const previewContainer = document.getElementById('previewContainer');
const selectBtn = document.getElementById('selectBtn');

selectBtn.addEventListener('click', (e) => {
  e.preventDefault();
  fileInput.click();
});

['dragenter', 'dragover', 'dragleave', 'drop'].forEach(evt => {
  fileUpload.addEventListener(evt, (e) => {
    e.preventDefault();
    e.stopPropagation();
  });
});

['dragenter', 'dragover'].forEach(evt => {
  fileUpload.addEventListener(evt, () => {
    uploadArea.classList.add('dragover');
  });
});

['dragleave', 'drop'].forEach(evt => {
  fileUpload.addEventListener(evt, () => {
    uploadArea.classList.remove('dragover');
  });
});

fileUpload.addEventListener('drop', (e) => {
  const files = e.dataTransfer.files;
  fileInput.files = files;
  handleFiles(files);
});

fileInput.addEventListener('change', (e) => {
  handleFiles(e.target.files);
});

function handleFiles(files) {
  previewContainer.innerHTML = '';
  
  Array.from(files).forEach((file, idx) => {
    const reader = new FileReader();
    reader.onload = (e) => {
      const item = document.createElement('div');
      item.className = 'preview-item';
      item.innerHTML = `
        <img src="${e.target.result}" alt="preview">
        <button class="remove" data-idx="${idx}">&times;</button>
      `;
      previewContainer.appendChild(item);
    };
    reader.readAsDataURL(file);
  });
}
"""
        }
    },

    # ──────────────────────────────────────────────────────────────────
    # DATA DISPLAY
    # ──────────────────────────────────────────────────────────────────
    "data_display": {
        "responsive_table": {
            "description": "Responsive data table with sorting and filtering",
            "html": """
<div class="table-container">
  <div class="table-controls">
    <input type="text" id="searchInput" placeholder="Search..." class="search-box">
    <button id="sortBtn" class="sort-btn">Sort</button>
  </div>
  <table id="dataTable" class="data-table">
    <thead>
      <tr>
        <th>Name</th>
        <th>Email</th>
        <th>Status</th>
        <th>Date</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td>John Doe</td>
        <td>john@example.com</td>
        <td><span class="badge active">Active</span></td>
        <td>2024-01-15</td>
      </tr>
      <tr>
        <td>Jane Smith</td>
        <td>jane@example.com</td>
        <td><span class="badge inactive">Inactive</span></td>
        <td>2024-01-16</td>
      </tr>
    </tbody>
  </table>
</div>
""",
            "css": """
.table-container {
  padding: 20px;
}
.table-controls {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
}
.search-box {
  flex: 1;
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
}
.data-table {
  width: 100%;
  border-collapse: collapse;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}
.data-table thead {
  background: #f5f5f5;
}
.data-table th {
  padding: 12px;
  text-align: left;
  font-weight: 600;
  color: #333;
  border-bottom: 2px solid #ddd;
  cursor: pointer;
}
.data-table td {
  padding: 12px;
  border-bottom: 1px solid #eee;
}
.data-table tr:hover {
  background: #fafafa;
}
.badge {
  display: inline-block;
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 500;
}
.badge.active {
  background: #d4edda;
  color: #155724;
}
.badge.inactive {
  background: #f8d7da;
  color: #721c24;
}
@media (max-width: 768px) {
  .data-table {
    font-size: 12px;
  }
  .data-table th, .data-table td {
    padding: 8px;
  }
}
""",
            "javascript": """
const searchInput = document.getElementById('searchInput');
const table = document.getElementById('dataTable');
const rows = table.querySelectorAll('tbody tr');

searchInput.addEventListener('input', (e) => {
  const query = e.target.value.toLowerCase();
  
  rows.forEach(row => {
    const text = row.textContent.toLowerCase();
    row.style.display = text.includes(query) ? '' : 'none';
  });
});

document.getElementById('sortBtn').addEventListener('click', () => {
  const tbody = table.querySelector('tbody');
  const rowsArray = Array.from(tbody.querySelectorAll('tr'));
  
  rowsArray.sort((a, b) => {
    const aVal = a.querySelector('td').textContent;
    const bVal = b.querySelector('td').textContent;
    return aVal.localeCompare(bVal);
  });
  
  tbody.innerHTML = '';
  rowsArray.forEach(row => tbody.appendChild(row));
});
"""
        },
        "infinite_scroll": {
            "description": "Infinite scroll pagination for dynamic loading",
            "javascript": """
const container = document.getElementById('itemContainer');
let page = 1;
let isLoading = false;

async function loadMore() {
  if (isLoading) return;
  isLoading = true;
  
  try {
    const response = await fetch(`/api/items?page=${page}`);
    const data = await response.json();
    
    data.items.forEach(item => {
      const el = document.createElement('div');
      el.className = 'item';
      el.innerHTML = item.html;
      container.appendChild(el);
    });
    
    page++;
  } catch (err) {
    console.error('Load error:', err);
  } finally {
    isLoading = false;
  }
}

const observer = new IntersectionObserver((entries) => {
  if (entries[0].isIntersecting) {
    loadMore();
  }
});

const sentinel = document.createElement('div');
sentinel.id = 'scroll-sentinel';
container.appendChild(sentinel);
observer.observe(sentinel);
""",
            "html": """
<div id="itemContainer" class="item-container">
  <!-- Items loaded dynamically -->
</div>
"""
        },
        "pagination": {
            "description": "Simple pagination controls",
            "html": """
<div class="pagination">
  <button class="prev" id="prevBtn" aria-label="Previous page">« Prev</button>
  <div class="page-numbers" id="pageNumbers"></div>
  <button class="next" id="nextBtn" aria-label="Next page">Next »</button>
</div>
""",
            "css": """
.pagination {
  display: flex;
  align-items: center;
  gap: 10px;
  justify-content: center;
  margin: 20px 0;
}
.pagination button, .pagination a {
  padding: 8px 12px;
  border: 1px solid #ddd;
  background: white;
  cursor: pointer;
  border-radius: 4px;
  transition: all 0.3s;
}
.pagination button:hover:not(:disabled), 
.pagination a:hover {
  background: #007bff;
  color: white;
  border-color: #007bff;
}
.pagination button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
.page-numbers {
  display: flex;
  gap: 5px;
}
.page-num.active {
  background: #007bff;
  color: white;
  border-color: #007bff;
}
""",
            "javascript": """
const pageNumbers = document.getElementById('pageNumbers');
const prevBtn = document.getElementById('prevBtn');
const nextBtn = document.getElementById('nextBtn');
let currentPage = 1;
const totalPages = 10;

function renderPagination() {
  pageNumbers.innerHTML = '';
  
  for (let i = Math.max(1, currentPage - 2); i <= Math.min(totalPages, currentPage + 2); i++) {
    const btn = document.createElement('button');
    btn.textContent = i;
    btn.className = `page-num ${i === currentPage ? 'active' : ''}`;
    btn.addEventListener('click', () => goToPage(i));
    pageNumbers.appendChild(btn);
  }
  
  prevBtn.disabled = currentPage === 1;
  nextBtn.disabled = currentPage === totalPages;
}

function goToPage(page) {
  currentPage = Math.max(1, Math.min(page, totalPages));
  renderPagination();
  console.log('Load page:', currentPage);
}

prevBtn.addEventListener('click', () => goToPage(currentPage - 1));
nextBtn.addEventListener('click', () => goToPage(currentPage + 1));

renderPagination();
"""
        }
    },

    # ──────────────────────────────────────────────────────────────────
    # STATE MANAGEMENT
    # ──────────────────────────────────────────────────────────────────
    "state_management": {
        "simple_state_store": {
            "description": "Minimal state management system (no dependencies)",
            "javascript": """
class Store {
  constructor(initialState = {}) {
    this.state = initialState;
    this.listeners = [];
  }
  
  setState(updates) {
    this.state = { ...this.state, ...updates };
    this.notify();
  }
  
  getState() {
    return this.state;
  }
  
  subscribe(listener) {
    this.listeners.push(listener);
    return () => {
      this.listeners = this.listeners.filter(l => l !== listener);
    };
  }
  
  notify() {
    this.listeners.forEach(listener => listener(this.state));
  }
}

// Usage:
const store = new Store({ count: 0, user: null });

store.subscribe((state) => {
  console.log('State updated:', state);
  document.getElementById('count').textContent = state.count;
});

document.getElementById('incrementBtn').addEventListener('click', () => {
  const current = store.getState();
  store.setState({ count: current.count + 1 });
});
"""
        }
    },

    # ──────────────────────────────────────────────────────────────────
    # API & ASYNC
    # ──────────────────────────────────────────────────────────────────
    "api_patterns": {
        "fetch_with_loading": {
            "description": "Fetch data with loading indicator and error handling",
            "javascript": """
async function fetchData(url) {
  const container = document.getElementById('container');
  
  // Show loading
  container.innerHTML = '<div class="spinner">Loading...</div>';
  
  try {
    const response = await fetch(url);
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    
    const data = await response.json();
    
    container.innerHTML = '';
    data.forEach(item => {
      const el = document.createElement('div');
      el.className = 'item';
      el.innerHTML = `<h3>${item.title}</h3><p>${item.description}</p>`;
      container.appendChild(el);
    });
    
  } catch (err) {
    container.innerHTML = `<div class="error">⚠️ ${err.message}</div>`;
    console.error('Fetch error:', err);
  }
}

// Usage:
fetchData('/api/items');
"""
        },
        "api_request_class": {
            "description": "Reusable API client class with methods",
            "javascript": """
class ApiClient {
  constructor(baseUrl) {
    this.baseUrl = baseUrl;
  }
  
  async request(endpoint, options = {}) {
    const url = `${this.baseUrl}${endpoint}`;
    const config = {
      headers: { 'Content-Type': 'application/json' },
      ...options
    };
    
    const response = await fetch(url, config);
    if (!response.ok) throw new Error(`${response.status}`);
    
    return response.json();
  }
  
  get(endpoint) {
    return this.request(endpoint, { method: 'GET' });
  }
  
  post(endpoint, data) {
    return this.request(endpoint, { 
      method: 'POST',
      body: JSON.stringify(data)
    });
  }
  
  put(endpoint, data) {
    return this.request(endpoint, { 
      method: 'PUT',
      body: JSON.stringify(data)
    });
  }
  
  delete(endpoint) {
    return this.request(endpoint, { method: 'DELETE' });
  }
}

// Usage:
const api = new ApiClient('https://api.example.com');
api.get('/users').then(users => console.log(users));
api.post('/posts', { title: 'Hello' }).then(post => console.log(post));
"""
        }
    },

    # ──────────────────────────────────────────────────────────────────
    # UTILITIES & HELPERS
    # ──────────────────────────────────────────────────────────────────
    "utilities": {
        "debounce_throttle": {
            "description": "Debounce and throttle functions for performance",
            "javascript": """
// Debounce: Wait until user stops typing
function debounce(func, delay) {
  let timeout;
  return function(...args) {
    clearTimeout(timeout);
    timeout = setTimeout(() => func(...args), delay);
  };
}

// Throttle: Max once per interval
function throttle(func, interval) {
  let lastCall = 0;
  return function(...args) {
    const now = Date.now();
    if (now - lastCall >= interval) {
      func(...args);
      lastCall = now;
    }
  };
}

// Usage:
const searchInput = document.getElementById('search');
const debouncedSearch = debounce((val) => {
  console.log('Searching for:', val);
}, 300);

searchInput.addEventListener('input', (e) => {
  debouncedSearch(e.target.value);
});

// Throttle on scroll
window.addEventListener('scroll', throttle(() => {
  console.log('Scrolling');
}, 100));
"""
        },
        "local_storage_helper": {
            "description": "LocalStorage wrapper with expiration",
            "javascript": """
const Storage = {
  set(key, value, expirationMinutes = null) {
    const data = {
      value,
      expiration: expirationMinutes ? Date.now() + expirationMinutes * 60000 : null
    };
    localStorage.setItem(key, JSON.stringify(data));
  },
  
  get(key) {
    const item = localStorage.getItem(key);
    if (!item) return null;
    
    const data = JSON.parse(item);
    if (data.expiration && Date.now() > data.expiration) {
      localStorage.removeItem(key);
      return null;
    }
    
    return data.value;
  },
  
  remove(key) {
    localStorage.removeItem(key);
  },
  
  clear() {
    localStorage.clear();
  }
};

// Usage:
Storage.set('user', { name: 'John' }, 60); // 60 minute expiration
const user = Storage.get('user');
"""
        }
    }
}


def execute(**kwargs):
    """
    Execute the HTML/JS snippets skill.
    
    Parameters:
      category    - Category name (e.g., "ui_components", "forms")
      type        - Snippet type within category (e.g., "modal", "dropdown")
      search      - Free-text search across all snippets
      format      - Return format: "full" (all code), "combined" (HTML+CSS+JS), 
                    "html", "css", "javascript" (default: "combined")
      list        - If True, list all available categories and types
    """
    
    category = str(kwargs.get("category", "")).strip().lower()
    snippet_type = str(kwargs.get("type", "")).strip().lower()
    search_term = str(kwargs.get("search", "")).strip().lower()
    output_format = str(kwargs.get("format", "combined")).lower()
    list_only = bool(kwargs.get("list", False))

    # ──────────────────────────────────────────────────────────────────
    # LIST MODE
    # ──────────────────────────────────────────────────────────────────
    if list_only:
        lines = ["Available HTML/JS Snippets:\n"]
        for cat in SNIPPETS_DB:
            lines.append(f"\n📂 {cat.upper()}")
            for snippet_type_name in SNIPPETS_DB[cat]:
                desc = SNIPPETS_DB[cat][snippet_type_name].get("description", "")
                lines.append(f"  • {snippet_type_name}: {desc}")
        return "\n".join(lines)

    # ──────────────────────────────────────────────────────────────────
    # SEARCH MODE
    # ──────────────────────────────────────────────────────────────────
    if search_term:
        lines = [f"Search results for: '{search_term}'\n"]
        found = False
        
        for cat in SNIPPETS_DB:
            for snippet_name in SNIPPETS_DB[cat]:
                snippet = SNIPPETS_DB[cat][snippet_name]
                desc = snippet.get("description", "").lower()
                name = snippet_name.lower()
                
                if search_term in desc or search_term in name:
                    found = True
                    lines.append(f"\n[{cat}] {snippet_name}")
                    lines.append(f"  {snippet.get('description', '')}")
        
        if not found:
            return f"No snippets found matching '{search_term}'"
        
        return "\n".join(lines)

    # ──────────────────────────────────────────────────────────────────
    # RETRIEVE SPECIFIC SNIPPET
    # ──────────────────────────────────────────────────────────────────
    if not category or not snippet_type:
        return "Error: Both 'category' and 'type' required. Use list=True to see options."

    if category not in SNIPPETS_DB:
        return f"Error: Category '{category}' not found."

    if snippet_type not in SNIPPETS_DB[category]:
        return f"Error: Type '{snippet_type}' not found in '{category}'."

    snippet = SNIPPETS_DB[category][snippet_type]

    # ──────────────────────────────────────────────────────────────────
    # FORMAT OUTPUT
    # ──────────────────────────────────────────────────────────────────
    output = []
    output.append(f"📍 [{category}] {snippet_type}")
    output.append(f"   {snippet.get('description', '')}\n")

    if output_format == "html" and "html" in snippet:
        output.append("──── HTML ────\n")
        output.append(snippet["html"])

    elif output_format == "css" and "css" in snippet:
        output.append("──── CSS ────\n")
        output.append(snippet["css"])

    elif output_format == "javascript" and "javascript" in snippet:
        output.append("──── JAVASCRIPT ────\n")
        output.append(snippet["javascript"])

    else:  # combined or full
        if "html" in snippet:
            output.append("──── HTML ────\n")
            output.append(snippet["html"])

        if "css" in snippet:
            output.append("\n──── CSS ────\n")
            output.append(snippet["css"])

        if "javascript" in snippet:
            output.append("\n──── JAVASCRIPT ────\n")
            output.append(snippet["javascript"])

    return "\n".join(output)


# ──────────────────────────────────────────────────────────────────
# EXAMPLE USAGE (uncomment to test standalone)
# ──────────────────────────────────────────────────────────────────
# if __name__ == "__main__":
#     print(execute(list=True))
#     print(execute(category="ui_components", type="modal"))
#     print(execute(search="form"))
#     print(execute(category="forms", type="form_validation", format="javascript"))
