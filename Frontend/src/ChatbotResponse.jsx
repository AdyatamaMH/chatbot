import React, { useState, useEffect } from "react";
import axios from "axios";
import "./Chatbot.css";

const Chatbot = () => {
  const [language, setLanguage] = useState("id");
  const [theme, setTheme] = useState("light"); 
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  // Language
  useEffect(() => {
    setMessages([
      {
        sender: "bot",
        text:
          language === "id"
            ? "Halo! Saya adalah Chatbot Jago, asisten cerdas yang membantu Anda menganalisis data keuangan."
            : "Hello! I am Chatbot Jago, your smart assistant for financial data analysis.",
      },
    ]);
  }, [language]);

  // Initial theme
  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
  }, [theme]);

  const handleSend = async () => {
    if (!input.trim()) return;
    const newMessages = [...messages, { sender: "user", text: input }];
    setMessages(newMessages);
    setInput("");
    setIsLoading(true);
    try {
      const response = await axios.post("http://localhost:8000/query", { query: input });
      const botResponse =
        language === "id"
          ? `Respon: ${response.data.response}\nKonteks: ${JSON.stringify(response.data.context)}`
          : `Response: ${response.data.response}\nContext: ${JSON.stringify(response.data.context)}`;
      setMessages([...newMessages, { sender: "bot", text: botResponse }]);
    } catch (error) {
      console.error("Error:", error);
      setMessages([
        ...newMessages,
        {
          sender: "bot",
          text:
            language === "id"
              ? "Maaf, terjadi kesalahan saat memproses permintaan Anda. Coba lagi nanti."
              : "Sorry, an error occurred while processing your request. Please try again later.",
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const toggleLanguage = () => {
    setLanguage((prevLang) => (prevLang === "id" ? "en" : "id"));
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
          <h2 className="title">{language === "id" ? "Chatbot Jago" : "Chatbot Jago"}</h2>
        </div>
        <div className="controls">
          <button onClick={toggleLanguage} className="languageButton">
            {language === "id" ? "Switch to English" : "Ubah ke Bahasa Indonesia"}
          </button>
          <button onClick={toggleTheme} className="themeButton">
            {theme === "light" ? "Dark Mode" : "Light Mode"}
          </button>
        </div>
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
              {language === "id" ? "Mengetik..." : "Typing..."}
            </div>
          </div>
        )}
      </div>

      {/* Input Section */}
      <div className="inputArea">
        <input
          type="text"
          placeholder={
            language === "id"
              ? "Masukan pertanyaan, saya akan membantu menganalisisnya."
              : "Enter a question, I will help analyze it."
          }
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSend()}
          className="input"
        />
        <button onClick={handleSend} className="button">
          {language === "id" ? "Kirim" : "Send"}
        </button>
      </div>
    </div>
  );
};

export default Chatbot;
