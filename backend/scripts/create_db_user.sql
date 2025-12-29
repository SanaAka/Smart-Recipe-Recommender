-- Run this as an admin user (or via mysql client) to create a dedicated DB user
-- Replace the password with a strong value and update backend/.env accordingly

CREATE DATABASE IF NOT EXISTS recipe_recommender DEFAULT CHARACTER SET = 'utf8mb4' DEFAULT COLLATE = 'utf8mb4_unicode_ci';

CREATE USER IF NOT EXISTS 'recipe_user'@'localhost' IDENTIFIED BY 'ChangeMeStrongP@ss!';
GRANT ALL PRIVILEGES ON recipe_recommender.* TO 'recipe_user'@'localhost';
FLUSH PRIVILEGES;

-- If you need TCP access (127.0.0.1), optionally create that host mapping too:
CREATE USER IF NOT EXISTS 'recipe_user'@'127.0.0.1' IDENTIFIED BY 'ChangeMeStrongP@ss!';
GRANT ALL PRIVILEGES ON recipe_recommender.* TO 'recipe_user'@'127.0.0.1';
FLUSH PRIVILEGES;
