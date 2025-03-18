import React from "react";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import Menu from "./Menu";
import Chatbot from "./ChatbotResponse";
import Chatbot2 from "./Chatbot2"

function App() {
    return (
        <Router>
            <Routes>
                <Route path="/" element={<Menu />} />
                <Route path="/chatbot" element={<Chatbot />} />
                <Route path="/chatbot2" element={<Chatbot2 />} />
            </Routes>
        </Router>
    );
}

export default App;
