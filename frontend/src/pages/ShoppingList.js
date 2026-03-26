import React, { useState, useEffect } from 'react';
import { FaShoppingCart, FaTrash, FaPrint, FaCheck } from 'react-icons/fa';
import { useToast } from '../context/ToastContext';
import { useConfirm } from '../context/ConfirmContext';
import './ShoppingList.css';

function ShoppingList() {
  const { toast } = useToast();
  const { confirm } = useConfirm();
  const [shoppingList, setShoppingList] = useState([]);
  const [groupedItems, setGroupedItems] = useState({});

  useEffect(() => {
    loadShoppingList();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const loadShoppingList = () => {
    const savedList = JSON.parse(localStorage.getItem('shoppingList') || '[]');
    setShoppingList(savedList);
    groupByCategory(savedList);
  };

  const groupByCategory = (items) => {
    const categories = {
      'Produce': ['vegetable', 'fruit', 'tomato', 'onion', 'garlic', 'pepper', 'carrot', 'potato', 'lettuce', 'spinach'],
      'Meat & Poultry': ['chicken', 'beef', 'pork', 'turkey', 'meat', 'sausage', 'bacon'],
      'Dairy & Eggs': ['milk', 'cheese', 'butter', 'egg', 'cream', 'yogurt'],
      'Pantry': ['flour', 'sugar', 'salt', 'pepper', 'oil', 'rice', 'pasta', 'bread'],
      'Spices & Herbs': ['oregano', 'basil', 'thyme', 'cumin', 'paprika', 'cinnamon', 'vanilla'],
      'Condiments': ['sauce', 'vinegar', 'mustard', 'ketchup', 'mayo'],
      'Beverages': ['water', 'juice', 'wine', 'beer', 'soda']
    };

    const grouped = { 'Other': [] };
    
    items.forEach(item => {
      let categorized = false;
      for (const [category, keywords] of Object.entries(categories)) {
        if (keywords.some(kw => item.name.toLowerCase().includes(kw))) {
          if (!grouped[category]) grouped[category] = [];
          grouped[category].push(item);
          categorized = true;
          break;
        }
      }
      if (!categorized) {
        grouped['Other'].push(item);
      }
    });

    setGroupedItems(grouped);
  };

  const toggleItem = (itemId) => {
    const updated = shoppingList.map(item =>
      item.id === itemId ? { ...item, checked: !item.checked } : item
    );
    setShoppingList(updated);
    localStorage.setItem('shoppingList', JSON.stringify(updated));
    groupByCategory(updated);
  };

  const removeItem = (itemId) => {
    const updated = shoppingList.filter(item => item.id !== itemId);
    setShoppingList(updated);
    localStorage.setItem('shoppingList', JSON.stringify(updated));
    groupByCategory(updated);
  };

  const clearList = async () => {
    const ok = await confirm({
      title: 'Clear Shopping List',
      message: `Remove all ${shoppingList.length} items from your shopping list?`,
      confirmText: 'Clear All',
      cancelText: 'Keep them',
      variant: 'warning',
    });
    if (!ok) return;

    setShoppingList([]);
    setGroupedItems({});
    localStorage.setItem('shoppingList', '[]');
    toast.success('Shopping list cleared');
  };

  const printList = () => {
    window.print();
  };

  return (
    <div className="shopping-list-page">
      <div className="container">
        <div className="shopping-header">
          <div className="header-content">
            <FaShoppingCart className="page-icon" />
            <div>
              <h1 className="page-title">Shopping List</h1>
              <p className="page-subtitle">
                {shoppingList.length} item{shoppingList.length !== 1 ? 's' : ''} total
                {shoppingList.filter(i => i.checked).length > 0 && 
                  ` • ${shoppingList.filter(i => i.checked).length} checked`}
              </p>
            </div>
          </div>

          {shoppingList.length > 0 && (
            <div className="header-actions">
              <button className="btn btn-secondary" onClick={printList}>
                <FaPrint />
                Print
              </button>
              <button className="btn btn-danger" onClick={clearList}>
                <FaTrash />
                Clear All
              </button>
            </div>
          )}
        </div>

        {shoppingList.length === 0 ? (
          <div className="empty-state">
            <FaShoppingCart className="empty-icon" />
            <h2>Your shopping list is empty</h2>
            <p>Add ingredients from recipes to build your list!</p>
          </div>
        ) : (
          <div className="shopping-categories">
            {Object.entries(groupedItems).map(([category, items]) => 
              items.length > 0 && (
                <div key={category} className="category-section">
                  <h2 className="category-title">{category}</h2>
                  <div className="items-list">
                    {items.map(item => (
                      <div key={item.id} className={`shopping-item ${item.checked ? 'checked' : ''}`}>
                        <label className="item-checkbox">
                          <input
                            type="checkbox"
                            checked={item.checked}
                            onChange={() => toggleItem(item.id)}
                          />
                          <span className="checkmark">
                            {item.checked && <FaCheck />}
                          </span>
                          <span className="item-name">{item.name}</span>
                          {item.quantity && <span className="item-quantity">({item.quantity})</span>}
                        </label>
                        <button 
                          className="remove-btn"
                          onClick={() => removeItem(item.id)}
                        >
                          <FaTrash />
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
              )
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default ShoppingList;
