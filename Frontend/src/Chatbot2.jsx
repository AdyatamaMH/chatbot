import React, { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import axios from "axios";
import { useTranslation } from "react-i18next";
import ReactMarkdown from "react-markdown";
import MyChartComponent from "./MyChartComponent";
import MySQLCredentialsModal from "./MySQLCredentialsModal";

import './styles2/2/layout.css';
import './styles2/2/chatbox.css';
import './styles2/2/buttons.css';
import './styles2/2/inputs.css';
import './styles2/2/table.css';

const Chatbot = () => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const { t, i18n } = useTranslation();
  const [tableData, setTableData] = useState([]);
  const [selectedRows, setSelectedRows] = useState([]);
  const [tableList, setTableList] = useState([]);
  const [currentTableIndex, setCurrentTableIndex] = useState(0);

  const [showCredentials, setShowCredentials] = useState(false);

  useEffect(() => {
    setMessages([{ sender: "bot", text: t("welcomeMessage") }]);
    fetchTableList();
  }, [t]);

  useEffect(() => {
    if (tableList.length > 0) fetchTableData(tableList[currentTableIndex]);
  }, [tableList, currentTableIndex]);

  const fetchTableList = async () => {
    try {
      const response = await axios.get("http://localhost:8000/get_table_list");
      setTableList(response.data);
    } catch (error) {
      console.error("Error fetching table list:", error);
    }
  };

  const fetchTableData = async (tableName) => {
    try {
      const response = await axios.get(`http://localhost:8000/get_mysql_data/${tableName}`);
      setTableData(response.data);
      setSelectedRows([]);
    } catch (error) {
      console.error("Error fetching table data:", error);
    }
  };

  const refreshTable = () => {
    if (tableList.length > 0) {
      fetchTableData(tableList[currentTableIndex]);
    }
  };

  const selectAllRows = () => {
    setSelectedRows(tableData);
  };

  const toggleLanguage = () => {
    const newLang = i18n.language === "id" ? "en" : "id";
    i18n.changeLanguage(newLang);
  };

  const handleRowSelect = (row) => {
    setSelectedRows((prev) =>
      prev.some((r) => r.id === row.id)
        ? prev.filter((r) => r.id !== row.id)
        : [...prev, row]
    );
  };

  const goToNextTable = () => {
    if (tableList.length > 0) {
      setCurrentTableIndex((prev) => (prev + 1) % tableList.length);
    }
  };

  const goToPreviousTable = () => {
    if (tableList.length > 0) {
      setCurrentTableIndex((prev) => (prev - 1 + tableList.length) % tableList.length);
    }
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

      const { response: botText, chartData, imageBase64 } = response.data;

      const botMessage = {
        sender: "bot",
        text: botText || t("noResponseMessage"),
        chartData: chartData || null,
        imageBase64: imageBase64 || null
      };

      setMessages([...newMessages, botMessage]);
    } catch (error) {
      console.error("Error fetching response:", error);
      setMessages([...newMessages, { sender: "bot", text: t("errorMessage") }]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <>
      <div className="custom-top-bar">
        <Link to="/" className="custom-button">{t("backToMenu")}</Link>
        <div className="custom-controls">
          <button onClick={toggleLanguage} className="custom-button">{t("switchLanguage")}</button>
          <button onClick={() => setShowCredentials(!showCredentials)} className="custom-button">
            {showCredentials ? "Hide Credentials" : "Edit MySQL Credentials"}
          </button>
        </div>
      </div>

      {showCredentials && (
  <MySQLCredentialsModal
    onSuccess={() => {
      fetchTableList();
      setShowCredentials(false);
    }}
    onCancel={() => setShowCredentials(false)}
  />
)}

      <div className="custom-split-container">
        <div className="custom-chat-container">
          <div className="custom-header">
            <div className="custom-title-container">
              <img src="/pictures/icon.png" alt="Icon" className="custom-icon" />
              <h2 className="custom-title">{t("chatbotTitle2")}</h2>
            </div>
          </div>

          <div className="custom-chatbox">
            {messages.map((msg, index) => (
              <div
                key={index}
                className={`custom-message ${msg.sender === "user" ? "user-message" : "bot-message"}`}
              >
                <div className="custom-bubble">
                  {msg.text && (msg.sender === "bot"
                    ? <ReactMarkdown>{msg.text}</ReactMarkdown>
                    : msg.text)}

                  {msg.chartData && (
                    <div style={{ maxWidth: "100%" }}>
                      <MyChartComponent data={msg.chartData} />
                    </div>
                  )}

                  {msg.imageBase64 && (
                    <img
                      src={`data:image/png;base64,${msg.imageBase64}`}
                      alt="Graph"
                      style={{ maxWidth: "100%", marginTop: "10px" }}
                    />
                  )}
                </div>
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

          <table className="custom-table">
            <thead>
              <tr>
                <th>{t("select")}</th>
                {tableData.length > 0 &&
                  Object.keys(tableData[0])
                    .filter(key => key !== "id")
                    .map((key) => <th key={key}>{key}</th>)
                }
              </tr>
            </thead>
            <tbody>
              {tableData.map((row, index) => (
                <tr
                  key={index}
                  onClick={() => handleRowSelect(row)}
                  className={selectedRows.some(r => r.id === row.id) ? "custom-selected" : ""}
                >
                  <td>
                    <input
                      type="checkbox"
                      checked={selectedRows.some(r => r.id === row.id)}
                      onChange={(e) => {
                        e.stopPropagation();
                        handleRowSelect(row);
                      }}
                    />
                  </td>
                  {Object.keys(row)
                    .filter(key => key !== "id")
                    .map((key) => <td key={key}>{row[key]}</td>)
                  }
                </tr>
              ))}
            </tbody>
          </table>

          <div style={{ display: "flex", gap: "10px", marginTop: "10px" }}>
            <button onClick={refreshTable} className="custom-button">{t("refreshData")}</button>
            <button onClick={selectAllRows} className="custom-button">{t("selectAll")}</button>
            <button onClick={() => setSelectedRows([])} className="custom-button">{t("deselectAll")}</button>
            <button onClick={goToPreviousTable} className="custom-button">{t("prevTable")}</button>
            <button onClick={goToNextTable} className="custom-button">{t("nextTable")}</button>
          </div>
        </div>
      </div>
    </>
  );
};

export default Chatbot;
