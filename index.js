const fs = require('fs');
const path = require('path');

// Chat API handler inline
async function handleChat(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') {
    res.status(200).end();
    return;
  }

  if (req.method !== 'POST') {
    res.status(405).json({ error: 'Method not allowed' });
    return;
  }

  try {
    const { message } = req.body;

    if (!message) {
      res.status(400).json({ error: 'Message is required' });
      return;
    }

    let reply = '';

    if (message.toLowerCase().includes('hello') || message.toLowerCase().includes('hi')) {
      reply = "Hello! 👋 I'm Claw AI, your intelligent coding assistant. How can I help you today?";
    } else if (message.toLowerCase().includes('what is claw')) {
      reply = "Claw AI is an advanced coding assistant that helps with:\n• Code analysis and debugging\n• Writing and refactoring code\n• Understanding complex systems\n• Planning implementations\n• Best practices and patterns\n\nAsk me anything coding-related!";
    } else if (message.toLowerCase().includes('help')) {
      reply = "I can help you with:\n• 💻 Code writing and refactoring\n• 🐛 Debugging issues\n• 📚 Explaining concepts\n• 🏗️ Architecture design\n• 🧪 Testing strategies\n• 📖 Documentation\n\nWhat would you like assistance with?";
    } else if (message.toLowerCase().includes('thank')) {
      reply = "You're welcome! 😊 Feel free to ask if you need more help.";
    } else {
      reply = `I received your message: "${message}"\n\nI'm currently in demo mode. To enable full AI capabilities, integrate with an LLM backend like:\n• Claude API\n• OpenAI API\n• Ollama (local)\n• Other LLM providers\n\nFor now, try asking me:\n• "What is Claw?"\n• "Hello"\n• "Help"`;
    }

    res.status(200).json({ reply });
  } catch (error) {
    console.error('Chat API Error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
}

// Main handler
module.exports = async (req, res) => {
  // Handle API routes
  if (req.url === '/api/chat' || req.url.startsWith('/api/chat')) {
    return handleChat(req, res);
  }

  // Serve index.html for all other routes (SPA routing)
  try {
    const indexPath = path.join(process.cwd(), 'index.html');
    const content = fs.readFileSync(indexPath, 'utf-8');
    res.setHeader('Content-Type', 'text/html; charset=utf-8');
    res.status(200).send(content);
  } catch (error) {
    console.error('Error serving index.html:', error);
    res.status(404).send('<!DOCTYPE html><html><body><h1>404 - Not Found</h1></body></html>');
  }
};

