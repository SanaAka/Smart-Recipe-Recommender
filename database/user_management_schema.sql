-- User Management Tables for Smart Recipe Recommender
-- Run this migration to add user authentication and personalization

USE recipe_recommender;

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP NULL,
    dietary_preferences JSON DEFAULT NULL,
    allergies JSON DEFAULT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    INDEX idx_username (username),
    INDEX idx_email (email),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- User favorites table
CREATE TABLE IF NOT EXISTS user_favorites (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    recipe_id INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (recipe_id) REFERENCES recipes(id) ON DELETE CASCADE,
    UNIQUE KEY unique_user_recipe (user_id, recipe_id),
    INDEX idx_user (user_id),
    INDEX idx_recipe (recipe_id),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Recipe ratings table
CREATE TABLE IF NOT EXISTS recipe_ratings (
    id INT PRIMARY KEY AUTO_INCREMENT,
    recipe_id INT NOT NULL,
    user_id INT NOT NULL,
    rating INT NOT NULL CHECK (rating BETWEEN 1 AND 5),
    review TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (recipe_id) REFERENCES recipes(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE KEY unique_user_recipe_rating (user_id, recipe_id),
    INDEX idx_recipe (recipe_id),
    INDEX idx_user (user_id),
    INDEX idx_rating (rating),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- User cooking history (for personalization)
CREATE TABLE IF NOT EXISTS user_cooking_history (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    recipe_id INT NOT NULL,
    cooked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    difficulty_rating INT CHECK (difficulty_rating BETWEEN 1 AND 5),
    would_make_again BOOLEAN,
    notes TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (recipe_id) REFERENCES recipes(id) ON DELETE CASCADE,
    INDEX idx_user (user_id),
    INDEX idx_recipe (recipe_id),
    INDEX idx_cooked_at (cooked_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- User recipe views (for analytics and recommendations)
CREATE TABLE IF NOT EXISTS user_recipe_views (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT,
    recipe_id INT NOT NULL,
    viewed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    view_duration INT COMMENT 'Duration in seconds',
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
    FOREIGN KEY (recipe_id) REFERENCES recipes(id) ON DELETE CASCADE,
    INDEX idx_user (user_id),
    INDEX idx_recipe (recipe_id),
    INDEX idx_viewed_at (viewed_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Create view for recipe statistics
CREATE OR REPLACE VIEW recipe_stats AS
SELECT 
    r.id as recipe_id,
    r.name as recipe_name,
    COUNT(DISTINCT rr.id) as rating_count,
    AVG(rr.rating) as average_rating,
    COUNT(DISTINCT uf.id) as favorite_count,
    COUNT(DISTINCT uch.id) as times_cooked,
    COUNT(DISTINCT urv.id) as view_count
FROM recipes r
LEFT JOIN recipe_ratings rr ON r.id = rr.recipe_id
LEFT JOIN user_favorites uf ON r.id = uf.recipe_id
LEFT JOIN user_cooking_history uch ON r.id = uch.recipe_id
LEFT JOIN user_recipe_views urv ON r.id = urv.recipe_id
GROUP BY r.id, r.name;
