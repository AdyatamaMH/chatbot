import React from "react";
import { Link } from "react-router-dom";
import './styles/menu.css';

const Menu = () => {
  return (
    <div className="menu-container">
      <h1>Welcome to the Jago Menu</h1>
      <p>Select an option:</p>
      <ul>
        <li>
          <strong>Manual</strong>
          <ul>
            <li><Link className="menu-button" to="/chatbot">📂 CSV file</Link></li>
            <li><Link className="menu-button" to="/chatbot2">🐬 MySQL</Link></li>
          </ul>
        </li>
        <li>
          <strong>Automatic</strong>
          <ul>
            <li><Link className="menu-button" to="/chatbot/automatic/local">💻 Locally</Link></li>
            <li><Link className="menu-button" to="/chatbot/automatic/online">🌍 Online</Link></li>
          </ul>
        </li>
      </ul>
    </div>
  );
};

export default Menu;
