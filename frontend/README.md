# Smart Recipe Recommender - Frontend

React-based web application for discovering and managing recipes.

## Setup

1. Install dependencies:
```powershell
npm install
```

2. Ensure backend is running on port 5000

## Running

Development mode:
```powershell
npm start
```

Runs on: http://localhost:3000

Build for production:
```powershell
npm run build
```

## Features

- **Home Page**: Get personalized recipe recommendations
- **Search Page**: Find recipes by name, ingredient, or cuisine
- **Recipe Detail**: View complete recipe information
- **Favorites**: Save and manage favorite recipes

## Project Structure

```
src/
├── components/          # Reusable components
│   ├── Header.js       # Navigation header
│   └── RecipeCard.js   # Recipe display card
├── pages/              # Page components
│   ├── Home.js         # Recommendation page
│   ├── Search.js       # Search page
│   ├── Favorites.js    # Favorites page
│   └── RecipeDetail.js # Recipe details page
├── App.js              # Main app component
└── index.js            # Entry point
```

## Technologies

- React 18
- React Router 6
- Axios for API calls
- React Icons
- Local Storage for favorites

## API Integration

The frontend communicates with the Flask backend API at `http://localhost:5000`

Proxy is configured in `package.json` for development.

## Styling

- Custom CSS with modern design
- Responsive layout for mobile devices
- Gradient backgrounds
- Smooth animations and transitions

## Local Storage

Favorites are stored in browser's localStorage:
- Key: `favorites`
- Value: JSON array of recipe IDs

## Available Scripts

- `npm start` - Start development server
- `npm run build` - Build for production
- `npm test` - Run tests
- `npm run eject` - Eject from Create React App

## Browser Support

- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)
