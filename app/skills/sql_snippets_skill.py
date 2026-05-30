"""
SQL/Database Snippets Skill for llama.cpp
──────────────────────────────────────────
SQL patterns for queries, optimization, migrations, and database design.
Covers PostgreSQL, MySQL, and SQLite.

Usage:
  execute(category="queries", type="joins")
  execute(search="index")
  execute(list=True)
"""

SNIPPETS_DB = {
    # ──────────────────────────────────────────────────────────────────
    # BASIC QUERIES
    # ──────────────────────────────────────────────────────────────────
    "queries": {
        "select_filter": {
            "description": "SELECT queries with filtering and sorting",
            "code": """
-- Basic SELECT
SELECT * FROM users;

-- Select specific columns
SELECT id, name, email FROM users;

-- WHERE clause (filtering)
SELECT * FROM users WHERE age > 18;

-- Multiple conditions (AND, OR)
SELECT * FROM users WHERE age > 18 AND status = 'active';
SELECT * FROM users WHERE country = 'USA' OR country = 'Canada';

-- IN operator
SELECT * FROM users WHERE status IN ('active', 'pending', 'archived');

-- LIKE pattern matching
SELECT * FROM users WHERE email LIKE '%@gmail.com';
SELECT * FROM users WHERE name LIKE 'J%';  -- Starts with J

-- BETWEEN
SELECT * FROM orders WHERE order_date BETWEEN '2024-01-01' AND '2024-12-31';

-- NULL checks
SELECT * FROM users WHERE phone IS NULL;
SELECT * FROM users WHERE phone IS NOT NULL;

-- DISTINCT values
SELECT DISTINCT country FROM users;

-- ORDER BY (sorting)
SELECT * FROM users ORDER BY age ASC;
SELECT * FROM users ORDER BY created_at DESC LIMIT 10;

-- LIMIT and OFFSET (pagination)
SELECT * FROM users ORDER BY id LIMIT 10 OFFSET 20;  -- Page 3 (20 per page)
"""
        },
        "joins": {
            "description": "JOIN operations for combining tables",
            "code": """
-- INNER JOIN (only matching rows)
SELECT users.name, orders.id, orders.amount
FROM users
INNER JOIN orders ON users.id = orders.user_id;

-- LEFT JOIN (all left table rows, matching right)
SELECT users.name, COUNT(orders.id) as order_count
FROM users
LEFT JOIN orders ON users.id = orders.user_id
GROUP BY users.id;

-- RIGHT JOIN (all right table rows, matching left)
SELECT users.name, orders.id
FROM users
RIGHT JOIN orders ON users.id = orders.user_id;

-- FULL OUTER JOIN (all rows from both tables)
SELECT users.name, orders.id
FROM users
FULL OUTER JOIN orders ON users.id = orders.user_id;

-- CROSS JOIN (Cartesian product)
SELECT * FROM users CROSS JOIN countries;

-- Multiple JOINs
SELECT 
  users.name,
  orders.id,
  products.name as product_name
FROM users
INNER JOIN orders ON users.id = orders.user_id
INNER JOIN products ON orders.product_id = products.id;

-- Self JOIN (table joined to itself)
SELECT 
  e1.name as employee,
  e2.name as manager
FROM employees e1
LEFT JOIN employees e2 ON e1.manager_id = e2.id;

-- Join with conditions
SELECT *
FROM users
INNER JOIN orders ON users.id = orders.user_id
  AND orders.status = 'completed'
WHERE users.country = 'USA';
"""
        },
        "aggregates": {
            "description": "Aggregate functions and GROUP BY",
            "code": """
-- COUNT: Number of rows
SELECT COUNT(*) as total_users FROM users;
SELECT COUNT(DISTINCT country) as unique_countries FROM users;

-- SUM: Total of values
SELECT SUM(amount) as total_sales FROM orders;

-- AVG: Average value
SELECT AVG(age) as average_age FROM users;

-- MIN/MAX: Minimum and maximum values
SELECT 
  MIN(age) as youngest,
  MAX(age) as oldest
FROM users;

-- GROUP BY: Group results
SELECT 
  country,
  COUNT(*) as user_count,
  AVG(age) as avg_age
FROM users
GROUP BY country;

-- GROUP BY with multiple columns
SELECT 
  country,
  status,
  COUNT(*) as count
FROM users
GROUP BY country, status;

-- HAVING: Filter groups (like WHERE for groups)
SELECT 
  country,
  COUNT(*) as user_count
FROM users
GROUP BY country
HAVING COUNT(*) > 100;

-- Complex aggregation
SELECT 
  u.country,
  COUNT(DISTINCT u.id) as users,
  COUNT(o.id) as total_orders,
  SUM(o.amount) as total_revenue,
  AVG(o.amount) as avg_order
FROM users u
LEFT JOIN orders o ON u.id = o.user_id
GROUP BY u.country
HAVING COUNT(o.id) > 10
ORDER BY total_revenue DESC;
"""
        }
    },

    # ──────────────────────────────────────────────────────────────────
    # ADVANCED QUERIES
    # ──────────────────────────────────────────────────────────────────
    "advanced": {
        "subqueries": {
            "description": "Subqueries and nested queries",
            "code": """
-- Subquery in WHERE
SELECT * FROM users
WHERE age > (SELECT AVG(age) FROM users);

-- Subquery with IN
SELECT * FROM orders
WHERE user_id IN (
  SELECT id FROM users WHERE country = 'USA'
);

-- Subquery in FROM
SELECT * FROM (
  SELECT 
    user_id,
    COUNT(*) as order_count,
    SUM(amount) as total
  FROM orders
  GROUP BY user_id
) as user_stats
WHERE total > 1000;

-- Correlated subquery (references outer query)
SELECT 
  u.id,
  u.name,
  (SELECT COUNT(*) FROM orders WHERE user_id = u.id) as order_count
FROM users u;

-- EXISTS (check if subquery returns rows)
SELECT * FROM users u
WHERE EXISTS (
  SELECT 1 FROM orders o WHERE o.user_id = u.id
);

-- NOT EXISTS
SELECT * FROM users u
WHERE NOT EXISTS (
  SELECT 1 FROM orders o WHERE o.user_id = u.id
);
"""
        },
        "window_functions": {
            "description": "Window functions for analytics (PostgreSQL/SQLite)",
            "code": """
-- ROW_NUMBER: Unique rank for each row
SELECT 
  id,
  name,
  salary,
  ROW_NUMBER() OVER (ORDER BY salary DESC) as rank
FROM employees;

-- RANK: Rank with ties
SELECT 
  id,
  name,
  salary,
  RANK() OVER (ORDER BY salary DESC) as rank
FROM employees;

-- LAG/LEAD: Access previous/next rows
SELECT 
  id,
  date,
  amount,
  LAG(amount) OVER (ORDER BY date) as prev_amount,
  LEAD(amount) OVER (ORDER BY date) as next_amount
FROM transactions;

-- Running total
SELECT 
  date,
  amount,
  SUM(amount) OVER (ORDER BY date) as running_total
FROM transactions;

-- Partition by groups
SELECT 
  department,
  employee,
  salary,
  AVG(salary) OVER (PARTITION BY department) as dept_avg
FROM employees;

-- Percent rank
SELECT 
  id,
  salary,
  PERCENT_RANK() OVER (ORDER BY salary) as percentile
FROM employees;
"""
        },
        "cte": {
            "description": "Common Table Expressions (WITH clause)",
            "code": """
-- Simple CTE
WITH recent_orders AS (
  SELECT * FROM orders
  WHERE order_date >= NOW() - INTERVAL 30 DAY
)
SELECT user_id, COUNT(*) as order_count
FROM recent_orders
GROUP BY user_id;

-- Multiple CTEs
WITH user_stats AS (
  SELECT 
    user_id,
    COUNT(*) as total_orders,
    SUM(amount) as total_spent
  FROM orders
  GROUP BY user_id
),
high_value_users AS (
  SELECT * FROM user_stats
  WHERE total_spent > 1000
)
SELECT * FROM high_value_users
WHERE total_orders > 5;

-- Recursive CTE (hierarchy/tree)
WITH RECURSIVE category_tree AS (
  -- Base case
  SELECT id, name, parent_id, 0 as depth
  FROM categories
  WHERE parent_id IS NULL
  
  UNION ALL
  
  -- Recursive case
  SELECT c.id, c.name, c.parent_id, ct.depth + 1
  FROM categories c
  INNER JOIN category_tree ct ON c.parent_id = ct.id
)
SELECT * FROM category_tree
ORDER BY depth, name;
"""
        }
    },

    # ──────────────────────────────────────────────────────────────────
    # MODIFICATIONS
    # ──────────────────────────────────────────────────────────────────
    "modifications": {
        "insert_update": {
            "description": "INSERT and UPDATE operations",
            "code": """
-- Basic INSERT
INSERT INTO users (name, email, age)
VALUES ('Alice', 'alice@example.com', 30);

-- Insert multiple rows
INSERT INTO users (name, email, age)
VALUES 
  ('Bob', 'bob@example.com', 25),
  ('Charlie', 'charlie@example.com', 35),
  ('Diana', 'diana@example.com', 28);

-- Insert from SELECT
INSERT INTO users_backup
SELECT * FROM users WHERE status = 'inactive';

-- ON DUPLICATE KEY UPDATE (MySQL)
INSERT INTO users (email, name, visits)
VALUES ('user@example.com', 'User', 1)
ON DUPLICATE KEY UPDATE
  name = VALUES(name),
  visits = visits + 1;

-- UPSERT (PostgreSQL)
INSERT INTO users (email, name)
VALUES ('user@example.com', 'User')
ON CONFLICT (email)
DO UPDATE SET name = EXCLUDED.name;

-- Basic UPDATE
UPDATE users SET age = 31 WHERE name = 'Alice';

-- Update multiple columns
UPDATE users
SET age = 40, status = 'active'
WHERE id = 1;

-- Update with calculation
UPDATE employees
SET salary = salary * 1.1
WHERE department = 'IT';

-- Update from another table
UPDATE users u
SET country = l.country
FROM locations l
WHERE u.location_id = l.id;

-- UPDATE with CASE
UPDATE users
SET tier = CASE
  WHEN total_spent > 5000 THEN 'platinum'
  WHEN total_spent > 1000 THEN 'gold'
  ELSE 'standard'
END;
"""
        },
        "delete": {
            "description": "DELETE operations with safety",
            "code": """
-- Delete specific rows
DELETE FROM users WHERE status = 'inactive';

-- Delete all rows (without deleting table)
DELETE FROM logs;  -- Can be slow for large tables
TRUNCATE TABLE logs;  -- Faster alternative

-- Delete with JOIN (MySQL)
DELETE u FROM users u
INNER JOIN inactive_users i ON u.id = i.id;

-- Delete with subquery
DELETE FROM orders
WHERE user_id IN (
  SELECT id FROM users WHERE status = 'deleted'
);

-- Safe delete pattern (archive first)
INSERT INTO users_deleted
SELECT * FROM users WHERE status = 'to_delete';

DELETE FROM users WHERE status = 'to_delete';

-- Delete old records
DELETE FROM logs
WHERE created_at < NOW() - INTERVAL 90 DAY;
"""
        }
    },

    # ──────────────────────────────────────────────────────────────────
    # SCHEMA & INDEXES
    # ──────────────────────────────────────────────────────────────────
    "schema": {
        "create_table": {
            "description": "CREATE TABLE with constraints",
            "code": """
-- Basic table
CREATE TABLE users (
  id INT PRIMARY KEY AUTO_INCREMENT,
  name VARCHAR(100) NOT NULL,
  email VARCHAR(100) UNIQUE,
  age INT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table with constraints
CREATE TABLE orders (
  id INT PRIMARY KEY AUTO_INCREMENT,
  user_id INT NOT NULL,
  amount DECIMAL(10, 2),
  status VARCHAR(20),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  
  FOREIGN KEY (user_id) REFERENCES users(id),
  CHECK (amount > 0),
  INDEX idx_user_date (user_id, created_at)
);

-- Table with composite primary key
CREATE TABLE order_items (
  order_id INT NOT NULL,
  product_id INT NOT NULL,
  quantity INT,
  price DECIMAL(10, 2),
  
  PRIMARY KEY (order_id, product_id),
  FOREIGN KEY (order_id) REFERENCES orders(id)
);

-- PostgreSQL with serial type
CREATE TABLE users_pg (
  id SERIAL PRIMARY KEY,
  name VARCHAR(100) NOT NULL,
  email VARCHAR(100) UNIQUE,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- SQLite simple table
CREATE TABLE notes (
  id INTEGER PRIMARY KEY,
  title TEXT NOT NULL,
  content TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
"""
        },
        "indexes": {
            "description": "Create and manage indexes for performance",
            "code": """
-- Single column index
CREATE INDEX idx_users_email ON users(email);

-- Composite index (multi-column)
CREATE INDEX idx_orders_user_date ON orders(user_id, created_at DESC);

-- Unique index
CREATE UNIQUE INDEX idx_users_email_unique ON users(email);

-- Index on expression
CREATE INDEX idx_users_lower_name ON users(LOWER(name));

-- Partial index (PostgreSQL)
CREATE INDEX idx_active_users ON users(id) WHERE status = 'active';

-- Full-text index (MySQL)
CREATE FULLTEXT INDEX idx_posts_content ON posts(title, content);

-- View existing indexes
SHOW INDEXES FROM users;  -- MySQL
\\d users  -- PostgreSQL psql

-- Drop index
DROP INDEX idx_users_email ON users;  -- MySQL
DROP INDEX idx_users_email;  -- PostgreSQL/SQLite

-- Analyze table (update statistics)
ANALYZE TABLE users;  -- MySQL
ANALYZE users;  -- SQLite

-- Query execution plan
EXPLAIN SELECT * FROM users WHERE email = 'test@example.com';
EXPLAIN ANALYZE SELECT * FROM orders WHERE user_id = 1;  -- PostgreSQL
"""
        },
        "migrations": {
            "description": "Alter table structure (migrations)",
            "code": """
-- Add column
ALTER TABLE users ADD COLUMN phone VARCHAR(20);

-- Add column with default
ALTER TABLE users ADD COLUMN status VARCHAR(20) DEFAULT 'active';

-- Add column after specific column (MySQL)
ALTER TABLE users ADD COLUMN phone VARCHAR(20) AFTER email;

-- Drop column
ALTER TABLE users DROP COLUMN phone;

-- Rename column (PostgreSQL)
ALTER TABLE users RENAME COLUMN name TO full_name;

-- Rename column (MySQL)
ALTER TABLE users CHANGE COLUMN name full_name VARCHAR(100);

-- Change column type
ALTER TABLE users MODIFY age INT;  -- MySQL
ALTER TABLE users ALTER COLUMN age TYPE INTEGER;  -- PostgreSQL

-- Add NOT NULL constraint
ALTER TABLE users MODIFY email VARCHAR(100) NOT NULL;

-- Add FOREIGN KEY
ALTER TABLE orders
ADD CONSTRAINT fk_user_id
FOREIGN KEY (user_id) REFERENCES users(id);

-- Drop constraint
ALTER TABLE orders
DROP CONSTRAINT fk_user_id;  -- PostgreSQL
ALTER TABLE orders DROP FOREIGN KEY fk_user_id;  -- MySQL

-- Add unique constraint
ALTER TABLE users
ADD CONSTRAINT unique_email UNIQUE (email);

-- Create new table from existing (safe migration)
CREATE TABLE users_new LIKE users;
INSERT INTO users_new SELECT * FROM users;
DROP TABLE users;
RENAME TABLE users_new TO users;
"""
        }
    },

    # ──────────────────────────────────────────────────────────────────
    # OPTIMIZATION
    # ──────────────────────────────────────────────────────────────────
    "optimization": {
        "query_optimization": {
            "description": "Query optimization techniques",
            "code": """
-- Inefficient: SELECT * (avoid in production)
SELECT * FROM large_table;  -- Too many columns

-- Better: Select only needed columns
SELECT id, name, email FROM users WHERE status = 'active';

-- Inefficient: Function in WHERE clause
SELECT * FROM orders WHERE YEAR(created_at) = 2024;

-- Better: Use range
SELECT * FROM orders
WHERE created_at >= '2024-01-01' AND created_at < '2025-01-01';

-- Inefficient: Using OR with different columns
SELECT * FROM users
WHERE id = 1 OR id = 2 OR id = 3;

-- Better: Use IN
SELECT * FROM users WHERE id IN (1, 2, 3);

-- Inefficient: Nested subqueries
SELECT * FROM users WHERE id IN (
  SELECT user_id FROM orders WHERE id IN (
    SELECT order_id FROM order_items WHERE product_id = 5
  )
);

-- Better: Use JOINs
SELECT DISTINCT u.* FROM users u
JOIN orders o ON u.id = o.user_id
JOIN order_items oi ON o.id = oi.order_id
WHERE oi.product_id = 5;

-- Efficient pagination
SELECT * FROM users
ORDER BY id
LIMIT 20 OFFSET 40;

-- Inefficient: DISTINCT on large result
SELECT DISTINCT * FROM orders;  -- Slow

-- Better: Use GROUP BY or specific columns
SELECT DISTINCT user_id FROM orders;

-- Add index for frequently filtered columns
CREATE INDEX idx_orders_user_created
ON orders(user_id, created_at DESC);

-- Use EXPLAIN to analyze
EXPLAIN SELECT * FROM orders
WHERE user_id = 1 AND created_at > '2024-01-01';
"""
        }
    }
}


def execute(**kwargs):
    """
    Execute the SQL/Database snippets skill.
    
    Parameters:
      category  - Category: queries, advanced, modifications, schema, optimization
      type      - Snippet type (e.g., "select_filter", "joins")
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
        lines = ["Available SQL/Database Snippets:\\n"]
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
    output.append("──── SQL ────\\n")
    output.append(snippet.get("code", ""))

    return "\\n".join(output)
