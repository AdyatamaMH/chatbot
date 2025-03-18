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
import './styles/file-upload.css';

const Chatbot = () => {
  const [theme, setTheme] = useState("light");
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [file, setFile] = useState(null);
  const { t, i18n } = useTranslation(); 

  // Language
  useEffect(() => {
    setMessages([{ sender: "bot", text: t("welcomeMessage") }]);
  }, [t]);

  // Initial theme
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
      const response = await axios.post("http://localhost:8000/query", { query: input });
      const botResponse = t("responseMessage", {
        response: response.data.response,
        context: JSON.stringify(response.data.context),
      });
      setMessages([...newMessages, { sender: "bot", text: botResponse }]);
    } catch (error) {
      console.error("Error:", error);
      setMessages([...newMessages, { sender: "bot", text: t("errorMessage") }]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleFileUpload = async (e) => {
    const uploadedFile = e.target.files[0];
    if (!uploadedFile || isUploading) return;
    setFile(uploadedFile);

    const formData = new FormData();
    formData.append("file", uploadedFile);

    try {
      setIsUploading(true);
      await axios.post("http://localhost:8000/upload_csv", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      alert(t("uploadSuccessMessage"));
    } catch (error) {
      console.error("File upload error:", error);
      alert(t("uploadErrorMessage"));
    } finally {
      setIsUploading(false);
    }
  };

  const toggleLanguage = () => {
    const newLang = i18n.language === "id" ? "en" : "id";
    i18n.changeLanguage(newLang); 
  };

  const toggleTheme = () => {
    setTheme((prevTheme) => (prevTheme === "light" ? "dark" : "light"));
  };

  return (
    <div className="container">
      {/* Header Section */}
      <div className="header">
        <div className="title-container">
          <img src="/pictures/jago-icon.png" alt="Jago Icon" className="icon" />
          <h2 className="title">{t("chatbotTitle")}</h2>
        </div>
        <div className="controls">
          <button onClick={toggleLanguage} className="languageButton">
            {t("switchLanguage")}
          </button>
          <button onClick={toggleTheme} className="themeButton">
            {theme === "light" ? "Dark Mode" : "Light Mode"}
          </button>
        </div>
      </div>

      {/* Back to Menu Button */}
      <div className="menu-back">
        <Link to="/" className="button">{t("backToMenu")}</Link>
      </div>

      {/* Chatbox Section */}
      <div className="chatbox">
        {messages.map((msg, index) => (
          <div
            key={index}
            className="message"
            style={{
              justifyContent: msg.sender === "user" ? "flex-end" : "flex-start",
            }}
          >
            <div
              className="bubble"
              style={{
                backgroundColor: msg.sender === "user" ? "#0078D7" : "#e5e5e5",
                color: msg.sender === "user" ? "#fff" : "#000",
              }}
            >
              {msg.text}
            </div>
          </div>
        ))}
        {isLoading && (
          <div className="message" style={{ justifyContent: "flex-start" }}>
            <div className="bubble" style={{ backgroundColor: "#e5e5e5" }}>
              {t("loadingMessage")}
            </div>
          </div>
        )}
      </div>

      {/* Input and File Upload Section */}
      <div className="input-container">
        <div className="file-upload">
          <input 
            type="file" 
            accept=".csv" 
            onChange={handleFileUpload} 
            id="file-input" 
          />
          <button 
            onClick={() => document.getElementById("file-input").click()} 
            className="upload-icon-button"
            disabled={isUploading}
          >
            📂
          </button>
        </div>

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
