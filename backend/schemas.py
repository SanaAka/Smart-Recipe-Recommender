"""
Request validation schemas using Pydantic
Provides type-safe input validation for all API endpoints
"""
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator
from enum import Enum


class SearchType(str, Enum):
    """Valid search types"""
    NAME = 'name'
    INGREDIENT = 'ingredient'
    CUISINE = 'cuisine'


class RecommendationRequest(BaseModel):
    """Schema for recipe recommendation requests"""
    ingredients: List[str] = Field(
        ..., 
        min_length=1, 
        max_length=50,
        description="List of available ingredients"
    )
    dietary_preference: Optional[str] = Field(
        default='',
        max_length=100,
        description="Dietary preference (vegetarian, vegan, keto, etc.)"
    )
    cuisine_type: Optional[str] = Field(
        default='',
        max_length=100,
        description="Cuisine type (Italian, Mexican, Chinese, etc.)"
    )
    limit: Optional[int] = Field(
        default=12,
        ge=1,
        le=50,
        description="Number of recommendations to return"
    )

    @field_validator('ingredients')
    @classmethod
    def validate_ingredients(cls, v: List[str]) -> List[str]:
        """Clean and validate ingredient list"""
        # Remove empty strings and strip whitespace
        cleaned = [i.strip() for i in v if i and i.strip()]
        if not cleaned:
            raise ValueError('At least one ingredient is required')
        # Limit ingredient string length
        for ingredient in cleaned:
            if len(ingredient) > 200:
                raise ValueError(f'Ingredient name too long: {ingredient[:50]}...')
        return cleaned

    @field_validator('dietary_preference', 'cuisine_type')
    @classmethod
    def validate_text_fields(cls, v: Optional[str]) -> str:
        """Sanitize text input"""
        if not v:
            return ''
        # Remove potentially dangerous characters
        sanitized = ''.join(c for c in v if c.isalnum() or c in (' ', '-', '_'))
        return sanitized.strip()


class SearchRequest(BaseModel):
    """Schema for recipe search requests"""
    query: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Search query"
    )
    search_type: SearchType = Field(
        default=SearchType.NAME,
        description="Type of search to perform"
    )
    limit: Optional[int] = Field(
        default=50,
        ge=1,
        le=100,
        description="Maximum number of results"
    )
    max_time: Optional[int] = Field(
        default=None,
        ge=0,
        le=1440,
        description="Maximum cooking time in minutes (0 = no filter)"
    )
    max_calories: Optional[int] = Field(
        default=None,
        ge=0,
        le=5000,
        description="Maximum calories per serving (0 = no filter)"
    )
    min_ingredients: Optional[int] = Field(
        default=None,
        ge=0,
        le=100,
        description="Minimum number of ingredients (0 = no filter)"
    )
    max_ingredients: Optional[int] = Field(
        default=None,
        ge=0,
        le=100,
        description="Maximum number of ingredients (0 = no filter)"
    )

    @field_validator('query')
    @classmethod
    def validate_query(cls, v: str) -> str:
        """Sanitize search query"""
        if not v or not v.strip():
            raise ValueError('Search query cannot be empty')
        # Remove potentially dangerous characters but allow common search chars
        sanitized = ''.join(c for c in v if c.isalnum() or c in (' ', '-', '_', ',', '.', "'"))
        return sanitized.strip()

    @field_validator('max_time', 'max_calories', 'min_ingredients', 'max_ingredients', mode='before')
    @classmethod
    def coerce_zero_to_none(cls, v):
        """Treat 0 as 'no filter'"""
        if v is not None and v == 0:
            return None
        return v


class BatchRecipeRequest(BaseModel):
    """Schema for batch recipe requests"""
    recipe_ids: List[int] = Field(
        ...,
        min_length=1,
        max_length=100,
        description="List of recipe IDs to fetch"
    )

    @field_validator('recipe_ids')
    @classmethod
    def validate_recipe_ids(cls, v: List[int]) -> List[int]:
        """Validate recipe IDs"""
        if not v:
            raise ValueError('At least one recipe ID is required')
        # Remove duplicates and validate range
        unique_ids = list(set(v))
        for recipe_id in unique_ids:
            if recipe_id <= 0:
                raise ValueError(f'Invalid recipe ID: {recipe_id}')
        return unique_ids


class UserRegistration(BaseModel):
    """Schema for user registration"""
    username: str = Field(
        ...,
        min_length=3,
        max_length=50,
        description="Username (3-50 characters)"
    )
    email: str = Field(
        ...,
        max_length=255,
        description="Email address"
    )
    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="Password (minimum 8 characters)"
    )

    @field_validator('username')
    @classmethod
    def validate_username(cls, v: str) -> str:
        """Validate username format"""
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('Username can only contain letters, numbers, hyphens, and underscores')
        return v.lower()

    @field_validator('email')
    @classmethod
    def validate_email(cls, v: str) -> str:
        """Basic email validation"""
        if '@' not in v or '.' not in v.split('@')[1]:
            raise ValueError('Invalid email format')
        return v.lower()

    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password strength"""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v


class UserLogin(BaseModel):
    """Schema for user login"""
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=1, max_length=128)


class ErrorResponse(BaseModel):
    """Standard error response"""
    error: str = Field(..., description="Error message")
    code: Optional[str] = Field(default=None, description="Error code")
    details: Optional[dict] = Field(default=None, description="Additional error details")
