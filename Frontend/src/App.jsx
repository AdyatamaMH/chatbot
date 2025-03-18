import React from "react";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import Menu from "./Menu";
import Chatbot from "./ChatbotResponse";

function App() {
    return (
        <Router>
            <Routes>
                <Route path="/" element={<Menu />} />
                <Route path="/chatbot" element={<Chatbot />} />
            </Routes>
        </Router>
    );
}

export default App;
