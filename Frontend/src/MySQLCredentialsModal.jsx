import React, { useState } from 'react';
import axios from 'axios';
import './styles2/2/MySQLCredentialsModal.css';

const MySQLCredentialsModal = ({ onSuccess, onCancel }) => {
  const [host, setHost] = useState("");
  const [user, setUser] = useState("");
  const [password, setPassword] = useState("");
  const [database, setDatabase] = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await axios.post("http://localhost:8000/update_mysql_credentials", {
        host,
        user,
        password,
        database,
      });
      if (onSuccess) onSuccess();
    } catch (error) {
      console.error("Failed to update credentials:", error);
    }
  };

  return (
    <div className="modal-overlay">
      <div className="modal-container">
        <h2 className="modal-title">Edit MySQL Credentials</h2>
        <form onSubmit={handleSubmit} className="modal-form">
          <input
            type="text"
            value={host}
            onChange={(e) => setHost(e.target.value)}
            placeholder="Host"
            required
            className="modal-input"
          />
          <input
            type="text"
            value={user}
            onChange={(e) => setUser(e.target.value)}
            placeholder="User"
            required
            className="modal-input"
          />
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="Password"
            className="modal-input"
          />
          <input
            type="text"
            value={database}
            onChange={(e) => setDatabase(e.target.value)}
            placeholder="Database"
            required
            className="modal-input"
          />
          <div className="modal-button-group">
            <button type="button" onClick={onCancel} className="modal-button cancel-button">Cancel</button>
            <button type="submit" className="modal-button">Save</button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default MySQLCredentialsModal;
