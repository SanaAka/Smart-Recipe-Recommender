/**
 * Category-based fallback images for recipes.
 * Uses hardcoded Unsplash CDN URLs (no API calls needed).
 * These are static URLs that load instantly for any recipe,
 * even when no real image has been fetched from Unsplash yet.
 */

const CATEGORY_IMAGES = {
  dessert:    'https://images.unsplash.com/photo-1551024601-bec78aea704b?w=400&h=300&fit=crop',
  cake:       'https://images.unsplash.com/photo-1578985545062-69928b1d9587?w=400&h=300&fit=crop',
  cookie:     'https://images.unsplash.com/photo-1499636136210-6f4ee915583e?w=400&h=300&fit=crop',
  pie:        'https://images.unsplash.com/photo-1621743478914-cc8a86d7e7b5?w=400&h=300&fit=crop',
  soup:       'https://images.unsplash.com/photo-1547592166-23ac45744acd?w=400&h=300&fit=crop',
  salad:      'https://images.unsplash.com/photo-1512621776951-a57141f2eefd?w=400&h=300&fit=crop',
  pasta:      'https://images.unsplash.com/photo-1621996346565-e3dbc646d9a9?w=400&h=300&fit=crop',
  chicken:    'https://images.unsplash.com/photo-1598103442097-8b74394b95c6?w=400&h=300&fit=crop',
  beef:       'https://images.unsplash.com/photo-1546833999-b9f581a1996d?w=400&h=300&fit=crop',
  pork:       'https://images.unsplash.com/photo-1432139555190-58524dae6a55?w=400&h=300&fit=crop',
  seafood:    'https://images.unsplash.com/photo-1615141982883-c7ad0e69fd62?w=400&h=300&fit=crop',
  fish:       'https://images.unsplash.com/photo-1467003909585-2f8a72700288?w=400&h=300&fit=crop',
  shrimp:     'https://images.unsplash.com/photo-1565680018434-b513d5e5fd47?w=400&h=300&fit=crop',
  rice:       'https://images.unsplash.com/photo-1536304929831-ee1ca9d44906?w=400&h=300&fit=crop',
  bread:      'https://images.unsplash.com/photo-1509440159596-0249088772ff?w=400&h=300&fit=crop',
  sandwich:   'https://images.unsplash.com/photo-1528735602780-2552fd46c7af?w=400&h=300&fit=crop',
  pizza:      'https://images.unsplash.com/photo-1565299624946-b28f40a0ae38?w=400&h=300&fit=crop',
  burger:     'https://images.unsplash.com/photo-1568901346375-23c9450c58cd?w=400&h=300&fit=crop',
  breakfast:  'https://images.unsplash.com/photo-1533089860892-a7c6f0a88666?w=400&h=300&fit=crop',
  egg:        'https://images.unsplash.com/photo-1482049016688-2d3e1b311543?w=400&h=300&fit=crop',
  smoothie:   'https://images.unsplash.com/photo-1505252585461-04db1eb84625?w=400&h=300&fit=crop',
  drink:      'https://images.unsplash.com/photo-1544145945-f90425340c7e?w=400&h=300&fit=crop',
  cocktail:   'https://images.unsplash.com/photo-1514362545857-3bc16c4c7d1b?w=400&h=300&fit=crop',
  vegetable:  'https://images.unsplash.com/photo-1540420773420-3366772f4999?w=400&h=300&fit=crop',
  curry:      'https://images.unsplash.com/photo-1455619452474-d2be8b1e70cd?w=400&h=300&fit=crop',
  steak:      'https://images.unsplash.com/photo-1544025162-d76694265947?w=400&h=300&fit=crop',
  bbq:        'https://images.unsplash.com/photo-1529193591184-b1d58069ecdd?w=400&h=300&fit=crop',
  taco:       'https://images.unsplash.com/photo-1565299585323-38d6b0865b47?w=400&h=300&fit=crop',
  sushi:      'https://images.unsplash.com/photo-1579871494447-9811cf80d66c?w=400&h=300&fit=crop',
  noodle:     'https://images.unsplash.com/photo-1569718212165-3a8278d5f624?w=400&h=300&fit=crop',
  stew:       'https://images.unsplash.com/photo-1534939561126-855b8675edd7?w=400&h=300&fit=crop',
  sauce:      'https://images.unsplash.com/photo-1472476443507-c7a5948772fc?w=400&h=300&fit=crop',
};

// Fallback for recipes that match no specific category
const DEFAULT_FOOD = 'https://images.unsplash.com/photo-1504674900247-0877df9cc836?w=400&h=300&fit=crop';

// Keywords mapped to categories (searched in recipe name)
const KEYWORD_MAP = [
  { keywords: ['cake', 'cupcake', 'cheesecake', 'brownie', 'muffin', 'frosting'], category: 'cake' },
  { keywords: ['cookie', 'biscuit', 'shortbread', 'macaroon', 'macaron'], category: 'cookie' },
  { keywords: ['pie', 'tart', 'cobbler', 'crumble', 'crisp'], category: 'pie' },
  { keywords: ['dessert', 'candy', 'fudge', 'truffle', 'pudding', 'mousse', 'tiramisu', 'ice cream', 'gelato', 'sorbet', 'chocolate', 'caramel', 'sweet'], category: 'dessert' },
  { keywords: ['soup', 'chowder', 'bisque', 'broth', 'gazpacho', 'minestrone'], category: 'soup' },
  { keywords: ['stew', 'chili', 'goulash', 'casserole', 'hotpot'], category: 'stew' },
  { keywords: ['salad', 'slaw', 'coleslaw'], category: 'salad' },
  { keywords: ['pasta', 'spaghetti', 'penne', 'fettuccine', 'linguine', 'macaroni', 'lasagna', 'ravioli', 'gnocchi', 'carbonara', 'alfredo', 'bolognese'], category: 'pasta' },
  { keywords: ['noodle', 'ramen', 'pho', 'udon', 'lo mein', 'pad thai', 'chow mein'], category: 'noodle' },
  { keywords: ['sushi', 'sashimi', 'maki', 'temaki'], category: 'sushi' },
  { keywords: ['pizza', 'flatbread', 'calzone'], category: 'pizza' },
  { keywords: ['burger', 'hamburger', 'slider'], category: 'burger' },
  { keywords: ['sandwich', 'panini', 'wrap', 'sub', 'hoagie', 'blt', 'club'], category: 'sandwich' },
  { keywords: ['taco', 'burrito', 'enchilada', 'quesadilla', 'fajita', 'nachos', 'tamale'], category: 'taco' },
  { keywords: ['curry', 'masala', 'tikka', 'tandoori', 'korma', 'vindaloo', 'biryani'], category: 'curry' },
  { keywords: ['chicken', 'poultry', 'turkey', 'wings', 'drumstick', 'thigh'], category: 'chicken' },
  { keywords: ['steak', 'filet', 'ribeye', 'sirloin', 't-bone', 'prime rib'], category: 'steak' },
  { keywords: ['beef', 'veal', 'meatball', 'meatloaf', 'brisket', 'roast beef'], category: 'beef' },
  { keywords: ['pork', 'bacon', 'ham', 'prosciutto', 'sausage', 'bratwurst', 'pulled pork', 'ribs'], category: 'pork' },
  { keywords: ['bbq', 'barbecue', 'grilled', 'grill', 'smoked'], category: 'bbq' },
  { keywords: ['shrimp', 'prawn', 'scampi', 'ceviche'], category: 'shrimp' },
  { keywords: ['fish', 'salmon', 'tuna', 'cod', 'tilapia', 'halibut', 'trout', 'bass', 'mahi'], category: 'fish' },
  { keywords: ['seafood', 'crab', 'lobster', 'mussel', 'clam', 'oyster', 'calamari', 'octopus', 'squid'], category: 'seafood' },
  { keywords: ['rice', 'fried rice', 'pilaf', 'risotto', 'paella', 'jambalaya'], category: 'rice' },
  { keywords: ['bread', 'roll', 'baguette', 'focaccia', 'sourdough', 'brioche', 'dough', 'pretzel', 'cornbread', 'biscuit'], category: 'bread' },
  { keywords: ['breakfast', 'pancake', 'waffle', 'french toast', 'oatmeal', 'granola', 'cereal', 'brunch'], category: 'breakfast' },
  { keywords: ['egg', 'omelet', 'omelette', 'frittata', 'quiche', 'scramble'], category: 'egg' },
  { keywords: ['smoothie', 'milkshake', 'shake', 'lassi'], category: 'smoothie' },
  { keywords: ['cocktail', 'margarita', 'mojito', 'martini', 'sangria', 'daiquiri'], category: 'cocktail' },
  { keywords: ['drink', 'lemonade', 'punch', 'juice', 'iced tea', 'cooler', 'beverage'], category: 'drink' },
  { keywords: ['sauce', 'dressing', 'dip', 'salsa', 'guacamole', 'hummus', 'marinade', 'glaze', 'gravy', 'pesto', 'aioli'], category: 'sauce' },
  { keywords: ['vegetable', 'vegan', 'vegetarian', 'roasted veggie', 'tofu', 'tempeh'], category: 'vegetable' },
];

/**
 * Return a category-appropriate fallback image URL based on recipe name.
 * No API call — instant, works for all 2M+ recipes.
 *
 * @param {string} recipeName - The recipe's name/title
 * @returns {string} A static Unsplash CDN URL
 */
export function getCategoryFallback(recipeName) {
  if (!recipeName) return DEFAULT_FOOD;

  const lower = recipeName.toLowerCase();

  for (const { keywords, category } of KEYWORD_MAP) {
    for (const kw of keywords) {
      if (lower.includes(kw)) {
        return CATEGORY_IMAGES[category];
      }
    }
  }

  return DEFAULT_FOOD;
}

export default getCategoryFallback;
