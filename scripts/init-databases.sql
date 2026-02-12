-- Create separate databases for each service
CREATE DATABASE auth_db;
CREATE DATABASE product_db;
CREATE DATABASE order_db;
CREATE DATABASE payment_db;

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE auth_db TO admin;
GRANT ALL PRIVILEGES ON DATABASE product_db TO admin;
GRANT ALL PRIVILEGES ON DATABASE order_db TO admin;
GRANT ALL PRIVILEGES ON DATABASE payment_db TO admin;