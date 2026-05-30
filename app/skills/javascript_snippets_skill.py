"""
JavaScript Advanced Snippets Skill for llama.cpp
─────────────────────────────────────────────────
Advanced JavaScript patterns: async/await, Promises, Node.js APIs,
error handling, performance optimization, and modern ES6+ techniques.

Usage:
  execute(category="async", type="fetch_with_retry")
  execute(search="promise")
  execute(list=True)
"""

SNIPPETS_DB = {
    # ──────────────────────────────────────────────────────────────────
    # ASYNC & PROMISES
    # ──────────────────────────────────────────────────────────────────
    "async": {
        "fetch_with_retry": {
            "description": "Robust fetch with automatic retry and timeout",
            "code": """
async function fetchWithRetry(url, options = {}) {
  const maxRetries = options.maxRetries || 3;
  const timeout = options.timeout || 5000;
  const delay = options.delay || 1000;
  
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), timeout);
      
      const response = await fetch(url, {
        ...options,
        signal: controller.signal
      });
      
      clearTimeout(timeoutId);
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      return response;
    } catch (error) {
      if (attempt === maxRetries) {
        throw error;
      }
      
      console.warn(`Attempt ${attempt} failed, retrying in ${delay}ms...`);
      await new Promise(r => setTimeout(r, delay));
    }
  }
}

// Usage
const response = await fetchWithRetry('https://api.example.com/data', {
  maxRetries: 3,
  timeout: 5000,
  delay: 1000
});
const data = await response.json();
console.log(data);
"""
        },
        "promise_patterns": {
            "description": "Promise utilities: race, all, allSettled, sequential execution",
            "code": """
// Promise.all - all must succeed
Promise.all([
  fetch('/api/users'),
  fetch('/api/posts'),
  fetch('/api/comments')
])
.then(responses => Promise.all(responses.map(r => r.json())))
.then(data => console.log('All data:', data))
.catch(err => console.error('Error:', err));

// Promise.allSettled - wait for all (success or fail)
const results = await Promise.allSettled([
  fetch('/api/good'),
  fetch('/api/bad'),
  fetch('/api/okay')
]);

results.forEach((result, i) => {
  if (result.status === 'fulfilled') {
    console.log(`Request ${i} succeeded:`, result.value);
  } else {
    console.log(`Request ${i} failed:`, result.reason);
  }
});

// Promise.race - first to complete wins
const fastestData = await Promise.race([
  fetch('https://server1.com/data'),
  fetch('https://server2.com/data'),
  fetch('https://server3.com/data')
]).then(r => r.json());

// Sequential execution
async function executeSequential(tasks) {
  const results = [];
  for (const task of tasks) {
    try {
      const result = await task();
      results.push(result);
    } catch (error) {
      console.error('Task failed:', error);
    }
  }
  return results;
}

// Usage
const tasks = [
  () => fetch('/api/1').then(r => r.json()),
  () => fetch('/api/2').then(r => r.json()),
  () => fetch('/api/3').then(r => r.json())
];
const data = await executeSequential(tasks);

// Parallel with limited concurrency
async function parallelLimit(tasks, limit) {
  const results = [];
  const executing = [];
  
  for (const [i, task] of tasks.entries()) {
    const promise = Promise.resolve().then(() => task()).then(
      result => {
        results[i] = result;
        return results[i];
      }
    );
    
    results[i] = promise;
    
    if (tasks.length >= limit) {
      executing.push(promise);
      if (executing.length >= limit) {
        await Promise.race(executing);
        executing.splice(executing.findIndex(p => p === promise), 1);
      }
    }
  }
  
  return Promise.all(results);
}
"""
        },
        "async_await_patterns": {
            "description": "Async/await with error handling, timeouts, cancellation",
            "code": """
// Basic async/await
async function getData() {
  try {
    const response = await fetch('/api/data');
    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Failed to fetch:', error);
    throw error;
  }
}

// Async timeout wrapper
function withTimeout(promise, timeoutMs) {
  return Promise.race([
    promise,
    new Promise((_, reject) =>
      setTimeout(() => reject(new Error('Timeout')), timeoutMs)
    )
  ]);
}

// Usage
const data = await withTimeout(fetch('/api/slow'), 5000);

// Async retry with exponential backoff
async function retryWithBackoff(fn, maxAttempts = 3) {
  for (let i = 1; i <= maxAttempts; i++) {
    try {
      return await fn();
    } catch (error) {
      if (i === maxAttempts) throw error;
      const delay = Math.pow(2, i - 1) * 1000; // 1s, 2s, 4s...
      await new Promise(r => setTimeout(r, delay));
    }
  }
}

// Abort controller for cancellation
const controller = new AbortController();
const timeoutId = setTimeout(() => controller.abort(), 5000);

try {
  const response = await fetch('/api/data', {
    signal: controller.signal
  });
  return response.json();
} catch (error) {
  if (error.name === 'AbortError') {
    console.log('Request cancelled');
  }
} finally {
  clearTimeout(timeoutId);
}

// Async generator for streaming
async function* fetchData(urls) {
  for (const url of urls) {
    const response = await fetch(url);
    const data = await response.json();
    yield data;
  }
}

// Usage
for await (const data of fetchData(['url1', 'url2', 'url3'])) {
  console.log('Received:', data);
}
"""
        }
    },

    # ──────────────────────────────────────────────────────────────────
    # NODE.JS
    # ──────────────────────────────────────────────────────────────────
    "nodejs": {
        "file_operations": {
            "description": "Node.js file system operations with async/await",
            "code": """
const fs = require('fs').promises;
const path = require('path');

// Read file
async function readFile(filepath) {
  try {
    return await fs.readFile(filepath, 'utf-8');
  } catch (error) {
    console.error('Error reading file:', error);
    throw error;
  }
}

// Write file (creates parent dirs if needed)
async function writeFile(filepath, content) {
  try {
    const dir = path.dirname(filepath);
    await fs.mkdir(dir, { recursive: true });
    await fs.writeFile(filepath, content, 'utf-8');
  } catch (error) {
    console.error('Error writing file:', error);
    throw error;
  }
}

// Read directory
async function listFiles(dirpath) {
  try {
    const files = await fs.readdir(dirpath);
    return files;
  } catch (error) {
    console.error('Error listing directory:', error);
    return [];
  }
}

// Find files by pattern
async function findFiles(dirpath, pattern) {
  const files = [];
  
  async function walk(dir) {
    const entries = await fs.readdir(dir, { withFileTypes: true });
    
    for (const entry of entries) {
      const fullPath = path.join(dir, entry.name);
      
      if (entry.isDirectory()) {
        await walk(fullPath);
      } else if (pattern.test(entry.name)) {
        files.push(fullPath);
      }
    }
  }
  
  await walk(dirpath);
  return files;
}

// Copy file
async function copyFile(src, dest) {
  try {
    const dir = path.dirname(dest);
    await fs.mkdir(dir, { recursive: true });
    await fs.copyFile(src, dest);
  } catch (error) {
    console.error('Error copying file:', error);
    throw error;
  }
}

// Delete file
async function deleteFile(filepath) {
  try {
    await fs.unlink(filepath);
  } catch (error) {
    if (error.code !== 'ENOENT') {
      throw error;
    }
  }
}

// Get file info
async function fileInfo(filepath) {
  const stats = await fs.stat(filepath);
  return {
    size: stats.size,
    isFile: stats.isFile(),
    isDir: stats.isDirectory(),
    created: stats.birthtime,
    modified: stats.mtime
  };
}

// Example usage
const content = await readFile('input.txt');
await writeFile('output.txt', content.toUpperCase());
"""
        },
        "http_server": {
            "description": "Simple HTTP server with routing",
            "code": """
const http = require('http');
const url = require('url');

const server = http.createServer(async (req, res) => {
  const { pathname, query } = url.parse(req.url, true);
  
  // Set CORS headers
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Content-Type', 'application/json');
  
  try {
    // GET /api/users
    if (req.method === 'GET' && pathname === '/api/users') {
      res.writeHead(200);
      return res.end(JSON.stringify({
        users: [
          { id: 1, name: 'Alice' },
          { id: 2, name: 'Bob' }
        ]
      }));
    }
    
    // POST /api/users
    if (req.method === 'POST' && pathname === '/api/users') {
      let body = '';
      req.on('data', chunk => body += chunk);
      req.on('end', () => {
        const userData = JSON.parse(body);
        res.writeHead(201);
        res.end(JSON.stringify({ id: 3, ...userData }));
      });
      return;
    }
    
    // GET /api/users/:id
    const match = pathname.match(/^\\/api\\/users\\/(\\d+)$/);
    if (req.method === 'GET' && match) {
      const id = parseInt(match[1]);
      res.writeHead(200);
      return res.end(JSON.stringify({ id, name: `User ${id}` }));
    }
    
    // 404
    res.writeHead(404);
    res.end(JSON.stringify({ error: 'Not found' }));
    
  } catch (error) {
    res.writeHead(500);
    res.end(JSON.stringify({ error: error.message }));
  }
});

const PORT = process.env.PORT || 3000;
server.listen(PORT, () => {
  console.log(`Server running on http://localhost:${PORT}`);
});
"""
        },
        "worker_threads": {
            "description": "Spawn worker threads for CPU-intensive tasks",
            "code": """
const { Worker } = require('worker_threads');
const path = require('path');

// Create worker
function runWorker(workerScript, data) {
  return new Promise((resolve, reject) => {
    const worker = new Worker(workerScript);
    
    worker.on('message', (result) => {
      resolve(result);
    });
    
    worker.on('error', (error) => {
      reject(error);
    });
    
    worker.on('exit', (code) => {
      if (code !== 0) {
        reject(new Error(`Worker exited with code ${code}`));
      }
    });
    
    worker.postMessage(data);
  });
}

// Example: Calculate fibonacci in worker
// worker.js:
// const { parentPort } = require('worker_threads');
// 
// function fibonacci(n) {
//   if (n <= 1) return n;
//   return fibonacci(n - 1) + fibonacci(n - 2);
// }
// 
// parentPort.on('message', (n) => {
//   const result = fibonacci(n);
//   parentPort.postMessage(result);
// });

// Usage in main thread
async function main() {
  const result = await runWorker(
    path.join(__dirname, 'worker.js'),
    40
  );
  console.log('Fibonacci(40):', result);
}

main();
"""
        }
    },

    # ──────────────────────────────────────────────────────────────────
    # ADVANCED PATTERNS
    # ──────────────────────────────────────────────────────────────────
    "advanced": {
        "event_emitter": {
            "description": "Custom event emitter implementation",
            "code": """
class EventEmitter {
  constructor() {
    this.events = {};
  }
  
  on(eventName, listener) {
    if (!this.events[eventName]) {
      this.events[eventName] = [];
    }
    this.events[eventName].push(listener);
  }
  
  off(eventName, listener) {
    if (this.events[eventName]) {
      this.events[eventName] = this.events[eventName].filter(
        l => l !== listener
      );
    }
  }
  
  once(eventName, listener) {
    const wrappedListener = (...args) => {
      listener(...args);
      this.off(eventName, wrappedListener);
    };
    this.on(eventName, wrappedListener);
  }
  
  emit(eventName, ...args) {
    if (this.events[eventName]) {
      this.events[eventName].forEach(listener => {
        listener(...args);
      });
    }
  }
}

// Usage
const emitter = new EventEmitter();

emitter.on('user:login', (username) => {
  console.log(`${username} logged in`);
});

emitter.emit('user:login', 'alice');
"""
        },
        "proxy_pattern": {
            "description": "JavaScript Proxy for intercepting object operations",
            "code": """
// Simple logging proxy
const user = {
  name: 'Alice',
  email: 'alice@example.com'
};

const handler = {
  get(target, property) {
    console.log(`Getting ${property}`);
    return target[property];
  },
  set(target, property, value) {
    console.log(`Setting ${property} to ${value}`);
    target[property] = value;
    return true;
  }
};

const proxiedUser = new Proxy(user, handler);
console.log(proxiedUser.name);    // Logs: Getting name
proxiedUser.name = 'Bob';         // Logs: Setting name to Bob

// Validation proxy
const validatedUser = new Proxy({}, {
  set(target, property, value) {
    if (property === 'age' && typeof value !== 'number') {
      throw new Error('Age must be a number');
    }
    if (property === 'email' && !value.includes('@')) {
      throw new Error('Invalid email');
    }
    target[property] = value;
    return true;
  }
});

validatedUser.age = 30;        // OK
validatedUser.email = 'x@ex.com'; // OK
validatedUser.age = 'thirty';  // Error: Age must be a number

// Lazy loading proxy
const dataProxy = new Proxy({}, {
  get(target, property) {
    if (!(property in target)) {
      console.log(`Loading ${property}...`);
      target[property] = fetch(`/api/${property}`).then(r => r.json());
    }
    return target[property];
  }
});
"""
        },
        "generator_iterators": {
            "description": "Generators and custom iterators",
            "code": """
// Generator function
function* countdown(n) {
  while (n > 0) {
    yield n;
    n--;
  }
}

// Usage
for (const num of countdown(5)) {
  console.log(num); // 5, 4, 3, 2, 1
}

// Infinite generator
function* infiniteSequence() {
  let id = 0;
  while (true) {
    yield id++;
  }
}

// Custom iterator
const iterable = {
  [Symbol.iterator]: function* () {
    yield 1;
    yield 2;
    yield 3;
  }
};

for (const val of iterable) {
  console.log(val); // 1, 2, 3
}

// Generator as state machine
function* trafficLight() {
  while (true) {
    yield 'red';
    yield 'yellow';
    yield 'green';
  }
}

const light = trafficLight();
console.log(light.next().value); // red
console.log(light.next().value); // yellow
console.log(light.next().value); // green

// Delegating to another generator
function* gen1() {
  yield 1;
  yield 2;
}

function* gen2() {
  yield* gen1();
  yield 3;
}

for (const val of gen2()) {
  console.log(val); // 1, 2, 3
}
"""
        }
    },

    # ──────────────────────────────────────────────────────────────────
    # PERFORMANCE
    # ──────────────────────────────────────────────────────────────────
    "performance": {
        "memoization": {
            "description": "Function memoization for caching results",
            "code": """
// Simple memoization
function memoize(fn) {
  const cache = new Map();
  
  return function(...args) {
    const key = JSON.stringify(args);
    
    if (cache.has(key)) {
      console.log('Cache hit');
      return cache.get(key);
    }
    
    console.log('Computing...');
    const result = fn(...args);
    cache.set(key, result);
    return result;
  };
}

// Fibonacci with memoization
const fib = memoize((n) => {
  if (n <= 1) return n;
  return fib(n - 1) + fib(n - 2);
});

console.log(fib(10)); // Computing... (fast)
console.log(fib(10)); // Cache hit

// Memoization with TTL (time-to-live)
function memoizeWithTTL(fn, ttl = 60000) {
  const cache = new Map();
  
  return function(...args) {
    const key = JSON.stringify(args);
    const cached = cache.get(key);
    
    if (cached && Date.now() - cached.time < ttl) {
      return cached.value;
    }
    
    const result = fn(...args);
    cache.set(key, { value: result, time: Date.now() });
    return result;
  };
}

// LRU Cache (Least Recently Used)
class LRUCache {
  constructor(size = 100) {
    this.cache = new Map();
    this.maxSize = size;
  }
  
  get(key) {
    if (!this.cache.has(key)) return null;
    
    const value = this.cache.get(key);
    this.cache.delete(key);
    this.cache.set(key, value);
    return value;
  }
  
  set(key, value) {
    if (this.cache.has(key)) {
      this.cache.delete(key);
    }
    this.cache.set(key, value);
    
    if (this.cache.size > this.maxSize) {
      const firstKey = this.cache.keys().next().value;
      this.cache.delete(firstKey);
    }
  }
}
"""
        }
    }
}


def execute(**kwargs):
    """
    Execute the JavaScript Advanced snippets skill.
    
    Parameters:
      category  - Category: async, nodejs, advanced, performance
      type      - Snippet type (e.g., "fetch_with_retry", "event_emitter")
      search    - Free-text search across snippets
      list      - If True, list all available snippets
    """
    
    category = str(kwargs.get("category", "")).strip().lower()
    snippet_type = str(kwargs.get("type", "")).strip().lower()
    search_term = str(kwargs.get("search", "")).strip().lower()
    list_only = bool(kwargs.get("list", False))

    # ──────────────────────────────────────────────────────────────────
    # LIST MODE
    # ──────────────────────────────────────────────────────────────────
    if list_only:
        lines = ["Available JavaScript Advanced Snippets:\\n"]
        for cat in SNIPPETS_DB:
            lines.append(f"\\n📂 {cat.upper()}")
            for snippet_name in SNIPPETS_DB[cat]:
                desc = SNIPPETS_DB[cat][snippet_name].get("description", "")
                lines.append(f"  • {snippet_name}: {desc}")
        return "\\n".join(lines)

    # ──────────────────────────────────────────────────────────────────
    # SEARCH MODE
    # ──────────────────────────────────────────────────────────────────
    if search_term:
        lines = [f"Search results for: '{search_term}'\\n"]
        found = False
        
        for cat in SNIPPETS_DB:
            for snippet_name in SNIPPETS_DB[cat]:
                snippet = SNIPPETS_DB[cat][snippet_name]
                desc = snippet.get("description", "").lower()
                
                if search_term in desc or search_term in snippet_name.lower():
                    found = True
                    lines.append(f"\\n[{cat}] {snippet_name}")
                    lines.append(f"  {snippet.get('description', '')}")
        
        if not found:
            return f"No snippets found matching '{search_term}'"
        
        return "\\n".join(lines)

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
    output.append(f"   {snippet.get('description', '')}\\n")
    output.append("──── JAVASCRIPT ────\\n")
    output.append(snippet.get("code", ""))

    return "\\n".join(output)
