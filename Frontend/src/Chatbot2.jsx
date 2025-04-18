import React, { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import axios from "axios";
import { useTranslation } from "react-i18next";
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

  const refreshTable = async () => {
    setSelectedRows([]);
    await fetchTableData();
  };

  const selectAllRows = () => {
    setSelectedRows(tableData);
  };

const handleSend = async () => {
  if (!input.trim() || isLoading) return;

  const newMessages = [...messages, { sender: "user", text: input }];
  setMessages(newMessages);
  setInput("");
  setIsLoading(true);

  try {
    const response = await axios.post("http://localhost:8000/query_mysql_ai", {
      query: input,
      selectedRows: selectedRows
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

  const handleRowSelect = (row) => {
    setSelectedRows((prev) =>
      prev.some((r) => r.actor_id === row.actor_id)
        ? prev.filter((r) => r.actor_id !== row.actor_id)
        : [...prev, row]
    );
  };

  return (
    <>
      <div className="custom-top-bar">
        <Link to="/" className="custom-button">{t("backToMenu")}</Link>
        <div className="custom-controls">
          <button onClick={toggleLanguage} className="custom-button">{t("switchLanguage")}</button>
          <button onClick={toggleTheme} className="custom-button">
            {theme === "light" ? "Dark Mode" : "Light Mode"}
          </button>
        </div>
      </div>

      <div className="custom-split-container">
        <div className="custom-chat-container">
          <div className="custom-header">
            <div className="custom-title-container">
              <img src="/pictures/jago-icon.png" alt="Jago Icon" className="custom-icon" />
              <h2 className="custom-title">{t("chatbotTitle2")}</h2>
            </div>
          </div>

          <div className="custom-chatbox">
            {messages.map((msg, index) => (
              <div
                key={index}
                className={`custom-message ${msg.sender === "user" ? "user-message" : "bot-message"}`}
              >
                <div className="custom-bubble">{msg.text}</div>
              </div>
            ))}
            {isLoading && (
              <div className="custom-message bot-message">
                <div className="custom-bubble">{t("loadingMessage")}</div>
              </div>
            )}
          </div>

          <div className="custom-input-container">
            <input
              type="text"
              placeholder={t("placeholder")}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSend()}
              className="custom-input"
            />
            <button onClick={handleSend} className="custom-button" disabled={isLoading}>
              {isLoading ? t("sending") + "..." : t("sendButton")}
            </button>
          </div>
        </div>

        <div className="custom-table-container">
          <h3 className="custom-table-title">{t("mysqlTableTitle")}</h3>
          <div style={{ display: "flex", gap: "10px" }}>
            <button onClick={refreshTable} className="custom-button">{t("refreshData")}</button>
            <button onClick={selectAllRows} className="custom-button">{t("selectAll")}</button>
            <button onClick={() => setSelectedRows([])} className="custom-button">{t("deselectAll")}</button>
          </div>

          <table className="custom-table">
            <thead>
              <tr>
                <th>{t("select")}</th>
                {tableData.length > 0 &&
                  Object.keys(tableData[0])
                    .filter(key => key !== "actor_id")
                    .map((key) => <th key={key}>{key}</th>)
                }
              </tr>
            </thead>
            <tbody>
              {tableData.map((row, index) => (
                <tr
                  key={index}
                  onClick={() => handleRowSelect(row)}
                  className={selectedRows.some(r => r.actor_id === row.actor_id) ? "custom-selected" : ""}
                >
                  <td>
                    <input
                      type="checkbox"
                      checked={selectedRows.some(r => r.actor_id === row.actor_id)}
                      onChange={(e) => {
                        e.stopPropagation();
                        handleRowSelect(row);
                      }}
                    />
                  </td>
                  {Object.keys(row)
                    .filter(key => key !== "actor_id")
                    .map((key) => <td key={key}>{row[key]}</td>)
                  }
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
