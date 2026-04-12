module.exports = (req, res) => {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Content-Type', 'application/json');

  if (req.method === 'POST') {
    const { message } = req.body;
    let reply = 'Hello!';
    
    if (message && message.toLowerCase().includes('hello')) {
      reply = "Hi! I'm Claw AI. Ask me about coding!";
    } else if (message && message.toLowerCase().includes('help')) {
      reply = "I can help with coding, debugging, and architecture!";
    }
    
    return res.status(200).json({ reply });
  }
  
  res.status(405).json({ error: 'Method not allowed' });
};
