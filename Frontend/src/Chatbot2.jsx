import React, { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import axios from "axios";
import { useTranslation } from "react-i18next";
import './styles2/2/theme.css';
import './styles2/2/layout.css';
import './styles2/2/chatbox.css';
import './styles2/2/buttons.css';
import './styles2/2/inputs.css';
import './styles2/2/table.css';

const Chatbot = () => {
  const [theme, setTheme] = useState("light");
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const { t, i18n } = useTranslation();

  // MySQL Data States
  const [tableData, setTableData] = useState([]);
  const [selectedRows, setSelectedRows] = useState([]);

  useEffect(() => {
    setMessages([{ sender: "bot", text: t("welcomeMessage") }]);
    fetchTableData();
  }, [t]);

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
  }, [theme]);

  const fetchTableData = async () => {
    try {
      const response = await axios.get("http://localhost:8000/get_mysql_data");
      setTableData(response.data);
    } catch (error) {
      console.error("Error fetching table data:", error);
    }
  };

  const handleSend = async () => {
    if (!input.trim() || isLoading) return;
    
    const newMessages = [...messages, { sender: "user", text: input }];
    setMessages(newMessages);
    setInput("");
    setIsLoading(true);

    try {
      const response = await axios.post("http://localhost:8000/query_mysql", { 
        query: input, 
        selectedRows 
      });
      const botResponse = response.data.response || t("noResponseMessage");
      setMessages([...newMessages, { sender: "bot", text: botResponse }]);
    } catch (error) {
      console.error("Error fetching response:", error);
      setMessages([...newMessages, { sender: "bot", text: t("errorMessage") }]);
    } finally {
      setIsLoading(false);
    }
  };

  const toggleLanguage = () => {
    const newLang = i18n.language === "id" ? "en" : "id";
    i18n.changeLanguage(newLang);
  };

  const toggleTheme = () => {
    setTheme(prevTheme => (prevTheme === "light" ? "dark" : "light"));
  };

  // Handle Row Selection
  const handleRowSelect = (row) => {
    setSelectedRows((prev) =>
      prev.includes(row) ? prev.filter((r) => r !== row) : [...prev, row]
    );
  };

  return (
    <>
      {/* Top Navigation Bar */}
      <div className="top-bar">
        <Link to="/" className="button">{t("backToMenu")}</Link>
        <div className="controls">
          <button onClick={toggleLanguage} className="button">{t("switchLanguage")}</button>
          <button onClick={toggleTheme} className="button">
            {theme === "light" ? "Dark Mode" : "Light Mode"}
          </button>
        </div>
      </div>

      {/* Split Container for Chatbox and MySQL Table */}
      <div className="split-container">
        {/* Left: Chatbox */}
        <div className="chat-container">
          <div className="header">
            <div className="title-container">
              <img src="/pictures/jago-icon.png" alt="Jago Icon" className="icon" />
              <h2 className="title">{t("chatbotTitle2")}</h2>
            </div>
          </div>

          <div className="chatbox">
            {messages.map((msg, index) => (
              <div key={index} className="message" style={{ justifyContent: msg.sender === "user" ? "flex-end" : "flex-start" }}>
                <div className="bubble" style={{
                  backgroundColor: msg.sender === "user" ? "#0078D7" : "#e5e5e5",
                  color: msg.sender === "user" ? "#fff" : "#000"
                }}>
                  {msg.text}
                </div>
              </div>
            ))}
            {isLoading && (
              <div className="message" style={{ justifyContent: "flex-start" }}>
                <div className="bubble" style={{ backgroundColor: "#e5e5e5" }}>{t("loadingMessage")}</div>
              </div>
            )}
          </div>

          <div className="input-container">
            <input
              type="text"
              placeholder={t("placeholder")}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSend()}
              className="input"
            />
            <button onClick={handleSend} className="button" disabled={isLoading}>
              {isLoading ? t("sending") + "..." : t("sendButton")}
            </button>
          </div>
        </div>

        {/* Right: MySQL Table Viewer */}
        <div className="table-container">
          <h3>{t("mysqlTableTitle")}</h3>
          <table>
            <thead>
              <tr>
                <th>{t("select")}</th>
                <th>{t("column1")}</th>
                <th>{t("column2")}</th>
                <th>{t("column3")}</th>
              </tr>
            </thead>
            <tbody>
              {tableData.map((row, index) => (
                <tr key={index} onClick={() => handleRowSelect(row)} className={selectedRows.includes(row) ? "selected" : ""}>
                  <td>
                    <input 
                      type="checkbox" 
                      checked={selectedRows.includes(row)} 
                      onChange={() => handleRowSelect(row)} 
                    />
                  </td>
                  <td>{row.column1}</td>
                  <td>{row.column2}</td>
                  <td>{row.column3}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </>
  );
};

export default Chatbot;
