-- Smart Recipe Recommender Database Schema
-- MySQL Database

CREATE DATABASE IF NOT EXISTS recipe_recommender;
USE recipe_recommender;

-- Recipes table
CREATE TABLE IF NOT EXISTS recipes (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(500) NOT NULL,
    minutes INT,
    description TEXT,
    contributor_id INT,
    submitted DATE,
    image_url VARCHAR(1000),
    source_url VARCHAR(1000),
    cuisine VARCHAR(100) DEFAULT NULL,
    INDEX idx_name (name(255)),
    INDEX idx_minutes (minutes),
    INDEX idx_cuisine (cuisine)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Ingredients table
CREATE TABLE IF NOT EXISTS ingredients (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(255) NOT NULL UNIQUE,
    INDEX idx_name (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Recipe-Ingredients relationship table
CREATE TABLE IF NOT EXISTS recipe_ingredients (
    id INT PRIMARY KEY AUTO_INCREMENT,
    recipe_id INT NOT NULL,
    ingredient_id INT NOT NULL,
    FOREIGN KEY (recipe_id) REFERENCES recipes(id) ON DELETE CASCADE,
    FOREIGN KEY (ingredient_id) REFERENCES ingredients(id) ON DELETE CASCADE,
    UNIQUE KEY unique_recipe_ingredient (recipe_id, ingredient_id),
    INDEX idx_recipe (recipe_id),
    INDEX idx_ingredient (ingredient_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tags table (for dietary preferences, cuisine types, etc.)
CREATE TABLE IF NOT EXISTS tags (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(255) NOT NULL UNIQUE,
    INDEX idx_name (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Recipe-Tags relationship table
CREATE TABLE IF NOT EXISTS recipe_tags (
    id INT PRIMARY KEY AUTO_INCREMENT,
    recipe_id INT NOT NULL,
    tag_id INT NOT NULL,
    FOREIGN KEY (recipe_id) REFERENCES recipes(id) ON DELETE CASCADE,
    FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE,
    UNIQUE KEY unique_recipe_tag (recipe_id, tag_id),
    INDEX idx_recipe (recipe_id),
    INDEX idx_tag (tag_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Nutrition information table
CREATE TABLE IF NOT EXISTS nutrition (
    id INT PRIMARY KEY AUTO_INCREMENT,
    recipe_id INT NOT NULL UNIQUE,
    calories DECIMAL(10, 2),
    total_fat DECIMAL(10, 2),
    sugar DECIMAL(10, 2),
    sodium DECIMAL(10, 2),
    protein DECIMAL(10, 2),
    saturated_fat DECIMAL(10, 2),
    carbohydrates DECIMAL(10, 2),
    FOREIGN KEY (recipe_id) REFERENCES recipes(id) ON DELETE CASCADE,
    INDEX idx_recipe (recipe_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Steps table (cooking instructions)
CREATE TABLE IF NOT EXISTS steps (
    id INT PRIMARY KEY AUTO_INCREMENT,
    recipe_id INT NOT NULL,
    step_number INT NOT NULL,
    description TEXT NOT NULL,
    FOREIGN KEY (recipe_id) REFERENCES recipes(id) ON DELETE CASCADE,
    INDEX idx_recipe (recipe_id),
    INDEX idx_step_number (step_number)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Create indexes for better query performance
CREATE INDEX idx_recipes_name_ft ON recipes(name(255));
CREATE INDEX idx_ingredients_name_ft ON ingredients(name);
CREATE INDEX idx_tags_name_ft ON tags(name);

-- Optional: Add FULLTEXT indexes for faster text search (run once)
-- The following block creates FULLTEXT indexes only if they do not already exist.
-- It is safe to source this file in MySQL client. If your MySQL user lacks
-- permission to create procedures, run the ALTER TABLE statements manually.
DELIMITER $$
CREATE PROCEDURE add_fulltext_indexes()
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM INFORMATION_SCHEMA.STATISTICS
        WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'recipes' AND INDEX_NAME = 'ft_recipes'
    ) THEN
        ALTER TABLE recipes ADD FULLTEXT ft_recipes (name, description);
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM INFORMATION_SCHEMA.STATISTICS
        WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'ingredients' AND INDEX_NAME = 'ft_ingredients_name'
    ) THEN
        ALTER TABLE ingredients ADD FULLTEXT ft_ingredients_name (name);
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM INFORMATION_SCHEMA.STATISTICS
        WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'tags' AND INDEX_NAME = 'ft_tags_name'
    ) THEN
        ALTER TABLE tags ADD FULLTEXT ft_tags_name (name);
    END IF;
END$$
DELIMITER ;

CALL add_fulltext_indexes();
DROP PROCEDURE IF EXISTS add_fulltext_indexes;

-- Add a denormalized search_text column and FULLTEXT index for combined searches
DELIMITER $$
CREATE PROCEDURE add_search_text_column_and_index()
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'recipes' AND COLUMN_NAME = 'search_text'
    ) THEN
        ALTER TABLE recipes ADD COLUMN search_text TEXT;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM INFORMATION_SCHEMA.STATISTICS
        WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'recipes' AND INDEX_NAME = 'ft_recipes_search'
    ) THEN
        ALTER TABLE recipes ADD FULLTEXT ft_recipes_search (search_text);
    END IF;
END$$
DELIMITER ;

CALL add_search_text_column_and_index();
DROP PROCEDURE IF EXISTS add_search_text_column_and_index;

-- NOTE: After running this, run `python backend/backfill_search_text.py` to populate
-- `search_text` for existing recipes. For very large datasets, run the backfill
-- in batches or use a maintenance window.
