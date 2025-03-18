import React, { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import axios from "axios";
import { useTranslation } from "react-i18next";
import './styles/base.css';
import './styles/theme.css';
import './styles/layout.css';
import './styles/chatbox.css';
import './styles/buttons.css';
import './styles/inputs.css';

const Chatbot = () => {
  const [theme, setTheme] = useState("light");
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const { t, i18n } = useTranslation();

  useEffect(() => {
    setMessages([{ sender: "bot", text: t("welcomeMessage") }]);
  }, [t]);

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
  }, [theme]);

  const handleSend = async () => {
    if (!input.trim() || isLoading) return;
    
    const newMessages = [...messages, { sender: "user", text: input }];
    setMessages(newMessages);
    setInput("");
    setIsLoading(true);

    try {
      const response = await axios.post("http://localhost:8000/query_mysql", { query: input });
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

  return (
    <div className="container">
      <div className="header">
        <div className="title-container">
          <img src="/pictures/jago-icon.png" alt="Jago Icon" className="icon" />
          <h2 className="title">{t("chatbotTitle2")}</h2>
        </div>
        <div className="controls">
          <button onClick={toggleLanguage} className="languageButton">{t("switchLanguage")}</button>
          <button onClick={toggleTheme} className="themeButton">
            {theme === "light" ? "Dark Mode" : "Light Mode"}
          </button>
        </div>
      </div>

      <div className="menu-back">
        <Link to="/" className="button">{t("backToMenu")}</Link>
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
  );
};

export default Chatbot;
